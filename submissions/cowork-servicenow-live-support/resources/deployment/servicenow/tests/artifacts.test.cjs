'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const { RECORD_ID, ANCHOR, GUARD, sha256, prepare, proposal } = require('../tools/legacy-fanout-patch.cjs');
const { build } = require('../tools/build-artifacts.cjs');

function original(script = '(function () {\n  ' + ANCHOR + '\n  sendLegacy();\n})();') {
    return {
        sys_id: RECORD_ID, collection: 'sys_cs_message', when: 'async', active: 'true',
        filter_condition: '', sys_mod_count: '3', sys_updated_on: '2026-10-16 14:00:00',
        name: 'Synthetic test-only fanout fixture', script
    };
}

test('legacy helper CLI refuses all-zero target before any file access', () => {
    const result = spawnSync(process.execPath, [path.resolve(__dirname, '..', 'tools', 'legacy-fanout-patch.cjs')], {
        encoding: 'utf8'
    });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /independently review and pin the target rule/);
    assert.equal(RECORD_ID, '0'.repeat(32));
});

test('legacy patch makes exactly the narrow exclusion with original hash and full rollback record', () => {
    const record = original(); const artifact = prepare(record, sha256(record.script));
    assert.deepEqual(artifact.originalRecord, record);
    assert.equal(artifact.originalScriptSha256, sha256(record.script));
    assert.equal(artifact.patchedScript, record.script.replace(ANCHOR, ANCHOR + '\n  ' + GUARD));
    const change = proposal(record, artifact);
    assert.deepEqual(Object.keys(change.fields), ['script']);
    assert.equal(change.preconditions.sys_mod_count, '3');
    assert.equal(change.sys_id, RECORD_ID);
});

test('legacy patch and rollback are idempotent and preserve active/filter/timing', () => {
    const record = original(); const artifact = prepare(record, sha256(record.script));
    const patched = { ...record, script: artifact.patchedScript, sys_mod_count: '4' };
    assert.equal(proposal(patched, artifact).changed, false);
    assert.equal(proposal(patched, artifact, true).fields.script, record.script);
    assert.equal(proposal(record, artifact, true).changed, false);
    for (const patch of [{ active: 'false' }, { when: 'after' }, { filter_condition: 'active=true' }])
        assert.throws(() => proposal({ ...patched, ...patch }, artifact, true));
});

test('unexpected occurrence count, existing marker, wrong record or wrong original hash fail closed', () => {
    for (const script of ['nothing', ANCHOR + '\n' + ANCHOR, ANCHOR + "\n// u_cowork_session_id"])
        assert.throws(() => prepare(original(script), sha256(script)));
    const record = original();
    assert.throws(() => prepare(record, '0'.repeat(64)));
    assert.throws(() => prepare({ ...record, sys_id: 'wrong' }, sha256(record.script)));
    assert.throws(() => prepare({ ...record, sys_mod_count: undefined }, sha256(record.script)));
});

test('concurrent modifications and tampered rollback artifacts refuse overwrite', () => {
    const record = original(); const artifact = prepare(record, sha256(record.script));
    assert.throws(() => proposal({ ...record, script: artifact.patchedScript + '\n// changed' }, artifact, true));
    assert.throws(() => proposal({ ...record, name: 'Renamed by someone else' }, artifact));
    assert.throws(() => proposal(record, { ...artifact, patchedScript: artifact.patchedScript + '\n// changed' }));
    assert.throws(() => proposal(record, { ...artifact, originalRecord: { ...record, active: false } }, true));
});

test('CRLF and Graph value objects retain exact original script content', () => {
    const record = original('(function () {\r\n    ' + ANCHOR + '\r\n    sendLegacy();\r\n})();');
    const wrapped = { result: [{ ...record, sys_id: { value: RECORD_ID } }] };
    const artifact = prepare(wrapped, sha256(record.script));
    assert.ok(artifact.patchedScript.includes('\r\n    ' + GUARD + '\r\n'));
    assert.equal(artifact.originalRecord.script, record.script);
    assert.equal(prepare({ status: 200, data: { result: [record] } }, sha256(record.script)).originalRecord.script, record.script);
});

test('review bundle is deterministic, disabled, self-contained and contains no deploy secrets', () => {
    const first = build(); const second = build();
    assert.deepEqual(first, second);
    assert.equal(first.deployable_without_review, false);
    const definition = first.definition;
    assert.equal(definition.properties.find(p => p.name === 'cowork_bridge.enabled').value, 'false');
    assert.ok(definition.business_rules.every(rule => !rule.active));
    assert.ok(definition.rest_definition.resources.every(resource => resource.requires_authentication && resource.requires_acl_authorization));
    assert.equal(first.scripts.length, 9);
    assert.equal(new Set(first.identities.map(item => item.proposed_sys_id)).size, first.identities.length);
    assert.match(definition.legacy_amendment.original_script_sha256, /^[0-9a-f]{64}$/);
    assert.equal(definition.legacy_amendment.original_record, null);
    assert.ok(!JSON.stringify(first.scripts).includes('CopilotBridgeAuth'));
    assert.ok(!JSON.stringify(first.scripts).includes('impersonate'));
    assert.equal(definition.properties.find(p => p.name === 'cowork_bridge.outbox_delivery_enabled').value, 'false');
    assert.ok(definition.scheduled_jobs.every(job => !job.active));
    assert.ok(definition.tables.find(table => table.name === 'u_cowork_outbox').columns.find(column => column.name === 'u_event_id').unique);
});
