var CoworkBridgeOutbox = Class.create();
CoworkBridgeOutbox.prototype = {
    initialize: function () {},

    enqueue: function (body, interactionId) {
        var snapshot = this._snapshot(body);
        var owner = new GlideRecord('interaction');
        if (!owner.get(interactionId) || !new CoworkBridgeWebhook()._isCowork(owner) ||
            String(owner.getValue('u_cowork_session_id')) !== snapshot.client_session_id ||
            String(owner.getValue('number')) !== snapshot.interaction_number)
            throw new Error('cowork_outbox_owner_mismatch');
        var payload = JSON.stringify(snapshot);
        var hash = String(new GlideDigest().getSHA256Hex(payload));
        var existing = this._find(snapshot.event_id);
        if (existing) return this._duplicate(existing, hash);
        var row = new GlideRecord('u_cowork_outbox');
        row.initialize();
        row.setValue('u_event_id', snapshot.event_id);
        row.setValue('u_event', snapshot.event);
        row.setValue('u_client_session_id', snapshot.client_session_id);
        row.setValue('u_interaction', interactionId);
        if (snapshot.message_sys_id) row.setValue('u_message', snapshot.message_sys_id);
        row.setValue('u_payload', payload);
        row.setValue('u_payload_hash', hash);
        row.setValue('u_status', 'pending');
        row.setValue('u_attempts', 0);
        row.setValue('u_next_attempt_at', new GlideDateTime());
        row.setValue('u_requires_attention', false);
        var id = null;
        try { id = row.insert(); } catch (ignored) {}
        if (!id) {
            existing = this._find(snapshot.event_id);
            if (existing) return this._duplicate(existing, hash);
            gs.error('Cowork outbox enqueue failed; operator reconciliation required.');
            throw new Error('cowork_outbox_enqueue_failed');
        }
        // Persistence always precedes OAuth/HTTP. A failure or crash leaves a retriable row.
        this._safeAttempt(String(id));
        return true;
    },

    retry: function () {
        if (!this._enabled()) return 0;
        var count = 0;
        var due = new GlideRecord('u_cowork_outbox');
        due.addQuery('u_status', 'IN', 'pending,retry');
        due.addQuery('u_next_attempt_at', '<=', new GlideDateTime());
        due.orderBy('u_next_attempt_at');
        due.setLimit(20);
        due.query();
        while (due.next()) {
            this._safeAttempt(String(due.getUniqueValue()));
            count++;
        }
        var expired = new GlideRecord('u_cowork_outbox');
        expired.addQuery('u_status', 'sending');
        expired.addQuery('u_lease_until', '<=', new GlideDateTime());
        expired.orderBy('u_lease_until');
        expired.setLimit(20);
        expired.query();
        while (expired.next()) {
            this._safeAttempt(String(expired.getUniqueValue()));
            count++;
        }
        var attention = new GlideRecord('u_cowork_outbox');
        attention.addQuery('u_requires_attention', true);
        attention.setLimit(1);
        attention.query();
        if (attention.next())
            gs.warn('Cowork outbox requires operator attention; inspect u_requires_attention=true. No events were discarded.');
        return count;
    },

    attempt: function (id) {
        if (!this._enabled()) return false;
        var row = this._claim(id);
        if (!row) return false;
        var errorCode = 'webhook_delivery_failed';
        var delivered = false;
        try {
            var payload = String(row.getValue('u_payload') || '');
            if (String(new GlideDigest().getSHA256Hex(payload)) !== String(row.getValue('u_payload_hash')))
                throw new Error('invalid_payload');
            var body = this._snapshot(JSON.parse(payload));
            if (body.event_id !== String(row.getValue('u_event_id')) ||
                body.client_session_id !== String(row.getValue('u_client_session_id')))
                throw new Error('invalid_payload');
            if (Number(row.getValue('u_attempts')) > 8) errorCode = 'retry_limit_reached';
            else delivered = new CoworkBridgeWebhook().deliver(body);
        } catch (ignored) {
            errorCode = 'outbox_payload_or_delivery_failed';
        }
        return this._finish(row, delivered, errorCode);
    },

    _safeAttempt: function (id) {
        try { return this.attempt(id); }
        catch (ignored) {
            // Do not roll back a successfully enqueued snapshot just because best-effort delivery failed.
            gs.warn('Cowork outbox attempt incomplete; retained event requires retry or lease recovery.');
            return false;
        }
    },

    _claim: function (id) {
        var row = new GlideRecord('u_cowork_outbox');
        if (!row.get(id)) return null;
        var status = String(row.getValue('u_status'));
        var now = new GlideDateTime();
        var due = status === 'sending' ? row.getValue('u_lease_until') : row.getValue('u_next_attempt_at');
        if (['pending', 'retry', 'sending'].indexOf(status) < 0 || !due ||
            Number(new GlideDateTime(String(due)).getNumericValue()) > Number(now.getNumericValue())) return null;
        var token = String(gs.generateGUID());
        if (!/^[0-9a-f]{32}$/.test(token)) throw new Error('cowork_outbox_lease_token_invalid');
        var lease = new GlideDateTime();
        lease.addSeconds(600);
        // Conditional UPDATE is the atomic lease; read-then-update alone is not safe across nodes.
        var claim = new GlideRecord('u_cowork_outbox');
        claim.addQuery('sys_id', id);
        claim.addQuery('sys_mod_count', row.getValue('sys_mod_count'));
        claim.addQuery('u_status', status);
        claim.addQuery(status === 'sending' ? 'u_lease_until' : 'u_next_attempt_at', '<=', now);
        claim.setValue('u_lease_token', token);
        claim.setValue('u_lease_until', lease);
        claim.setValue('u_status', 'sending');
        claim.setValue('u_attempts', Number(row.getValue('u_attempts') || 0) + 1);
        claim.updateMultiple();
        if (!row.get(id) || String(row.getValue('u_lease_token')) !== token) return null;
        return row;
    },

    _finish: function (row, delivered, errorCode) {
        var attempts = Number(row.getValue('u_attempts'));
        var status = delivered ? 'delivered' : (attempts >= 8 ? 'dead_letter' : 'retry');
        var update = new GlideRecord('u_cowork_outbox');
        update.addQuery('sys_id', String(row.getUniqueValue()));
        update.addQuery('u_status', 'sending');
        update.addQuery('u_lease_token', String(row.getValue('u_lease_token')));
        update.setValue('u_status', status);
        update.setValue('u_last_error', delivered ? '' : errorCode);
        update.setValue('u_lease_token', '');
        update.setValue('u_lease_until', '');
        if (status === 'retry') {
            var next = new GlideDateTime();
            next.addSeconds(Math.min(3600, 30 * Math.pow(2, attempts - 1)));
            update.setValue('u_next_attempt_at', next);
        } else update.setValue('u_next_attempt_at', '');
        if (delivered) update.setValue('u_delivered_at', new GlideDateTime());
        if (status === 'dead_letter') update.setValue('u_requires_attention', true);
        update.updateMultiple();
        var verified = new GlideRecord('u_cowork_outbox');
        if (!verified.get(String(row.getUniqueValue())) || String(verified.getValue('u_status')) !== status) return false;
        if (status === 'dead_letter') {
            gs.error('Cowork outbox dead letter retained; event_id=' + String(row.getValue('u_event_id')));
            // Event parameters are correlation metadata only; never include payload, URLs or tokens.
            try { gs.eventQueue('cowork_bridge.outbox.dead_letter', verified, String(row.getValue('u_event_id')), errorCode); }
            catch (ignored) { gs.error('Cowork outbox alert failed; inspect u_requires_attention=true.'); }
        }
        return delivered;
    },

    _duplicate: function (row, hash) {
        if (String(row.getValue('u_payload_hash')) !== hash) {
            // Do not overwrite a prior approved event snapshot merely because its ID was reused.
            var alert = new GlideRecord('u_cowork_outbox');
            alert.addQuery('sys_id', String(row.getUniqueValue()));
            alert.setValue('u_requires_attention', true);
            alert.updateMultiple();
            gs.error('Cowork outbox event-ID payload conflict; operator reconciliation required.');
            return false;
        }
        return true;
    },

    _snapshot: function (body) {
        if (!body || body.bot !== 'cowork_mcp' || ['accepted', 'message', 'closed'].indexOf(body.event) < 0 ||
            typeof body.client_session_id !== 'string' || !/^[A-Za-z0-9-]{16,80}$/.test(body.client_session_id) ||
            typeof body.interaction_number !== 'string' || !body.interaction_number || body.interaction_number.length > 80 ||
            typeof body.text !== 'string' || body.text.length > 8000 ||
            typeof body.agent_name !== 'string' || body.agent_name.length > 200 ||
            typeof body.event_id !== 'string')
            throw new Error('cowork_outbox_invalid_event');
        if (body.event === 'message') {
            if (!/^[0-9a-f]{32}$/.test(body.event_id) || body.message_sys_id !== body.event_id)
                throw new Error('cowork_outbox_invalid_event');
        } else if (!(new RegExp('^[0-9a-f]{32}:' + body.event + ':[A-Za-z0-9 :.-]{1,64}$')).test(body.event_id))
            throw new Error('cowork_outbox_invalid_event');
        var snapshot = {
            event: body.event, bot: 'cowork_mcp', client_session_id: body.client_session_id,
            interaction_number: body.interaction_number, text: body.text, agent_name: body.agent_name,
            event_id: body.event_id
        };
        if (body.event === 'message') snapshot.message_sys_id = body.message_sys_id;
        return snapshot;
    },

    _find: function (eventId) {
        var row = new GlideRecord('u_cowork_outbox');
        row.addQuery('u_event_id', eventId);
        row.setLimit(1);
        row.query();
        return row.next() ? row : null;
    },
    _enabled: function () {
        return String(gs.getProperty('cowork_bridge.outbox_delivery_enabled', 'false')) === 'true';
    },
    type: 'CoworkBridgeOutbox'
};
