using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace CoworkSn;

public sealed class ChatException(string code, string message, int httpStatus = 400) : Exception(message)
{
    public string Code { get; } = code;
    public int HttpStatus { get; } = httpStatus;
}

public static partial class Input
{
    public static string Text(string? value, string name, int max = 8000, int maxJsonBytes = 8000)
    {
        if (string.IsNullOrWhiteSpace(value) || value.Length > max ||
            Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(value)) > maxJsonBytes + 2)
            throw new ChatException("invalid_argument", $"{name} is required and must fit {max} characters and {maxJsonBytes} JSON-encoded bytes.");
        return value;
    }
    public static string Key(string? value, string name)
    {
        if (value is null || !KeyPattern().IsMatch(value))
            throw new ChatException("invalid_argument", $"{name} must be 1–128 ASCII letters, digits, hyphens, underscores, colons or periods.");
        return value;
    }
    public static string SessionId(string? value)
    {
        if (!Guid.TryParseExact(value, "N", out _))
            throw new ChatException("invalid_argument", "sessionId must be a server-issued ID.");
        return value!;
    }
    public static string? Language(string? value)
    {
        if (value is not null && (value.Length > 32 || !LanguagePattern().IsMatch(value)))
            throw new ChatException("invalid_argument", "language must be a language tag up to 32 characters.");
        return value;
    }
    [GeneratedRegex("^[A-Za-z0-9_.:-]{1,128}$", RegexOptions.CultureInvariant)] private static partial Regex KeyPattern();
    [GeneratedRegex("^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8}){0,3}$", RegexOptions.CultureInvariant)] private static partial Regex LanguagePattern();
}

public sealed record ChatEvent(string Id, long Sequence, string Kind, string Author, string Text,
    DateTimeOffset Timestamp, string? OriginalText = null, string? Language = null);
public sealed record ChatView(string SessionId, string Status, string Summary,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.Never)] string? InteractionNumber,
    IReadOnlyList<ChatEvent> Events, long NextCursor, bool HasMore);

public sealed class ChatSession
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string TenantId { get; set; } = "";
    public string UserId { get; set; } = "";
    public string Email { get; set; } = "";
    public string RequestId { get; set; } = "";
    public string InitialSummary { get; set; } = "";
    public string Summary { get; set; } = "";
    public string? OriginalText { get; set; }
    public string? Language { get; set; }
    public string Status { get; set; } = "draft";
    public string? ConversationId { get; set; }
    public string? InteractionNumber { get; set; }
    public bool JoinAnnounced { get; set; }
    public DateTimeOffset CreatedAt { get; set; }
    public DateTimeOffset? OpenedAt { get; set; }
    public DateTimeOffset? AcceptedAt { get; set; }
    public DateTimeOffset LastActivityAt { get; set; }
    public DateTimeOffset? TerminalAt { get; set; }
    public string? CloseReason { get; set; }
    public DateTimeOffset? CloseRetryAt { get; set; }
    public long Sequence { get; set; }
    [JsonIgnore] public bool Terminal => Status is "closed" or "failed" or "unavailable";
}

public sealed record WebhookEvent(
    [property: JsonPropertyName("event")] string Event,
    [property: JsonPropertyName("bot")] string Bot,
    [property: JsonPropertyName("client_session_id")] string ClientSessionId,
    [property: JsonPropertyName("interaction_number")] string InteractionNumber,
    [property: JsonPropertyName("text")] string? Text,
    [property: JsonPropertyName("agent_name")] string? AgentName,
    [property: JsonPropertyName("message_sys_id")] string? MessageSysId,
    [property: JsonPropertyName("event_id")] string EventId);

public static class ChatJson
{
    public static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web)
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };
}
