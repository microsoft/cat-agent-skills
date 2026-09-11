# Connector authentication

Authentication is independent of package validity. A ZIP can pass manifest
validation and still enter a connector retry loop because its OAuth
configuration is missing or invalid.

## Decision table

| Server behavior | Manifest configuration | Required setup |
|---|---|---|
| Anonymous endpoint | `authorization.type: None` | No `referenceId` |
| OAuth server with RFC 7591 registration endpoint | Dynamic registration supported by the current schema | Server registration endpoint |
| OAuth server without dynamic registration | `OAuthPluginVault` | Provider app plus Enterprise Token Store auth config |
| Microsoft Entra protected endpoint | `OAuthPluginVault` | Static Entra app and OAuth client registration |

Microsoft Entra ID does not publish a Dynamic Client Registration endpoint.
Do not choose DCR for an Entra-protected MCP server.

## Discovery

Probe the MCP URL without credentials. On HTTP 401, inspect the
`WWW-Authenticate` header for `resource_metadata`, then retrieve:

```text
/.well-known/oauth-protected-resource
```

Record:

- Resource identifier
- Authorization server
- Supported scopes
- PKCE methods

Retrieve the authorization server's OpenID configuration and verify whether a
`registration_endpoint` exists.

## Static OAuth registration

1. Register the OAuth client with the identity provider.
2. Add the Teams callback:
   `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`
3. Grant the required delegated API permissions.
4. For Dataverse MCP, add the client ID to the Power Platform environment's
   allowed MCP clients list.
5. In Teams Developer Portal, create an OAuth client registration:
   - Base URL exactly matches the MCP URL.
   - Restrict usage by app: **Any Teams app**.
   - Set client ID and secret, endpoints, scopes, and PKCE.
6. Copy the generated **OAuth client registration ID** into:

```json
"authorization": {
  "type": "OAuthPluginVault",
  "referenceId": "<generated OAuth client registration ID>"
}
```

The Microsoft 365 app ID, Entra application client ID, and OAuth client
registration ID are three different identifiers. Do not substitute one for
another.

## Secret handling

- Client secrets belong in the identity provider and Enterprise Token Store.
- Never write secrets to `manifest.json`, `.env` files committed to source,
  `SKILL.md`, tool descriptions, logs, or troubleshooting output.
- Redact access tokens, refresh tokens, cookies, authorization codes, and
  client secrets from network traces.

## Deployment gate

Before sideloading an authenticated connector:

- OAuth client registration ID is present and not a placeholder.
- Provider app redirect URI matches exactly.
- Required delegated permission can be consented to.
- Required administrator consent is complete.
- The MCP server allows the registered client.
- Package version has been incremented.
