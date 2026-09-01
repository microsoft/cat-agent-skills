# Troubleshooting

## Failure matrix

| Symptom | Layer | Likely cause | Action |
|---|---|---|---|
| Upload rejects missing `mcpToolDescription` | Manifest | Numbered schema requires a bundled tool file | Add a package-relative tool file captured from `tools/list` |
| Validator says tool-description file is absent although it is in the ZIP | Manifest path | Referenced path does not match the archive path or casing | Match the packaged file path and rebuild |
| Nested skill name must match parent folder | Skill layout | Companion documents are named `SKILL.md` | Rename non-registered documents to `REFERENCE.md` or `CAPABILITY.md` |
| `Invalid encoded OAuthConfigurationId` | OAuth lookup | Placeholder or wrong identifier in `referenceId` | Use Teams Developer Portal's generated OAuth client registration ID |
| OAuth base URL mismatch | OAuth config | Portal base URL differs from MCP URL | Make the values identical |
| Repeated sign-in or retry button | OAuth/consent | Auth config missing, invalid, or consent denied | Stop retrying and inspect the first failed network request |
| `Need admin approval` | Consent | Delegated scope requires tenant consent | Request administrator consent for the provider app |
| HTTP 401 from MCP after sign-in | Token | Wrong audience, scope, or expired/revoked authorization | Inspect protected-resource metadata and token configuration |
| HTTP 403 from Dataverse MCP | Server policy | Client app is not enabled in allowed MCP clients | Enable the Entra client in Power Platform admin center |
| HTTP 404 after successful provisioning | OAuth app restriction | OAuth config was bound to a specific Teams app | Set registration to **Any Teams app** |
| `atk import openplugin` rejects `mcpServers` | Import | Inline object duplicates `.mcp.json` | Remove it from a staging copy and retry |
| Package validates but connector fails | Runtime | Package validation does not test OAuth or server policy | Test sign-in, handshake, and one read-only tool |

## Diagnostic order

1. Save the first failing request URL, HTTP status, and sanitized response.
2. Check whether failure occurs before the MCP URL is contacted.
3. Verify `authorization.referenceId` against Teams Developer Portal.
4. Verify OAuth base URL, endpoints, scope, PKCE, and app restriction.
5. Verify identity-provider permission and consent.
6. Verify MCP server allowed-client policy.
7. Run an MCP initialization and `tools/list`.
8. Test one read-only tool before testing writes.

## Retry policy

Retry transient network failures only. Do not retry:

- Invalid manifest paths
- Invalid OAuth configuration IDs
- Missing consent
- Disallowed client applications
- Unsupported authentication types

Surface the configuration error and the exact remediation instead.
