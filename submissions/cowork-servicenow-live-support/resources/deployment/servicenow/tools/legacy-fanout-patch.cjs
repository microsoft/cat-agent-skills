'use strict';

const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');
const RECORD_ID = '00000000000000000000000000000000';
const ANCHOR = 'if (!ix.next()) return;';
const GUARD = "if (ix.getValue('u_cowork_session_id')) return; // Cowork sessions use their isolated callback only.";
const sha256 = value => crypto.createHash('sha256').update(value, 'utf8').digest('hex');

function value(field) {
    return field && typeof field === 'object' && 'value' in field ? field.value : field;
}

function normalize(record) {
    if (record?.data?.result) record = record.data.result;
    if (record?.result) record = record.result;
    if (Array.isArray(record)) {
        if (record.length !== 1) throw new Error('Exactly one exported sys_script record is required.');
        record = record[0];
    }
    if (!record || typeof record !== 'object') throw new Error('Expected a sys_script JSON record.');
    return Object.fromEntries(Object.entries(record).map(([key, field]) => [key, value(field)]));
}

function assertTarget(record) {
    if (record.sys_id !== RECORD_ID || record.collection !== 'sys_cs_message' ||
        record.when !== 'async' || ![true, 'true', '1', 1].includes(record.active) ||
        record.filter_condition !== '' || typeof record.script !== 'string' ||
        record.sys_mod_count === undefined)
        throw new Error('Target identity/timing/active/filter/revision preconditions do not match.');
}

function patchScript(script) {
    if (script.split(ANCHOR).length !== 2 || script.includes('u_cowork_session_id'))
        throw new Error('Expected exactly one unmodified interaction lookup anchor.');
    const newline = script.includes('\r\n') ? '\r\n' : '\n';
    const position = script.indexOf(ANCHOR);
    const lineStart = script.lastIndexOf('\n', position) + 1;
    const indent = script.slice(lineStart, position).match(/^\s*/)[0];
    return script.replace(ANCHOR, ANCHOR + newline + indent + GUARD);
}

function prepare(record, expectedOriginalSha256) {
    const originalRecord = normalize(record);
    assertTarget(originalRecord);
    if (!/^[a-f0-9]{64}$/.test(expectedOriginalSha256) ||
        sha256(originalRecord.script) !== expectedOriginalSha256)
        throw new Error('Original script SHA-256 does not match the separately reviewed pin.');
    const patchedScript = patchScript(originalRecord.script);
    return {
        format: 'cowork-fanout-patch-v1',
        table: 'sys_script',
        sys_id: RECORD_ID,
        originalScriptSha256: expectedOriginalSha256,
        originalRecordSha256: sha256(JSON.stringify(originalRecord)),
        patchedScriptSha256: sha256(patchedScript),
        originalRecord,
        patchedScript
    };
}

function verifyArtifact(artifact) {
    if (artifact.format !== 'cowork-fanout-patch-v1' || artifact.table !== 'sys_script' ||
        artifact.sys_id !== RECORD_ID) throw new Error('Wrong patch artifact.');
    const expected = prepare(artifact.originalRecord, artifact.originalScriptSha256);
    if (expected.originalRecordSha256 !== artifact.originalRecordSha256 ||
        expected.patchedScriptSha256 !== artifact.patchedScriptSha256 ||
        expected.patchedScript !== artifact.patchedScript)
        throw new Error('Patch or rollback snapshot has been modified.');
}

function proposal(record, artifact, rollback = false) {
    verifyArtifact(artifact);
    const current = normalize(record);
    assertTarget(current);
    // ServiceNow updates these audit fields when the script changes; do not overwrite them.
    const audit = new Set(['script', 'sys_mod_count', 'sys_updated_on', 'sys_updated_by']);
    for (const key of Object.keys(artifact.originalRecord)) {
        if (!audit.has(key) && JSON.stringify(current[key]) !== JSON.stringify(artifact.originalRecord[key]))
            throw new Error('Concurrent non-script modification requires re-review: ' + key);
    }
    const currentHash = sha256(current.script);
    const target = rollback ? artifact.originalRecord.script : artifact.patchedScript;
    const targetHash = rollback ? artifact.originalScriptSha256 : artifact.patchedScriptSha256;
    const sourceHash = rollback ? artifact.patchedScriptSha256 : artifact.originalScriptSha256;
    if (currentHash === targetHash)
        return { table: 'sys_script', sys_id: RECORD_ID, changed: false, fields: {} };
    if (currentHash !== sourceHash)
        throw new Error('Concurrent script modification: refusing blind patch or rollback.');
    return {
        table: 'sys_script', sys_id: RECORD_ID, changed: true,
        preconditions: { scriptSha256: currentHash, sys_mod_count: String(current.sys_mod_count) },
        fields: { script: target }
    };
}

module.exports = { RECORD_ID, ANCHOR, GUARD, sha256, prepare, proposal, normalize };

if (require.main === module) {
    if (/^0+$/.test(RECORD_ID)) throw new Error('Nondeployable template: independently review and pin the target rule before using this CLI.');
    const [command, recordPath, artifactOrHash, outputPath] = process.argv.slice(2);
    if (!['prepare', 'apply', 'rollback'].includes(command) || !recordPath || !artifactOrHash || !outputPath)
        throw new Error('Usage: node legacy-fanout-patch.cjs prepare|apply|rollback record.json hash|artifact.json output.json');
    const root = path.resolve(__dirname, '..');
    const output = path.resolve(outputPath);
    if (!output.startsWith(path.join(root, 'review') + path.sep))
        throw new Error('Write private review artifacts only inside the Git-ignored servicenow\\review folder.');
    const record = JSON.parse(fs.readFileSync(recordPath, 'utf8').replace(/^\uFEFF/, ''));
    const result = command === 'prepare' ? prepare(record, artifactOrHash) :
        proposal(record, JSON.parse(fs.readFileSync(artifactOrHash, 'utf8').replace(/^\uFEFF/, '')), command === 'rollback');
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
    console.log('Review artifact written. No ServiceNow API was called.');
}
