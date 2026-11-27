using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Text.Json;
using System.Text.Json.Nodes;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;

namespace CoworkSn;

/// <summary>
/// MCP Apps visibility is host-enforced presentation metadata, NOT an authentication boundary.
/// A compliant host omits app-only tools from its model while proxying the widget's tools/call.
/// All calls independently require delegated authentication and session ownership. Never trust
/// a client-supplied "app" header as authorization. The UI explicitly confirms edited summaries.
/// </summary>
[McpServerToolType]
public sealed class ChatTools(ChatService service, IHttpContextAccessor context, BridgeOptions options)
{
    public const string ResourceUri = "ui://cowork-sn/live-chat.html";
    public const string StartUi = """{"resourceUri":"ui://cowork-sn/live-chat.html","visibility":["model","app"]}""";
    public const string AppUi = """{"visibility":["app"]}""";
    private Owner Owner => options.Demo.Enabled ? Owner.Demo : Owner.FromPrincipal(context.HttpContext!.User, options.Auth);

    public static CallToolResult Result(ChatView view) => new()
    {
        Content = [new TextContentBlock
        {
            Text = $"Support chat {view.SessionId}: {view.Status}. " +
                (view.Status == "draft" ? "Review and explicitly confirm the summary in the chat app. No support request has been sent." :
                    "Open the chat app for messages and controls.")
        }],
        StructuredContent = JsonSerializer.SerializeToElement(view, ChatJson.Options)
    };

    public static async Task<CallToolResult> Invoke(Func<Task<ChatView>> action)
    {
        try { return Result(await action()); }
        catch (ChatException ex)
        {
            return new CallToolResult { IsError = true, Content = [new TextContentBlock { Text = $"{ex.Code}: {ex.Message}" }] };
        }
    }

    [McpServerTool(Name = "start_live_chat", ReadOnly = false, Destructive = false, Idempotent = true)]
    [McpMeta("ui", "", JsonValue = StartUi)]
    [Description("Prepare a draft support chat. This does NOT contact ServiceNow. The user must review and confirm in the app. Reuse requestId for retries.")]
    public Task<CallToolResult> Start(
        [Description("Draft summary for user review."), MaxLength(4000)] string summary,
        [Description("Caller-generated retry ID, 1–128 ASCII letters, digits, _, -, . or :."), MaxLength(128)] string requestId,
        [MaxLength(8000)] string? originalText = null, [MaxLength(32)] string? language = null) =>
        Invoke(() => Task.FromResult(service.Start(Owner, summary, requestId, originalText, language)));

    [McpServerTool(Name = "confirm_live_chat", ReadOnly = false, Destructive = false, Idempotent = true)]
    [McpMeta("ui", "", JsonValue = AppUi)]
    [Description("App only: send the user's explicitly approved, edited summary to support, once.")]
    public Task<CallToolResult> Confirm([MaxLength(32)] string sessionId, [MaxLength(4000)] string summary) =>
        Invoke(() => service.ConfirmAsync(Owner, sessionId, summary));

    [McpServerTool(Name = "get_live_chat_updates", ReadOnly = true, Idempotent = true)]
    [McpMeta("ui", "", JsonValue = AppUi)]
    [Description("App only: get at most five durable events after the cursor. Polling does not extend chat activity.")]
    public Task<CallToolResult> Updates([MaxLength(32)] string sessionId, [Range(0, int.MaxValue)] int afterSequence = 0) =>
        Invoke(() => Task.FromResult(service.Updates(Owner, sessionId, afterSequence)));

    [McpServerTool(Name = "send_live_chat_message", ReadOnly = false, Destructive = false, Idempotent = true)]
    [McpMeta("ui", "", JsonValue = AppUi)]
    [Description("App only: send a user-authored message. Always reuse clientMessageId for retries.")]
    public Task<CallToolResult> Send([MaxLength(32)] string sessionId, [MaxLength(8000)] string text,
        [MaxLength(128)] string clientMessageId) => Invoke(() => service.SendAsync(Owner, sessionId, text, clientMessageId));

    [McpServerTool(Name = "request_end_live_chat", ReadOnly = false, Destructive = false, Idempotent = true)]
    [McpMeta("ui", "", JsonValue = AppUi)]
    [Description("App only: cancel a draft/waiting request or politely ask a connected representative to close. Does not pretend network failures are closure.")]
    public Task<CallToolResult> End([MaxLength(32)] string sessionId, [MaxLength(128)] string clientMessageId) =>
        Invoke(() => service.RequestEndAsync(Owner, sessionId, clientMessageId));
}

public sealed class WidgetResource(BridgeOptions options, IHostEnvironment environment)
{
    public const string MimeType = "text/html;profile=mcp-app";
    private string PathToWidget
    {
        get
        {
            if (!string.IsNullOrWhiteSpace(options.WidgetPath))
                return Path.GetFullPath(options.WidgetPath, environment.ContentRootPath);
            var published = Path.Combine(AppContext.BaseDirectory, "widget", "index.html");
            if (File.Exists(published)) return published;
            return Path.GetFullPath(Path.Combine(environment.ContentRootPath, "..", "..", "widget", "dist", "index.html"));
        }
    }

    public string Html() => File.Exists(PathToWidget) ? File.ReadAllText(PathToWidget) :
        """<!doctype html><html><head><meta charset="utf-8"></head><body><h1>Support chat app unavailable</h1><p>The chat app has not been built. Existing chats may still be active. Ask the administrator to build and deploy the widget.</p></body></html>""";

    [McpServerResource(UriTemplate = ChatTools.ResourceUri, Name = "live_chat", MimeType = MimeType)]
    [Description("User-controlled live support chat app. Contains no access tokens or service credentials.")]
    public TextResourceContents Read() => new()
    {
        Uri = ChatTools.ResourceUri,
        MimeType = MimeType,
        Text = Html(),
        Meta = new JsonObject
        {
            ["ui"] = new JsonObject
            {
                ["prefersBorder"] = true,
                ["csp"] = new JsonObject { ["connectDomains"] = new JsonArray(), ["resourceDomains"] = new JsonArray() }
            }
        }
    };
}
