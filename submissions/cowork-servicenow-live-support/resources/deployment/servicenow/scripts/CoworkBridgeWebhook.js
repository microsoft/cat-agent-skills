var CoworkBridgeWebhook = Class.create();
CoworkBridgeWebhook.prototype = {
    initialize: function () {},

    configuration: function () {
        var config = {
            url: String(gs.getProperty('cowork_bridge.webhook_url', '')),
            entity: String(gs.getProperty('cowork_bridge.webhook_oauth_entity', '')),
            scope: String(gs.getProperty('cowork_bridge.webhook_oauth_scope', '')),
            principal: String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''))
        };
        if (!/^https:\/\/[A-Za-z0-9.-]+(?::443)?\/api\/livechat\/sn$/.test(config.url) ||
            config.entity.length < 1 || config.entity.length > 160 || /[\r\n]/.test(config.entity) ||
            !/^\S+\/\.default$/.test(config.scope) || config.scope.length > 512 ||
            !/^[0-9a-f]{32}$/.test(config.principal))
            this._error('webhook_configuration_required');
        return config;
    },

    interaction: function (current, previous) {
        if (!previous || !this._isCowork(current)) return false;
        var state = String(current.getValue('state'));
        var oldState = String(previous.getValue('state'));
        var event = '';
        if (state.indexOf('closed') === 0 && oldState.indexOf('closed') !== 0) event = 'closed';
        else if (state === 'work_in_progress' && current.getValue('assigned_to') &&
            (oldState !== state || String(current.getValue('assigned_to')) !== String(previous.getValue('assigned_to'))))
            event = 'accepted';
        if (!event) return false;
        if (event === 'accepted' && !this._realAgent(current, String(current.getValue('assigned_to')))) return false;
        var version = String(current.getValue('sys_mod_count') || current.getValue('sys_updated_on') || '');
        if (!version) return false;
        var body = this._body(current, event, event === 'accepted' ? 'An agent accepted the chat.' : 'The chat is closed.');
        body.event_id = String(current.getUniqueValue()) + ':' + event + ':' + version;
        return new CoworkBridgeOutbox().enqueue(body, String(current.getUniqueValue()));
    },

    message: function (message) {
        var type = String(message.getValue('q_data_message_type') || '');
        if (String(message.getValue('message_type')) !== 'text' ||
            (type !== 'systemTextMessage' && type !== 'consumerTextMessage')) return false;
        var interaction = new GlideRecord('interaction');
        interaction.addQuery('channel_metadata_document', String(message.getValue('conversation')));
        interaction.setLimit(2);
        interaction.query();
        if (!interaction.next() || !this._isCowork(interaction)) return false;
        var id = String(interaction.getUniqueValue());
        if (interaction.next() || !interaction.get(id)) return false;
        var principal = String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''));
        if (!/^[0-9a-f]{32}$/.test(principal)) return false;
        var sender = String(message.getValue('sender') || '');
        if (sender !== String(interaction.getValue('assigned_to')) || !this._realAgent(interaction, sender)) return false;
        var agent = new GlideRecord('sys_user');
        if (!agent.get(sender) || !/^(true|1)$/.test(String(agent.getValue('active')))) return false;
        var text = String(message.getValue('payload') || '');
        if (!text || text.length > 8000) return false;
        var body = this._body(interaction, 'message', text);
        body.agent_name = String(agent.getDisplayValue() || '').substring(0, 200);
        body.message_sys_id = String(message.getUniqueValue());
        body.event_id = body.message_sys_id;
        return new CoworkBridgeOutbox().enqueue(body, id);
    },

    deliver: function (body) {
        if (!this._enabled()) return false;
        try {
            var config = this.configuration();
            var client = new sn_auth.GlideOAuthClient();
            var tokenResponse = client.requestToken(config.entity, JSON.stringify({
                grant_type: 'client_credentials', scope: config.scope
            }));
            if (!tokenResponse || tokenResponse.getErrorMessage()) this._error('webhook_oauth_failed');
            var token = tokenResponse.getToken();
            var access = token && String(token.getAccessToken() || '');
            if (!access || /[\r\n]/.test(access) ||
                (typeof token.getExpiresIn === 'function' && Number(token.getExpiresIn()) <= 30))
                this._error('webhook_oauth_failed');
            var request = new sn_ws.RESTMessageV2();
            request.setEndpoint(config.url);
            request.setHttpMethod('post');
            request.setHttpTimeout(10000);
            request.setLogLevel('basic');
            request.setRequestHeader('Content-Type', 'application/json');
            request.setRequestHeader('Accept', 'application/json');
            request.setRequestHeader('Authorization', 'Bearer ' + access);
            request.setRequestHeader('X-Cowork-Event-Id', body.event_id);
            request.setRequestHeader('X-Cowork-Bot', 'cowork_mcp');
            request.setRequestBody(JSON.stringify(body));
            var result = request.execute();
            var status = Number(result.getStatusCode());
            if (result.haveError() || status < 200 || status >= 300) this._error('webhook_delivery_failed');
            return true;
        } catch (ignored) {
            // Neither exception text, token responses, nor transcript payloads go into application logs.
            return false;
        }
    },

    _body: function (interaction, event, text) {
        return {
            event: event, bot: 'cowork_mcp',
            client_session_id: String(interaction.getValue('u_cowork_session_id')),
            interaction_number: String(interaction.getValue('number') || ''),
            text: text,
            agent_name: String(interaction.getDisplayValue('assigned_to') || '').substring(0, 200)
        };
    },
    _enabled: function () { return String(gs.getProperty('cowork_bridge.outbox_delivery_enabled', 'false')) === 'true'; },
    _realAgent: function (interaction, sender) {
        var principal = String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''));
        var virtualAgent = String(gs.getProperty('cowork_bridge.virtual_agent_user_sys_id', ''));
        if (!/^[0-9a-f]{32}$/.test(principal) || !/^[0-9a-f]{32}$/.test(virtualAgent) ||
            !sender || sender === principal || sender === virtualAgent ||
            sender === String(interaction.getValue('opened_for'))) return false;
        var user = new GlideRecord('sys_user');
        return user.get(sender) && /^(true|1)$/.test(String(user.getValue('active')));
    },
    _isCowork: function (interaction) {
        return /^[A-Za-z0-9-]{16,80}$/.test(String(interaction.getValue('u_cowork_session_id') || '')) &&
            !!interaction.getValue('u_cowork_upn') &&
            !(interaction.isValidField('u_copilot_upn') && interaction.getValue('u_copilot_upn')) &&
            !(interaction.isValidField('u_bridge_session_id') && interaction.getValue('u_bridge_session_id'));
    },
    _error: function (code) {
        var error = new Error(code);
        error.coworkStatus = 503;
        error.coworkCode = code;
        throw error;
    },
    type: 'CoworkBridgeWebhook'
};
