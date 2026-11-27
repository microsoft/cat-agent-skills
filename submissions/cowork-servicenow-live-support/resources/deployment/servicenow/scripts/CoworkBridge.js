var CoworkBridge = Class.create();
CoworkBridge.prototype = {
    initialize: function () {},

    handle: function (operation, request, response) {
        var command = null;
        try {
            var principal = String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''));
            if (!/^[0-9a-f]{32}$/.test(principal))
                this._throw(503, 'configuration_required');
            if (String(gs.getUserID()) !== principal)
                this._throw(403, 'integration_principal_required');
            if (operation === 'open_chat' && String(gs.getProperty('cowork_bridge.enabled', 'false')) !== 'true') {
                    return this._respond(response, 200, {
                        conversation_sys_id: '', interaction_number: '', unavailable: true,
                        message: String(gs.getProperty('cowork_bridge.unavailable_message',
                            'Live chat is unavailable. Please use your IT support portal.')).substring(0, 1000)
                    });
            }

            var body = request.body && request.body.data;
            if (!body || typeof body !== 'object' || Array.isArray(body))
                this._throw(400, 'invalid_body');
            var input = this._validate(operation, body);
            var config = operation === 'open_chat' ? this._config(principal) : null;
            var owned = operation === 'open_chat' ? null : this._owned(input.conversation_sys_id);
            var key = operation === 'open_chat' ? 'open:' + input.client_session_id :
                (operation === 'send_message' ? 'send:' : 'close:') + input.conversation_sys_id +
                (input.client_message_id ? ':' + input.client_message_id : '');
            var hash = String(new GlideDigest().getSHA256Hex(JSON.stringify(input)));
            command = this._reserve(key, hash);
            if (command.cached)
                return this._respond(response, 200, command.cached);

            var result;
            if (operation === 'open_chat') result = this._open(input, config, command.row);
            else if (operation === 'send_message') result = this._send(input, owned);
            else result = this._close(owned);
            command.row.setValue('u_result', JSON.stringify(result));
            command.row.setValue('u_status', 'completed');
            if (owned) command.row.setValue('u_conversation', input.conversation_sys_id);
            this._update(command.row);
            return this._respond(response, 200, result);
        } catch (error) {
            // Never persist exception text: platform errors can contain message bodies or credentials.
            var code = error.coworkCode || 'platform_operation_failed';
            if (command && command.row && !command.cached) {
                try {
                    command.row.setValue('u_status', 'failed');
                    command.row.setValue('u_error', code);
                    command.row.update();
                } catch (ignored) {}
                return this._respond(response, 409, {
                    error: 'command_ambiguous',
                    message: 'Command may have partially executed. Reconcile its ledger before retrying.'
                });
            }
            return this._respond(response, error.coworkStatus || 500, { error: code });
        }
    },

    _validate: function (operation, body) {
        var input;
        if (operation === 'open_chat') {
            if (body.bot !== 'cowork_mcp') this._throw(400, 'invalid_bot');
            input = {
                email: this._email(body.email),
                summary: this._string(body.summary, 1, 4000, 'summary'),
                lang: body.lang === undefined ? '' : this._string(body.lang, 0, 32, 'lang'),
                client_session_id: this._clientId(body.client_session_id),
                bot: 'cowork_mcp'
            };
            if (input.lang && !/^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8}){0,3}$/.test(input.lang))
                this._throw(400, 'invalid_lang');
            input.lang = input.lang.toLowerCase();
        } else if (operation === 'send_message' || operation === 'close_chat') {
            input = { conversation_sys_id: this._sysId(body.conversation_sys_id) };
            if (operation === 'send_message') {
                input.text = this._string(body.text, 1, 8000, 'text');
                input.email = this._email(body.email);
                input.client_message_id = this._clientId(body.client_message_id);
            } else if (body.client_message_id !== undefined) {
                input.client_message_id = this._clientId(body.client_message_id);
            }
        } else this._throw(404, 'unknown_operation');
        return input;
    },

    _config: function (principal) {
        var names = ['queue_sys_id', 'service_channel_sys_id', 'vendor_sys_id', 'virtual_agent_user_sys_id'];
        var config = { principal: principal };
        for (var i = 0; i < names.length; i++) {
            var value = String(gs.getProperty('cowork_bridge.' + names[i], ''));
            if (!/^[0-9a-f]{32}$/.test(value)) this._throw(503, 'routing_configuration_required');
            config[names[i]] = value;
        }
        var queue = this._get('awa_queue', config.queue_sys_id);
        var channel = this._get('awa_service_channel', config.service_channel_sys_id);
        var user = this._get('sys_user', principal);
        var va = this._get('sys_user', config.virtual_agent_user_sys_id);
        this._get('sys_cs_vendor', config.vendor_sys_id);
        if (!this._true(queue.getValue('active')) || !this._true(channel.getValue('active')) ||
            !this._true(user.getValue('active')) || !this._true(va.getValue('active')) ||
            String(queue.getValue('service_channel')) !== config.service_channel_sys_id ||
            config.virtual_agent_user_sys_id === principal)
            this._throw(503, 'routing_configuration_invalid');
        // Callback routing must be complete before reserving a command or creating chat records.
        new CoworkBridgeWebhook().configuration();
        return config;
    },

    _reserve: function (key, hash) {
        var existing = this._command(key);
        if (existing) return this._replay(existing, hash);
        var row = new GlideRecord('u_cowork_command');
        row.initialize();
        row.setValue('u_key', key);
        row.setValue('u_request_hash', hash);
        row.setValue('u_status', 'pending');
        var id = null;
        try { id = row.insert(); } catch (ignored) {}
        if (!id) {
            // The unique database index, not this preceding lookup, wins a concurrent reservation.
            existing = this._command(key);
            if (existing) return this._replay(existing, hash);
            this._throw(409, 'command_reservation_unconfirmed');
        }
        return { row: row };
    },

    _command: function (key) {
        var row = new GlideRecord('u_cowork_command');
        row.addQuery('u_key', key);
        row.setLimit(1);
        row.query();
        return row.next() ? row : null;
    },

    _replay: function (row, hash) {
        if (String(row.getValue('u_request_hash')) !== hash)
            this._throw(409, 'idempotency_key_reused');
        if (String(row.getValue('u_status')) !== 'completed')
            this._throw(409, 'command_ambiguous');
        var result;
        try { result = JSON.parse(String(row.getValue('u_result'))); } catch (ignored) {}
        if (!result || typeof result !== 'object') this._throw(409, 'command_ambiguous');
        var key = String(row.getValue('u_key'));
        if ((key.indexOf('open:') === 0 &&
            (result.unavailable !== false || !/^[0-9a-f]{32}$/.test(String(result.conversation_sys_id || '')) ||
                typeof result.interaction_number !== 'string' || !result.interaction_number)) ||
            (key.indexOf('send:') === 0 &&
                !((result.sent === true && result.closed === false) || (result.sent === false && result.closed === true))) ||
            (key.indexOf('close:') === 0 && result.closed !== true))
            this._throw(409, 'command_ambiguous');
        return { cached: result };
    },

    _open: function (input, config, command) {
        var user = new GlideRecord('sys_user');
        user.addQuery('email', input.email);
        user.addActiveQuery();
        user.setLimit(2);
        user.query();
        if (!user.next()) this._throw(404, 'requester_not_found');
        var userId = String(user.getUniqueValue());
        if (user.next()) this._throw(409, 'requester_not_unique');
        if (userId === config.principal || userId === config.virtual_agent_user_sys_id)
            this._throw(400, 'requester_must_be_end_user');

        var prior = new GlideRecord('interaction');
        prior.addQuery('u_cowork_session_id', input.client_session_id);
        prior.setLimit(1);
        prior.query();
        if (prior.next()) this._throw(409, 'session_already_exists');
        var conversationId = String(sn_cs.VASystemObject.createConversation(userId) || '');
        if (!/^[0-9a-f]{32}$/.test(conversationId)) this._throw(500, 'conversation_creation_failed');
        command.setValue('u_conversation', conversationId);
        this._update(command);
        var conversation = this._get('sys_cs_conversation', conversationId);
        var interaction = this._interaction(conversationId);
        if (!interaction) this._throw(500, 'interaction_creation_failed');
        if ((interaction.isValidField('u_copilot_upn') && interaction.getValue('u_copilot_upn')) ||
            (interaction.isValidField('u_bridge_session_id') && interaction.getValue('u_bridge_session_id')) ||
            interaction.getValue('u_cowork_session_id'))
            this._throw(409, 'interaction_not_isolated');

        // Persist the correlation key before any explicit message insert or AWA insert/update.
        interaction.setValue('u_cowork_session_id', input.client_session_id);
        interaction.setValue('u_cowork_upn', input.email);
        interaction.setValue('assigned_to', '');
        interaction.setValue('opened_for', userId);
        interaction.setValue('short_description', 'Copilot Cowork: ' + input.summary.substring(0, 140));
        interaction.setValue('direction', 'inbound');
        interaction.setValue('type', 'chat');
        interaction.setValue('state', 'new');
        if (input.lang) interaction.setValue('user_language', input.lang);
        this._update(interaction);
        interaction = this._get('interaction', String(interaction.getUniqueValue()));
        if (String(interaction.getValue('u_cowork_session_id')) !== input.client_session_id ||
            !interaction.getValue('number')) this._throw(500, 'correlation_not_persisted');

        var device = String(conversation.getValue('current_device') || '');
        var consumer = String(conversation.getValue('consumer') || '');
        var account = String(conversation.getValue('consumer_account') || '');
        if (!device || !consumer || !account) this._throw(500, 'conversation_context_incomplete');
        conversation.setValue('state', 'chatInProgress');
        conversation.setValue('live_agent_transfer_time', new GlideDateTime());
        conversation.setValue('opened_for', userId);
        conversation.setValue('title', 'Copilot Cowork: ' + input.summary.substring(0, 80));
        this._update(conversation);

        var sessionId = this._insert('sys_cs_session', {
            consumer: consumer, consumer_account: account, vendor: config.vendor_sys_id,
            device_id: device, device_type: 'mweb', direction: 'inbound', interaction: 'QnA',
            start_time: new GlideDateTime()
        });
        this._insert('sys_cs_session_binding', {
            session: sessionId, system_topic: conversationId, topic: conversationId,
            channel_type: 'AMB', channel_id: '/cs/messages/' + sessionId,
            client_connected: true, online: true, guest: false,
            last_client_activity_time: new GlideDateTime()
        });
        var first = 'Escalated from Copilot Cowork.\nReason: ' + input.summary +
            (input.lang ? '\nRequester language: ' + input.lang : '');
        this._insert('sys_cs_message', {
            conversation: conversationId, session: sessionId, consumer: consumer,
            consumer_account: account, vendor: config.vendor_sys_id, direction: 'inbound',
            message_type: 'text', q_data_message_type: 'consumerTextMessage',
            payload: first, message_size: first.length, sender: userId,
            recipient: config.virtual_agent_user_sys_id, status: 'received',
            send_time: new GlideDateTime(), receive_time: new GlideDateTime(),
            task: String(interaction.getUniqueValue())
        });
        this._ensureWorkItem(String(interaction.getUniqueValue()), config.queue_sys_id);
        return {
            conversation_sys_id: conversationId,
            interaction_number: String(interaction.getValue('number')), unavailable: false
        };
    },

    _ensureWorkItem: function (interactionId, queueId) {
        var existing = this._activeWorkItem(interactionId, queueId);
        if (existing) return;
        var row = new GlideRecord('awa_work_item');
        row.initialize();
        row.setValue('document_id', interactionId);
        row.setValue('document_table', 'interaction');
        row.setValue('queue', queueId);
        row.setValue('active', true);
        var id = row.insert();
        if (!id) {
            if (this._activeWorkItem(interactionId, queueId)) return;
            this._throw(500, 'work_item_creation_failed');
        }
        var work = this._get('awa_work_item', String(id));
        work.setValue('state', 'queued');
        this._update(work);
    },

    _activeWorkItem: function (interactionId, queueId) {
        var row = new GlideRecord('awa_work_item');
        row.addQuery('document_id', interactionId);
        row.addQuery('active', true);
        row.setLimit(2);
        row.query();
        if (!row.next()) return false;
        if (String(row.getValue('queue')) !== queueId ||
            ['queued', 'pending_accept', 'accepted'].indexOf(String(row.getValue('state'))) < 0)
            this._throw(409, 'work_item_routing_mismatch');
        if (row.next()) this._throw(409, 'multiple_active_work_items');
        return true;
    },

    _owned: function (id) {
        var conversation = this._get('sys_cs_conversation', id);
        var interaction = this._interaction(id);
        if (!interaction || !/^[A-Za-z0-9-]{16,80}$/.test(String(interaction.getValue('u_cowork_session_id') || '')) ||
            !interaction.getValue('u_cowork_upn') ||
            (interaction.isValidField('u_copilot_upn') && interaction.getValue('u_copilot_upn')) ||
            (interaction.isValidField('u_bridge_session_id') && interaction.getValue('u_bridge_session_id')))
            this._throw(403, 'not_a_cowork_conversation');
        return { conversation: conversation, interaction: interaction };
    },

    _send: function (input, owned) {
        if (this._closed(owned)) return { sent: false, closed: true };
        var requester = this._get('sys_user', String(owned.interaction.getValue('opened_for')));
        var display = String(requester.getDisplayValue() || 'Requester').replace(/[\r\n]/g, ' ').substring(0, 200);
        // AgentChat uses the authenticated, dedicated integration user. No impersonation or email-derived name.
        var sent = sn_cs.AgentChatScriptObject.send(input.conversation_sys_id,
            display + ' (via Copilot Cowork): ' + input.text, null, false);
        if (sent === false) this._throw(500, 'chat_send_failed');
        var binding = new GlideRecord('sys_cs_session_binding');
        binding.addQuery('system_topic', input.conversation_sys_id);
        binding.addQuery('topic', input.conversation_sys_id);
        binding.query();
        while (binding.next()) {
            binding.setValue('last_client_activity_time', new GlideDateTime());
            binding.setValue('online', true);
            binding.setValue('client_connected', true);
            this._update(binding);
        }
        return { sent: true, closed: false };
    },

    _close: function (owned) {
        // Preserve Cowork metadata and business-rule execution: our closed callback must still fire.
        if (String(owned.interaction.getValue('state')).indexOf('closed') !== 0) {
            owned.interaction.setValue('state', 'closed_complete');
            this._update(owned.interaction);
        }
        if (String(owned.conversation.getValue('state')).indexOf('closed') !== 0) {
            owned.conversation.setValue('state', 'closed');
            this._update(owned.conversation);
        }
        return { closed: true };
    },

    _closed: function (owned) {
        return String(owned.interaction.getValue('state')).indexOf('closed') === 0 ||
            String(owned.conversation.getValue('state')).indexOf('closed') === 0;
    },

    _interaction: function (id) {
        var row = new GlideRecord('interaction');
        row.addQuery('channel_metadata_document', id);
        row.setLimit(2);
        row.query();
        if (!row.next()) return null;
        var sid = String(row.getUniqueValue());
        if (row.next()) this._throw(409, 'ambiguous_interaction');
        return this._get('interaction', sid);
    },

    _get: function (table, id) {
        var row = new GlideRecord(table);
        if (!row.get(id)) this._throw(404, 'required_record_not_found');
        return row;
    },

    _insert: function (table, values) {
        var row = new GlideRecord(table);
        row.initialize();
        for (var field in values)
            if (Object.prototype.hasOwnProperty.call(values, field)) row.setValue(field, values[field]);
        var id = row.insert();
        if (!id) this._throw(500, 'record_insert_failed');
        return String(id);
    },

    _update: function (row) {
        if (!row.update()) this._throw(500, 'record_update_failed');
    },

    _string: function (value, min, max, name) {
        if (typeof value !== 'string' || value.length < min || value.length > max ||
            value.indexOf('\u0000') !== -1 || (min > 0 && !/\S/.test(value)))
            this._throw(400, 'invalid_' + name);
        return value;
    },

    _email: function (value) {
        var email = this._string(value, 3, 254, 'email').toLowerCase();
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) this._throw(400, 'invalid_email');
        return email;
    },

    _clientId: function (value) {
        if (typeof value !== 'string' || !/^[A-Za-z0-9-]{16,80}$/.test(value))
            this._throw(400, 'invalid_client_id');
        return value;
    },

    _sysId: function (value) {
        if (typeof value !== 'string' || !/^[0-9a-f]{32}$/.test(value))
            this._throw(400, 'invalid_conversation_sys_id');
        return value;
    },

    _true: function (value) { return String(value) === 'true' || String(value) === '1'; },
    _throw: function (status, code) {
        var error = new Error(code);
        error.coworkStatus = status;
        error.coworkCode = code;
        throw error;
    },
    _respond: function (response, status, body) {
        response.setStatus(status);
        response.setBody(body);
    },
    type: 'CoworkBridge'
};
