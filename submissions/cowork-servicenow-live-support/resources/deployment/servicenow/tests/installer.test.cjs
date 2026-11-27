'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { build } = require('../tools/build-artifacts.cjs');
const { createManifest, generate, installRuntime, stableId, sha256 } = require('../tools/generate-install.cjs');

const manifest = createManifest();
const manifestHash = sha256(JSON.stringify(manifest));
const applyOptions = { dryRun: false, reviewedDefinition: manifest.definition_sha256 };
const by = (table, name) => manifest.records.find(r => r.table === table && r.identity === name);
const legacyFields = ['u_copilot_upn', 'u_bridge_session_id'];

// Models only the deliberately supported metadata contract, not ServiceNow DDL/ACL behavior.
function fixture(options = {}) {
    const schema = new Map();
    const rows = new Map();
    const inserted = [];
    const output = [];
    const mutations = [];
    const legacyDataAccesses = [];
    const adminId = 'a'.repeat(32);
    const addTable = (name, fields) => {
        if (!schema.has(name)) schema.set(name, {});
        Object.assign(schema.get(name), Object.fromEntries(fields.map(field =>
            [field, { type: 'string', reference: '', length: 1000000 }])));
        if (!rows.has(name)) rows.set(name, []);
    };
    const setED = (table, field, type, reference = '') => {
        schema.get(table)[field] = { type, reference, length: 1000000 };
    };
    for (const record of manifest.records) {
        addTable(record.table, [...Object.keys(record.fields), 'sys_id']);
        if (record.fields.sys_scope) setED(record.table, 'sys_scope', 'reference', 'sys_scope');
        for (const field of record.booleans) setED(record.table, field, 'boolean');
    }
    addTable('sys_scope', ['sys_id', 'scope']);
    addTable('sys_user_role_contains', ['sys_id', 'role', 'contains']);
    addTable('interaction', ['sys_id', 'state', 'assigned_to', 'channel_metadata_document',
        'opened_for', ...(options.legacyFields ?? legacyFields)]);
    addTable('sys_cs_message', ['sys_id', 'conversation', 'sender', 'message_type', 'q_data_message_type', 'payload']);
    addTable('sys_cs_conversation', ['sys_id']);
    setED('sys_ws_definition', 'enforce_acl', 'glide_list', 'sys_security_acl');
    setED('sys_ws_operation', 'enforce_acl', 'glide_list', 'sys_security_acl');
    setED('sys_ws_operation', 'web_service_definition', 'reference', 'sys_ws_definition');
    setED('sys_security_acl_role', 'sys_security_acl', 'reference', 'sys_security_acl');
    setED('sys_security_acl_role', 'sys_user_role', 'reference', 'sys_user_role');
    setED('sysauto_script', 'run_period', 'glide_duration');
    rows.get('sys_scope').push({ sys_id: 'global', scope: 'global' });
    rows.get('sys_user_role').push({ sys_id: adminId, name: 'admin' });
    const legacy = { sys_id: manifest.legacy.sys_id, name: 'Synthetic original harness',
        script: 'DO NOT CHANGE ORIGINAL', active: '1' };
    rows.get('sys_script').push(legacy);

    function materialize(row) {
        if (row.internal_type === 'collection' && !options.missingTable) {
            addTable(row.name, ['sys_id', 'sys_created_on', 'sys_updated_on',
                'sys_created_by', 'sys_updated_by', 'sys_mod_count']);
        } else if (row.element && !options.missingField) {
            if (!schema.has(row.name)) return;
            schema.get(row.name)[row.element] = {
                type: row.internal_type, reference: row.reference || '',
                length: options.shortField ? 1 : Number(row.max_length || 40)
            };
        }
    }
    class GlideRecord {
        constructor(table) {
            this.table = table;
            this.filters = [];
            this.limit = Infinity;
            this.current = null;
            this.results = [];
            this.cursor = 0;
        }
        isValid() { return schema.has(this.table); }
        isValidField(field) { return !!schema.get(this.table)?.[field]; }
        getElement(field) {
            assert.ok(this.isValidField(field), this.table + '.' + field);
            const ed = schema.get(this.table)[field];
            return { getReferenceTable: () => ed.reference, getED: () => ({
                getInternalType: () => ed.type, getLength: () => ed.length, getReference: () => ed.reference
            }) };
        }
        addQuery(field, value) {
            assert.ok(this.isValidField(field), 'Unknown query field: ' + this.table + '.' + field);
            this.filters.push(row => String(row[field] ?? '') === String(value));
        }
        addNullQuery(field) { this.filters.push(row => row[field] == null || row[field] === ''); }
        setLimit(limit) { this.limit = limit; }
        query() {
            if (this.table === 'interaction') legacyDataAccesses.push('query interaction');
            this.results = (rows.get(this.table) || []).filter(row => this.filters.every(test => test(row))).slice(0, this.limit);
            this.cursor = 0;
        }
        next() {
            this.current = this.results[this.cursor++] || null;
            return !!this.current;
        }
        get(id) {
            if (this.table === 'interaction') legacyDataAccesses.push('get interaction');
            this.current = (rows.get(this.table) || []).find(row => row.sys_id === id) || null;
            return !!this.current;
        }
        getValue(field) {
            assert.ok(this.isValidField(field), 'Unknown read field: ' + this.table + '.' + field);
            if (this.table === 'interaction' && legacyFields.includes(field)) legacyDataAccesses.push('read ' + field);
            return this.current?.[field] ?? null;
        }
        getUniqueValue() { return this.current?.sys_id ?? null; }
        initialize() { this.current = {}; }
        setNewGuidValue(id) { this.current.sys_id = id; }
        setValue(field, value) {
            if (this.table === 'interaction' && legacyFields.includes(field)) legacyDataAccesses.push('write ' + field);
            assert.ok(this.isValidField(field), 'Unknown write field: ' + this.table + '.' + field);
            this.current[field] = String(value);
        }
        insert() {
            const row = { ...this.current };
            if (options.failInsertTable === this.table) return null;
            assert.ok(!rows.get(this.table).some(r => r.sys_id === row.sys_id), 'Duplicate primary key');
            for (const field of Object.keys(row))
                if (schema.get(this.table)[field]?.type === 'boolean') row[field] = row[field] === 'true' ? '1' : '0';
            if (options.mutateOnInsert) options.mutateOnInsert(this.table, row);
            rows.get(this.table).push(row);
            inserted.push({ table: this.table, ...row });
            if (this.table === 'sys_dictionary') materialize(row);
            if (this.table === 'sys_db_object' && options.autoCollection) {
                const collection = {
                    sys_id: sha256('platform-generated:' + row.name).slice(0, 32),
                    name: row.name, element: '', internal_type: 'collection', sys_scope: 'global'
                };
                if (options.mutateCollection) options.mutateCollection(collection);
                rows.get('sys_dictionary').push(collection);
                materialize(collection);
            }
            return row.sys_id;
        }
        update() { mutations.push('update'); throw new Error('UPDATE MUST NEVER BE CALLED'); }
        deleteRecord() { mutations.push('delete'); throw new Error('DELETE MUST NEVER BE CALLED'); }
        setWorkflow() { throw new Error('SCHEMA WORKFLOW MUST NOT BE DISABLED'); }
    }
    const context = {
        GlideRecord,
        GlideDigest: function () { this.getSHA256Hex = sha256; },
        gs: {
            getProperty: name => name === 'instance_name' ? (options.instance || 'example') : '',
            getCurrentApplicationId: () => options.scope || 'global',
            getCurrentScopeName: () => options.scopeName || 'global',
            getSession: () => ({ getRoles: () => options.roles === undefined ? 'admin,security_admin' : options.roles }),
            requireSecurityAdmin: () => { if (options.noElevation) throw new Error('sensitive platform detail'); },
            print: message => output.push(String(message))
        }
    };
    vm.createContext(context);
    const run = (opts = {}, payload = manifest, expected = manifestHash) => {
        context.input = payload; context.expected = expected; context.options = opts;
        return vm.runInContext('(' + installRuntime.toString() + ')(input, expected, options)', context);
    };
    return { schema, rows, inserted, output, mutations, legacy, legacyDataAccesses, run, context, adminId };
}

test('standalone artifact parses, is deterministic and matches current sources and definition IDs', () => {
    const first = generate();
    assert.equal(first, generate());
    new vm.Script(first);
    assert.equal(fs.readFileSync(path.resolve(__dirname, '..', 'artifacts', 'install.js'), 'utf8'), first);
    for (const id of build().identities)
        assert.ok(manifest.records.some(r => r.table === id.table && r.sys_id === id.proposed_sys_id));
    assert.equal(new Set(manifest.records.map(r => r.sys_id)).size, manifest.records.length);
    for (const source of build().scripts)
        assert.ok(manifest.records.some(r => r.fields.script === source.source || r.fields.operation_script === source.source));
});

test('dry-run is default even for truthy/string false; standalone default performs zero writes', () => {
    for (const opts of [{}, { dryRun: true }, { dryRun: 'false' }, { dryRun: 0 }]) {
        const f = fixture();
        const counts = f.run(opts);
        assert.equal(counts.planned, manifest.records.length);
        assert.equal(counts.created, 0);
        assert.equal(f.inserted.length, 0);
    }
    const f = fixture();
    vm.runInContext(generate(), f.context);
    assert.equal(f.inserted.length, 0);
    assert.ok(f.output.some(line => line.includes('DRY_RUN_COMPLETE')));
});

test('nondeployable template pins and empty-instance legacy sentinel remain exact', () => {
    const target = build().definition.target;
    assert.equal(target.instance, 'example.invalid');
    assert.equal(target.namespace, 'cowork_review');
    assert.equal(target.base_path, '/api/cowork_review/cowork_bridge');
    assert.equal(manifest.instance, 'example');
    assert.equal(manifest.scope, 'global');
    assert.equal(manifest.namespace, 'cowork_review');
    assert.equal(manifest.legacy.sys_id, '0'.repeat(32));
    assert.equal(manifest.legacy.original_script_sha256, '0'.repeat(64));
    const f = fixture();
    f.rows.set('sys_script', []);
    assert.equal(f.run().planned, manifest.records.length);
    assert.equal(f.inserted.length, 0);
});

test('shipped template matches dry-run source and in-memory apply changes only the two reviewed gates', () => {
    const folder = path.resolve(__dirname, '..', 'artifacts');
    const dryRun = fs.readFileSync(path.join(folder, 'install.js'), 'utf8');
    assert.equal(dryRun, generate());
    assert.deepEqual(JSON.parse(fs.readFileSync(path.join(folder, 'install-bundle.json'), 'utf8')), build());
    assert.match(dryRun, /NONDEPLOYABLE TEMPLATE/);
    assert.equal((dryRun.match(/var COWORK_INSTALL_DRY_RUN = true;/g) || []).length, 1);
    assert.equal((dryRun.match(/var COWORK_INSTALL_REVIEWED_DEFINITION = '';/g) || []).length, 1);
    const apply = dryRun.replace('var COWORK_INSTALL_DRY_RUN = true;', 'var COWORK_INSTALL_DRY_RUN = false;')
            .replace("var COWORK_INSTALL_REVIEWED_DEFINITION = '';",
                'var COWORK_INSTALL_REVIEWED_DEFINITION = ' + JSON.stringify(manifest.definition_sha256) + ';');
    new vm.Script(apply);
    const f = fixture({ legacyFields: [] });
    vm.runInContext(apply, f.context);
    assert.equal(f.inserted.length, 83);
    assert.deepEqual(f.legacyDataAccesses, []);
    for (const field of legacyFields)
        assert.ok(!manifest.records.some(record => record.table === 'sys_dictionary' &&
            record.fields.name === 'interaction' && record.fields.element === field));
});

test('absent, empty, populated and partial legacy schemas stage without reading or writing legacy data', () => {
    for (const present of [[], [legacyFields[0]], [legacyFields[1]], legacyFields]) {
        for (const value of ['', 'legacy-private-owner']) {
            const f = fixture({ legacyFields: present });
            f.rows.get('interaction').push({ sys_id: 'b'.repeat(32),
                ...Object.fromEntries(present.map(field => [field, value])) });
            const before = JSON.stringify(f.rows.get('interaction'));
            assert.equal(f.run().planned, 83);
            assert.equal(f.inserted.length, 0);
            assert.equal(f.run(applyOptions).created, 83);
            assert.equal(f.run(applyOptions).unchanged, 83);
            assert.equal(f.inserted.length, 83);
            assert.equal(JSON.stringify(f.rows.get('interaction')), before);
            assert.deepEqual(f.legacyDataAccesses, []);
            for (const field of legacyFields) {
                assert.equal(!!f.schema.get('interaction')[field], present.includes(field));
                assert.ok(f.output.some(line => line.includes('LEGACY_FIELD_PRESENCE interaction.' +
                    field + '=' + present.includes(field))));
            }
            assert.ok(!f.output.join('\n').includes('legacy-private-owner'));
        }
    }
});

test('legacy field presence drift after capture or elevation revalidation stops before first insert', () => {
    for (const field of legacyFields) {
        for (const initiallyPresent of [false, true]) {
            for (const phase of ['preflight', 'elevation']) {
                const f = fixture({ legacyFields: initiallyPresent ? legacyFields : [] });
                const drift = () => {
                    if (initiallyPresent) delete f.schema.get('interaction')[field];
                    else f.schema.get('interaction')[field] = { type: 'string', reference: '', length: 80 };
                };
                if (phase === 'preflight') {
                    const print = f.context.gs.print;
                    f.context.gs.print = message => {
                        print(message);
                        if (message.includes('LEGACY_FIELD_PRESENCE interaction.u_bridge_session_id=')) drift();
                    };
                } else {
                    let calls = 0;
                    f.context.gs.getSession = () => {
                        if (++calls === 2) drift();
                        return { getRoles: () => 'admin,security_admin' };
                    };
                }
                assert.throws(() => f.run(applyOptions), new RegExp('legacy_field_presence_changed:interaction\\.' + field));
                assert.equal(f.inserted.length, 0);
                assert.deepEqual(f.legacyDataAccesses, []);
            }
        }
    }
});

test('legacy field presence drift between inserts or at completion stops without repair or success report', () => {
    for (const field of legacyFields) {
        for (const initiallyPresent of [false, true]) {
            for (const after of [1, 83]) {
                const f = fixture({ legacyFields: initiallyPresent ? legacyFields : [] });
                const print = f.context.gs.print;
                f.context.gs.print = message => {
                    print(message);
                    if (message.includes('] CREATED ') && f.inserted.length === after) {
                        if (initiallyPresent) delete f.schema.get('interaction')[field];
                        else f.schema.get('interaction')[field] = { type: 'string', reference: '', length: 80 };
                    }
                };
                assert.throws(() => f.run(applyOptions), /legacy_field_presence_changed/);
                assert.equal(f.inserted.length, after);
                assert.deepEqual(f.mutations, []);
                assert.deepEqual(f.legacyDataAccesses, []);
                assert.ok(!f.output.some(line => line.includes('STAGED_DISABLED_NOT_ACTIVATION_READY')));
            }
        }
    }
    const f = fixture({ legacyFields: [] });
    const print = f.context.gs.print;
    f.context.gs.print = message => {
        print(message);
        if (message.includes('WOULD_CREATE')) f.schema.get('interaction').u_copilot_upn = { type: 'string' };
    };
    assert.throws(() => f.run(), /legacy_field_presence_changed/);
    assert.equal(f.inserted.length, 0);
    assert.ok(!f.output.some(line => line.includes('DRY_RUN_COMPLETE')));
});

test('explicit apply requires exact review hash, active session elevation and any present native guard', () => {
    for (const opts of [{ dryRun: false }, { dryRun: false, reviewedDefinition: 'wrong' }]) {
        const f = fixture();
        assert.throws(() => f.run(opts), /review_required/);
        assert.equal(f.inserted.length, 0);
    }
    const f = fixture({ noElevation: true });
    assert.throws(() => f.run(applyOptions), /platform_error_no_details_logged/);
    assert.equal(f.inserted.length, 0);
    assert.ok(!f.output.join('\n').includes('sensitive platform detail'));
    delete f.context.gs.requireSecurityAdmin;
    assert.equal(f.run(applyOptions).created, manifest.records.length);
    const missing = fixture();
    delete missing.context.gs.getSession;
    assert.throws(() => missing.run(applyOptions), /active_session_roles_API_required/);
    assert.equal(missing.inserted.length, 0);
});

test('session roles require exact security_admin token with no admin or substring shortcut', () => {
    for (const roles of ['admin', 'admin,not_security_admin', '[admin, security_admin_backup]',
        ',admin,agent_security_admin', ',admin,agent_security_admin,security_admin_extra',
        '["admin","security_admin.other"]', '{security_admin:true}', '[admin,security_admin',
        '[["security_admin"]]', ['security_admin', 1], null, {}, '', ['admin']]) {
        const f = fixture({ roles });
        delete f.context.gs.requireSecurityAdmin;
        f.context.gs.hasRole = () => true;
        assert.throws(() => f.run(applyOptions), /security_admin_elevation_required|unrecognized_session_roles/);
        assert.equal(f.inserted.length, 0);
    }
    for (const roles of ['admin,security_admin', '[admin, security_admin]', '["admin","security_admin"]',
        ',admin,agent_security_admin,security_admin',
        ['admin', 'security_admin'], { size: () => 2, get: index => ['admin', 'security_admin'][index] },
        { toString: () => '[admin, security_admin]' }]) {
        const f = fixture({ roles, scopeName: 'rhino.global' });
        delete f.context.gs.requireSecurityAdmin;
        assert.equal(f.run(applyOptions).created, manifest.records.length);
    }
});

test('observed prefixed-comma session with only agent_security_admin refuses ACL writes', () => {
    const f = fixture({ roles: ',admin,agent_security_admin', scopeName: 'rhino.global' });
    delete f.context.gs.requireSecurityAdmin;
    f.context.gs.hasRole = () => true;
    assert.throws(() => f.run(applyOptions), /security_admin_elevation_required/);
    assert.equal(f.inserted.length, 0);
    assert.ok(!f.output.join('\n').includes('agent_security_admin'));
});

test('elevation loss between preflight and insert stops with zero writes', () => {
    const f = fixture();
    let calls = 0;
    f.context.gs.getSession = () => ({ getRoles: () => ++calls === 1 ? 'admin,security_admin' : 'admin' });
    assert.throws(() => f.run(applyOptions), /security_admin_elevation_required/);
    assert.equal(f.inserted.length, 0);
});

test('wrong instance, application ID and scope name fail before all writes', () => {
    for (const options of [{ instance: 'prod' }, { instance: 'example.invalid' },
        { instance: 'another-instance' }, { instance: 'example.invalid' },
        { scope: 'another-app' }, { scopeName: 'x_another' }, { scopeName: 'rhino.global.other' }]) {
        const f = fixture(options);
        assert.throws(() => f.run(applyOptions), /wrong_instance|wrong_scope/);
        assert.equal(f.inserted.length, 0);
    }
});

test('create-only apply verifies baseline hashes and identical rerun is unchanged', () => {
    const f = fixture();
    const before = JSON.stringify(f.legacy);
    const first = f.run(applyOptions);
    assert.equal(first.created, manifest.records.length);
    const second = f.run(applyOptions);
    assert.equal(second.created, 0);
    assert.equal(second.unchanged, manifest.records.length);
    assert.equal(f.inserted.length, manifest.records.length);
    assert.equal(JSON.stringify(f.legacy), before);
    assert.deepEqual(f.mutations, []);
    assert.ok(f.output.some(line => line.includes('STAGED_DISABLED_NOT_ACTIVATION_READY')));
    assert.ok(f.output.some(line => line.includes('LEGACY_SEPARATE_REVIEW_ONLY')));
    assert.ok(f.output.every(line => !line.includes('DO NOT CHANGE ORIGINAL')));
});

test('original record is not a write target and all metadata targets stay in the exact allowlist', () => {
    const allowed = new Set(['sys_user_role', 'sys_security_acl', 'sys_security_acl_role',
        'sys_db_object', 'sys_dictionary', 'sys_choice', 'sys_properties', 'sys_script_include',
        'sys_ws_definition', 'sys_ws_operation', 'sys_script', 'sysauto_script', 'sysevent_register']);
    for (const record of manifest.records) {
        assert.ok(allowed.has(record.table));
        assert.notEqual(record.sys_id, manifest.legacy.sys_id);
        assert.equal(record.sys_id, stableId(record.table, record.identity));
        if (record.table === 'sys_dictionary' && record.fields.name === 'interaction')
            assert.match(record.fields.element, /^u_cowork_(session_id|upn)$/);
    }
    const runtime = installRuntime.toString();
    assert.doesNotMatch(runtime, /\.(update|updateMultiple|deleteRecord|deleteMultiple|setWorkflow|execute|eventQueue)\s*\(/);
    assert.doesNotMatch(runtime, /sys_user['"]|oauth_entity|GlideOAuth|RESTMessageV2|GlideTableCreator/);
    assert.doesNotMatch(runtime, /get\s*\(\s*manifest\.legacy/);
});

test('schema, REST ACL reference/type and unsupported fields fail closed during preflight', () => {
    for (const mutate of [
        f => f.schema.delete('sys_cs_message'),
        f => delete f.schema.get('sys_ws_operation').requires_authentication,
        f => delete f.schema.get('sys_ws_definition').namespace,
        f => delete f.schema.get('sysevent_register').event_name,
        f => delete f.schema.get('sys_dictionary').unique,
        f => { f.schema.get('sys_ws_definition').enforce_acl.type = 'boolean'; },
        f => { f.schema.get('sys_ws_operation').enforce_acl.reference = 'sys_user_role'; },
        f => { f.schema.get('sys_ws_operation').web_service_definition.reference = 'sys_scope'; },
        f => { f.schema.get('sys_dictionary').sys_scope.reference = 'sys_app'; },
        f => { f.schema.get('sysauto_script').run_period.type = 'string'; }
    ]) {
        const f = fixture();
        mutate(f);
        assert.throws(() => f.run(applyOptions), /missing_table|missing_field|schema_mismatch/);
        assert.equal(f.inserted.length, 0);
    }
});

test('every record collision is checked before inserting anything, including the last event', () => {
    for (const record of [manifest.records[0], by('sys_ws_definition', '/api/cowork_review/cowork_bridge'),
        manifest.records[manifest.records.length - 1]]) {
        const f = fixture();
        f.rows.get(record.table).push({ ...record.fields, sys_id: 'b'.repeat(32) });
        assert.throws(() => f.run(applyOptions), /name_collision/);
        assert.equal(f.inserted.length, 0);
    }
    const f = fixture();
    f.rows.get('sys_script').push({ ...by('sys_script', 'Cowork agent message callback').fields,
        name: 'Unrelated record', sys_id: by('sys_script', 'Cowork agent message callback').sys_id });
    assert.throws(() => f.run(applyOptions), /baseline_drift/);
    assert.equal(f.inserted.length, 0);
});

test('renamed REST path or alternate-name API cannot bypass natural-key collision checks', () => {
    const f = fixture();
    const api = by('sys_ws_definition', '/api/cowork_review/cowork_bridge');
    f.rows.get(api.table).push({ ...api.fields, sys_id: 'b'.repeat(32), name: 'Another API' });
    assert.throws(() => f.run(applyOptions), /name_collision/);
    assert.equal(f.inserted.length, 0);
});

test('configured properties, activated rules, scripts, roles and scopes are never reset on rerun', () => {
    for (const [table, identity, field, changed] of [
        ['sys_properties', 'cowork_bridge.webhook_url', 'value', 'sensitive-value-never-log'],
        ['sys_script', 'Cowork agent message callback', 'active', '1'],
        ['sys_script_include', 'CoworkBridge', 'script', '/* different */'],
        ['sys_script_include', 'CoworkBridge', 'sys_scope', 'other'],
        ['sys_user_role', 'cowork_bridge.integration', 'elevated_privilege', '1'],
        ['sys_ws_definition', '/api/cowork_review/cowork_bridge', 'enforce_acl', 'extra-acl']
    ]) {
        const f = fixture();
        f.run(applyOptions);
        const record = f.rows.get(table).find(row => row.sys_id === by(table, identity).sys_id);
        record[field] = changed;
        const inserted = f.inserted.length;
        assert.throws(() => f.run(applyOptions), /baseline_drift/);
        assert.equal(f.inserted.length, inserted);
        assert.equal(record[field], changed);
        assert.ok(!f.output.join('\n').includes('sensitive-value-never-log'));
    }
});

test('unexpected ACL role links or inherited roles block apply and are not removed', () => {
    for (const relation of ['acl', 'role', 'operation']) {
        const f = fixture();
        const acl = manifest.records.find(r => r.table === 'sys_security_acl');
        if (relation === 'acl') f.rows.get('sys_security_acl_role').push({
            sys_id: 'b'.repeat(32), sys_security_acl: acl.sys_id, sys_user_role: 'c'.repeat(32)
        });
        else if (relation === 'role') f.rows.get('sys_user_role_contains').push({
            sys_id: 'b'.repeat(32), role: by('sys_user_role', 'cowork_bridge.integration').sys_id,
            contains: f.adminId
        });
        else f.rows.get('sys_ws_operation').push({
            sys_id: 'b'.repeat(32), name: 'Unexpected resource',
            web_service_definition: by('sys_ws_definition', '/api/cowork_review/cowork_bridge').sys_id
        });
        assert.throws(() => f.run(applyOptions), /unexpected_acl_role|unexpected_inherited_role|unexpected_rest_operation/);
        assert.equal(f.inserted.length, 0);
    }
});

test('metadata-only tables and missing/short physical fields stop', () => {
    for (const options of [{ missingTable: true }, { missingField: true },
        { shortField: true }, { autoCollection: true, missingTable: true }]) {
        const f = fixture(options);
        assert.throws(() => f.run(applyOptions), /missing_table|missing_field|backing_field_length|name_collision/);
        assert.ok(f.inserted.length > 0);
        assert.ok(!f.inserted.some(r => r.table === 'sys_ws_definition'));
        assert.ok(!f.inserted.some(r => r.table === 'sys_script_include'));
        assert.deepEqual(f.mutations, []);
        assert.ok(f.output.some(line => line.includes('No rollback/delete attempted')));
    }
});

test('platform-generated collections are bound to newly inserted owned tables and reused on rerun', () => {
    const f = fixture({ autoCollection: true, scopeName: 'rhino.global' });
    delete f.context.gs.requireSecurityAdmin;
    const first = f.run(applyOptions);
    assert.equal(first.created, manifest.records.length);
    assert.equal(first.unchanged, 0);
    assert.equal(f.inserted.length, manifest.records.length - 2);
    for (const name of ['u_cowork_command', 'u_cowork_outbox']) {
        const id = sha256('platform-generated:' + name).slice(0, 32);
        assert.ok(f.output.some(line => line.includes('PLATFORM_CREATED sys_dictionary:' + id)));
        assert.ok(!f.inserted.some(row => row.sys_id === by('sys_dictionary', name + '.').sys_id));
        assert.ok(f.schema.get(name).u_status);
    }
    const second = f.run(applyOptions);
    assert.equal(second.created, 0);
    assert.equal(second.unchanged, manifest.records.length);
    assert.deepEqual(f.mutations, []);
});

test('pre-existing unrelated collection cannot be adopted before its table is owned', () => {
    const f = fixture({ autoCollection: true });
    f.rows.get('sys_dictionary').push({
        sys_id: 'f'.repeat(32), name: 'u_cowork_command', element: '', internal_type: 'collection', sys_scope: 'global'
    });
    assert.throws(() => f.run(applyOptions), /unowned_collection/);
    assert.equal(f.inserted.length, 0);
});

test('wrong collection type/scope or duplicate collection and parent drift fail without updates', () => {
    for (const change of [
        c => { c.internal_type = 'string'; },
        c => { c.sys_scope = 'other'; }
    ]) {
        const f = fixture({ autoCollection: true, mutateCollection: change });
        assert.throws(() => f.run(applyOptions), /collection_baseline_drift/);
        assert.ok(!f.inserted.some(row => row.table === 'sys_dictionary'));
        assert.deepEqual(f.mutations, []);
    }
    for (const change of [
        f => f.rows.get('sys_dictionary').push({
            sys_id: 'f'.repeat(32), name: 'u_cowork_command', element: '', internal_type: 'collection', sys_scope: 'global'
        }),
        f => { f.rows.get('sys_db_object')[0].ws_access = '1'; },
        f => { f.rows.get('sys_db_object')[0].sys_id = 'f'.repeat(32); }
    ]) {
        const f = fixture({ autoCollection: true });
        f.run(applyOptions);
        change(f);
        const before = f.inserted.length;
        assert.throws(() => f.run(applyOptions), /ambiguous_collection|baseline_drift|name_collision/);
        assert.equal(f.inserted.length, before);
        assert.deepEqual(f.mutations, []);
    }
});

test('unowned backing schema is not mistaken for an installable absent metadata record', () => {
    for (const mutate of [
        f => f.schema.set('u_cowork_command', { sys_id: { type: 'string' } }),
        f => { f.schema.get('interaction').u_cowork_session_id = { type: 'string' }; }
    ]) {
        const f = fixture();
        mutate(f);
        assert.throws(() => f.run(applyOptions), /unowned_backing_table|unowned_backing_field/);
        assert.equal(f.inserted.length, 0);
    }
});

test('insert failure and platform rewrite are readback-checked without updates or enabling', () => {
    for (const options of [{ failInsertTable: 'sys_ws_definition' }, {
        mutateOnInsert: (table, row) => { if (table === 'sys_ws_definition') row.namespace = 'wrong'; }
    }]) {
        const f = fixture(options);
        assert.throws(() => f.run(applyOptions), /insert_failed|baseline_drift/);
        assert.deepEqual(f.mutations, []);
        assert.ok(!f.inserted.some(r => r.table === 'sys_ws_operation'));
        assert.ok(!f.inserted.some(r => r.table === 'sys_script'));
    }
});

test('REST security binds only own ACL using real fields, not boolean enforce_acl or fabricated M2M', () => {
    const acl = manifest.records.find(r => r.table === 'sys_security_acl' && r.fields.type === 'REST_Endpoint');
    assert.equal(acl.fields.operation, 'execute');
    assert.equal(acl.fields.admin_overrides, 'false');
    assert.match(acl.fields.script, /getUserID/);
    assert.match(acl.fields.script, /cowork_bridge\.integration_user_sys_id/);
    const links = manifest.records.filter(r => r.table === 'sys_security_acl_role' && r.fields.sys_security_acl === acl.sys_id);
    assert.equal(links.length, 1);
    assert.equal(links[0].fields.sys_user_role, by('sys_user_role', 'cowork_bridge.integration').sys_id);
    const api = by('sys_ws_definition', '/api/cowork_review/cowork_bridge');
    assert.equal(api.fields.namespace, 'cowork_review');
    assert.equal(api.fields.enforce_acl, acl.sys_id);
    assert.equal(api.fields.active, 'false');
    assert.ok(!('requires_authentication' in api.fields));
    const ops = manifest.records.filter(r => r.table === 'sys_ws_operation');
    assert.equal(ops.length, 3);
    for (const op of ops) {
        assert.equal(op.fields.web_service_definition, api.sys_id);
        assert.equal(op.fields.enforce_acl, acl.sys_id);
        assert.equal(op.fields.active, 'false');
        assert.equal(op.fields.requires_authentication, 'true');
        assert.equal(op.fields.requires_acl_authorization, 'true');
    }
});

test('table collections, choices, unique requests, protections and disabled runtime are explicit', () => {
    const f = fixture();
    f.run(applyOptions);
    for (const table of ['u_cowork_command', 'u_cowork_outbox']) {
        const db = by('sys_db_object', table);
        assert.equal(db.fields.create_access_controls, 'false');
        assert.equal(db.fields.ws_access, 'false');
        const collection = by('sys_dictionary', table + '.');
        assert.equal(collection.fields.internal_type, 'collection');
        assert.equal(collection.fields.element, '');
        assert.ok(f.schema.has(table));
        for (const operation of ['create', 'read', 'write', 'delete']) {
            const acl = by('sys_security_acl', 'record:' + table + ':' + operation);
            assert.match(acl.fields.script, /hasRole\('admin'\)/);
            assert.ok(manifest.records.some(r => r.table === 'sys_security_acl_role' &&
                r.fields.sys_security_acl === acl.sys_id && r.fields.sys_user_role === '@admin_role'));
        }
    }
    assert.equal(by('sys_dictionary', 'u_cowork_command.u_key').fields.unique, 'true');
    assert.equal(by('sys_dictionary', 'u_cowork_outbox.u_event_id').fields.unique, 'true');
    assert.equal(by('sys_dictionary', 'interaction.u_cowork_session_id').fields.unique, 'false');
    assert.equal(manifest.index_requests.filter(index => index.unique).length, 2);
    assert.equal(manifest.index_requests.filter(index => !index.unique).length, 4);
    assert.equal(manifest.records.filter(r => r.table === 'sys_choice').length, 11);
    assert.ok(manifest.records.filter(r => r.table === 'sys_choice').every(r => !('sys_scope' in r.fields)));
    for (const record of manifest.records) {
        if (['sys_script', 'sysauto_script'].includes(record.table)) assert.equal(record.fields.active, 'false');
        if (record.table === 'sys_properties' && record.fields.name.endsWith('enabled'))
            assert.equal(record.fields.value, 'false');
    }
    const job = by('sysauto_script', 'Cowork outbox retry');
    assert.equal(job.fields.run_as, undefined);
    assert.equal(job.fields.run_period, '1970-01-01 00:01:00');
    assert.equal(by('sysevent_register', 'cowork_bridge.outbox.dead_letter').fields.event_name, 'cowork_bridge.outbox.dead_letter');
});

test('platform-computed metadata is not mistaken for deployment drift', () => {
    assert.equal(by('sys_db_object', 'u_cowork_command').fields.label, 'Cowork Command');
    assert.equal(by('sys_ws_definition', '/api/cowork_review/cowork_bridge').fields.default_version, undefined);
    assert.equal(by('sys_dictionary', 'u_cowork_command.u_key').fields.calculation, undefined);
    assert.ok(by('sysevent_register', 'cowork_bridge.outbox.dead_letter').fields.description.length <= 100);
});

test('tampered artifact manifest is rejected without attempting to repair baselines', () => {
    const f = fixture();
    const changed = structuredClone(manifest);
    changed.records[0].fields.name = 'foreign_role';
    assert.throws(() => f.run(applyOptions, changed), /artifact_hash_mismatch/);
    assert.equal(f.inserted.length, 0);
    assert.throws(() => f.run(applyOptions, changed, sha256(JSON.stringify(changed))), /ownership_violation/);
    assert.equal(f.inserted.length, 0);
});
