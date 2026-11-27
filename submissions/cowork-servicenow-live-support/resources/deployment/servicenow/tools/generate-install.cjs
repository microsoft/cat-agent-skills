'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const { build } = require('./build-artifacts.cjs');

const root = path.resolve(__dirname, '..');
const sha256 = value => crypto.createHash('sha256').update(value, 'utf8').digest('hex');
const stableId = (table, identity) => sha256('cowork-sn:v1:' + table + ':' + identity).slice(0, 32);
const canonical = fields => JSON.stringify(Object.keys(fields).sort().map(key => [key, fields[key]]));

function createManifest() {
    const bundle = build();
    const d = bundle.definition;
    if (d.target.instance !== 'example.invalid' ||
        d.target.execution_scope !== 'global' || d.target.namespace !== 'cowork_review' ||
        d.target.base_path !== '/api/cowork_review/cowork_bridge')
        throw new Error('Target changed: independently review the generator first.');
    const records = [];
    const scripts = new Map(bundle.scripts.map(item => [item.file, item]));
    const add = (table, identity, values, keys, options = {}) => {
        const fields = { ...values };
        if (options.scoped !== false) fields.sys_scope = 'global';
        for (const key of Object.keys(fields)) fields[key] = String(fields[key]);
        const record = {
            table, identity, sys_id: stableId(table, identity),
            fields, keys: keys || [{ name: fields.name }],
            booleans: Object.keys(values).filter(key => typeof values[key] === 'boolean'),
            baseline_sha256: sha256(canonical(fields)), ...options
        };
        delete record.scoped;
        records.push(record);
        return record.sys_id;
    };
    const source = item => scripts.get(item.script_file).source;
    const roleIds = {};
    for (const role of d.roles) {
        if (role.name !== 'cowork_bridge.integration' || role.contains_roles.length)
            throw new Error('Unexpected role or inherited privileges.');
        roleIds[role.name] = add('sys_user_role', role.name, {
            name: role.name, description: role.description, elevated_privilege: false
        });
    }

    // Restrictive ACLs precede schema creation; no auto-generated permissive ACLs.
    let restAclId;
    for (const acl of d.access_controls) {
        for (const name of acl.names || [acl.name]) {
            for (const operation of acl.operations || [acl.operation]) {
                const identity = acl.type + ':' + name + ':' + operation;
                const type = acl.type === 'rest_endpoint' ? 'REST_Endpoint' : acl.type;
                const aclId = add('sys_security_acl', identity, {
                    name, type, operation, active: true, advanced: true,
                    admin_overrides: acl.admin_overrides, condition: '', script: acl.script
                }, [{ name, type, operation }]);
                if (acl.type === 'rest_endpoint') restAclId = aclId;
                for (const role of acl.required_roles) {
                    const roleId = role === 'admin' ? '@admin_role' : roleIds[role];
                    if (!roleId) throw new Error('Unknown ACL role: ' + role);
                    add('sys_security_acl_role', identity + ':' + role, {
                        sys_security_acl: aclId, sys_user_role: roleId
                    }, [{ sys_security_acl: aclId, sys_user_role: roleId }], { scoped: false });
                }
            }
        }
    }
    if (!restAclId) throw new Error('REST execute ACL is required.');

    function column(table, c) {
        const fields = {
            name: table, element: c.name, column_label: c.label, internal_type: c.type,
            active: true, mandatory: !!c.mandatory, unique: !!c.unique,
            default_value: c.default || '', choice: c.choices ? '3' : '0',
            reference: c.reference || '', audit: false, read_only: false,
            display: false, virtual: false, attributes: ''
        };
        if (c.max_length !== undefined) fields.max_length = c.max_length;
        else if (c.type === 'reference') fields.max_length = 32;
        add('sys_dictionary', table + '.' + c.name, fields,
            [{ name: table, element: c.name }], { verify_field: [table, c.name] });
        for (const [index, value] of (c.choices || []).entries()) {
            const identity = table + '.' + c.name + ':en:' + value;
            add('sys_choice', identity, {
                name: table, element: c.name, language: 'en', value, label: value,
                sequence: (index + 1) * 100, inactive: false, dependent_value: '', sys_domain: 'global'
            }, [{ name: table, element: c.name, language: 'en', value, dependent_value: '' }],
            { scoped: false });
        }
    }
    const indexRequests = [];
    for (const table of d.tables) {
        if (!['u_cowork_command', 'u_cowork_outbox'].includes(table.name) || table.extends)
            throw new Error('Only the two new standalone Cowork tables are allowed.');
        add('sys_db_object', table.name, {
            name: table.name, label: table.label, super_class: '', is_extendable: false,
            access: 'public', create_access: false, read_access: false, update_access: false,
            delete_access: false, ws_access: false, create_access_controls: false
        });
        add('sys_dictionary', table.name + '.', {
            name: table.name, element: '', internal_type: 'collection', active: true,
            audit: false, attributes: '', mandatory: false, unique: false,
            max_length: 40, column_label: table.label
        }, [{ name: table.name, element: '' }], { verify_table: table.name, platform_collection: true });
        for (const c of table.columns) {
            column(table.name, c);
            if (c.unique) indexRequests.push({ table: table.name, columns: [c.name], unique: true,
                mechanism: 'sys_dictionary.unique=true; physical enforcement MUST be independently verified' });
        }
        for (const index of table.indexes || []) {
            if (index.unique && table.columns.some(c => c.unique && index.columns.length === 1 && c.name === index.columns[0]))
                continue;
            indexRequests.push({ table: table.name, columns: index.columns, unique: index.unique,
                mechanism: 'MANUAL: supported Tables > Database Indexes workflow; no guessed index metadata writes' });
        }
    }
    for (const extension of d.extensions) {
        if (extension.table !== 'interaction') throw new Error('Unexpected table extension.');
        for (const c of extension.columns) {
            if (!['u_cowork_session_id', 'u_cowork_upn'].includes(c.name))
                throw new Error('Unexpected interaction field.');
            column(extension.table, c);
            if (c.indexed) indexRequests.push({ table: extension.table, columns: [c.name], unique: false,
                mechanism: 'MANUAL: supported Tables > Database Indexes workflow; no guessed index metadata writes' });
        }
    }
    for (const property of d.properties) {
        if (!property.name.startsWith('cowork_bridge.') ||
            (property.name.endsWith('enabled') && property.value !== 'false'))
            throw new Error('Unexpected or enabled property.');
        add('sys_properties', property.name, { name: property.name, type: property.type,
            value: property.value, is_private: true, ignore_cache: false });
    }
    for (const item of d.script_includes) {
        if (!['CoworkBridge', 'CoworkBridgeOutbox', 'CoworkBridgeWebhook'].includes(item.name))
            throw new Error('Unexpected Script Include.');
        add('sys_script_include', item.name, {
            name: item.name, api_name: 'global.' + item.name, active: true,
            client_callable: false, access: 'public', script: source(item)
        }, [{ name: item.name }, { api_name: 'global.' + item.name }]);
    }
    const api = d.rest_definition;
    const apiId = add('sys_ws_definition', d.target.base_path, {
        name: api.name, service_id: api.service_id, namespace: api.namespace,
        base_uri: d.target.base_path, active: false, is_versioned: false,
        enforce_acl: restAclId, consumes: 'application/json', produces: 'application/json',
        consumes_customized: true, produces_customized: true
    }, [{ name: api.name }, { namespace: api.namespace, service_id: api.service_id },
        { base_uri: d.target.base_path }]);
    for (const resource of api.resources) {
        if (!['open_chat', 'send_message', 'close_chat'].includes(resource.name) ||
            resource.relative_path !== '/' + resource.name || resource.http_method !== 'POST')
            throw new Error('Unexpected REST resource.');
        add('sys_ws_operation', d.target.base_path + resource.relative_path, {
            name: resource.name, web_service_definition: apiId, web_service_version: '',
            relative_path: resource.relative_path, http_method: 'POST', active: false,
            operation_script: source(resource), requires_authentication: true,
            requires_acl_authorization: true, enforce_acl: restAclId,
            consumes: 'application/json', produces: 'application/json',
            consumes_customized: true, produces_customized: true
        }, [{ web_service_definition: apiId, name: resource.name },
            { web_service_definition: apiId, relative_path: resource.relative_path, http_method: 'POST' }]);
    }
    for (const item of d.business_rules) {
        if (item.active || !item.name.startsWith('Cowork ')) throw new Error('Unexpected active rule.');
        const fields = { name: item.name };
        for (const key of ['collection', 'active', 'advanced', 'when', 'order',
            'action_insert', 'action_update', 'action_delete', 'action_query', 'filter_condition', 'condition'])
            fields[key] = item[key];
        fields.script = source(item);
        add('sys_script', item.name, fields);
    }
    for (const item of d.scheduled_jobs) {
        if (item.name !== 'Cowork outbox retry' || item.active || item.run_period_seconds !== 60)
            throw new Error('Unexpected retry schedule.');
        add('sysauto_script', item.name, {
            name: item.name, active: false, run_type: 'periodically', run_period: '1970-01-01 00:01:00',
            conditional: false, condition: '', script: source(item)
        });
    }
    for (const item of d.event_registry) {
        if (!item.name.startsWith('cowork_bridge.')) throw new Error('Unexpected event.');
        add('sysevent_register', item.name, {
            event_name: item.name, table: item.table, description: item.description.substring(0, 100), queue: ''
        }, [{ event_name: item.name }]);
    }
    for (const proposed of bundle.identities) {
        if (!records.some(r => r.table === proposed.table && r.sys_id === proposed.proposed_sys_id))
            throw new Error('Missing definition identity: ' + proposed.table + ':' + proposed.identity);
    }
    if (new Set(records.map(r => r.sys_id)).size !== records.length) throw new Error('Duplicate IDs.');
    return {
        format: 'cowork-create-only-installer-v1', definition_sha256: bundle.definition_sha256,
        instance: 'example', scope: 'global', namespace: 'cowork_review', records,
        index_requests: indexRequests,
        legacy: { table: d.legacy_amendment.table, sys_id: d.legacy_amendment.sys_id,
            original_script_sha256: d.legacy_amendment.original_script_sha256 },
        prerequisites: [
            'Review this exact artifact and same-release table/dictionary creation behavior before apply. No inferred schema fallback.',
            'Use one elevated security_admin installer session in global; no concurrent installer or metadata edits.',
            'Legacy interaction ownership fields are optional: inspect presence only, never their data; presence drift during this run stops installation. Runtime rejects either populated legacy field independently.',
            'NONDEPLOYABLE TEMPLATE: independently review target instance, native Global namespace and API base_uri before adapting exact guards.',
            'Dictionary unique=true requests the unique database indexes; verify physical enforcement separately. Nonunique indexes are manual.',
            'Installation stages DISABLED metadata only. No OAuth, credentials, users, memberships, queues, notifications or activation are created.',
            'Legacy fanout amendment is optional and target-specific. If absent, do not create or amend a rule. All-zero sentinels and helper refusal remain; this installer never reads or patches legacy scripts.'
        ]
    };
}

// Serialized verbatim into the standalone ES5 Background Script. No Node dependencies.
function installRuntime(manifest, expectedManifestHash, options) {
    'use strict';
    options = options || {};
    var dryRun = options.dryRun !== false;
    var counts = { created: 0, unchanged: 0, planned: 0 };
    var adminId = '';
    var records = manifest.records;
    var preexistingTables = {}, createdTables = {}, collectionIds = {};
    var preflight = true;
    var legacyFields = ['u_copilot_upn', 'u_bridge_session_id'], legacyFieldPresence = {};
    var prefix = '[Cowork installer] ';
    function report(message) { gs.print(prefix + message); }
    function fail(code) {
        report('STOP ' + code + '; created=' + counts.created + ', unchanged=' + counts.unchanged +
            ', planned=' + counts.planned + '. No rollback/delete attempted. Inspect partial metadata before retry.');
        var error = new Error('Cowork installer: ' + code);
        error.coworkInstaller = true;
        throw error;
    }
    function digest(text) { return String(new GlideDigest().getSHA256Hex(text)).toLowerCase(); }
    function canonical(fields) {
        var keys = Object.keys(fields).sort(), pairs = [];
        for (var i = 0; i < keys.length; i++) pairs.push([keys[i], fields[keys[i]]]);
        return JSON.stringify(pairs);
    }
    function value(raw) { return raw === null || raw === undefined ? '' : String(raw); }
    function resolved(raw) { return raw === '@admin_role' ? adminId : raw; }
    function table(name) {
        var gr = new GlideRecord(name);
        if (!gr.isValid()) fail('missing_table:' + name);
        return gr;
    }
    function requireFields(name, fields) {
        var gr = table(name);
        for (var i = 0; i < fields.length; i++)
            if (!gr.isValidField(fields[i])) fail('missing_field:' + name + '.' + fields[i]);
        return gr;
    }
    function requireDescriptor(name, field, type, reference) {
        var gr = requireFields(name, [field]);
        var element = gr.getElement(field), ed = element.getED();
        if (value(ed.getInternalType()) !== type ||
            (reference && value(ed.getReference()) !== reference))
            fail('schema_mismatch:' + name + '.' + field);
    }
    function checkLegacyFieldPresence(capture) {
        var gr = table('interaction');
        for (var i = 0; i < legacyFields.length; i++) {
            var field = legacyFields[i], present = !!gr.isValidField(field);
            if (capture) {
                legacyFieldPresence[field] = present;
                report('LEGACY_FIELD_PRESENCE interaction.' + field + '=' + present + '; no data inspected');
            } else if (legacyFieldPresence[field] !== present) {
                fail('legacy_field_presence_changed:interaction.' + field);
            }
        }
    }
    function query(name, keys) {
        var gr = requireFields(name, Object.keys(keys));
        for (var key in keys) {
            if (keys.hasOwnProperty(key)) {
                if (keys[key] === '') gr.addNullQuery(key);
                else gr.addQuery(key, resolved(keys[key]));
            }
        }
        gr.setLimit(2);
        gr.query();
        return gr;
    }
    function findUnique(name, keys) {
        var gr = query(name, keys);
        if (!gr.next()) return '';
        var id = value(gr.getUniqueValue());
        if (gr.next()) fail('ambiguous_prerequisite:' + name);
        return id;
    }
    function requireElevatedSession() {
        if (typeof gs.getSession !== 'function') fail('active_session_roles_API_required');
        var session = gs.getSession();
        if (!session || typeof session.getRoles !== 'function') fail('active_session_roles_API_required');
        var raw = session.getRoles(), roles = [], i, count, allowEmptyCsvToken = false;
        if (Array.isArray(raw)) roles = raw;
        else if (raw && typeof raw.size === 'function' && typeof raw.get === 'function') {
            count = Number(raw.size());
            if (count < 0 || count > 4096 || count !== Math.floor(count)) fail('unrecognized_session_roles');
            for (i = 0; i < count; i++) roles.push(raw.get(i));
        } else {
            var text = value(raw).replace(/^\s+|\s+$/g, '');
            if (text.charAt(0) === '[' && text.charAt(text.length - 1) === ']') {
                if (text.indexOf('"') !== -1) {
                    try { roles = JSON.parse(text); } catch (ignored) { fail('unrecognized_session_roles'); }
                    if (!Array.isArray(roles)) fail('unrecognized_session_roles');
                } else {
                    roles = text.substring(1, text.length - 1).split(',');
                    allowEmptyCsvToken = true;
                }
            } else {
                roles = text.split(',');
                allowEmptyCsvToken = true;
            }
        }
        if (roles.length > 4096) fail('unrecognized_session_roles');
        var elevated = false;
        for (i = 0; i < roles.length; i++) {
            if (Array.isArray(roles[i]) ||
                (typeof roles[i] !== 'string' && typeof roles[i] !== 'object'))
                fail('unrecognized_session_roles');
            var role = value(roles[i]).replace(/^\s+|\s+$/g, '');
            if (allowEmptyCsvToken && role === '') continue;
            if (!/^[A-Za-z0-9_.-]+$/.test(role)) fail('unrecognized_session_roles');
            if (role === 'security_admin') elevated = true;
        }
        if (!elevated) fail('security_admin_elevation_required');
        // The exact active-session role is mandatory even when this optional helper exists.
        if (typeof gs.requireSecurityAdmin === 'function') gs.requireSecurityAdmin();
    }
    function normalize(record, field, raw) {
        var text = value(raw);
        if (record.fields[field] === '@admin_role' && text === adminId) return '@admin_role';
        if (record.booleans.indexOf(field) !== -1) {
            if (text === '1' || text === 'true') return 'true';
            if (text === '0' || text === 'false') return 'false';
        }
        return text;
    }
    function baseline(record, gr) {
        var fields = {};
        for (var field in record.fields)
            if (record.fields.hasOwnProperty(field))
                fields[field] = normalize(record, field, gr.getValue(field));
        if (digest(canonical(fields)) !== record.baseline_sha256)
            fail('baseline_drift:' + record.table + ':' + record.sys_id);
    }
    function owned(record) {
        var f = record.fields, t = record.table;
        var ownTable = /^(u_cowork_command|u_cowork_outbox)$/;
        if (t === 'sys_user_role') return f.name === 'cowork_bridge.integration';
        if (t === 'sys_db_object') return ownTable.test(f.name);
        if (t === 'sys_dictionary' || t === 'sys_choice')
            return ownTable.test(f.name) || (f.name === 'interaction' &&
                /^(u_cowork_session_id|u_cowork_upn)$/.test(f.element));
        if (t === 'sys_properties') return /^cowork_bridge\./.test(f.name);
        if (t === 'sys_script_include') return /^(CoworkBridge|CoworkBridgeOutbox|CoworkBridgeWebhook)$/.test(f.name);
        if (t === 'sys_script') return /^(Cowork interaction accepted or closed|Cowork agent message callback)$/.test(f.name);
        if (t === 'sysauto_script') return f.name === 'Cowork outbox retry';
        if (t === 'sysevent_register') return f.event_name === 'cowork_bridge.outbox.dead_letter';
        if (t === 'sys_ws_definition') return f.name === 'Cowork Bridge' && f.service_id === 'cowork_bridge' &&
            f.namespace === 'cowork_review' && f.base_uri === '/api/cowork_review/cowork_bridge';
        if (t === 'sys_ws_operation') return /^(open_chat|send_message|close_chat)$/.test(f.name) &&
            f.web_service_definition === digest('cowork-sn:v1:sys_ws_definition:/api/cowork_review/cowork_bridge').substring(0, 32);
        if (t === 'sys_security_acl') return (f.type === 'REST_Endpoint' && f.name === 'Cowork Bridge' &&
            f.operation === 'execute') || (f.type === 'record' &&
            /^(u_cowork_command|u_cowork_outbox|interaction\.u_cowork_session_id|interaction\.u_cowork_upn)$/.test(f.name));
        if (t === 'sys_security_acl_role') {
            for (var i = 0; i < records.length; i++)
                if (records[i].table === 'sys_security_acl' && records[i].sys_id === f.sys_security_acl)
                    return f.sys_user_role === '@admin_role' ||
                        f.sys_user_role === digest('cowork-sn:v1:sys_user_role:cowork_bridge.integration').substring(0, 32);
        }
        return false;
    }
    function inspect(record) {
        if (record.platform_collection) return inspectCollection(record);
        var existing = table(record.table);
        var found = existing.get(record.sys_id);
        if (found) baseline(record, existing);
        for (var i = 0; i < record.keys.length; i++) {
            var matches = query(record.table, record.keys[i]);
            while (matches.next())
                if (value(matches.getUniqueValue()) !== record.sys_id)
                    fail('name_collision:' + record.table + ':' + record.sys_id +
                        ':existing=' + value(matches.getUniqueValue()));
        }
        if (record.table === 'sys_db_object' && !found && new GlideRecord(record.fields.name).isValid())
            fail('unowned_backing_table:' + record.fields.name);
        if (record.table === 'sys_db_object' && found && preflight) preexistingTables[record.fields.name] = true;
        if (record.table === 'sys_dictionary' && record.fields.element && !found) {
            var target = new GlideRecord(record.fields.name);
            if (target.isValid() && target.isValidField(record.fields.element))
                fail('unowned_backing_field:' + record.fields.name + '.' + record.fields.element);
        }
        return found;
    }
    function inspectCollection(record) {
        var reserved = table('sys_dictionary');
        if (reserved.get(record.sys_id)) baseline(record, reserved);
        var matches = query('sys_dictionary', { name: record.fields.name, element: '' });
        if (!matches.next()) return false;
        var id = value(matches.getUniqueValue());
        if (!/^[0-9a-f]{32}$/.test(id)) fail('invalid_collection_id:' + record.fields.name);
        var invariant = {
            name: value(matches.getValue('name')), element: value(matches.getValue('element')),
            internal_type: value(matches.getValue('internal_type')), sys_scope: value(matches.getValue('sys_scope'))
        };
        if (digest(canonical(invariant)) !== digest(canonical({
            name: record.fields.name, element: '', internal_type: 'collection', sys_scope: 'global'
        }))) fail('collection_baseline_drift:' + record.fields.name);
        if (matches.next()) fail('ambiguous_collection:' + record.fields.name);
        var parent = null;
        for (var i = 0; i < records.length; i++)
            if (records[i].table === 'sys_db_object' && records[i].fields.name === record.fields.name)
                parent = records[i];
        if (!parent || !inspect(parent) ||
            (!preexistingTables[record.fields.name] && !createdTables[record.fields.name]))
            fail('unowned_collection:' + record.fields.name);
        if (collectionIds[record.sys_id] && collectionIds[record.sys_id] !== id)
            fail('collection_changed_during_run:' + record.fields.name);
        collectionIds[record.sys_id] = id;
        verifyPhysical(record);
        return id;
    }
    function verifyPhysical(record) {
        if (record.verify_table) requireFields(record.verify_table, ['sys_id', 'sys_created_on',
            'sys_updated_on', 'sys_created_by', 'sys_updated_by', 'sys_mod_count']);
        if (record.verify_field) {
            var target = requireFields(record.verify_field[0], [record.verify_field[1]]);
            var element = target.getElement(record.verify_field[1]), ed = element.getED();
            if (value(ed.getInternalType()) !== record.fields.internal_type)
                fail('backing_field_type:' + record.verify_field.join('.'));
            if (record.fields.reference && value(ed.getReference()) !== record.fields.reference)
                fail('backing_field_reference:' + record.verify_field.join('.'));
            if (record.fields.max_length && record.fields.internal_type === 'string' &&
                Number(ed.getLength()) < Number(record.fields.max_length))
                fail('backing_field_length:' + record.verify_field.join('.'));
        }
    }
    function verifyRelations() {
        for (var i = 0; i < records.length; i++) {
            var record = records[i];
            if (record.table === 'sys_security_acl') {
                var links = requireFields('sys_security_acl_role', ['sys_security_acl']);
                links.addQuery('sys_security_acl', record.sys_id);
                links.query();
                while (links.next()) {
                    var expected = false;
                    for (var j = 0; j < records.length; j++)
                        if (records[j].table === 'sys_security_acl_role' &&
                            records[j].sys_id === value(links.getUniqueValue())) expected = true;
                    if (!expected) fail('unexpected_acl_role:' + record.sys_id);
                }
            }
        }
        var contains = requireFields('sys_user_role_contains', ['role', 'contains']);
        contains.addQuery('role', digest('cowork-sn:v1:sys_user_role:cowork_bridge.integration').substring(0, 32));
        contains.query();
        if (contains.next()) fail('unexpected_inherited_role');
        var operations = requireFields('sys_ws_operation', ['web_service_definition']);
        operations.addQuery('web_service_definition',
            digest('cowork-sn:v1:sys_ws_definition:/api/cowork_review/cowork_bridge').substring(0, 32));
        operations.query();
        while (operations.next()) {
            var planned = false;
            for (var k = 0; k < records.length; k++)
                if (records[k].table === 'sys_ws_operation' &&
                    records[k].sys_id === value(operations.getUniqueValue())) planned = true;
            if (!planned) fail('unexpected_rest_operation');
        }
    }
    try {
        if (value(gs.getProperty('instance_name', '')) !== manifest.instance) fail('wrong_instance');
        var scopeName = value(gs.getCurrentScopeName());
        if (value(gs.getCurrentApplicationId()) !== 'global' ||
            (scopeName !== 'global' && scopeName !== 'rhino.global')) fail('wrong_scope');
        if (digest(JSON.stringify(manifest)) !== expectedManifestHash) fail('artifact_hash_mismatch');
        if (!dryRun && options.reviewedDefinition !== manifest.definition_sha256)
            fail('review_required:copy_definition_sha256_only_after_INSTALLER_txt_prerequisites');
        requireFields('sys_scope', ['scope']);
        var global = table('sys_scope');
        if (!global.get('global') || value(global.getValue('scope')) !== 'global') fail('global_scope_record_required');
        adminId = findUnique('sys_user_role', { name: 'admin' });
        if (!adminId) fail('admin_role_required');
        if (!dryRun) requireElevatedSession();
        report((dryRun ? 'DRY RUN (no writes)' : 'APPLY create-only, disabled') +
            '; definition_sha256=' + manifest.definition_sha256);
        for (var p = 0; p < manifest.prerequisites.length; p++) report('REVIEW ' + manifest.prerequisites[p]);
        requireFields('interaction', ['sys_id', 'state', 'assigned_to', 'channel_metadata_document',
            'opened_for']);
        checkLegacyFieldPresence(true);
        requireFields('sys_cs_message', ['sys_id', 'conversation', 'sender', 'message_type', 'q_data_message_type', 'payload']);
        requireFields('sys_cs_conversation', ['sys_id']);
        requireDescriptor('sys_ws_definition', 'enforce_acl', 'glide_list', 'sys_security_acl');
        requireDescriptor('sys_ws_operation', 'enforce_acl', 'glide_list', 'sys_security_acl');
        requireDescriptor('sys_ws_operation', 'web_service_definition', 'reference', 'sys_ws_definition');
        requireDescriptor('sys_ws_definition', 'namespace', 'string');
        requireDescriptor('sys_ws_definition', 'service_id', 'string');
        requireDescriptor('sys_security_acl_role', 'sys_security_acl', 'reference', 'sys_security_acl');
        requireDescriptor('sys_security_acl_role', 'sys_user_role', 'reference', 'sys_user_role');
        requireDescriptor('sysauto_script', 'run_period', 'glide_duration');
        requireDescriptor('sys_dictionary', 'unique', 'boolean');
        var i, record;
        // Complete read-only preflight before ANY insert, including late collisions.
        for (i = 0; i < records.length; i++) {
            record = records[i];
            if (!owned(record) || record.sys_id === manifest.legacy.sys_id) fail('ownership_violation');
            if (digest('cowork-sn:v1:' + record.table + ':' + record.identity).substring(0, 32) !== record.sys_id ||
                digest(canonical(record.fields)) !== record.baseline_sha256) fail('record_hash_mismatch');
            requireFields(record.table, Object.keys(record.fields).concat(['sys_id']));
            if (record.fields.sys_scope) requireDescriptor(record.table, 'sys_scope', 'reference', 'sys_scope');
            if (inspect(record)) verifyPhysical(record);
        }
        verifyRelations();
        checkLegacyFieldPresence(false);
        preflight = false;
        for (i = 0; i < records.length; i++) {
            record = records[i];
            if (inspect(record)) {
                verifyPhysical(record);
                var actualId = collectionIds[record.sys_id] || record.sys_id;
                if (record.platform_collection && createdTables[record.fields.name]) {
                    counts.created++;
                    report('PLATFORM_CREATED ' + record.table + ':' + actualId + '; table=' + record.fields.name);
                } else {
                    counts.unchanged++;
                    report('UNCHANGED ' + record.table + ':' + actualId);
                }
            } else if (dryRun) {
                counts.planned++;
                report('WOULD_CREATE ' + record.table + ':' + record.sys_id);
            } else {
                requireElevatedSession();
                if (record.table === 'sys_db_object' &&
                    query('sys_dictionary', { name: record.fields.name, element: '' }).next())
                    fail('unowned_collection:' + record.fields.name);
                var gr = table(record.table);
                gr.initialize();
                gr.setNewGuidValue(record.sys_id);
                for (var field in record.fields)
                    if (record.fields.hasOwnProperty(field)) gr.setValue(field, resolved(record.fields[field]));
                checkLegacyFieldPresence(false);
                // Do not suppress dictionary/table business rules: those materialize the schema.
                var id = value(gr.insert());
                if (id) {
                    counts.created++;
                    report('CREATED ' + record.table + ':' + (/^[0-9a-f]{32}$/.test(id) ? id : 'invalid_returned_id'));
                }
                if (id !== record.sys_id) fail('insert_failed:' + record.table + ':' + record.sys_id);
                var readBack = table(record.table);
                if (!readBack.get(record.sys_id)) fail('readback_missing:' + record.table + ':' + record.sys_id);
                baseline(record, readBack);
                if (record.table === 'sys_db_object') createdTables[record.fields.name] = true;
                verifyPhysical(record);
            }
        }
        if (!dryRun) {
            for (i = 0; i < records.length; i++) {
                if (!inspect(records[i])) fail('final_record_missing:' + records[i].sys_id);
                verifyPhysical(records[i]);
            }
            verifyRelations();
        }
        checkLegacyFieldPresence(false);
        for (i = 0; i < manifest.index_requests.length; i++) {
            var index = manifest.index_requests[i];
            report('INDEX_REVIEW ' + index.table + '(' + index.columns.join(',') + '), unique=' +
                index.unique + '; ' + index.mechanism);
        }
        report('LEGACY_SEPARATE_REVIEW_ONLY ' + manifest.legacy.table + ':' + manifest.legacy.sys_id +
            '; original_script_sha256=' + manifest.legacy.original_script_sha256 +
            '; fresh-read/revision-check the separate fanout artifact; never applied here.');
        report((dryRun ? 'DRY_RUN_COMPLETE' : 'STAGED_DISABLED_NOT_ACTIVATION_READY') +
            '; created=' + counts.created + ', unchanged=' + counts.unchanged + ', planned=' + counts.planned +
            '; physical indexes, ACL effectiveness, namespace and internal chat APIs require operator verification.');
        return counts;
    } catch (error) {
        if (error && error.coworkInstaller) throw error;
        // Platform exception messages can include data; only emit a fixed failure code.
        fail('platform_error_no_details_logged');
    }
}

function generate() {
    const manifest = createManifest();
    const text = JSON.stringify(manifest, null, 2);
    const source = [
        '// NONDEPLOYABLE TEMPLATE generated offline. Review INSTALLER.txt before target-specific adaptation.',
        '// Global Background Script; default dry run. Never patches the original harness.',
        '// Change BOTH deliberate gates only after independent review; do not invoke twice in one paste.',
        'var COWORK_INSTALL_DRY_RUN = true;',
        "var COWORK_INSTALL_REVIEWED_DEFINITION = '';",
        'var COWORK_INSTALL_MANIFEST = ' + text + ';',
        'var COWORK_INSTALL_MANIFEST_SHA256 = ' + JSON.stringify(sha256(JSON.stringify(manifest))) + ';',
        'var CoworkInstall = ' + installRuntime.toString() + ';',
        'CoworkInstall(COWORK_INSTALL_MANIFEST, COWORK_INSTALL_MANIFEST_SHA256, {',
        '    dryRun: COWORK_INSTALL_DRY_RUN, reviewedDefinition: COWORK_INSTALL_REVIEWED_DEFINITION',
        '});', ''
    ].join('\n');
    new vm.Script(source, { filename: 'install.js' });
    return source;
}

module.exports = { createManifest, generate, installRuntime, stableId, sha256 };
if (require.main === module) {
    const output = path.join(root, 'artifacts', 'install.js');
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, generate(), 'utf8');
    console.log('Offline, dry-run-default Background Script written: ' + output);
}
