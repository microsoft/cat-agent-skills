namespace CoworkSn;

/// <summary>
/// DEPLOYMENT / INTEGRATION CONTRACT
///
/// Build widget\dist\index.html first, then:
/// dotnet build src\CoworkSn\CoworkSn.csproj
/// dotnet test tests\CoworkSn.Tests\CoworkSn.Tests.csproj
/// dotnet publish src\CoworkSn\CoworkSn.csproj -c Release
/// The project copies built HTML into widget\index.html in the publish directory.
/// WidgetPath overrides this path (absolute, or relative to the application's content root).
///
/// Local browser demo (PowerShell, from repository root):
/// $env:ASPNETCORE_ENVIRONMENT='Development'; $env:Demo__Enabled='true'
/// dotnet run --project src\CoworkSn\CoworkSn.csproj --no-launch-profile
/// Visit http://localhost:5078/?demo=1 (Demo:Port overrides 5078).
/// GET /dev/mode returns {enabled:true,mode:"demo"} for the widget's explicit demo handshake.
/// POST /dev/tools/{name} accepts the normal tool arguments as a JSON object and
/// returns a standard MCP CallToolResult envelope with root ChatView in structuredContent.
/// Invalid tool arguments return isError=true with safe text content. These routes and the browser page
/// are completely absent in live mode. No CORS is enabled. Use the same origin.
/// The MCP endpoint is /mcp in both modes. Demo traffic is synthetic and local only.
///
/// LIVE configuration (colon notation; replace ":" with "__" in environment variables):
/// PublicBaseUrl: required external HTTPS origin, no path, e.g. https://support.example.org
/// Auth:TenantId: required Entra tenant GUID; only this issuer's v2 access tokens are accepted.
/// Auth:UserAudience: required exact aud claim from the user API access token (often an app GUID).
/// Auth:WebhookAudience: required DISTINCT aud claim for ServiceNow's separate application token.
/// Auth:DelegatedScope: required fully-qualified consent scope, e.g. api://APP-ID/LiveChat.Access.
/// Auth:EmailClaim: explicitly choose preferred_username or email from the validated token.
/// Auth:AllowedEmailDomains: required array of accepted ServiceNow identity-mapping domains.
/// Auth:AllowedWebhookCallers: required array of Entra application/client GUIDs.
/// User tokens require tid, oid, delegated scp LiveChat.Access, and the configured email claim.
/// Configure Entra accessTokenAcceptedVersion=2, expose LiveChat.Access, grant host consent,
/// configure the host's OAuth client/redirect URI, and assign LiveChat.Webhook to ServiceNow's app.
/// The host must support Entra OAuth/pre-registration; Entra is not a generic dynamic-registration server.
/// OAuth metadata is served by the official SDK at /.well-known/oauth-protected-resource,
/// using the configured PUBLIC origin rather than untrusted request headers.
///
/// ServiceNow:BaseUrl: required HTTPS INSTANCE ORIGIN, not the API path.
/// ServiceNow:OAuth:TokenUrl, ServiceNow:OAuth:ClientId, ServiceNow:OAuth:ClientSecret:
/// required independent client-credentials registration, never the old Agents SDK credentials.
/// Set the secret using the process environment or dotnet user-secrets for this project.
/// Template requests use /api/cowork_review/cowork_bridge/{open_chat|send_message|close_chat}.
/// Independently review and align the namespace with the target installation before live use.
/// send_message responds result.sent=true,closed=false; sent=false,closed=true proves it was
/// already closed and the message was not sent. close_chat must respond result.closed=true.
/// No result.ok field is required. A bare HTTP 200 is not proof of delivery/closure.
/// ServiceNow wire client_message_id is restricted to 16–80 alphanumeric/hyphen characters.
/// User/tool IDs remain 1–128 ASCII letters/digits/._:-, but send wire IDs are deterministically
/// mapped to "msg-"+uppercase SHA256(sessionId+":"+clientMessageId), including polite end requests.
/// This also prevents collisions when the same caller ID is used in different sessions.
/// The only bot value is cowork_mcp. No Basic or shared-secret webhook fallback exists.
/// The authenticated webhook is POST /api/livechat/sn with separate audience, app allow-list,
/// role LiveChat.Webhook and no delegated scp. An event is committed before 200 acknowledgement.
///
/// HTTPS reverse proxy: configure ASPNETCORE_URLS for the private listener and TrustedProxyIps
/// (an array of explicit proxy IP addresses). Preserve the public Host header and set
/// X-Forwarded-Proto=https. Forwarded Host is never trusted. Without trusted proxies, terminate
/// TLS in Kestrel. Restrict access to the private listener at the network layer.
///
/// Storage:DatabasePath: local persistent volume, default data\cowork-sn.db.
/// Exactly ONE deployed instance, no network filesystem, no horizontal replica sharing.
/// Files contain personal/chat data: apply OS ACLs, encryption at rest and consistent backups.
/// Storage:RetentionDays defaults to 7 and must exceed Timeouts:MaxChatDurationMinutes.
/// Timeouts:AcceptanceMinutes=5, InactivityMinutes=15, MaxChatDurationMinutes=120,
/// ScanSeconds=30, CloseRetrySeconds=30. Polls/accepted retries do not refresh activity.
/// Active and ambiguous sessions are NEVER retention-deleted. Terminal events remain readable.
///
/// Translator:Enabled=false by default; optional outbound Azure Translator v3 integration.
/// If enabled, configure Translator:Key, optionally Region, Endpoint and AgentLanguage (default en).
/// Outbound translations are explicitly labelled and original text retained. Agent source text
/// is always stored as received, labelled with AgentLanguage. No translation in demo mode.
/// If translation plus original would exceed the bridge message bound, send the original only.
///
/// CRASH / AMBIGUITY:
/// Session ID and operation keys are committed before network I/O. Pending/ambiguous open/send
/// operations are NOT automatically repeated, even after restart. Never instruct the user to
/// retry with a new ID: it could duplicate a request or message. The bridge contract has no
/// read/reconciliation endpoint. Administrators must reconcile client_session_id and
/// client_message_id against ServiceNow; an unresolved opening remains retained in starting
/// or closing, not falsely closed. A closed callback can resolve it without the open response.
/// Only transient close_chat failures are retried, with a stable close-SESSION_ID key, so its
/// implementation MUST be idempotent. HTTP409 means prior command ambiguity: close retries
/// pause, the session stays retained in closing, and operators must reconcile that existing key.
/// Repeated app-only end requests on a connected session send one polite
/// message, never close_chat, except for the explicitly configured timeout safety net.
///
/// MCP Apps: ui://cowork-sn/live-chat.html, text/html;profile=mcp-app. Official SDK discovery
/// publishes _meta.ui.visibility=["app"] for controls and ["model","app"] for draft creation.
/// Visibility is enforced by the MCP Apps HOST, not an independent user security identity.
/// Hosts must omit app-only tools from model discovery and require the explicit confirmation UI.
/// No bearer tokens/credentials are passed to the widget. All reads/writes recheck JWT ownership.
/// Deltas contain at most 5 events and at most 60KiB JSON. User tool text has an 8000-character
/// AND 8000 JSON-byte bound; ServiceNow callbacks allow the full 8000 Unicode characters
/// (up to 48000 escaped JSON bytes). Read until hasMore=false using nextCursor.
/// Unseen replies arriving after closure are retained as late_message without reopening the
/// session. Closed remote sessions continue low-rate widget refresh while visible.
/// Error tool results use the normal MCP isError/text representation, never fabricated success.
/// Successful tools always have root sessionId,status,summary,interactionNumber,events,
/// nextCursor,hasMore in structuredContent plus a short plain-text fallback.
/// Uncertain send/end delivery returns MCP isError with delivery_unconfirmed and a durable
/// transcript error; retries preserve the operation ID and never falsely acknowledge delivery.
/// </summary>
internal static class Deployment;
