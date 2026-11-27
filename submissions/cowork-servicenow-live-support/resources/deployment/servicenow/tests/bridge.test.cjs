'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const sid = digit => digit.repeat(32);
const ids = {
    principal: sid('1'), requester: sid('2'), agent: sid('3'), queue: sid('4'),
    channel: sid('5'), vendor: sid('6'), va: sid('7'), conversation: sid('8'), interaction: sid('9')
};
const session = 'cowork-session-000001';
const messageId = 'cowork-message-000001';
const openBody = { email: 'person@example.test', summary: 'Need support', lang: 'en', client_session_id: session, bot: 'cowork_mcp' };
const legacyFields = ['u_copilot_upn', 'u_bridge_session_id'];
const legacySchemas = [[], [legacyFields[0]], [legacyFields[1]], legacyFields];

function fixture(overrides = {}, options = {}) {
    const state = {
        tables: {}, inserts: [], updates: [], sends: [], requests: [], tokenCalls: [], warnings: [],
        next: 100, caller: ids.principal, failInsert: '', failUpdate: '', tokenError: '', token: 'test-access-token',
        httpStatus: 200, createCalls: 0, throwAfterSend: false, race: false,
        now: Date.parse('2026-10-16T14:00:00Z'), events: [], beforeConditionalUpdate: null,
        createdInteractionValues: {}, invalidFieldAccesses: [], legacyReads: [], legacyWrites: []
    };
    const schema = { interaction: new Set([
        'sys_id', 'sys_mod_count', 'sys_updated_on', 'state', 'assigned_to', 'channel_metadata_document',
        'opened_for', 'number', 'short_description', 'direction', 'type', 'user_language',
        'u_cowork_session_id', 'u_cowork_upn', ...(options.legacyFields ?? legacyFields)
    ]) };
    function checkField(record, name, write) {
        if (schema[record.table] && !record.isValidField(name)) {
            state.invalidFieldAccesses.push(record.table + '.' + name);
            throw new Error('Unknown field: ' + record.table + '.' + name);
        }
        if (record.table === 'interaction' && legacyFields.includes(name))
            (write ? state.legacyWrites : state.legacyReads).push(name);
    }
    const properties = {
        'cowork_bridge.enabled': 'true',
        'cowork_bridge.outbox_delivery_enabled': 'true',
        'cowork_bridge.integration_user_sys_id': ids.principal,
        'cowork_bridge.queue_sys_id': ids.queue,
        'cowork_bridge.service_channel_sys_id': ids.channel,
        'cowork_bridge.vendor_sys_id': ids.vendor,
        'cowork_bridge.virtual_agent_user_sys_id': ids.va,
        'cowork_bridge.webhook_url': 'https://backend.example.test/api/livechat/sn',
        'cowork_bridge.webhook_oauth_entity': 'Cowork dedicated OAuth provider',
        'cowork_bridge.webhook_oauth_scope': 'api://cowork-prototype/.default',
        ...overrides
    };
    function put(table, values) {
        const row = { sys_id: (++state.next).toString(16).padStart(32, '0'), sys_mod_count: '0', ...values };
        (state.tables[table] ||= []).push(row);
        return row;
    }
    function GlideRecord(table) {
        this.table = table; this.filters = []; this.results = []; this.index = -1; this.row = {}; this.limit = Infinity;
    }
    function matches(row, filters) {
        return filters.every(([key, operator, value]) => {
            const current = String(row[key] ?? '');
            if (operator === '<=') return current <= value;
            if (operator === 'IN') return value.split(',').includes(current);
            return current === value;
        });
    }
    GlideRecord.prototype = {
        isValidField(name) { return !!schema[this.table]?.has(name); },
        initialize() { this.row = {}; },
        setValue(name, value) {
            checkField(this, name, true);
            this.row[name] = value && typeof value === 'object' ? String(value) : value;
        },
        getValue(name) {
            checkField(this, name, false);
            const v = this.row?.[name]; return v === undefined || v === null ? '' : String(v);
        },
        getUniqueValue() { return this.row?.sys_id || ''; },
        getDisplayValue(field) {
            if (field === 'assigned_to') return state.tables.sys_user.find(row => row.sys_id === this.row.assigned_to)?.name || '';
            return this.row.name || this.row.number || '';
        },
        get(key, value) {
            if (value === undefined) { value = key; key = 'sys_id'; }
            const found = (state.tables[this.table] || []).find(row => String(row[key]) === String(value));
            this.row = found ? { ...found } : null;
            return !!found;
        },
        addQuery(key, operator, value) {
            if (value === undefined) { value = operator; operator = '='; }
            this.filters.push([key, operator, String(value)]);
        },
        addActiveQuery() { this.addQuery('active', 'true'); },
        setLimit(limit) { this.limit = limit; },
        orderBy(field) { this.order = field; },
        query() {
            this.results = (state.tables[this.table] || [])
                .filter(row => matches(row, this.filters));
            if (this.order) this.results.sort((left, right) => String(left[this.order] || '').localeCompare(String(right[this.order] || '')));
            this.results = this.results.slice(0, this.limit);
            this.index = -1;
        },
        next() { const row = this.results[++this.index]; this.row = row ? { ...row } : null; return !!row; },
        insert() {
            if (state.failInsert === this.table) return null;
            if (this.table === 'u_cowork_command') {
                if (state.race) {
                    state.race = false;
                    put(this.table, { ...this.row, u_status: 'pending' });
                    return null;
                }
                if (this.table === 'u_cowork_outbox' &&
                    (state.tables[this.table] || []).some(row => row.u_event_id === this.row.u_event_id)) return null;
                if ((state.tables[this.table] || []).some(row => row.u_key === this.row.u_key)) return null;
            }
            if (this.table === 'awa_work_item') {
                assert.equal(state.tables.interaction.find(row => row.sys_id === this.row.document_id).u_cowork_session_id, session);
                state.correlationBeforeAwa = true;
            }
            const row = put(this.table, this.row);
            this.row = { ...row };
            state.inserts.push({ table: this.table, ...row });
            return row.sys_id;
        },
        update() {
            if (state.failUpdate === this.table) return null;
            const stored = (state.tables[this.table] || []).find(row => row.sys_id === this.row.sys_id);
            if (!stored) return null;
            const previous = { ...stored };
            Object.assign(stored, this.row, { sys_mod_count: String(Number(stored.sys_mod_count || 0) + 1) });
            this.row = { ...stored };
            state.updates.push({ table: this.table, ...stored });
            if (this.table === 'interaction' && state.autoQueue && stored.u_cowork_session_id &&
                !(state.tables.awa_work_item || []).some(row => row.document_id === stored.sys_id)) {
                put('awa_work_item', { document_id: stored.sys_id, queue: state.autoQueue, state: 'queued', active: true });
            }
            if (this.table === 'interaction' && state.fireCallbacks) {
                const old = new GlideRecord('interaction'); old.row = previous;
                new context.CoworkBridgeWebhook().interaction(this, old);
            }
            return stored.sys_id;
        },
        updateMultiple() {
            const hook = state.beforeConditionalUpdate;
            if (hook) { state.beforeConditionalUpdate = null; hook(this); }
            if (state.failUpdate === this.table) return;
            for (const stored of state.tables[this.table] || []) {
                if (matches(stored, this.filters)) {
                    Object.assign(stored, this.row, { sys_mod_count: String(Number(stored.sys_mod_count || 0) + 1) });
                    state.updates.push({ table: this.table, ...stored });
                }
            }
        }
    };
    put('sys_user', { sys_id: ids.principal, active: true, name: 'Dedicated Cowork account' });
    put('sys_user', { sys_id: ids.requester, active: true, email: openBody.email, name: 'Actual Requester' });
    put('sys_user', { sys_id: ids.agent, active: true, name: 'Actual Agent' });
    put('sys_user', { sys_id: ids.va, active: true, name: 'Virtual Agent' });
    put('awa_queue', { sys_id: ids.queue, active: true, service_channel: ids.channel });
    put('awa_service_channel', { sys_id: ids.channel, active: true });
    put('sys_cs_vendor', { sys_id: ids.vendor });

    const context = vm.createContext({
        Class: { create: () => function () { this.initialize?.(); } },
        GlideRecord,
        GlideDateTime: function (value) {
            this.time = value ? Date.parse(String(value).replace(' ', 'T') + 'Z') : state.now;
            this.toString = () => new Date(this.time).toISOString().slice(0, 19).replace('T', ' ');
            this.getNumericValue = () => this.time;
            this.addSeconds = seconds => { this.time += seconds * 1000; };
        },
        GlideDigest: function () { this.getSHA256Hex = value => crypto.createHash('sha256').update(value).digest('hex'); },
        gs: {
            getProperty: (name, fallback) => Object.hasOwn(properties, name) ? properties[name] : fallback,
            getUserID: () => state.caller,
            warn: message => state.warnings.push(message),
            error: message => state.warnings.push(message),
            generateGUID: () => (++state.next).toString(16).padStart(32, '0'),
            eventQueue: (name, row, id, error) => state.events.push({ name, id, error })
        },
        sn_cs: {
            VASystemObject: {
                createConversation(userId) {
                    state.createCalls++;
                    put('sys_cs_conversation', {
                        sys_id: ids.conversation, opened_for: userId, current_device: 'test-device',
                        consumer: 'test-consumer', consumer_account: 'test-account'
                    });
                    put('interaction', {
                        sys_id: ids.interaction, channel_metadata_document: ids.conversation,
                        opened_for: userId, assigned_to: ids.va, state: 'new', number: 'TEST0001',
                        ...state.createdInteractionValues
                    });
                    return ids.conversation;
                }
            },
            AgentChatScriptObject: {
                send(conversation, text) {
                    state.sends.push({ conversation, text });
                    if (state.throwAfterSend) throw new Error('Sensitive transcript in an exception');
                }
            }
        },
        sn_auth: {
            GlideOAuthClient: function () {
                this.requestToken = (entity, body) => {
                    state.tokenCalls.push({ entity, body });
                    return {
                        getErrorMessage: () => state.tokenError,
                        getToken: () => state.token ? { getAccessToken: () => state.token, getExpiresIn: () => 3600 } : null
                    };
                };
            }
        },
        sn_ws: {
            RESTMessageV2: function () {
                const request = { headers: {} };
                this.setEndpoint = value => { request.url = value; };
                this.setHttpMethod = value => { request.method = value; };
                this.setHttpTimeout = value => { request.timeout = value; };
                this.setLogLevel = value => { request.logLevel = value; };
                this.setRequestHeader = (name, value) => { request.headers[name] = value; };
                this.setRequestBody = value => { request.body = JSON.parse(value); };
                this.execute = () => {
                    state.requests.push(request);
                    return { getStatusCode: () => state.httpStatus, haveError: () => false };
                };
            }
        }
    });
    for (const name of ['CoworkBridgeOutbox', 'CoworkBridgeWebhook', 'CoworkBridge'])
        vm.runInContext(fs.readFileSync(path.join(root, 'scripts', name + '.js'), 'utf8'), context);
    function invoke(operation, body) {
        const response = { setStatus(value) { this.status = value; }, setBody(value) { this.body = JSON.parse(JSON.stringify(value)); } };
        new context.CoworkBridge().handle(operation, { body: { data: body } }, response);
        return response;
    }
    function record(table, id) { const row = new GlideRecord(table); assert.ok(row.get(id)); return row; }
    function owned() {
        assert.equal(invoke('open_chat', openBody).status, 200);
        state.tables.interaction[0].assigned_to = ids.agent;
        state.tables.interaction[0].state = 'work_in_progress';
    }
    return { state, schema, properties, context, invoke, put, record, owned };
}

test('all REST endpoints reject a different authenticated principal before any writes', () => {
    const f = fixture(); f.state.caller = ids.agent;
    for (const operation of ['open_chat', 'send_message', 'close_chat'])
        assert.equal(f.invoke(operation, openBody).status, 403);
    assert.equal(f.state.inserts.length, 0);
});

test('disabled by default: new chats unavailable and malformed mutations still rejected', () => {
    const f = fixture({ 'cowork_bridge.enabled': undefined });
    const opened = f.invoke('open_chat', openBody);
    assert.equal(opened.status, 200); assert.equal(opened.body.unavailable, true);
    assert.equal(f.invoke('send_message', {}).status, 400);
    assert.equal(f.invoke('close_chat', {}).status, 400);
    assert.equal(f.state.createCalls, 0);
});

test('entry switch and unavailable queue do not prevent existing owned sessions from draining', () => {
    const f = fixture();
    f.owned();
    f.properties['cowork_bridge.enabled'] = 'false';
    f.properties['cowork_bridge.queue_sys_id'] = '';
    assert.deepEqual(f.invoke('send_message', {
        conversation_sys_id: ids.conversation, text: 'finish this chat', email: openBody.email, client_message_id: messageId
    }).body, { sent: true, closed: false });
    assert.deepEqual(f.invoke('close_chat', { conversation_sys_id: ids.conversation }).body, { closed: true });
    assert.equal(f.invoke('open_chat', openBody).body.unavailable, true);
});

test('summary accepts the same 4000-character limit as the backend and widget', () => {
    const f = fixture();
    assert.equal(f.invoke('open_chat', { ...openBody, summary: 'x'.repeat(4000) }).status, 200);
});

test('all routing and callback properties are required before even reserving a command', () => {
    for (const suffix of ['queue_sys_id', 'service_channel_sys_id', 'vendor_sys_id', 'virtual_agent_user_sys_id',
        'webhook_url', 'webhook_oauth_entity', 'webhook_oauth_scope']) {
        const f = fixture({ ['cowork_bridge.' + suffix]: '' });
        assert.equal(f.invoke('open_chat', openBody).status, 503, suffix);
        assert.equal(f.state.inserts.length, 0, suffix);
    }
});

test('input bounds and command identifiers are validated', () => {
    for (const patch of [
        { client_session_id: 'short' }, { client_session_id: 'x'.repeat(81) },
        { client_session_id: 'unsafe_session_000' }, { email: 'bad' }, { summary: 'x'.repeat(4001) },
        { summary: '  ' }, { lang: 'toolonglanguage-abcdefghi' }, { bot: 'copilot' }
    ]) {
        const f = fixture();
        assert.equal(f.invoke('open_chat', { ...openBody, ...patch }).status, 400);
        assert.equal(f.state.inserts.length, 0);
    }
});

test('open persists isolated metadata before AWA and uses QnA/AMB plumbing', () => {
    const f = fixture(); const result = f.invoke('open_chat', openBody);
    assert.equal(result.status, 200); assert.equal(result.body.unavailable, false);
    assert.equal(f.state.correlationBeforeAwa, true);
    const ix = f.state.tables.interaction[0];
    assert.equal(ix.u_cowork_upn, openBody.email);
    assert.equal(ix.u_copilot_upn, undefined); assert.equal(ix.u_bridge_session_id, undefined);
    assert.equal(f.state.tables.sys_cs_session[0].interaction, 'QnA');
    assert.equal(f.state.tables.sys_cs_session_binding[0].channel_type, 'AMB');
    assert.equal(f.state.tables.awa_work_item[0].state, 'queued');
    assert.equal(f.state.tables.u_cowork_command[0].u_status, 'completed');
});

test('language metadata accepts the same tags as the MCP backend', () => {
    for (const lang of ['es-419', 'zh-Hant-TW', 'en-US']) {
        const f = fixture();
        assert.equal(f.invoke('open_chat', { ...openBody, lang }).status, 200);
        assert.equal(f.state.tables.interaction[0].user_language, lang.toLowerCase());
    }
});

test('open reuses a platform-routed work item only when it belongs to the own queue', () => {
    const f = fixture();
    f.state.autoQueue = ids.queue;
    assert.equal(f.invoke('open_chat', openBody).status, 200);
    assert.equal(f.state.tables.awa_work_item.length, 1);
    assert.equal(f.state.inserts.filter(row => row.table === 'awa_work_item').length, 0);
    const wrong = fixture();
    wrong.state.autoQueue = sid('f');
    const failure = wrong.invoke('open_chat', openBody);
    assert.equal(failure.status, 409);
    assert.equal(wrong.state.tables.u_cowork_command[0].u_error, 'work_item_routing_mismatch');
});

test('duplicate completed open returns the exact result without creating another conversation', () => {
    const f = fixture(); const first = f.invoke('open_chat', openBody);
    assert.deepEqual(f.invoke('open_chat', openBody).body, first.body);
    assert.equal(f.state.createCalls, 1);
    const changed = f.invoke('open_chat', { ...openBody, summary: 'Different command' });
    assert.equal(changed.status, 409); assert.equal(changed.body.error, 'idempotency_key_reused');
});

test('pending or failed commands are ambiguous, never retried blindly', () => {
    for (const status of ['pending', 'failed']) {
        const f = fixture(); f.invoke('open_chat', openBody);
        f.state.tables.u_cowork_command[0].u_status = status;
        const response = f.invoke('open_chat', openBody);
        assert.equal(response.status, 409); assert.equal(response.body.error, 'command_ambiguous');
        assert.equal(f.state.createCalls, 1);
    }
});

test('corrupted completed ledger results are not success-shaped fallbacks', () => {
    const f = fixture(); f.invoke('open_chat', openBody);
    for (const value of ['not JSON', '{}', '{"unavailable":false}']) {
        f.state.tables.u_cowork_command[0].u_result = value;
        assert.equal(f.invoke('open_chat', openBody).status, 409);
    }
    assert.equal(f.state.createCalls, 1);
});

test('unique reservation race is explicit409 with no chat mutation', () => {
    const f = fixture(); f.state.race = true;
    assert.equal(f.invoke('open_chat', openBody).status, 409);
    assert.equal(f.state.createCalls, 0);
});

test('partial creation leaves a failed ledger with conversation reference and sanitized error', () => {
    const f = fixture(); f.state.failInsert = 'sys_cs_session_binding';
    const response = f.invoke('open_chat', openBody);
    assert.equal(response.status, 409);
    const command = f.state.tables.u_cowork_command[0];
    assert.equal(command.u_status, 'failed'); assert.equal(command.u_conversation, ids.conversation);
    assert.equal(command.u_error, 'record_insert_failed');
    assert.equal((f.state.tables.awa_work_item || []).length, 0);
});

test('foreign or mixed-harness conversations cannot be sent to or closed', () => {
    for (const patch of [{ u_cowork_session_id: '' }, { u_copilot_upn: 'other@example.test' }, { u_bridge_session_id: 'legacy' }]) {
        const f = fixture(); f.owned(); Object.assign(f.state.tables.interaction[0], patch);
        assert.equal(f.invoke('send_message', { conversation_sys_id: ids.conversation, text: 'hello', email: openBody.email, client_message_id: messageId }).status, 403);
        assert.equal(f.invoke('close_chat', { conversation_sys_id: ids.conversation }).status, 403);
        assert.equal(f.state.sends.length, 0);
    }
});

for (const present of legacySchemas) {
    const label = present.join(',') || 'absent';
    test('legacy schema ' + label + ': empty ownership permits open/send/accepted/message/close', () => {
        const f = fixture({}, { legacyFields: present });
        f.state.createdInteractionValues = Object.fromEntries(present.map(field => [field, '']));
        f.owned();
        assert.equal(f.invoke('send_message', {
            conversation_sys_id: ids.conversation, text: 'hello', email: openBody.email, client_message_id: messageId
        }).status, 200);
        assert.equal(enqueueAccepted(f), true);
        const message = f.put('sys_cs_message', {
            conversation: ids.conversation, message_type: 'text', q_data_message_type: 'systemTextMessage',
            sender: ids.agent, payload: 'Agent reply'
        });
        assert.equal(new f.context.CoworkBridgeWebhook().message(f.record('sys_cs_message', message.sys_id)), true);
        f.state.fireCallbacks = true;
        assert.equal(f.invoke('close_chat', { conversation_sys_id: ids.conversation }).status, 200);
        assert.deepEqual(f.state.requests.map(request => request.body.event), ['accepted', 'message', 'closed']);
        assert.deepEqual([...new Set(f.state.legacyReads)].sort(), [...present].sort());
        assert.deepEqual(f.state.invalidFieldAccesses, []);
        assert.deepEqual(f.state.legacyWrites, []);
    });

    test('legacy schema ' + label + ': own session/upn and principal checks remain mandatory', () => {
        for (const patch of [{ u_cowork_session_id: '' }, { u_cowork_session_id: 'bad' }, { u_cowork_upn: '' }]) {
            const f = fixture({}, { legacyFields: present }); f.owned();
            Object.assign(f.state.tables.interaction[0], patch);
            const before = JSON.stringify([f.state.inserts, f.state.updates]);
            assert.equal(f.invoke('send_message', {
                conversation_sys_id: ids.conversation, text: 'hello', email: openBody.email, client_message_id: messageId
            }).status, 403);
            assert.equal(f.invoke('close_chat', { conversation_sys_id: ids.conversation }).status, 403);
            assert.equal(enqueueAccepted(f), false);
            assert.equal(JSON.stringify([f.state.inserts, f.state.updates]), before);
            assert.deepEqual(f.state.requests, []);
            assert.deepEqual(f.state.invalidFieldAccesses, []);
        }
        const f = fixture({}, { legacyFields: present }); f.state.caller = ids.agent;
        for (const operation of ['open_chat', 'send_message', 'close_chat'])
            assert.equal(f.invoke(operation, openBody).status, 403);
        assert.deepEqual(f.state.inserts, []);
    });

    for (const field of present) {
        test('legacy schema ' + label + ': populated ' + field + ' rejects new and existing mixed ownership', () => {
            for (const value of ['legacy-owner', ' ', '0']) {
                const opening = fixture({}, { legacyFields: present });
                opening.state.createdInteractionValues = { [field]: value };
                assert.equal(opening.invoke('open_chat', openBody).status, 409);
                assert.equal(opening.state.tables.u_cowork_command[0].u_error, 'interaction_not_isolated');
                assert.ok(opening.state.updates.every(row => row.table === 'u_cowork_command'));
                assert.ok(opening.state.inserts.every(row => row.table === 'u_cowork_command'));
                assert.equal(opening.state.tables.interaction[0].u_cowork_session_id, undefined);
                assert.equal(opening.state.tables.interaction[0][field], value);

                const f = fixture({}, { legacyFields: present }); f.owned();
                f.state.tables.interaction[0][field] = value;
                const before = JSON.stringify([f.state.inserts, f.state.updates]);
                assert.equal(f.invoke('send_message', {
                    conversation_sys_id: ids.conversation, text: 'hello', email: openBody.email, client_message_id: messageId
                }).status, 403);
                assert.equal(f.invoke('close_chat', { conversation_sys_id: ids.conversation }).status, 403);
                assert.equal(enqueueAccepted(f), false);
                const current = f.record('interaction', ids.interaction);
                current.row.state = 'closed_complete';
                assert.equal(new f.context.CoworkBridgeWebhook().interaction(current, f.record('interaction', ids.interaction)), false);
                const message = f.put('sys_cs_message', {
                    conversation: ids.conversation, message_type: 'text', q_data_message_type: 'systemTextMessage',
                    sender: ids.agent, payload: 'Agent reply'
                });
                assert.equal(new f.context.CoworkBridgeWebhook().message(f.record('sys_cs_message', message.sys_id)), false);
                assert.equal(JSON.stringify([f.state.inserts, f.state.updates]), before);
                assert.equal(f.state.tables.interaction[0][field], value);
                for (const candidate of [opening, f]) {
                    assert.deepEqual(candidate.state.sends, []);
                    assert.deepEqual(candidate.state.requests, []);
                    assert.deepEqual(candidate.state.invalidFieldAccesses, []);
                    assert.deepEqual(candidate.state.legacyWrites, []);
                }
            }
        });
    }
}

test('send is deduplicated and labels the opened_for user, not untrusted email', () => {
    const f = fixture(); f.owned();
    const input = { conversation_sys_id: ids.conversation, text: 'hello', email: 'attacker@example.test', client_message_id: messageId };
    const response = f.invoke('send_message', input);
    assert.deepEqual(response.body, { sent: true, closed: false });
    assert.deepEqual(f.invoke('send_message', input).body, response.body);
    assert.equal(f.state.sends.length, 1);
    assert.equal(f.state.sends[0].text, 'Actual Requester (via Copilot Cowork): hello');
});

test('uncertain sends never repeat and never persist transcript exceptions', () => {
    const f = fixture(); f.owned(); f.state.throwAfterSend = true;
    const input = { conversation_sys_id: ids.conversation, text: 'hello', email: openBody.email, client_message_id: messageId };
    assert.equal(f.invoke('send_message', input).status, 409);
    assert.equal(f.invoke('send_message', input).status, 409);
    assert.equal(f.state.sends.length, 1);
    assert.equal(f.state.tables.u_cowork_command[1].u_error, 'platform_operation_failed');
});

test('close preserves tags, emits terminal callback, and repeated close/send are idempotent', () => {
    const f = fixture(); f.owned(); f.state.fireCallbacks = true;
    assert.deepEqual(f.invoke('close_chat', { conversation_sys_id: ids.conversation }).body, { closed: true });
    assert.deepEqual(f.invoke('close_chat', { conversation_sys_id: ids.conversation }).body, { closed: true });
    assert.equal(f.state.tables.interaction[0].u_cowork_session_id, session);
    assert.equal(f.state.requests.length, 1);
    assert.equal(f.state.requests[0].body.event, 'closed');
    assert.deepEqual(f.invoke('send_message', {
        conversation_sys_id: ids.conversation, text: 'after close', email: openBody.email, client_message_id: messageId
    }).body, { sent: false, closed: true });
    assert.equal(f.state.sends.length, 0);
});

test('accepted callback has a deterministic interaction/event/version ID', () => {
    const f = fixture(); f.owned();
    const current = f.record('interaction', ids.interaction);
    const previous = f.record('interaction', ids.interaction); previous.row.state = 'new';
    const helper = new f.context.CoworkBridgeWebhook();
    assert.equal(helper.interaction(current, previous), true);
    assert.equal(helper.interaction(current, previous), true);
    assert.equal(f.state.requests.length, 1);
    assert.equal(f.state.tables.u_cowork_outbox.length, 1);
    assert.equal(f.state.requests[0].body.event_id, ids.interaction + ':accepted:1');
    assert.equal(f.state.requests[0].body.bot, 'cowork_mcp');
    assert.equal(f.state.requests[0].headers['X-Cowork-Event-Id'], f.state.requests[0].body.event_id);
    assert.equal(f.state.requests[0].logLevel, 'basic');
});

test('acceptance cannot claim the integration account, Virtual Agent, or requester is an agent', () => {
    const f = fixture(); f.owned();
    const previous = f.record('interaction', ids.interaction); previous.row.state = 'new';
    for (const assigned of [ids.principal, ids.va, ids.requester]) {
        const current = f.record('interaction', ids.interaction); current.row.assigned_to = assigned;
        assert.equal(new f.context.CoworkBridgeWebhook().interaction(current, previous), false);
    }
    assert.equal(f.state.requests.length, 0);
});

test('agent-only callbacks ignore own service sends, opened_for, wrong types and other agents', () => {
    const f = fixture(); f.owned();
    const message = f.put('sys_cs_message', {
        conversation: ids.conversation, message_type: 'text', q_data_message_type: 'systemTextMessage',
        sender: ids.agent, payload: 'Agent reply'
    });
    const helper = new f.context.CoworkBridgeWebhook();
    assert.equal(helper.message(f.record('sys_cs_message', message.sys_id)), true);
    assert.equal(f.state.requests[0].body.event_id, message.sys_id);
    assert.equal(f.state.requests[0].body.message_sys_id, message.sys_id);
    for (const patch of [
        { sender: ids.principal }, { sender: ids.requester }, { sender: ids.va },
        { q_data_message_type: 'typingMessage' }, { message_type: 'typing' }
    ]) {
        const row = f.record('sys_cs_message', message.sys_id); Object.assign(row.row, patch);
        assert.equal(helper.message(row), false);
    }
    assert.equal(f.state.requests.length, 1);
});

test('verified original system/consumer text types still require a real assigned agent', () => {
    for (const type of ['systemTextMessage', 'consumerTextMessage']) {
        const f = fixture(); f.owned();
        const message = f.put('sys_cs_message', {
            conversation: ids.conversation, message_type: 'text', q_data_message_type: type,
            sender: ids.agent, payload: 'Agent reply'
        });
        const helper = new f.context.CoworkBridgeWebhook();
        assert.equal(helper.message(f.record('sys_cs_message', message.sys_id)), true);
        for (const sender of [ids.requester, ids.principal, ids.va]) {
            const current = f.record('sys_cs_message', message.sys_id); current.row.sender = sender;
            assert.equal(helper.message(current), false);
        }
        assert.equal(f.state.requests.length, 1);
    }
});

test('callbacks fail closed without own URL/provider/scope/token; no inherited properties', () => {
    for (const failure of ['url', 'entity', 'scope', 'error', 'token', 'disabled', 'http']) {
        const f = fixture(); f.owned();
        f.properties['copilot_bridge.webhook_url'] = 'https://legacy.example.test/api/webhook';
        if (failure === 'url') f.properties['cowork_bridge.webhook_url'] = '';
        if (failure === 'entity') f.properties['cowork_bridge.webhook_oauth_entity'] = '';
        if (failure === 'scope') f.properties['cowork_bridge.webhook_oauth_scope'] = '';
        if (failure === 'error') f.state.tokenError = 'Do not log this OAuth response';
        if (failure === 'token') f.state.token = '';
        if (failure === 'disabled') f.properties['cowork_bridge.outbox_delivery_enabled'] = 'false';
        if (failure === 'http') f.state.httpStatus = 401;
        const helper = new f.context.CoworkBridgeWebhook();
        assert.equal(helper.deliver({ event_id: 'test', bot: 'cowork_mcp' }), false);
        assert.equal(f.state.requests.length, failure === 'http' ? 1 : 0);
        assert.ok(!JSON.stringify(f.state.warnings).includes('OAuth response'));
    }
});

test('invalid URL redirects/query/credentials or non-default OAuth scopes are rejected', () => {
    for (const value of ['http://backend.example.test/api/livechat/sn', 'https://u:p@backend.example.test/api/livechat/sn',
        'https://backend.example.test/api/livechat/sn?token=x', 'https://backend.example.test/other']) {
        const f = fixture({ 'cowork_bridge.webhook_url': value });
        assert.equal(f.invoke('open_chat', openBody).status, 503);
    }
});

test('all resource and business-rule files compile in the built-in VM', () => {
    for (const name of ['open_chat', 'send_message', 'close_chat', 'interaction_callback', 'message_callback', 'outbox_retry'])
        assert.doesNotThrow(() => new vm.Script(fs.readFileSync(path.join(root, 'scripts', name + '.js'), 'utf8')));
});

function enqueueAccepted(f) {
    const current = f.record('interaction', ids.interaction);
    const previous = f.record('interaction', ids.interaction); previous.row.state = 'new';
    return new f.context.CoworkBridgeWebhook().interaction(current, previous);
}

test('failed immediate HTTP delivery retains the event, then scheduled retry delivers the same ID', () => {
    const f = fixture(); f.owned(); f.state.httpStatus = 503;
    assert.equal(enqueueAccepted(f), true);
    const row = f.state.tables.u_cowork_outbox[0];
    assert.equal(row.u_status, 'retry'); assert.equal(row.u_attempts, 1);
    const firstId = f.state.requests[0].body.event_id;
    const payload = row.u_payload;
    new f.context.CoworkBridgeOutbox().retry();
    assert.equal(f.state.requests.length, 1, 'backoff must be respected');
    f.state.now += 31000; f.state.httpStatus = 200;
    new f.context.CoworkBridgeOutbox().retry();
    assert.equal(row.u_status, 'delivered'); assert.equal(row.u_attempts, 2);
    assert.equal(f.state.requests[1].body.event_id, firstId);
    assert.equal(row.u_payload, payload);
    assert.equal(row.u_lease_token, '');
});

test('duplicate callbacks never create or resend a second event, even while waiting for retry', () => {
    const f = fixture(); f.owned(); f.state.httpStatus = 503;
    assert.equal(enqueueAccepted(f), true); assert.equal(enqueueAccepted(f), true);
    assert.equal(f.state.tables.u_cowork_outbox.length, 1);
    assert.equal(f.state.requests.length, 1);
});

test('OAuth errors keep outbox data durable with no HTTP or secret fallback', () => {
    const f = fixture(); f.owned(); f.state.tokenError = 'Private response';
    assert.equal(enqueueAccepted(f), true);
    const row = f.state.tables.u_cowork_outbox[0];
    assert.equal(row.u_status, 'retry'); assert.equal(f.state.requests.length, 0);
    assert.ok(!JSON.stringify(row).includes('Private response'));
    assert.ok(!JSON.stringify(row).includes('test-access-token'));
    f.state.now += 31000; f.state.tokenError = '';
    new f.context.CoworkBridgeOutbox().retry();
    assert.equal(row.u_status, 'delivered');
    assert.equal(f.state.requests[0].headers.Authorization, 'Bearer test-access-token');
});

test('terminal events survive paused delivery and disabled REST until delivery resumes', () => {
    const f = fixture(); f.owned();
    f.properties['cowork_bridge.enabled'] = 'false';
    f.properties['cowork_bridge.outbox_delivery_enabled'] = 'false';
    const previous = f.record('interaction', ids.interaction);
    const current = f.record('interaction', ids.interaction); current.row.state = 'closed_complete';
    assert.equal(new f.context.CoworkBridgeWebhook().interaction(current, previous), true);
    const row = f.state.tables.u_cowork_outbox[0];
    assert.equal(row.u_status, 'pending'); assert.equal(f.state.requests.length, 0);
    f.properties['cowork_bridge.outbox_delivery_enabled'] = 'true';
    new f.context.CoworkBridgeOutbox().retry();
    assert.equal(row.u_status, 'delivered'); assert.equal(f.state.requests[0].body.event, 'closed');
});

test('terminal failure exhaustion retains dead letter and raises metadata-only ops alert', () => {
    const f = fixture(); f.owned(); f.state.httpStatus = 503;
    const previous = f.record('interaction', ids.interaction);
    const current = f.record('interaction', ids.interaction); current.row.state = 'closed_complete';
    new f.context.CoworkBridgeWebhook().interaction(current, previous);
    const row = f.state.tables.u_cowork_outbox[0];
    for (let i = 1; i < 8; i++) {
        f.state.now += 3601000;
        new f.context.CoworkBridgeOutbox().retry();
    }
    assert.equal(row.u_status, 'dead_letter'); assert.equal(row.u_attempts, 8);
    assert.equal(row.u_requires_attention, true);
    assert.equal(JSON.parse(row.u_payload).event, 'closed');
    assert.equal(f.state.events.length, 1);
    assert.equal(f.state.events[0].id, row.u_event_id);
    assert.ok(!JSON.stringify(f.state.events).includes('The chat is closed'));
    f.state.now += 3601000; new f.context.CoworkBridgeOutbox().retry();
    assert.equal(f.state.requests.length, 8);
});

test('lease prevents concurrent attempts; abandoned lease expires and is recovered', () => {
    const f = fixture({ 'cowork_bridge.outbox_delivery_enabled': 'false' }); f.owned();
    enqueueAccepted(f);
    f.properties['cowork_bridge.outbox_delivery_enabled'] = 'true';
    const outbox = new f.context.CoworkBridgeOutbox();
    const row = f.state.tables.u_cowork_outbox[0];
    const lease = outbox._claim(row.sys_id);
    assert.ok(lease);
    assert.equal(outbox.attempt(row.sys_id), false);
    assert.equal(f.state.requests.length, 0);
    f.state.now += 601000;
    outbox.retry();
    assert.equal(row.u_status, 'delivered'); assert.equal(f.state.requests.length, 1);
    assert.equal(outbox._finish(lease, false, 'stale_worker'), false);
    assert.equal(row.u_status, 'delivered', 'stale worker cannot overwrite the new worker');
});

test('conditional lease loses cleanly when another worker changes the observed revision', () => {
    const f = fixture({ 'cowork_bridge.outbox_delivery_enabled': 'false' }); f.owned(); enqueueAccepted(f);
    f.properties['cowork_bridge.outbox_delivery_enabled'] = 'true';
    const row = f.state.tables.u_cowork_outbox[0];
    f.state.beforeConditionalUpdate = () => { row.sys_mod_count = String(Number(row.sys_mod_count) + 1); };
    assert.equal(new f.context.CoworkBridgeOutbox().attempt(row.sys_id), false);
    assert.equal(f.state.requests.length, 0); assert.equal(row.u_status, 'pending');
});

test('outbox keeps only approved callback fields and refuses changed duplicate payloads', () => {
    const f = fixture({ 'cowork_bridge.outbox_delivery_enabled': 'false' }); f.owned();
    const body = {
        event: 'message', bot: 'cowork_mcp', client_session_id: session, interaction_number: 'TEST0001',
        text: 'Approved agent text', agent_name: 'Actual Agent', event_id: sid('a'), message_sys_id: sid('a'),
        access_token: 'never-store-this', webhook_url: 'never-store-url'
    };
    const helper = new f.context.CoworkBridgeOutbox();
    assert.equal(helper.enqueue(body, ids.interaction), true);
    const row = f.state.tables.u_cowork_outbox[0];
    assert.ok(!row.u_payload.includes('never-store'));
    assert.equal(helper.enqueue({ ...body, text: 'Changed' }, ids.interaction), false);
    assert.equal(row.u_requires_attention, true);
    assert.equal(JSON.parse(row.u_payload).text, body.text);
});

test('an outbox insert failure never sends an unpersisted callback', () => {
    const f = fixture(); f.owned(); f.state.failInsert = 'u_cowork_outbox';
    assert.throws(() => enqueueAccepted(f), /cowork_outbox_enqueue_failed/);
    assert.equal(f.state.requests.length, 0); assert.equal(f.state.tokenCalls.length, 0);
});

test('post-delivery persistence exceptions do not discard enqueue and recover under the same event ID', () => {
    const f = fixture(); f.owned();
    const prototype = f.context.CoworkBridgeOutbox.prototype;
    const finish = prototype._finish;
    prototype._finish = () => { throw new Error('private platform exception'); };
    assert.equal(enqueueAccepted(f), true);
    const row = f.state.tables.u_cowork_outbox[0];
    assert.equal(row.u_status, 'sending'); assert.equal(f.state.requests.length, 1);
    prototype._finish = finish; f.state.now += 601000;
    new f.context.CoworkBridgeOutbox().retry();
    assert.equal(row.u_status, 'delivered');
    assert.equal(f.state.requests[0].body.event_id, f.state.requests[1].body.event_id);
    assert.ok(!JSON.stringify(f.state.warnings).includes('private platform exception'));
});
