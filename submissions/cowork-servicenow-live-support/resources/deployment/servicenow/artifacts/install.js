// NONDEPLOYABLE TEMPLATE generated offline. Review INSTALLER.txt before target-specific adaptation.
// Global Background Script; default dry run. Never patches the original harness.
// Change BOTH deliberate gates only after independent review; do not invoke twice in one paste.
var COWORK_INSTALL_DRY_RUN = true;
var COWORK_INSTALL_REVIEWED_DEFINITION = '';
var COWORK_INSTALL_MANIFEST = {
  "format": "cowork-create-only-installer-v1",
  "definition_sha256": "82d75da13ad93c4a96c85d39f640c17e06be2a95f6904e961d045e59b540431e",
  "instance": "example",
  "scope": "global",
  "namespace": "cowork_review",
  "records": [
    {
      "table": "sys_user_role",
      "identity": "cowork_bridge.integration",
      "sys_id": "f8d0a2303bf82309dd0500e06401815d",
      "fields": {
        "name": "cowork_bridge.integration",
        "description": "Restricts the new Scripted REST API; only the dedicated integration account receives this role.",
        "elevated_privilege": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.integration"
        }
      ],
      "booleans": [
        "elevated_privilege"
      ],
      "baseline_sha256": "9655463166531c9eb96be7309a59c7b27e59d814d71774798dc49f4dce51570d"
    },
    {
      "table": "sys_security_acl",
      "identity": "rest_endpoint:Cowork Bridge:execute",
      "sys_id": "01af399fbf8ceb48a1ba6d603b0f4bdd",
      "fields": {
        "name": "Cowork Bridge",
        "type": "REST_Endpoint",
        "operation": "execute",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "false",
        "condition": "",
        "script": "answer = String(gs.getUserID()) === String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''));",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "Cowork Bridge",
          "type": "REST_Endpoint",
          "operation": "execute"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "45dd0f9bc8dd13faf72d139cda579adf1aacfead6ab702a04957acc310c01fc3"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "rest_endpoint:Cowork Bridge:execute:cowork_bridge.integration",
      "sys_id": "bf612389aa8e03f00b01b119bb17d433",
      "fields": {
        "sys_security_acl": "01af399fbf8ceb48a1ba6d603b0f4bdd",
        "sys_user_role": "f8d0a2303bf82309dd0500e06401815d"
      },
      "keys": [
        {
          "sys_security_acl": "01af399fbf8ceb48a1ba6d603b0f4bdd",
          "sys_user_role": "f8d0a2303bf82309dd0500e06401815d"
        }
      ],
      "booleans": [],
      "baseline_sha256": "d7ca25ee21ee817460bd00e92e821fddd90d6f45941c857f6921856d28a51d0a"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:u_cowork_command:create",
      "sys_id": "1894e90665859a4afb2bf2fc3813fa3a",
      "fields": {
        "name": "u_cowork_command",
        "type": "record",
        "operation": "create",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin');",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "type": "record",
          "operation": "create"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "37229d2b37a6cb9c8752947ade0c39b91258d897a85345fa07e6ee3ae6551125"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "record:u_cowork_command:create:admin",
      "sys_id": "90831f55df553152989bc14ede518ce2",
      "fields": {
        "sys_security_acl": "1894e90665859a4afb2bf2fc3813fa3a",
        "sys_user_role": "@admin_role"
      },
      "keys": [
        {
          "sys_security_acl": "1894e90665859a4afb2bf2fc3813fa3a",
          "sys_user_role": "@admin_role"
        }
      ],
      "booleans": [],
      "baseline_sha256": "dc9cae190cd38d17e1205dc4a953864ab53f11d1f8ec49b7ef8baf5e9df73d96"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:u_cowork_command:read",
      "sys_id": "90e06bb47c006d0634d05749e3436332",
      "fields": {
        "name": "u_cowork_command",
        "type": "record",
        "operation": "read",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin');",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "type": "record",
          "operation": "read"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "1a0a2fdb6f0104b99038375d258a23a31f4d0e1d11f323c0e5450bc041ed9d2b"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "record:u_cowork_command:read:admin",
      "sys_id": "6662c73361bf9021e6df6a90da305a68",
      "fields": {
        "sys_security_acl": "90e06bb47c006d0634d05749e3436332",
        "sys_user_role": "@admin_role"
      },
      "keys": [
        {
          "sys_security_acl": "90e06bb47c006d0634d05749e3436332",
          "sys_user_role": "@admin_role"
        }
      ],
      "booleans": [],
      "baseline_sha256": "f3a6e2371f6c9a65911ed9003d589bfe4cf07078c3fa32c3d0e2da8576812b48"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:u_cowork_command:write",
      "sys_id": "1754f16540f5088bc925492897b14d60",
      "fields": {
        "name": "u_cowork_command",
        "type": "record",
        "operation": "write",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin');",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "type": "record",
          "operation": "write"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "a449d62e94d0d1bb37d7fb4c421e4f2d8429fcbc6e610a4046ee78795ac220cb"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "record:u_cowork_command:write:admin",
      "sys_id": "caa45138799c1cfdec886ee924c8dddf",
      "fields": {
        "sys_security_acl": "1754f16540f5088bc925492897b14d60",
        "sys_user_role": "@admin_role"
      },
      "keys": [
        {
          "sys_security_acl": "1754f16540f5088bc925492897b14d60",
          "sys_user_role": "@admin_role"
        }
      ],
      "booleans": [],
      "baseline_sha256": "acfa0d7b1fed9eb909323406323129147be31c76b59e1523fe9956016022edc5"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:u_cowork_command:delete",
      "sys_id": "f202eead0b123b41f1d95bc9d05b550e",
      "fields": {
        "name": "u_cowork_command",
        "type": "record",
        "operation": "delete",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin');",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "type": "record",
          "operation": "delete"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "0fe327c826ddf1fefa2cec70c43104000d0fb83113602dab1d1d656bfbbe2c89"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "record:u_cowork_command:delete:admin",
      "sys_id": "b8dad0807838c4a92e5afa65343b796c",
      "fields": {
        "sys_security_acl": "f202eead0b123b41f1d95bc9d05b550e",
        "sys_user_role": "@admin_role"
      },
      "keys": [
        {
          "sys_security_acl": "f202eead0b123b41f1d95bc9d05b550e",
          "sys_user_role": "@admin_role"
        }
      ],
      "booleans": [],
      "baseline_sha256": "4de81a0a19e2701900134d1b8d96c925bbfe815fc487b4ac0df63fece1ca6a99"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:interaction.u_cowork_session_id:create",
      "sys_id": "ebe1223fa4f4325cbfd89d3ff9828ae1",
      "fields": {
        "name": "interaction.u_cowork_session_id",
        "type": "record",
        "operation": "create",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin') || (gs.hasRole('cowork_bridge.integration') && String(gs.getUserID()) === String(gs.getProperty('cowork_bridge.integration_user_sys_id', '')));",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "interaction.u_cowork_session_id",
          "type": "record",
          "operation": "create"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "d557ff5c40d854284d962ea7c9b906b2bedcc15589bffead2ad2f70e24283139"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:interaction.u_cowork_session_id:write",
      "sys_id": "a4bb5374a63843ed9a54070951845236",
      "fields": {
        "name": "interaction.u_cowork_session_id",
        "type": "record",
        "operation": "write",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin') || (gs.hasRole('cowork_bridge.integration') && String(gs.getUserID()) === String(gs.getProperty('cowork_bridge.integration_user_sys_id', '')));",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "interaction.u_cowork_session_id",
          "type": "record",
          "operation": "write"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "7f58eafa9b36a92c899a1031520ab1054ce5fcdfb30db7e9962135cee0923d78"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:interaction.u_cowork_upn:create",
      "sys_id": "789390facafc0ffe9fc4c419fd8aa9b4",
      "fields": {
        "name": "interaction.u_cowork_upn",
        "type": "record",
        "operation": "create",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin') || (gs.hasRole('cowork_bridge.integration') && String(gs.getUserID()) === String(gs.getProperty('cowork_bridge.integration_user_sys_id', '')));",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "interaction.u_cowork_upn",
          "type": "record",
          "operation": "create"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "6b4ced988b2a50d4981ddb0383df8d7a5a4b7aec4a81480134804efc26508cd6"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:interaction.u_cowork_upn:write",
      "sys_id": "831a21170023d2638fed2b1dcac3e79e",
      "fields": {
        "name": "interaction.u_cowork_upn",
        "type": "record",
        "operation": "write",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin') || (gs.hasRole('cowork_bridge.integration') && String(gs.getUserID()) === String(gs.getProperty('cowork_bridge.integration_user_sys_id', '')));",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "interaction.u_cowork_upn",
          "type": "record",
          "operation": "write"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "d2bc59750adfee48407523f541eb23a86bd6e657c66a31502e3dda33fe8661a7"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:u_cowork_outbox:create",
      "sys_id": "016152626f099e63c7932f9b78c97999",
      "fields": {
        "name": "u_cowork_outbox",
        "type": "record",
        "operation": "create",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin');",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "type": "record",
          "operation": "create"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "294fef72120a8e88e1b82e29f92ebc01ab6425af9d8e9bc74a0a75fac332cf9e"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "record:u_cowork_outbox:create:admin",
      "sys_id": "38ba4e9f50f4f863171d038e5457efd8",
      "fields": {
        "sys_security_acl": "016152626f099e63c7932f9b78c97999",
        "sys_user_role": "@admin_role"
      },
      "keys": [
        {
          "sys_security_acl": "016152626f099e63c7932f9b78c97999",
          "sys_user_role": "@admin_role"
        }
      ],
      "booleans": [],
      "baseline_sha256": "a06bed3b70769192a12ddeb884c99a7622e726c8675567a692d6f1a6177da8cf"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:u_cowork_outbox:read",
      "sys_id": "9bf2ef0498613025936f04f45661017a",
      "fields": {
        "name": "u_cowork_outbox",
        "type": "record",
        "operation": "read",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin');",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "type": "record",
          "operation": "read"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "2928b9b714b10b8d72e4ef88071fd47257323875c7d02d69b6818f5e5b596c37"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "record:u_cowork_outbox:read:admin",
      "sys_id": "98c540e1754ebaf2359b142b372ce8e1",
      "fields": {
        "sys_security_acl": "9bf2ef0498613025936f04f45661017a",
        "sys_user_role": "@admin_role"
      },
      "keys": [
        {
          "sys_security_acl": "9bf2ef0498613025936f04f45661017a",
          "sys_user_role": "@admin_role"
        }
      ],
      "booleans": [],
      "baseline_sha256": "a5d5297a0b381ea892ef76b1c61588f29ae0f3db700cbb924cbcab23a3cd3615"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:u_cowork_outbox:write",
      "sys_id": "9a425dbb525b7da83d5fa70f6b5e0025",
      "fields": {
        "name": "u_cowork_outbox",
        "type": "record",
        "operation": "write",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin');",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "type": "record",
          "operation": "write"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "231eb2e4059b148232b6c6df359f9a611e32202abf62c4fd49ab0eaa0ac1b380"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "record:u_cowork_outbox:write:admin",
      "sys_id": "37a5689ba3827a60622ad3c9594465c6",
      "fields": {
        "sys_security_acl": "9a425dbb525b7da83d5fa70f6b5e0025",
        "sys_user_role": "@admin_role"
      },
      "keys": [
        {
          "sys_security_acl": "9a425dbb525b7da83d5fa70f6b5e0025",
          "sys_user_role": "@admin_role"
        }
      ],
      "booleans": [],
      "baseline_sha256": "f359d06738e746b164fe5415b0fdfe77d99e5bc458dfbadbfca0fa2df36bb161"
    },
    {
      "table": "sys_security_acl",
      "identity": "record:u_cowork_outbox:delete",
      "sys_id": "6738c6d00ed6cf9df99f7d50e23603fd",
      "fields": {
        "name": "u_cowork_outbox",
        "type": "record",
        "operation": "delete",
        "active": "true",
        "advanced": "true",
        "admin_overrides": "true",
        "condition": "",
        "script": "answer = gs.hasRole('admin');",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "type": "record",
          "operation": "delete"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "admin_overrides"
      ],
      "baseline_sha256": "ccc0eea678a88fe3d3ec2d3900756af678285585d416c5b7d7736ad055269bcb"
    },
    {
      "table": "sys_security_acl_role",
      "identity": "record:u_cowork_outbox:delete:admin",
      "sys_id": "e003d3b61aaa78bf02e3f03583278f09",
      "fields": {
        "sys_security_acl": "6738c6d00ed6cf9df99f7d50e23603fd",
        "sys_user_role": "@admin_role"
      },
      "keys": [
        {
          "sys_security_acl": "6738c6d00ed6cf9df99f7d50e23603fd",
          "sys_user_role": "@admin_role"
        }
      ],
      "booleans": [],
      "baseline_sha256": "99de5a05510b3ceee5e27d111507e1581de22b9d87830332425294916362b669"
    },
    {
      "table": "sys_db_object",
      "identity": "u_cowork_command",
      "sys_id": "01fc81bd555bfa04c7ec5301c1dc79e6",
      "fields": {
        "name": "u_cowork_command",
        "label": "Cowork Command",
        "super_class": "",
        "is_extendable": "false",
        "access": "public",
        "create_access": "false",
        "read_access": "false",
        "update_access": "false",
        "delete_access": "false",
        "ws_access": "false",
        "create_access_controls": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command"
        }
      ],
      "booleans": [
        "is_extendable",
        "create_access",
        "read_access",
        "update_access",
        "delete_access",
        "ws_access",
        "create_access_controls"
      ],
      "baseline_sha256": "56874a98a6568480588905eba07fc7a5af00ecaae9e62349ee3a11644faccfa4"
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_command.",
      "sys_id": "edf89d5d4eaa2b1f75f94c05fca80c59",
      "fields": {
        "name": "u_cowork_command",
        "element": "",
        "internal_type": "collection",
        "active": "true",
        "audit": "false",
        "attributes": "",
        "mandatory": "false",
        "unique": "false",
        "max_length": "40",
        "column_label": "Cowork Command",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": ""
        }
      ],
      "booleans": [
        "active",
        "audit",
        "mandatory",
        "unique"
      ],
      "baseline_sha256": "490a3dd7806e68e28db3f6f15e83ed58c77c20612f5f5595c34960af86be6940",
      "verify_table": "u_cowork_command",
      "platform_collection": true
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_command.u_key",
      "sys_id": "859e3e5b00df0e09199fb0037adeeed4",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_key",
        "column_label": "Command key",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "true",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "240",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_key"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "85a66e54ce5aa25c94730fa8602d329396babbb963cce435599a964c1d3ec6ee",
      "verify_field": [
        "u_cowork_command",
        "u_key"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_command.u_request_hash",
      "sys_id": "a6789e0e6fc08dce2282a778a9c38e69",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_request_hash",
        "column_label": "Request SHA-256",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "64",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_request_hash"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "05faaffcffe4d0507db93116445560a1737b0bea5d4f65a4c22faade79e9e25d",
      "verify_field": [
        "u_cowork_command",
        "u_request_hash"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_command.u_status",
      "sys_id": "093956a2e19c11132823ee89da1c55a0",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_status",
        "column_label": "Status",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "false",
        "default_value": "pending",
        "choice": "3",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "20",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_status"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "6b5922f1ba0f08ea1a7e93bad7508bfc8265e95aecc057059435b60143596048",
      "verify_field": [
        "u_cowork_command",
        "u_status"
      ]
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_command.u_status:en:pending",
      "sys_id": "27fa7fdb7513a1faec85b212ee7eae64",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_status",
        "language": "en",
        "value": "pending",
        "label": "pending",
        "sequence": "100",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_status",
          "language": "en",
          "value": "pending",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "c217a52d063b2f4cdb680d8ecb20b9ac12cb7d26135cf54ebdfbb50ac09e90f8"
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_command.u_status:en:completed",
      "sys_id": "4b5cb34f9e4bb8ad0739b039e2fb8228",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_status",
        "language": "en",
        "value": "completed",
        "label": "completed",
        "sequence": "200",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_status",
          "language": "en",
          "value": "completed",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "24b7e13a48a2998435aa949b1f95df9426667d4acb3663c86754252f8d231f51"
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_command.u_status:en:failed",
      "sys_id": "46eedeab6cc828944b9d8f5b633fe56b",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_status",
        "language": "en",
        "value": "failed",
        "label": "failed",
        "sequence": "300",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_status",
          "language": "en",
          "value": "failed",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "a0830c5a55cb6c320eb6e16d2f5ad2131dfa3337aa77b8a4041b7eb09f72be70"
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_command.u_result",
      "sys_id": "548384400081776862f81e182b896a74",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_result",
        "column_label": "Result JSON",
        "internal_type": "string",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "8000",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_result"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "b783ad1851721b1f07ca2db11ad21415db8d8b41a7098981e1766ecf50d078b8",
      "verify_field": [
        "u_cowork_command",
        "u_result"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_command.u_error",
      "sys_id": "3f39c77710e3abf56d4527937dd909bc",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_error",
        "column_label": "Sanitized error code",
        "internal_type": "string",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "1000",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_error"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "9ea394a094cc360356314f3c17f788bd4f6b6612b240425742a9da07db92a6b8",
      "verify_field": [
        "u_cowork_command",
        "u_error"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_command.u_conversation",
      "sys_id": "d4e98ca0811b224fa441c9bd3c578eb5",
      "fields": {
        "name": "u_cowork_command",
        "element": "u_conversation",
        "column_label": "Conversation",
        "internal_type": "reference",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "sys_cs_conversation",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "32",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_command",
          "element": "u_conversation"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "9b68e578c3b67d6a18d85de14a32b6663babf41cd85e9d0c3931891a60d6a4b6",
      "verify_field": [
        "u_cowork_command",
        "u_conversation"
      ]
    },
    {
      "table": "sys_db_object",
      "identity": "u_cowork_outbox",
      "sys_id": "60079012809484c351a20eddacd313fc",
      "fields": {
        "name": "u_cowork_outbox",
        "label": "Cowork Callback Outbox",
        "super_class": "",
        "is_extendable": "false",
        "access": "public",
        "create_access": "false",
        "read_access": "false",
        "update_access": "false",
        "delete_access": "false",
        "ws_access": "false",
        "create_access_controls": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox"
        }
      ],
      "booleans": [
        "is_extendable",
        "create_access",
        "read_access",
        "update_access",
        "delete_access",
        "ws_access",
        "create_access_controls"
      ],
      "baseline_sha256": "3abc66e338166dc6adbf012d43ac98b5663c797fe6235c8248590c36cf248cae"
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.",
      "sys_id": "1e4d368cc90e40d51acedceca127851c",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "",
        "internal_type": "collection",
        "active": "true",
        "audit": "false",
        "attributes": "",
        "mandatory": "false",
        "unique": "false",
        "max_length": "40",
        "column_label": "Cowork Callback Outbox",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": ""
        }
      ],
      "booleans": [
        "active",
        "audit",
        "mandatory",
        "unique"
      ],
      "baseline_sha256": "0c280f04e026b3a767de90697eb7e27d2e59323bfb7a6143d06c1fa608555171",
      "verify_table": "u_cowork_outbox",
      "platform_collection": true
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_event_id",
      "sys_id": "86e01d96d8f6d5031e36ad4284e57161",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_event_id",
        "column_label": "Stable event ID",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "true",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "160",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_event_id"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "4e6a57291d2725f0038ba25b1b9da042de1d7ad7c50722829fd5f322a828b3ae",
      "verify_field": [
        "u_cowork_outbox",
        "u_event_id"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_event",
      "sys_id": "0b492b098151e9d0e17182e76886b6d8",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_event",
        "column_label": "Event",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "false",
        "default_value": "",
        "choice": "3",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "20",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_event"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "5887b96791514955b499456fb0c01fd443dd2c45feb7991fd3dcec1b31449dec",
      "verify_field": [
        "u_cowork_outbox",
        "u_event"
      ]
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_outbox.u_event:en:accepted",
      "sys_id": "0e2512147d7257a77320f47fb88ed380",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_event",
        "language": "en",
        "value": "accepted",
        "label": "accepted",
        "sequence": "100",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_event",
          "language": "en",
          "value": "accepted",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "7a132932589ac9ed671e0e632ddc866ad26dd78a0fbf5d1f6a060b1104289d05"
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_outbox.u_event:en:message",
      "sys_id": "261b7e7e787145886b2202b50e6aef5c",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_event",
        "language": "en",
        "value": "message",
        "label": "message",
        "sequence": "200",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_event",
          "language": "en",
          "value": "message",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "3e08be1325c350d93d0390d8abf60a260f5b1263469fbd20d95a141316850302"
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_outbox.u_event:en:closed",
      "sys_id": "ae0c677b16a29638628ce44ed250621f",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_event",
        "language": "en",
        "value": "closed",
        "label": "closed",
        "sequence": "300",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_event",
          "language": "en",
          "value": "closed",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "f04b61f46b30d29f966ae8eb290fa7d6e64ed08e22cde745007ca858613c1e3f"
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_client_session_id",
      "sys_id": "3316b1cdb15fa3883050c8cd00e270a3",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_client_session_id",
        "column_label": "Cowork session ID",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "80",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_client_session_id"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "62b53e422397061a33f3d64a9160d531c01dbe4938cdf6d2eb64d9fda7593d2e",
      "verify_field": [
        "u_cowork_outbox",
        "u_client_session_id"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_interaction",
      "sys_id": "ccf5a433a5e035a272e852e949e5138a",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_interaction",
        "column_label": "Interaction",
        "internal_type": "reference",
        "active": "true",
        "mandatory": "true",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "interaction",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "32",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_interaction"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "82c549353817950c4a846f5f85395d7fe160cd62b02e9378abd2f7887366c189",
      "verify_field": [
        "u_cowork_outbox",
        "u_interaction"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_message",
      "sys_id": "1b721abedc1ffa249942404a42484b71",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_message",
        "column_label": "Message",
        "internal_type": "reference",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "sys_cs_message",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "32",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_message"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "917f56a6f8bb63e26d0f5e976a0637255e559e344ed22ce1a83aad00d90f6ae2",
      "verify_field": [
        "u_cowork_outbox",
        "u_message"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_payload",
      "sys_id": "a468970478ee4a70ccf2fdb944b812b3",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_payload",
        "column_label": "Approved callback snapshot JSON",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "65535",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_payload"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "ebe814bcb3feab102196b38802027a7a19657eeaa467794e146f5fd4948c87b9",
      "verify_field": [
        "u_cowork_outbox",
        "u_payload"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_payload_hash",
      "sys_id": "b60944fa27698d7e99257e65071ca126",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_payload_hash",
        "column_label": "Snapshot SHA-256",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "64",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_payload_hash"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "1f1c060397bc119a6242b159ba18a8168a18cfdfa3b15e1b7955c20a41ee798f",
      "verify_field": [
        "u_cowork_outbox",
        "u_payload_hash"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_status",
      "sys_id": "85a6ef6d6bfaf240c5be0682ac618425",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_status",
        "column_label": "Status",
        "internal_type": "string",
        "active": "true",
        "mandatory": "true",
        "unique": "false",
        "default_value": "pending",
        "choice": "3",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "20",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_status"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "259bbfab6b4c78e6eaf01775633bb9dd1e21e79a3e5be86db57c8de14012ec7a",
      "verify_field": [
        "u_cowork_outbox",
        "u_status"
      ]
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_outbox.u_status:en:pending",
      "sys_id": "32a792302d6eac54dce580f1518944cf",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_status",
        "language": "en",
        "value": "pending",
        "label": "pending",
        "sequence": "100",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_status",
          "language": "en",
          "value": "pending",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "92e80925fa4de9cdd65ec0e9610473515c0073e9a8d459f3157b3ce4e34b4c3e"
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_outbox.u_status:en:sending",
      "sys_id": "74eb92dd883eb3be44556ccd9f212432",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_status",
        "language": "en",
        "value": "sending",
        "label": "sending",
        "sequence": "200",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_status",
          "language": "en",
          "value": "sending",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "4e589e2c5aecfac6e45386d76762da30ab55732d899df00329598004a5db8ae3"
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_outbox.u_status:en:retry",
      "sys_id": "fafd8f1a16eadca8f92dd37af4a62630",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_status",
        "language": "en",
        "value": "retry",
        "label": "retry",
        "sequence": "300",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_status",
          "language": "en",
          "value": "retry",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "b2ce17ed4315a4234c25e6a9038e3a2378b714695d5366f92cb6311dec037af5"
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_outbox.u_status:en:delivered",
      "sys_id": "ea41c58928fce5946fd8c32c8ca033ae",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_status",
        "language": "en",
        "value": "delivered",
        "label": "delivered",
        "sequence": "400",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_status",
          "language": "en",
          "value": "delivered",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "4ec1d953d180cc2296b8885dba8b3b943db5ae1b296c82c1e19a66df994f4f79"
    },
    {
      "table": "sys_choice",
      "identity": "u_cowork_outbox.u_status:en:dead_letter",
      "sys_id": "de5e90d73b1658a0fcca1eda186f8f74",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_status",
        "language": "en",
        "value": "dead_letter",
        "label": "dead_letter",
        "sequence": "500",
        "inactive": "false",
        "dependent_value": "",
        "sys_domain": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_status",
          "language": "en",
          "value": "dead_letter",
          "dependent_value": ""
        }
      ],
      "booleans": [
        "inactive"
      ],
      "baseline_sha256": "d034e69e862c450fac39441936965bf3bf6ed2ed0c96a3bbabc71db5a65f916d"
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_attempts",
      "sys_id": "6e92e8297ee702253b1b14b3f2ca7830",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_attempts",
        "column_label": "Claim attempts",
        "internal_type": "integer",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "0",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_attempts"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "45fcb4dcbfb488aecd8c55d352600298a13c8b95bec90682e0c3c770dd13d141",
      "verify_field": [
        "u_cowork_outbox",
        "u_attempts"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_next_attempt_at",
      "sys_id": "4f4fe880d3255d6739d63af947165396",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_next_attempt_at",
        "column_label": "Next attempt",
        "internal_type": "glide_date_time",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_next_attempt_at"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "4e6fc52b59404198b5ceacb818409337fc5af2d4e85c491d93fddc68db336c7a",
      "verify_field": [
        "u_cowork_outbox",
        "u_next_attempt_at"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_lease_token",
      "sys_id": "bb8a0c018e80cbf217ec13b3a6383ee6",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_lease_token",
        "column_label": "Worker lease correlation ID",
        "internal_type": "string",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "32",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_lease_token"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "9d8fb8e6fb88cd50c16d219653767d75bee19dfc90ad458df3457cec83445e06",
      "verify_field": [
        "u_cowork_outbox",
        "u_lease_token"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_lease_until",
      "sys_id": "f82bd7a2bd15c565f295fe3f370fc461",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_lease_until",
        "column_label": "Worker lease expiry",
        "internal_type": "glide_date_time",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_lease_until"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "78436f00a46067535c251cab82ea39db15df2a31db85ffc0ae062cd72fedffd2",
      "verify_field": [
        "u_cowork_outbox",
        "u_lease_until"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_delivered_at",
      "sys_id": "a35267b8974659c85c93d9d6a1f50a41",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_delivered_at",
        "column_label": "Delivered",
        "internal_type": "glide_date_time",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_delivered_at"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "d4d16c0c038f1ab44dfe5400066d24ffea19fb985586f9ee47daa25427e5db95",
      "verify_field": [
        "u_cowork_outbox",
        "u_delivered_at"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_last_error",
      "sys_id": "2836ec71761c3986fc35735c1c2bc173",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_last_error",
        "column_label": "Sanitized error code",
        "internal_type": "string",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "1000",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_last_error"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "77377fed63d349d82c748425e01cee71b46d6a9a466bef9d87d5e6f52470cdf4",
      "verify_field": [
        "u_cowork_outbox",
        "u_last_error"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "u_cowork_outbox.u_requires_attention",
      "sys_id": "9d5079eadcc20531710ff5db1c7eea22",
      "fields": {
        "name": "u_cowork_outbox",
        "element": "u_requires_attention",
        "column_label": "Operator attention required",
        "internal_type": "boolean",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "false",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "u_cowork_outbox",
          "element": "u_requires_attention"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "72d2631b3e8ca0cc68b7e0118801a20427f82af784a53b4654b447df58b969d9",
      "verify_field": [
        "u_cowork_outbox",
        "u_requires_attention"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "interaction.u_cowork_session_id",
      "sys_id": "8f535f999666b2a581883d2d76c5463e",
      "fields": {
        "name": "interaction",
        "element": "u_cowork_session_id",
        "column_label": "Cowork session ID",
        "internal_type": "string",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "80",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "interaction",
          "element": "u_cowork_session_id"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "ceb3d4d7476ea877754d3e810585f6c5cbfe0fba73d10271f4eb53194cd4cc7b",
      "verify_field": [
        "interaction",
        "u_cowork_session_id"
      ]
    },
    {
      "table": "sys_dictionary",
      "identity": "interaction.u_cowork_upn",
      "sys_id": "45768d134a35208ed83f6901072bcf1b",
      "fields": {
        "name": "interaction",
        "element": "u_cowork_upn",
        "column_label": "Cowork requester UPN",
        "internal_type": "string",
        "active": "true",
        "mandatory": "false",
        "unique": "false",
        "default_value": "",
        "choice": "0",
        "reference": "",
        "audit": "false",
        "read_only": "false",
        "display": "false",
        "virtual": "false",
        "attributes": "",
        "max_length": "254",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "interaction",
          "element": "u_cowork_upn"
        }
      ],
      "booleans": [
        "active",
        "mandatory",
        "unique",
        "audit",
        "read_only",
        "display",
        "virtual"
      ],
      "baseline_sha256": "398a98d25ee5d422e895e892364b678969773446cc274c9730661c5be2068653",
      "verify_field": [
        "interaction",
        "u_cowork_upn"
      ]
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.enabled",
      "sys_id": "9900be932e7ea43262447743a6a18f9a",
      "fields": {
        "name": "cowork_bridge.enabled",
        "type": "boolean",
        "value": "false",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.enabled"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "fe6d0b08fd98e82da8467fe9fe196e9e4e4d75355b525dd48431a726153e3191"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.outbox_delivery_enabled",
      "sys_id": "fe7fcd73cc9747549f7df7d7434aeeb3",
      "fields": {
        "name": "cowork_bridge.outbox_delivery_enabled",
        "type": "boolean",
        "value": "false",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.outbox_delivery_enabled"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "d4bd671c602e0353956e56b1edd25d235a0545a3087c3997db74c740532b65ca"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.integration_user_sys_id",
      "sys_id": "752da148b2af6cd543ed872241b9ff14",
      "fields": {
        "name": "cowork_bridge.integration_user_sys_id",
        "type": "string",
        "value": "",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.integration_user_sys_id"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "a2780d950cbbc971831853fb9ce564791f0f65293b3238916d7508501a3220b7"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.queue_sys_id",
      "sys_id": "aeefae6d0af5d76d2f8af2cafddd6ff9",
      "fields": {
        "name": "cowork_bridge.queue_sys_id",
        "type": "string",
        "value": "",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.queue_sys_id"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "9c4ffa71218b37c067169c74382956efab48ad6b1e5cbbc7e83df3e9fd5b6c0c"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.service_channel_sys_id",
      "sys_id": "9ffc768df6cbf19621a030366fe32e58",
      "fields": {
        "name": "cowork_bridge.service_channel_sys_id",
        "type": "string",
        "value": "",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.service_channel_sys_id"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "d35cbd40518814153208d7a61413416a2e2e080c37fccb2be29302d6bdeed217"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.vendor_sys_id",
      "sys_id": "b9135dc5c590db66121871679a112903",
      "fields": {
        "name": "cowork_bridge.vendor_sys_id",
        "type": "string",
        "value": "",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.vendor_sys_id"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "573765b339cbab540674f7b17de4c2c2f18b75df78497a560810d5de8f5c759a"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.virtual_agent_user_sys_id",
      "sys_id": "40957d01b8139255b580e5985f9001a0",
      "fields": {
        "name": "cowork_bridge.virtual_agent_user_sys_id",
        "type": "string",
        "value": "",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.virtual_agent_user_sys_id"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "0020aff0bd7cb72e47ca447a227c88d16853fadbc25f7a581f4208a46b88fa56"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.webhook_url",
      "sys_id": "c708a1355393ce25bfb25968ae2b4665",
      "fields": {
        "name": "cowork_bridge.webhook_url",
        "type": "string",
        "value": "",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.webhook_url"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "a42dd9eb49efb45c0009d2925c5d9748dc82f67db6766c5d14019dbe0804d03b"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.webhook_oauth_entity",
      "sys_id": "fc206eed91666bdd2f6ba0bf1ed85781",
      "fields": {
        "name": "cowork_bridge.webhook_oauth_entity",
        "type": "string",
        "value": "",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.webhook_oauth_entity"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "e6f4f57da6761507c40441961f07ae64df2f680439aa4718f928b48279ada6b7"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.webhook_oauth_scope",
      "sys_id": "b63844782378f91de13964ffddf6c652",
      "fields": {
        "name": "cowork_bridge.webhook_oauth_scope",
        "type": "string",
        "value": "",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.webhook_oauth_scope"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "8925b43633aa8938f971c6d593995b4c6031a3c638dc0dbd2e11053542113b16"
    },
    {
      "table": "sys_properties",
      "identity": "cowork_bridge.unavailable_message",
      "sys_id": "822fcc66c6095d6f7f04d7f6bd42c580",
      "fields": {
        "name": "cowork_bridge.unavailable_message",
        "type": "string",
        "value": "Live chat is unavailable. Please use your IT support portal.",
        "is_private": "true",
        "ignore_cache": "false",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "cowork_bridge.unavailable_message"
        }
      ],
      "booleans": [
        "is_private",
        "ignore_cache"
      ],
      "baseline_sha256": "1765790bbf2a89f5ff7151251fbc69876f05548bcb7656026cc9d1c65da606a5"
    },
    {
      "table": "sys_script_include",
      "identity": "CoworkBridgeOutbox",
      "sys_id": "c06a3197d6944001e6970917fbd13578",
      "fields": {
        "name": "CoworkBridgeOutbox",
        "api_name": "global.CoworkBridgeOutbox",
        "active": "true",
        "client_callable": "false",
        "access": "public",
        "script": "var CoworkBridgeOutbox = Class.create();\nCoworkBridgeOutbox.prototype = {\n    initialize: function () {},\n\n    enqueue: function (body, interactionId) {\n        var snapshot = this._snapshot(body);\n        var owner = new GlideRecord('interaction');\n        if (!owner.get(interactionId) || !new CoworkBridgeWebhook()._isCowork(owner) ||\n            String(owner.getValue('u_cowork_session_id')) !== snapshot.client_session_id ||\n            String(owner.getValue('number')) !== snapshot.interaction_number)\n            throw new Error('cowork_outbox_owner_mismatch');\n        var payload = JSON.stringify(snapshot);\n        var hash = String(new GlideDigest().getSHA256Hex(payload));\n        var existing = this._find(snapshot.event_id);\n        if (existing) return this._duplicate(existing, hash);\n        var row = new GlideRecord('u_cowork_outbox');\n        row.initialize();\n        row.setValue('u_event_id', snapshot.event_id);\n        row.setValue('u_event', snapshot.event);\n        row.setValue('u_client_session_id', snapshot.client_session_id);\n        row.setValue('u_interaction', interactionId);\n        if (snapshot.message_sys_id) row.setValue('u_message', snapshot.message_sys_id);\n        row.setValue('u_payload', payload);\n        row.setValue('u_payload_hash', hash);\n        row.setValue('u_status', 'pending');\n        row.setValue('u_attempts', 0);\n        row.setValue('u_next_attempt_at', new GlideDateTime());\n        row.setValue('u_requires_attention', false);\n        var id = null;\n        try { id = row.insert(); } catch (ignored) {}\n        if (!id) {\n            existing = this._find(snapshot.event_id);\n            if (existing) return this._duplicate(existing, hash);\n            gs.error('Cowork outbox enqueue failed; operator reconciliation required.');\n            throw new Error('cowork_outbox_enqueue_failed');\n        }\n        // Persistence always precedes OAuth/HTTP. A failure or crash leaves a retriable row.\n        this._safeAttempt(String(id));\n        return true;\n    },\n\n    retry: function () {\n        if (!this._enabled()) return 0;\n        var count = 0;\n        var due = new GlideRecord('u_cowork_outbox');\n        due.addQuery('u_status', 'IN', 'pending,retry');\n        due.addQuery('u_next_attempt_at', '<=', new GlideDateTime());\n        due.orderBy('u_next_attempt_at');\n        due.setLimit(20);\n        due.query();\n        while (due.next()) {\n            this._safeAttempt(String(due.getUniqueValue()));\n            count++;\n        }\n        var expired = new GlideRecord('u_cowork_outbox');\n        expired.addQuery('u_status', 'sending');\n        expired.addQuery('u_lease_until', '<=', new GlideDateTime());\n        expired.orderBy('u_lease_until');\n        expired.setLimit(20);\n        expired.query();\n        while (expired.next()) {\n            this._safeAttempt(String(expired.getUniqueValue()));\n            count++;\n        }\n        var attention = new GlideRecord('u_cowork_outbox');\n        attention.addQuery('u_requires_attention', true);\n        attention.setLimit(1);\n        attention.query();\n        if (attention.next())\n            gs.warn('Cowork outbox requires operator attention; inspect u_requires_attention=true. No events were discarded.');\n        return count;\n    },\n\n    attempt: function (id) {\n        if (!this._enabled()) return false;\n        var row = this._claim(id);\n        if (!row) return false;\n        var errorCode = 'webhook_delivery_failed';\n        var delivered = false;\n        try {\n            var payload = String(row.getValue('u_payload') || '');\n            if (String(new GlideDigest().getSHA256Hex(payload)) !== String(row.getValue('u_payload_hash')))\n                throw new Error('invalid_payload');\n            var body = this._snapshot(JSON.parse(payload));\n            if (body.event_id !== String(row.getValue('u_event_id')) ||\n                body.client_session_id !== String(row.getValue('u_client_session_id')))\n                throw new Error('invalid_payload');\n            if (Number(row.getValue('u_attempts')) > 8) errorCode = 'retry_limit_reached';\n            else delivered = new CoworkBridgeWebhook().deliver(body);\n        } catch (ignored) {\n            errorCode = 'outbox_payload_or_delivery_failed';\n        }\n        return this._finish(row, delivered, errorCode);\n    },\n\n    _safeAttempt: function (id) {\n        try { return this.attempt(id); }\n        catch (ignored) {\n            // Do not roll back a successfully enqueued snapshot just because best-effort delivery failed.\n            gs.warn('Cowork outbox attempt incomplete; retained event requires retry or lease recovery.');\n            return false;\n        }\n    },\n\n    _claim: function (id) {\n        var row = new GlideRecord('u_cowork_outbox');\n        if (!row.get(id)) return null;\n        var status = String(row.getValue('u_status'));\n        var now = new GlideDateTime();\n        var due = status === 'sending' ? row.getValue('u_lease_until') : row.getValue('u_next_attempt_at');\n        if (['pending', 'retry', 'sending'].indexOf(status) < 0 || !due ||\n            Number(new GlideDateTime(String(due)).getNumericValue()) > Number(now.getNumericValue())) return null;\n        var token = String(gs.generateGUID());\n        if (!/^[0-9a-f]{32}$/.test(token)) throw new Error('cowork_outbox_lease_token_invalid');\n        var lease = new GlideDateTime();\n        lease.addSeconds(600);\n        // Conditional UPDATE is the atomic lease; read-then-update alone is not safe across nodes.\n        var claim = new GlideRecord('u_cowork_outbox');\n        claim.addQuery('sys_id', id);\n        claim.addQuery('sys_mod_count', row.getValue('sys_mod_count'));\n        claim.addQuery('u_status', status);\n        claim.addQuery(status === 'sending' ? 'u_lease_until' : 'u_next_attempt_at', '<=', now);\n        claim.setValue('u_lease_token', token);\n        claim.setValue('u_lease_until', lease);\n        claim.setValue('u_status', 'sending');\n        claim.setValue('u_attempts', Number(row.getValue('u_attempts') || 0) + 1);\n        claim.updateMultiple();\n        if (!row.get(id) || String(row.getValue('u_lease_token')) !== token) return null;\n        return row;\n    },\n\n    _finish: function (row, delivered, errorCode) {\n        var attempts = Number(row.getValue('u_attempts'));\n        var status = delivered ? 'delivered' : (attempts >= 8 ? 'dead_letter' : 'retry');\n        var update = new GlideRecord('u_cowork_outbox');\n        update.addQuery('sys_id', String(row.getUniqueValue()));\n        update.addQuery('u_status', 'sending');\n        update.addQuery('u_lease_token', String(row.getValue('u_lease_token')));\n        update.setValue('u_status', status);\n        update.setValue('u_last_error', delivered ? '' : errorCode);\n        update.setValue('u_lease_token', '');\n        update.setValue('u_lease_until', '');\n        if (status === 'retry') {\n            var next = new GlideDateTime();\n            next.addSeconds(Math.min(3600, 30 * Math.pow(2, attempts - 1)));\n            update.setValue('u_next_attempt_at', next);\n        } else update.setValue('u_next_attempt_at', '');\n        if (delivered) update.setValue('u_delivered_at', new GlideDateTime());\n        if (status === 'dead_letter') update.setValue('u_requires_attention', true);\n        update.updateMultiple();\n        var verified = new GlideRecord('u_cowork_outbox');\n        if (!verified.get(String(row.getUniqueValue())) || String(verified.getValue('u_status')) !== status) return false;\n        if (status === 'dead_letter') {\n            gs.error('Cowork outbox dead letter retained; event_id=' + String(row.getValue('u_event_id')));\n            // Event parameters are correlation metadata only; never include payload, URLs or tokens.\n            try { gs.eventQueue('cowork_bridge.outbox.dead_letter', verified, String(row.getValue('u_event_id')), errorCode); }\n            catch (ignored) { gs.error('Cowork outbox alert failed; inspect u_requires_attention=true.'); }\n        }\n        return delivered;\n    },\n\n    _duplicate: function (row, hash) {\n        if (String(row.getValue('u_payload_hash')) !== hash) {\n            // Do not overwrite a prior approved event snapshot merely because its ID was reused.\n            var alert = new GlideRecord('u_cowork_outbox');\n            alert.addQuery('sys_id', String(row.getUniqueValue()));\n            alert.setValue('u_requires_attention', true);\n            alert.updateMultiple();\n            gs.error('Cowork outbox event-ID payload conflict; operator reconciliation required.');\n            return false;\n        }\n        return true;\n    },\n\n    _snapshot: function (body) {\n        if (!body || body.bot !== 'cowork_mcp' || ['accepted', 'message', 'closed'].indexOf(body.event) < 0 ||\n            typeof body.client_session_id !== 'string' || !/^[A-Za-z0-9-]{16,80}$/.test(body.client_session_id) ||\n            typeof body.interaction_number !== 'string' || !body.interaction_number || body.interaction_number.length > 80 ||\n            typeof body.text !== 'string' || body.text.length > 8000 ||\n            typeof body.agent_name !== 'string' || body.agent_name.length > 200 ||\n            typeof body.event_id !== 'string')\n            throw new Error('cowork_outbox_invalid_event');\n        if (body.event === 'message') {\n            if (!/^[0-9a-f]{32}$/.test(body.event_id) || body.message_sys_id !== body.event_id)\n                throw new Error('cowork_outbox_invalid_event');\n        } else if (!(new RegExp('^[0-9a-f]{32}:' + body.event + ':[A-Za-z0-9 :.-]{1,64}$')).test(body.event_id))\n            throw new Error('cowork_outbox_invalid_event');\n        var snapshot = {\n            event: body.event, bot: 'cowork_mcp', client_session_id: body.client_session_id,\n            interaction_number: body.interaction_number, text: body.text, agent_name: body.agent_name,\n            event_id: body.event_id\n        };\n        if (body.event === 'message') snapshot.message_sys_id = body.message_sys_id;\n        return snapshot;\n    },\n\n    _find: function (eventId) {\n        var row = new GlideRecord('u_cowork_outbox');\n        row.addQuery('u_event_id', eventId);\n        row.setLimit(1);\n        row.query();\n        return row.next() ? row : null;\n    },\n    _enabled: function () {\n        return String(gs.getProperty('cowork_bridge.outbox_delivery_enabled', 'false')) === 'true';\n    },\n    type: 'CoworkBridgeOutbox'\n};\n",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "CoworkBridgeOutbox"
        },
        {
          "api_name": "global.CoworkBridgeOutbox"
        }
      ],
      "booleans": [
        "active",
        "client_callable"
      ],
      "baseline_sha256": "fa7d2893dabab85138165bab2d1a4c17ef4d5edfbbc81bf3eecbdf92f7331ba1"
    },
    {
      "table": "sys_script_include",
      "identity": "CoworkBridgeWebhook",
      "sys_id": "c816a3d07d613dffcdb0a4bb0033ce79",
      "fields": {
        "name": "CoworkBridgeWebhook",
        "api_name": "global.CoworkBridgeWebhook",
        "active": "true",
        "client_callable": "false",
        "access": "public",
        "script": "var CoworkBridgeWebhook = Class.create();\r\nCoworkBridgeWebhook.prototype = {\r\n    initialize: function () {},\r\n\r\n    configuration: function () {\r\n        var config = {\r\n            url: String(gs.getProperty('cowork_bridge.webhook_url', '')),\r\n            entity: String(gs.getProperty('cowork_bridge.webhook_oauth_entity', '')),\r\n            scope: String(gs.getProperty('cowork_bridge.webhook_oauth_scope', '')),\r\n            principal: String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''))\r\n        };\r\n        if (!/^https:\\/\\/[A-Za-z0-9.-]+(?::443)?\\/api\\/livechat\\/sn$/.test(config.url) ||\r\n            config.entity.length < 1 || config.entity.length > 160 || /[\\r\\n]/.test(config.entity) ||\r\n            !/^\\S+\\/\\.default$/.test(config.scope) || config.scope.length > 512 ||\r\n            !/^[0-9a-f]{32}$/.test(config.principal))\r\n            this._error('webhook_configuration_required');\r\n        return config;\r\n    },\r\n\r\n    interaction: function (current, previous) {\r\n        if (!previous || !this._isCowork(current)) return false;\r\n        var state = String(current.getValue('state'));\r\n        var oldState = String(previous.getValue('state'));\r\n        var event = '';\r\n        if (state.indexOf('closed') === 0 && oldState.indexOf('closed') !== 0) event = 'closed';\r\n        else if (state === 'work_in_progress' && current.getValue('assigned_to') &&\r\n            (oldState !== state || String(current.getValue('assigned_to')) !== String(previous.getValue('assigned_to'))))\r\n            event = 'accepted';\r\n        if (!event) return false;\r\n        if (event === 'accepted' && !this._realAgent(current, String(current.getValue('assigned_to')))) return false;\r\n        var version = String(current.getValue('sys_mod_count') || current.getValue('sys_updated_on') || '');\r\n        if (!version) return false;\r\n        var body = this._body(current, event, event === 'accepted' ? 'An agent accepted the chat.' : 'The chat is closed.');\r\n        body.event_id = String(current.getUniqueValue()) + ':' + event + ':' + version;\r\n        return new CoworkBridgeOutbox().enqueue(body, String(current.getUniqueValue()));\r\n    },\r\n\r\n    message: function (message) {\r\n        var type = String(message.getValue('q_data_message_type') || '');\r\n        if (String(message.getValue('message_type')) !== 'text' ||\r\n            (type !== 'systemTextMessage' && type !== 'consumerTextMessage')) return false;\r\n        var interaction = new GlideRecord('interaction');\r\n        interaction.addQuery('channel_metadata_document', String(message.getValue('conversation')));\r\n        interaction.setLimit(2);\r\n        interaction.query();\r\n        if (!interaction.next() || !this._isCowork(interaction)) return false;\r\n        var id = String(interaction.getUniqueValue());\r\n        if (interaction.next() || !interaction.get(id)) return false;\r\n        var principal = String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''));\r\n        if (!/^[0-9a-f]{32}$/.test(principal)) return false;\r\n        var sender = String(message.getValue('sender') || '');\r\n        if (sender !== String(interaction.getValue('assigned_to')) || !this._realAgent(interaction, sender)) return false;\r\n        var agent = new GlideRecord('sys_user');\r\n        if (!agent.get(sender) || !/^(true|1)$/.test(String(agent.getValue('active')))) return false;\r\n        var text = String(message.getValue('payload') || '');\r\n        if (!text || text.length > 8000) return false;\r\n        var body = this._body(interaction, 'message', text);\r\n        body.agent_name = String(agent.getDisplayValue() || '').substring(0, 200);\r\n        body.message_sys_id = String(message.getUniqueValue());\r\n        body.event_id = body.message_sys_id;\r\n        return new CoworkBridgeOutbox().enqueue(body, id);\r\n    },\r\n\r\n    deliver: function (body) {\r\n        if (!this._enabled()) return false;\r\n        try {\r\n            var config = this.configuration();\r\n            var client = new sn_auth.GlideOAuthClient();\r\n            var tokenResponse = client.requestToken(config.entity, JSON.stringify({\r\n                grant_type: 'client_credentials', scope: config.scope\r\n            }));\r\n            if (!tokenResponse || tokenResponse.getErrorMessage()) this._error('webhook_oauth_failed');\r\n            var token = tokenResponse.getToken();\r\n            var access = token && String(token.getAccessToken() || '');\r\n            if (!access || /[\\r\\n]/.test(access) ||\r\n                (typeof token.getExpiresIn === 'function' && Number(token.getExpiresIn()) <= 30))\r\n                this._error('webhook_oauth_failed');\r\n            var request = new sn_ws.RESTMessageV2();\r\n            request.setEndpoint(config.url);\r\n            request.setHttpMethod('post');\r\n            request.setHttpTimeout(10000);\r\n            request.setLogLevel('basic');\r\n            request.setRequestHeader('Content-Type', 'application/json');\r\n            request.setRequestHeader('Accept', 'application/json');\r\n            request.setRequestHeader('Authorization', 'Bearer ' + access);\r\n            request.setRequestHeader('X-Cowork-Event-Id', body.event_id);\r\n            request.setRequestHeader('X-Cowork-Bot', 'cowork_mcp');\r\n            request.setRequestBody(JSON.stringify(body));\r\n            var result = request.execute();\r\n            var status = Number(result.getStatusCode());\r\n            if (result.haveError() || status < 200 || status >= 300) this._error('webhook_delivery_failed');\r\n            return true;\r\n        } catch (ignored) {\r\n            // Neither exception text, token responses, nor transcript payloads go into application logs.\r\n            return false;\r\n        }\r\n    },\r\n\r\n    _body: function (interaction, event, text) {\r\n        return {\r\n            event: event, bot: 'cowork_mcp',\r\n            client_session_id: String(interaction.getValue('u_cowork_session_id')),\r\n            interaction_number: String(interaction.getValue('number') || ''),\r\n            text: text,\r\n            agent_name: String(interaction.getDisplayValue('assigned_to') || '').substring(0, 200)\r\n        };\r\n    },\r\n    _enabled: function () { return String(gs.getProperty('cowork_bridge.outbox_delivery_enabled', 'false')) === 'true'; },\r\n    _realAgent: function (interaction, sender) {\r\n        var principal = String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''));\r\n        var virtualAgent = String(gs.getProperty('cowork_bridge.virtual_agent_user_sys_id', ''));\r\n        if (!/^[0-9a-f]{32}$/.test(principal) || !/^[0-9a-f]{32}$/.test(virtualAgent) ||\r\n            !sender || sender === principal || sender === virtualAgent ||\r\n            sender === String(interaction.getValue('opened_for'))) return false;\r\n        var user = new GlideRecord('sys_user');\r\n        return user.get(sender) && /^(true|1)$/.test(String(user.getValue('active')));\r\n    },\r\n    _isCowork: function (interaction) {\r\n        return /^[A-Za-z0-9-]{16,80}$/.test(String(interaction.getValue('u_cowork_session_id') || '')) &&\r\n            !!interaction.getValue('u_cowork_upn') &&\r\n            !(interaction.isValidField('u_copilot_upn') && interaction.getValue('u_copilot_upn')) &&\r\n            !(interaction.isValidField('u_bridge_session_id') && interaction.getValue('u_bridge_session_id'));\r\n    },\r\n    _error: function (code) {\r\n        var error = new Error(code);\r\n        error.coworkStatus = 503;\r\n        error.coworkCode = code;\r\n        throw error;\r\n    },\r\n    type: 'CoworkBridgeWebhook'\r\n};\r\n",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "CoworkBridgeWebhook"
        },
        {
          "api_name": "global.CoworkBridgeWebhook"
        }
      ],
      "booleans": [
        "active",
        "client_callable"
      ],
      "baseline_sha256": "c4bdba2770484310c3286d5b6b20d4dfff7c10c9296c49857562012f0e371f9b"
    },
    {
      "table": "sys_script_include",
      "identity": "CoworkBridge",
      "sys_id": "3404bd0fe155751375dec96015db9d18",
      "fields": {
        "name": "CoworkBridge",
        "api_name": "global.CoworkBridge",
        "active": "true",
        "client_callable": "false",
        "access": "public",
        "script": "var CoworkBridge = Class.create();\r\nCoworkBridge.prototype = {\r\n    initialize: function () {},\r\n\r\n    handle: function (operation, request, response) {\r\n        var command = null;\r\n        try {\r\n            var principal = String(gs.getProperty('cowork_bridge.integration_user_sys_id', ''));\r\n            if (!/^[0-9a-f]{32}$/.test(principal))\r\n                this._throw(503, 'configuration_required');\r\n            if (String(gs.getUserID()) !== principal)\r\n                this._throw(403, 'integration_principal_required');\r\n            if (operation === 'open_chat' && String(gs.getProperty('cowork_bridge.enabled', 'false')) !== 'true') {\r\n                    return this._respond(response, 200, {\r\n                        conversation_sys_id: '', interaction_number: '', unavailable: true,\r\n                        message: String(gs.getProperty('cowork_bridge.unavailable_message',\r\n                            'Live chat is unavailable. Please use your IT support portal.')).substring(0, 1000)\r\n                    });\r\n            }\r\n\r\n            var body = request.body && request.body.data;\r\n            if (!body || typeof body !== 'object' || Array.isArray(body))\r\n                this._throw(400, 'invalid_body');\r\n            var input = this._validate(operation, body);\r\n            var config = operation === 'open_chat' ? this._config(principal) : null;\r\n            var owned = operation === 'open_chat' ? null : this._owned(input.conversation_sys_id);\r\n            var key = operation === 'open_chat' ? 'open:' + input.client_session_id :\r\n                (operation === 'send_message' ? 'send:' : 'close:') + input.conversation_sys_id +\r\n                (input.client_message_id ? ':' + input.client_message_id : '');\r\n            var hash = String(new GlideDigest().getSHA256Hex(JSON.stringify(input)));\r\n            command = this._reserve(key, hash);\r\n            if (command.cached)\r\n                return this._respond(response, 200, command.cached);\r\n\r\n            var result;\r\n            if (operation === 'open_chat') result = this._open(input, config, command.row);\r\n            else if (operation === 'send_message') result = this._send(input, owned);\r\n            else result = this._close(owned);\r\n            command.row.setValue('u_result', JSON.stringify(result));\r\n            command.row.setValue('u_status', 'completed');\r\n            if (owned) command.row.setValue('u_conversation', input.conversation_sys_id);\r\n            this._update(command.row);\r\n            return this._respond(response, 200, result);\r\n        } catch (error) {\r\n            // Never persist exception text: platform errors can contain message bodies or credentials.\r\n            var code = error.coworkCode || 'platform_operation_failed';\r\n            if (command && command.row && !command.cached) {\r\n                try {\r\n                    command.row.setValue('u_status', 'failed');\r\n                    command.row.setValue('u_error', code);\r\n                    command.row.update();\r\n                } catch (ignored) {}\r\n                return this._respond(response, 409, {\r\n                    error: 'command_ambiguous',\r\n                    message: 'Command may have partially executed. Reconcile its ledger before retrying.'\r\n                });\r\n            }\r\n            return this._respond(response, error.coworkStatus || 500, { error: code });\r\n        }\r\n    },\r\n\r\n    _validate: function (operation, body) {\r\n        var input;\r\n        if (operation === 'open_chat') {\r\n            if (body.bot !== 'cowork_mcp') this._throw(400, 'invalid_bot');\r\n            input = {\r\n                email: this._email(body.email),\r\n                summary: this._string(body.summary, 1, 4000, 'summary'),\r\n                lang: body.lang === undefined ? '' : this._string(body.lang, 0, 32, 'lang'),\r\n                client_session_id: this._clientId(body.client_session_id),\r\n                bot: 'cowork_mcp'\r\n            };\r\n            if (input.lang && !/^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8}){0,3}$/.test(input.lang))\r\n                this._throw(400, 'invalid_lang');\r\n            input.lang = input.lang.toLowerCase();\r\n        } else if (operation === 'send_message' || operation === 'close_chat') {\r\n            input = { conversation_sys_id: this._sysId(body.conversation_sys_id) };\r\n            if (operation === 'send_message') {\r\n                input.text = this._string(body.text, 1, 8000, 'text');\r\n                input.email = this._email(body.email);\r\n                input.client_message_id = this._clientId(body.client_message_id);\r\n            } else if (body.client_message_id !== undefined) {\r\n                input.client_message_id = this._clientId(body.client_message_id);\r\n            }\r\n        } else this._throw(404, 'unknown_operation');\r\n        return input;\r\n    },\r\n\r\n    _config: function (principal) {\r\n        var names = ['queue_sys_id', 'service_channel_sys_id', 'vendor_sys_id', 'virtual_agent_user_sys_id'];\r\n        var config = { principal: principal };\r\n        for (var i = 0; i < names.length; i++) {\r\n            var value = String(gs.getProperty('cowork_bridge.' + names[i], ''));\r\n            if (!/^[0-9a-f]{32}$/.test(value)) this._throw(503, 'routing_configuration_required');\r\n            config[names[i]] = value;\r\n        }\r\n        var queue = this._get('awa_queue', config.queue_sys_id);\r\n        var channel = this._get('awa_service_channel', config.service_channel_sys_id);\r\n        var user = this._get('sys_user', principal);\r\n        var va = this._get('sys_user', config.virtual_agent_user_sys_id);\r\n        this._get('sys_cs_vendor', config.vendor_sys_id);\r\n        if (!this._true(queue.getValue('active')) || !this._true(channel.getValue('active')) ||\r\n            !this._true(user.getValue('active')) || !this._true(va.getValue('active')) ||\r\n            String(queue.getValue('service_channel')) !== config.service_channel_sys_id ||\r\n            config.virtual_agent_user_sys_id === principal)\r\n            this._throw(503, 'routing_configuration_invalid');\r\n        // Callback routing must be complete before reserving a command or creating chat records.\r\n        new CoworkBridgeWebhook().configuration();\r\n        return config;\r\n    },\r\n\r\n    _reserve: function (key, hash) {\r\n        var existing = this._command(key);\r\n        if (existing) return this._replay(existing, hash);\r\n        var row = new GlideRecord('u_cowork_command');\r\n        row.initialize();\r\n        row.setValue('u_key', key);\r\n        row.setValue('u_request_hash', hash);\r\n        row.setValue('u_status', 'pending');\r\n        var id = null;\r\n        try { id = row.insert(); } catch (ignored) {}\r\n        if (!id) {\r\n            // The unique database index, not this preceding lookup, wins a concurrent reservation.\r\n            existing = this._command(key);\r\n            if (existing) return this._replay(existing, hash);\r\n            this._throw(409, 'command_reservation_unconfirmed');\r\n        }\r\n        return { row: row };\r\n    },\r\n\r\n    _command: function (key) {\r\n        var row = new GlideRecord('u_cowork_command');\r\n        row.addQuery('u_key', key);\r\n        row.setLimit(1);\r\n        row.query();\r\n        return row.next() ? row : null;\r\n    },\r\n\r\n    _replay: function (row, hash) {\r\n        if (String(row.getValue('u_request_hash')) !== hash)\r\n            this._throw(409, 'idempotency_key_reused');\r\n        if (String(row.getValue('u_status')) !== 'completed')\r\n            this._throw(409, 'command_ambiguous');\r\n        var result;\r\n        try { result = JSON.parse(String(row.getValue('u_result'))); } catch (ignored) {}\r\n        if (!result || typeof result !== 'object') this._throw(409, 'command_ambiguous');\r\n        var key = String(row.getValue('u_key'));\r\n        if ((key.indexOf('open:') === 0 &&\r\n            (result.unavailable !== false || !/^[0-9a-f]{32}$/.test(String(result.conversation_sys_id || '')) ||\r\n                typeof result.interaction_number !== 'string' || !result.interaction_number)) ||\r\n            (key.indexOf('send:') === 0 &&\r\n                !((result.sent === true && result.closed === false) || (result.sent === false && result.closed === true))) ||\r\n            (key.indexOf('close:') === 0 && result.closed !== true))\r\n            this._throw(409, 'command_ambiguous');\r\n        return { cached: result };\r\n    },\r\n\r\n    _open: function (input, config, command) {\r\n        var user = new GlideRecord('sys_user');\r\n        user.addQuery('email', input.email);\r\n        user.addActiveQuery();\r\n        user.setLimit(2);\r\n        user.query();\r\n        if (!user.next()) this._throw(404, 'requester_not_found');\r\n        var userId = String(user.getUniqueValue());\r\n        if (user.next()) this._throw(409, 'requester_not_unique');\r\n        if (userId === config.principal || userId === config.virtual_agent_user_sys_id)\r\n            this._throw(400, 'requester_must_be_end_user');\r\n\r\n        var prior = new GlideRecord('interaction');\r\n        prior.addQuery('u_cowork_session_id', input.client_session_id);\r\n        prior.setLimit(1);\r\n        prior.query();\r\n        if (prior.next()) this._throw(409, 'session_already_exists');\r\n        var conversationId = String(sn_cs.VASystemObject.createConversation(userId) || '');\r\n        if (!/^[0-9a-f]{32}$/.test(conversationId)) this._throw(500, 'conversation_creation_failed');\r\n        command.setValue('u_conversation', conversationId);\r\n        this._update(command);\r\n        var conversation = this._get('sys_cs_conversation', conversationId);\r\n        var interaction = this._interaction(conversationId);\r\n        if (!interaction) this._throw(500, 'interaction_creation_failed');\r\n        if ((interaction.isValidField('u_copilot_upn') && interaction.getValue('u_copilot_upn')) ||\r\n            (interaction.isValidField('u_bridge_session_id') && interaction.getValue('u_bridge_session_id')) ||\r\n            interaction.getValue('u_cowork_session_id'))\r\n            this._throw(409, 'interaction_not_isolated');\r\n\r\n        // Persist the correlation key before any explicit message insert or AWA insert/update.\r\n        interaction.setValue('u_cowork_session_id', input.client_session_id);\r\n        interaction.setValue('u_cowork_upn', input.email);\r\n        interaction.setValue('assigned_to', '');\r\n        interaction.setValue('opened_for', userId);\r\n        interaction.setValue('short_description', 'Copilot Cowork: ' + input.summary.substring(0, 140));\r\n        interaction.setValue('direction', 'inbound');\r\n        interaction.setValue('type', 'chat');\r\n        interaction.setValue('state', 'new');\r\n        if (input.lang) interaction.setValue('user_language', input.lang);\r\n        this._update(interaction);\r\n        interaction = this._get('interaction', String(interaction.getUniqueValue()));\r\n        if (String(interaction.getValue('u_cowork_session_id')) !== input.client_session_id ||\r\n            !interaction.getValue('number')) this._throw(500, 'correlation_not_persisted');\r\n\r\n        var device = String(conversation.getValue('current_device') || '');\r\n        var consumer = String(conversation.getValue('consumer') || '');\r\n        var account = String(conversation.getValue('consumer_account') || '');\r\n        if (!device || !consumer || !account) this._throw(500, 'conversation_context_incomplete');\r\n        conversation.setValue('state', 'chatInProgress');\r\n        conversation.setValue('live_agent_transfer_time', new GlideDateTime());\r\n        conversation.setValue('opened_for', userId);\r\n        conversation.setValue('title', 'Copilot Cowork: ' + input.summary.substring(0, 80));\r\n        this._update(conversation);\r\n\r\n        var sessionId = this._insert('sys_cs_session', {\r\n            consumer: consumer, consumer_account: account, vendor: config.vendor_sys_id,\r\n            device_id: device, device_type: 'mweb', direction: 'inbound', interaction: 'QnA',\r\n            start_time: new GlideDateTime()\r\n        });\r\n        this._insert('sys_cs_session_binding', {\r\n            session: sessionId, system_topic: conversationId, topic: conversationId,\r\n            channel_type: 'AMB', channel_id: '/cs/messages/' + sessionId,\r\n            client_connected: true, online: true, guest: false,\r\n            last_client_activity_time: new GlideDateTime()\r\n        });\r\n        var first = 'Escalated from Copilot Cowork.\\nReason: ' + input.summary +\r\n            (input.lang ? '\\nRequester language: ' + input.lang : '');\r\n        this._insert('sys_cs_message', {\r\n            conversation: conversationId, session: sessionId, consumer: consumer,\r\n            consumer_account: account, vendor: config.vendor_sys_id, direction: 'inbound',\r\n            message_type: 'text', q_data_message_type: 'consumerTextMessage',\r\n            payload: first, message_size: first.length, sender: userId,\r\n            recipient: config.virtual_agent_user_sys_id, status: 'received',\r\n            send_time: new GlideDateTime(), receive_time: new GlideDateTime(),\r\n            task: String(interaction.getUniqueValue())\r\n        });\r\n        this._ensureWorkItem(String(interaction.getUniqueValue()), config.queue_sys_id);\r\n        return {\r\n            conversation_sys_id: conversationId,\r\n            interaction_number: String(interaction.getValue('number')), unavailable: false\r\n        };\r\n    },\r\n\r\n    _ensureWorkItem: function (interactionId, queueId) {\r\n        var existing = this._activeWorkItem(interactionId, queueId);\r\n        if (existing) return;\r\n        var row = new GlideRecord('awa_work_item');\r\n        row.initialize();\r\n        row.setValue('document_id', interactionId);\r\n        row.setValue('document_table', 'interaction');\r\n        row.setValue('queue', queueId);\r\n        row.setValue('active', true);\r\n        var id = row.insert();\r\n        if (!id) {\r\n            if (this._activeWorkItem(interactionId, queueId)) return;\r\n            this._throw(500, 'work_item_creation_failed');\r\n        }\r\n        var work = this._get('awa_work_item', String(id));\r\n        work.setValue('state', 'queued');\r\n        this._update(work);\r\n    },\r\n\r\n    _activeWorkItem: function (interactionId, queueId) {\r\n        var row = new GlideRecord('awa_work_item');\r\n        row.addQuery('document_id', interactionId);\r\n        row.addQuery('active', true);\r\n        row.setLimit(2);\r\n        row.query();\r\n        if (!row.next()) return false;\r\n        if (String(row.getValue('queue')) !== queueId ||\r\n            ['queued', 'pending_accept', 'accepted'].indexOf(String(row.getValue('state'))) < 0)\r\n            this._throw(409, 'work_item_routing_mismatch');\r\n        if (row.next()) this._throw(409, 'multiple_active_work_items');\r\n        return true;\r\n    },\r\n\r\n    _owned: function (id) {\r\n        var conversation = this._get('sys_cs_conversation', id);\r\n        var interaction = this._interaction(id);\r\n        if (!interaction || !/^[A-Za-z0-9-]{16,80}$/.test(String(interaction.getValue('u_cowork_session_id') || '')) ||\r\n            !interaction.getValue('u_cowork_upn') ||\r\n            (interaction.isValidField('u_copilot_upn') && interaction.getValue('u_copilot_upn')) ||\r\n            (interaction.isValidField('u_bridge_session_id') && interaction.getValue('u_bridge_session_id')))\r\n            this._throw(403, 'not_a_cowork_conversation');\r\n        return { conversation: conversation, interaction: interaction };\r\n    },\r\n\r\n    _send: function (input, owned) {\r\n        if (this._closed(owned)) return { sent: false, closed: true };\r\n        var requester = this._get('sys_user', String(owned.interaction.getValue('opened_for')));\r\n        var display = String(requester.getDisplayValue() || 'Requester').replace(/[\\r\\n]/g, ' ').substring(0, 200);\r\n        // AgentChat uses the authenticated, dedicated integration user. No impersonation or email-derived name.\r\n        var sent = sn_cs.AgentChatScriptObject.send(input.conversation_sys_id,\r\n            display + ' (via Copilot Cowork): ' + input.text, null, false);\r\n        if (sent === false) this._throw(500, 'chat_send_failed');\r\n        var binding = new GlideRecord('sys_cs_session_binding');\r\n        binding.addQuery('system_topic', input.conversation_sys_id);\r\n        binding.addQuery('topic', input.conversation_sys_id);\r\n        binding.query();\r\n        while (binding.next()) {\r\n            binding.setValue('last_client_activity_time', new GlideDateTime());\r\n            binding.setValue('online', true);\r\n            binding.setValue('client_connected', true);\r\n            this._update(binding);\r\n        }\r\n        return { sent: true, closed: false };\r\n    },\r\n\r\n    _close: function (owned) {\r\n        // Preserve Cowork metadata and business-rule execution: our closed callback must still fire.\r\n        if (String(owned.interaction.getValue('state')).indexOf('closed') !== 0) {\r\n            owned.interaction.setValue('state', 'closed_complete');\r\n            this._update(owned.interaction);\r\n        }\r\n        if (String(owned.conversation.getValue('state')).indexOf('closed') !== 0) {\r\n            owned.conversation.setValue('state', 'closed');\r\n            this._update(owned.conversation);\r\n        }\r\n        return { closed: true };\r\n    },\r\n\r\n    _closed: function (owned) {\r\n        return String(owned.interaction.getValue('state')).indexOf('closed') === 0 ||\r\n            String(owned.conversation.getValue('state')).indexOf('closed') === 0;\r\n    },\r\n\r\n    _interaction: function (id) {\r\n        var row = new GlideRecord('interaction');\r\n        row.addQuery('channel_metadata_document', id);\r\n        row.setLimit(2);\r\n        row.query();\r\n        if (!row.next()) return null;\r\n        var sid = String(row.getUniqueValue());\r\n        if (row.next()) this._throw(409, 'ambiguous_interaction');\r\n        return this._get('interaction', sid);\r\n    },\r\n\r\n    _get: function (table, id) {\r\n        var row = new GlideRecord(table);\r\n        if (!row.get(id)) this._throw(404, 'required_record_not_found');\r\n        return row;\r\n    },\r\n\r\n    _insert: function (table, values) {\r\n        var row = new GlideRecord(table);\r\n        row.initialize();\r\n        for (var field in values)\r\n            if (Object.prototype.hasOwnProperty.call(values, field)) row.setValue(field, values[field]);\r\n        var id = row.insert();\r\n        if (!id) this._throw(500, 'record_insert_failed');\r\n        return String(id);\r\n    },\r\n\r\n    _update: function (row) {\r\n        if (!row.update()) this._throw(500, 'record_update_failed');\r\n    },\r\n\r\n    _string: function (value, min, max, name) {\r\n        if (typeof value !== 'string' || value.length < min || value.length > max ||\r\n            value.indexOf('\\u0000') !== -1 || (min > 0 && !/\\S/.test(value)))\r\n            this._throw(400, 'invalid_' + name);\r\n        return value;\r\n    },\r\n\r\n    _email: function (value) {\r\n        var email = this._string(value, 3, 254, 'email').toLowerCase();\r\n        if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) this._throw(400, 'invalid_email');\r\n        return email;\r\n    },\r\n\r\n    _clientId: function (value) {\r\n        if (typeof value !== 'string' || !/^[A-Za-z0-9-]{16,80}$/.test(value))\r\n            this._throw(400, 'invalid_client_id');\r\n        return value;\r\n    },\r\n\r\n    _sysId: function (value) {\r\n        if (typeof value !== 'string' || !/^[0-9a-f]{32}$/.test(value))\r\n            this._throw(400, 'invalid_conversation_sys_id');\r\n        return value;\r\n    },\r\n\r\n    _true: function (value) { return String(value) === 'true' || String(value) === '1'; },\r\n    _throw: function (status, code) {\r\n        var error = new Error(code);\r\n        error.coworkStatus = status;\r\n        error.coworkCode = code;\r\n        throw error;\r\n    },\r\n    _respond: function (response, status, body) {\r\n        response.setStatus(status);\r\n        response.setBody(body);\r\n    },\r\n    type: 'CoworkBridge'\r\n};\r\n",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "CoworkBridge"
        },
        {
          "api_name": "global.CoworkBridge"
        }
      ],
      "booleans": [
        "active",
        "client_callable"
      ],
      "baseline_sha256": "cb517201ee7d4e970c35f6f5409947ea45f0aa7fba109eccc4fb66c9f8b431c4"
    },
    {
      "table": "sys_ws_definition",
      "identity": "/api/cowork_review/cowork_bridge",
      "sys_id": "4c0c9189fc050c8849da02bcde47fd53",
      "fields": {
        "name": "Cowork Bridge",
        "service_id": "cowork_bridge",
        "namespace": "cowork_review",
        "base_uri": "/api/cowork_review/cowork_bridge",
        "active": "false",
        "is_versioned": "false",
        "enforce_acl": "01af399fbf8ceb48a1ba6d603b0f4bdd",
        "consumes": "application/json",
        "produces": "application/json",
        "consumes_customized": "true",
        "produces_customized": "true",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "Cowork Bridge"
        },
        {
          "namespace": "cowork_review",
          "service_id": "cowork_bridge"
        },
        {
          "base_uri": "/api/cowork_review/cowork_bridge"
        }
      ],
      "booleans": [
        "active",
        "is_versioned",
        "consumes_customized",
        "produces_customized"
      ],
      "baseline_sha256": "581f15802b8591c0fd0dc23fdcf5bf18475a91a329c74089cf47f1b2c7ff566e"
    },
    {
      "table": "sys_ws_operation",
      "identity": "/api/cowork_review/cowork_bridge/open_chat",
      "sys_id": "6929fd52f55bf627506cf0b372b111f0",
      "fields": {
        "name": "open_chat",
        "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
        "web_service_version": "",
        "relative_path": "/open_chat",
        "http_method": "POST",
        "active": "false",
        "operation_script": "(function process(request, response) {\n    new CoworkBridge().handle('open_chat', request, response);\n})(request, response);\n",
        "requires_authentication": "true",
        "requires_acl_authorization": "true",
        "enforce_acl": "01af399fbf8ceb48a1ba6d603b0f4bdd",
        "consumes": "application/json",
        "produces": "application/json",
        "consumes_customized": "true",
        "produces_customized": "true",
        "sys_scope": "global"
      },
      "keys": [
        {
          "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
          "name": "open_chat"
        },
        {
          "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
          "relative_path": "/open_chat",
          "http_method": "POST"
        }
      ],
      "booleans": [
        "active",
        "requires_authentication",
        "requires_acl_authorization",
        "consumes_customized",
        "produces_customized"
      ],
      "baseline_sha256": "9e5a8cd2c753b33658f507c0973fea3b09569b584988cac61f41ed985bf9a1cb"
    },
    {
      "table": "sys_ws_operation",
      "identity": "/api/cowork_review/cowork_bridge/send_message",
      "sys_id": "a7a8d6a8bbaa9382c21b6179cd7630c6",
      "fields": {
        "name": "send_message",
        "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
        "web_service_version": "",
        "relative_path": "/send_message",
        "http_method": "POST",
        "active": "false",
        "operation_script": "(function process(request, response) {\n    new CoworkBridge().handle('send_message', request, response);\n})(request, response);\n",
        "requires_authentication": "true",
        "requires_acl_authorization": "true",
        "enforce_acl": "01af399fbf8ceb48a1ba6d603b0f4bdd",
        "consumes": "application/json",
        "produces": "application/json",
        "consumes_customized": "true",
        "produces_customized": "true",
        "sys_scope": "global"
      },
      "keys": [
        {
          "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
          "name": "send_message"
        },
        {
          "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
          "relative_path": "/send_message",
          "http_method": "POST"
        }
      ],
      "booleans": [
        "active",
        "requires_authentication",
        "requires_acl_authorization",
        "consumes_customized",
        "produces_customized"
      ],
      "baseline_sha256": "e995d7615b7ea3ca968b6188eeb48efee586e46b383a1b5e4b6dfafa58a5486e"
    },
    {
      "table": "sys_ws_operation",
      "identity": "/api/cowork_review/cowork_bridge/close_chat",
      "sys_id": "a8c26b6f1889cf6d2616cf398e163a4e",
      "fields": {
        "name": "close_chat",
        "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
        "web_service_version": "",
        "relative_path": "/close_chat",
        "http_method": "POST",
        "active": "false",
        "operation_script": "(function process(request, response) {\n    new CoworkBridge().handle('close_chat', request, response);\n})(request, response);\n",
        "requires_authentication": "true",
        "requires_acl_authorization": "true",
        "enforce_acl": "01af399fbf8ceb48a1ba6d603b0f4bdd",
        "consumes": "application/json",
        "produces": "application/json",
        "consumes_customized": "true",
        "produces_customized": "true",
        "sys_scope": "global"
      },
      "keys": [
        {
          "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
          "name": "close_chat"
        },
        {
          "web_service_definition": "4c0c9189fc050c8849da02bcde47fd53",
          "relative_path": "/close_chat",
          "http_method": "POST"
        }
      ],
      "booleans": [
        "active",
        "requires_authentication",
        "requires_acl_authorization",
        "consumes_customized",
        "produces_customized"
      ],
      "baseline_sha256": "ad78516570c9b3be019feac26e2169dc1e85e2b29723c36517a377b90afd65c7"
    },
    {
      "table": "sys_script",
      "identity": "Cowork interaction accepted or closed",
      "sys_id": "6747594fcc6e52e207d76a4cd04d9592",
      "fields": {
        "name": "Cowork interaction accepted or closed",
        "collection": "interaction",
        "active": "false",
        "advanced": "true",
        "when": "after",
        "order": "200",
        "action_insert": "false",
        "action_update": "true",
        "action_delete": "false",
        "action_query": "false",
        "filter_condition": "u_cowork_session_idISNOTEMPTY^u_cowork_upnISNOTEMPTY",
        "condition": "current.state.changes() || current.assigned_to.changes()",
        "script": "(function executeRule(current, previous) {\n    new CoworkBridgeWebhook().interaction(current, previous);\n})(current, previous);\n",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "Cowork interaction accepted or closed"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "action_insert",
        "action_update",
        "action_delete",
        "action_query"
      ],
      "baseline_sha256": "99a320044de4d515c58207e0eeaa66eaa0ab48d4bbda0bc6e702736918683f4c"
    },
    {
      "table": "sys_script",
      "identity": "Cowork agent message callback",
      "sys_id": "8b551ecd5fcf05400b13ed322094a5a3",
      "fields": {
        "name": "Cowork agent message callback",
        "collection": "sys_cs_message",
        "active": "false",
        "advanced": "true",
        "when": "after",
        "order": "200",
        "action_insert": "true",
        "action_update": "false",
        "action_delete": "false",
        "action_query": "false",
        "filter_condition": "message_type=text",
        "condition": "",
        "script": "(function executeRule(current, previous) {\n    new CoworkBridgeWebhook().message(current);\n})(current, previous);\n",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "Cowork agent message callback"
        }
      ],
      "booleans": [
        "active",
        "advanced",
        "action_insert",
        "action_update",
        "action_delete",
        "action_query"
      ],
      "baseline_sha256": "9cce090fd3e0c5441edca2bdb014bf55ee294bd04af5b09be9560154c1711940"
    },
    {
      "table": "sysauto_script",
      "identity": "Cowork outbox retry",
      "sys_id": "99f8699315bfe457ebc11295742db141",
      "fields": {
        "name": "Cowork outbox retry",
        "active": "false",
        "run_type": "periodically",
        "run_period": "1970-01-01 00:01:00",
        "conditional": "false",
        "condition": "",
        "script": "(function retryCoworkCallbacks() {\n    new CoworkBridgeOutbox().retry();\n})();\n",
        "sys_scope": "global"
      },
      "keys": [
        {
          "name": "Cowork outbox retry"
        }
      ],
      "booleans": [
        "active",
        "conditional"
      ],
      "baseline_sha256": "c3bc0bfd745f8f2210a5310ef91684ffef0fb69bbd2b5ffab19d16c6ce525f0a"
    },
    {
      "table": "sysevent_register",
      "identity": "cowork_bridge.outbox.dead_letter",
      "sys_id": "474ffacb015f98091ec2dda04b994997",
      "fields": {
        "event_name": "cowork_bridge.outbox.dead_letter",
        "table": "u_cowork_outbox",
        "description": "Retained event needs operator recovery. Parm1 is stable event ID; parm2 is sanitized error code; no ",
        "queue": "",
        "sys_scope": "global"
      },
      "keys": [
        {
          "event_name": "cowork_bridge.outbox.dead_letter"
        }
      ],
      "booleans": [],
      "baseline_sha256": "dc47cc707be6de5d5413edf4a64046930df95d0d7baa7c7b66ce122db07ddc60"
    }
  ],
  "index_requests": [
    {
      "table": "u_cowork_command",
      "columns": [
        "u_key"
      ],
      "unique": true,
      "mechanism": "sys_dictionary.unique=true; physical enforcement MUST be independently verified"
    },
    {
      "table": "u_cowork_outbox",
      "columns": [
        "u_event_id"
      ],
      "unique": true,
      "mechanism": "sys_dictionary.unique=true; physical enforcement MUST be independently verified"
    },
    {
      "table": "u_cowork_outbox",
      "columns": [
        "u_status",
        "u_next_attempt_at"
      ],
      "unique": false,
      "mechanism": "MANUAL: supported Tables > Database Indexes workflow; no guessed index metadata writes"
    },
    {
      "table": "u_cowork_outbox",
      "columns": [
        "u_status",
        "u_lease_until"
      ],
      "unique": false,
      "mechanism": "MANUAL: supported Tables > Database Indexes workflow; no guessed index metadata writes"
    },
    {
      "table": "u_cowork_outbox",
      "columns": [
        "u_requires_attention"
      ],
      "unique": false,
      "mechanism": "MANUAL: supported Tables > Database Indexes workflow; no guessed index metadata writes"
    },
    {
      "table": "interaction",
      "columns": [
        "u_cowork_session_id"
      ],
      "unique": false,
      "mechanism": "MANUAL: supported Tables > Database Indexes workflow; no guessed index metadata writes"
    }
  ],
  "legacy": {
    "table": "sys_script",
    "sys_id": "00000000000000000000000000000000",
    "original_script_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "prerequisites": [
    "Review this exact artifact and same-release table/dictionary creation behavior before apply. No inferred schema fallback.",
    "Use one elevated security_admin installer session in global; no concurrent installer or metadata edits.",
    "Legacy interaction ownership fields are optional: inspect presence only, never their data; presence drift during this run stops installation. Runtime rejects either populated legacy field independently.",
    "NONDEPLOYABLE TEMPLATE: independently review target instance, native Global namespace and API base_uri before adapting exact guards.",
    "Dictionary unique=true requests the unique database indexes; verify physical enforcement separately. Nonunique indexes are manual.",
    "Installation stages DISABLED metadata only. No OAuth, credentials, users, memberships, queues, notifications or activation are created.",
    "Legacy fanout amendment is optional and target-specific. If absent, do not create or amend a rule. All-zero sentinels and helper refusal remain; this installer never reads or patches legacy scripts."
  ]
};
var COWORK_INSTALL_MANIFEST_SHA256 = "3b606fda58b9df7734554ee33a2fcfb3988f325833bfb2ffacba503517466ab5";
var CoworkInstall = function installRuntime(manifest, expectedManifestHash, options) {
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
};
CoworkInstall(COWORK_INSTALL_MANIFEST, COWORK_INSTALL_MANIFEST_SHA256, {
    dryRun: COWORK_INSTALL_DRY_RUN, reviewedDefinition: COWORK_INSTALL_REVIEWED_DEFINITION
});
