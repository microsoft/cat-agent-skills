'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const hash = value => crypto.createHash('sha256').update(value, 'utf8').digest('hex');

function build() {
    const definitionText = fs.readFileSync(path.join(root, 'install-definition.json'), 'utf8');
    const definition = JSON.parse(definitionText);
    const files = [...definition.script_includes, ...definition.rest_definition.resources,
        ...definition.business_rules, ...definition.scheduled_jobs];
    const scripts = files.map(item => {
        const source = fs.readFileSync(path.join(root, ...item.script_file.split('\\')), 'utf8');
        new vm.Script(source, { filename: item.script_file });
        return { file: item.script_file, sha256: hash(source), source };
    });
    const identities = [];
    const add = (table, identity) => identities.push({
        table, identity, proposed_sys_id: hash('cowork-sn:v1:' + table + ':' + identity).substring(0, 32)
    });
    for (const item of definition.roles) add('sys_user_role', item.name);
    for (const item of definition.tables) {
        add('sys_db_object', item.name);
        for (const column of item.columns) add('sys_dictionary', item.name + '.' + column.name);
    }
    for (const item of definition.extensions)
        for (const column of item.columns) add('sys_dictionary', item.table + '.' + column.name);
    for (const item of definition.properties) add('sys_properties', item.name);
    for (const item of definition.access_controls)
        for (const name of item.names || [item.name])
            for (const operation of item.operations || [item.operation])
                add('sys_security_acl', item.type + ':' + name + ':' + operation);
    for (const item of definition.script_includes) add('sys_script_include', item.name);
    for (const item of definition.business_rules) add('sys_script', item.name);
    for (const item of definition.scheduled_jobs) add('sysauto_script', item.name);
    for (const item of definition.event_registry) add('sysevent_register', item.name);
    add('sys_ws_definition', definition.target.base_path);
    for (const item of definition.rest_definition.resources)
        add('sys_ws_operation', definition.target.base_path + item.relative_path);
    return {
        format: 'cowork-review-bundle-v1', deployable_without_review: false,
        definition_sha256: hash(definitionText), definition, identities, scripts,
        blockers: [
            'If a relevant legacy fanout rule exists, fresh-read its revision and compare with a separately approved hash-qualified preview. If absent, do not create or amend legacy rules.',
            'Installer must generate and review instance-specific ACL/index/choice metadata; this bundle does not execute writes.',
            'Namespace/scope, API/plugin compatibility, minimum roles, OAuth providers and all routing values require operator verification.'
        ]
    };
}
module.exports = { build };
if (require.main === module) {
    const output = path.join(root, 'artifacts', 'install-bundle.json');
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, JSON.stringify(build(), null, 2) + '\n', 'utf8');
    console.log('Deterministic offline review bundle written: ' + output);
}
