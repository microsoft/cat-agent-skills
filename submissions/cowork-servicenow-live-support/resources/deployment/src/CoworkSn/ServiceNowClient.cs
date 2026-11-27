using System.Net.Http.Headers;
using System.Text.Json;

namespace CoworkSn;

public sealed record OpenChatResult(string ConversationId, string InteractionNumber, bool Unavailable, string? Message = null);
public sealed class RemoteCommandAmbiguousException() : HttpRequestException("ServiceNow requires reconciliation of an ambiguous prior command.");
public sealed class RemoteChatClosedException() : HttpRequestException("ServiceNow reports this conversation is already closed.");
public interface IServiceNowClient
{
    Task<OpenChatResult> OpenAsync(ChatSession session, string summary, CancellationToken cancellationToken);
    Task SendAsync(ChatSession session, string text, string clientMessageId, CancellationToken cancellationToken);
    Task CloseAsync(ChatSession session, string clientMessageId, CancellationToken cancellationToken);
}

/// <summary>
/// Independent OAuth registration and isolated /api/cowork_review/cowork_bridge template API.
/// The bridge must deduplicate client_session_id, client_message_id and close_chat keys durably.
/// HTTP mutation errors are ambiguous, not proof of non-delivery. No automatic open/send retry.
/// Never log response bodies, tokens, credentials, email addresses or chat text.
/// </summary>
public sealed class ServiceNowClient(IHttpClientFactory factory, BridgeOptions options) : IServiceNowClient, IDisposable
{
    private readonly SemaphoreSlim _tokenLock = new(1, 1);
    private string? _token;
    private DateTimeOffset _expires;

    private async Task<string> TokenAsync(CancellationToken ct)
    {
        await _tokenLock.WaitAsync(ct);
        try
        {
            if (_token is not null && DateTimeOffset.UtcNow < _expires) return _token;
            using var request = new HttpRequestMessage(HttpMethod.Post, options.ServiceNow.OAuth.TokenUrl)
            {
                Content = new FormUrlEncodedContent(new Dictionary<string, string>
                {
                    ["grant_type"] = "client_credentials",
                    ["client_id"] = options.ServiceNow.OAuth.ClientId!,
                    ["client_secret"] = options.ServiceNow.OAuth.ClientSecret!
                })
            };
            using var response = await factory.CreateClient("ServiceNow").SendAsync(request, ct);
            response.EnsureSuccessStatusCode();
            using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync(ct));
            _token = document.RootElement.GetProperty("access_token").GetString()
                ?? throw new InvalidOperationException("ServiceNow OAuth response is missing an access token.");
            var ttl = document.RootElement.TryGetProperty("expires_in", out var expires) ? expires.GetInt32() : 300;
            if (ttl <= 0) throw new InvalidOperationException("ServiceNow OAuth token has expired.");
            _expires = DateTimeOffset.UtcNow.AddSeconds(Math.Max(1, ttl - Math.Min(60, ttl / 2)));
            return _token;
        }
        finally { _tokenLock.Release(); }
    }

    private async Task<JsonDocument> PostAsync(string operation, object body, CancellationToken ct)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post,
            $"{options.ServiceNow.BaseUrl!.TrimEnd('/')}/api/cowork_review/cowork_bridge/{operation}")
        {
            Content = JsonContent.Create(body)
        };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", await TokenAsync(ct));
        using var response = await factory.CreateClient("ServiceNow").SendAsync(request, ct);
        if (response.StatusCode == System.Net.HttpStatusCode.Conflict)
            throw new RemoteCommandAmbiguousException();
        response.EnsureSuccessStatusCode();
        var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync(ct));
        if (document.RootElement.TryGetProperty("error", out _))
        {
            document.Dispose();
            throw new HttpRequestException("ServiceNow rejected the operation.");
        }
        return document;
    }

    public async Task<OpenChatResult> OpenAsync(ChatSession session, string summary, CancellationToken cancellationToken)
    {
        using var document = await PostAsync("open_chat", new
        {
            email = session.Email, summary, lang = session.Language ?? "",
            client_session_id = session.Id, bot = "cowork_mcp"
        }, cancellationToken);
        var result = document.RootElement.GetProperty("result");
        if (result.TryGetProperty("unavailable", out var unavailable) && unavailable.ValueKind == JsonValueKind.True)
            return new("", "", true);
        var conversation = result.GetProperty("conversation_sys_id").GetString();
        var interaction = result.GetProperty("interaction_number").GetString();
        if (string.IsNullOrWhiteSpace(conversation) || string.IsNullOrWhiteSpace(interaction) ||
            conversation.Length > 128 || interaction.Length > 128)
            throw new HttpRequestException("ServiceNow returned an invalid open_chat result.");
        return new(conversation, interaction, false);
    }

    public async Task SendAsync(ChatSession session, string text, string clientMessageId, CancellationToken cancellationToken)
    {
        using var document = await PostAsync("send_message", new
        {
            conversation_sys_id = session.ConversationId, text, email = session.Email, client_message_id = clientMessageId
        }, cancellationToken);
        var result = document.RootElement.GetProperty("result");
        var hasSent = result.TryGetProperty("sent", out var sent);
        var hasClosed = result.TryGetProperty("closed", out var closed);
        if (hasSent && hasClosed && sent.ValueKind == JsonValueKind.False && closed.ValueKind == JsonValueKind.True)
            throw new RemoteChatClosedException();
        if (!hasSent || !hasClosed || sent.ValueKind != JsonValueKind.True || closed.ValueKind != JsonValueKind.False)
            throw new HttpRequestException("ServiceNow did not accept the message.");
    }

    public async Task CloseAsync(ChatSession session, string clientMessageId, CancellationToken cancellationToken)
    {
        using var document = await PostAsync("close_chat", new
        {
            conversation_sys_id = session.ConversationId, client_message_id = clientMessageId
        }, cancellationToken);
        var result = document.RootElement.GetProperty("result");
        if (!result.TryGetProperty("closed", out var closed) || closed.ValueKind != JsonValueKind.True)
            throw new HttpRequestException("ServiceNow did not acknowledge closure.");
    }
    public void Dispose() => _tokenLock.Dispose();
}

public sealed class DemoServiceNowClient : IServiceNowClient
{
    public Task<OpenChatResult> OpenAsync(ChatSession session, string summary, CancellationToken cancellationToken) =>
        Task.FromResult(new OpenChatResult("demo-" + session.Id, "DEMO-" + session.Id[..8].ToUpperInvariant(), false));
    public Task SendAsync(ChatSession session, string text, string clientMessageId, CancellationToken cancellationToken) => Task.CompletedTask;
    public Task CloseAsync(ChatSession session, string clientMessageId, CancellationToken cancellationToken) => Task.CompletedTask;
}

public sealed class DisconnectedServiceNowClient : IServiceNowClient
{
    public Task<OpenChatResult> OpenAsync(ChatSession session, string summary, CancellationToken cancellationToken) =>
        Task.FromResult(new OpenChatResult("", "", true, "ServiceNow is not connected in this pilot. No support request was sent."));
    public Task SendAsync(ChatSession session, string text, string clientMessageId, CancellationToken cancellationToken) =>
        throw new ChatException("integration_disconnected", "ServiceNow is disconnected. No message was sent.", 503);
    public Task CloseAsync(ChatSession session, string clientMessageId, CancellationToken cancellationToken) =>
        throw new ChatException("integration_disconnected", "ServiceNow is disconnected. Remote closure cannot be confirmed.", 503);
}

public sealed record Translation(string Text, string? SourceLanguage, bool Translated);

/// <summary>Optional Azure Translator v3, OFF by default. A failed translation preserves original text without claiming it was translated.</summary>
public sealed class TranslationService(IHttpClientFactory factory, BridgeOptions options)
{
    public async Task<Translation> TranslateAsync(string text, string to, string? from, CancellationToken ct)
    {
        if (!options.Translator.Enabled || options.Demo.Enabled || string.Equals(to, from, StringComparison.OrdinalIgnoreCase))
            return new(text, from, false);
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post,
                $"{options.Translator.Endpoint.TrimEnd('/')}/translate?api-version=3.0&to={Uri.EscapeDataString(to)}" +
                (from is null ? "" : $"&from={Uri.EscapeDataString(from)}"))
            {
                Content = JsonContent.Create(new[] { new { Text = text } })
            };
            request.Headers.Add("Ocp-Apim-Subscription-Key", options.Translator.Key);
            if (!string.IsNullOrWhiteSpace(options.Translator.Region))
                request.Headers.Add("Ocp-Apim-Subscription-Region", options.Translator.Region);
            using var response = await factory.CreateClient("Translator").SendAsync(request, ct);
            response.EnsureSuccessStatusCode();
            using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync(ct));
            var first = document.RootElement[0];
            var source = from;
            if (first.TryGetProperty("detectedLanguage", out var detected) &&
                detected.TryGetProperty("score", out var score) && score.GetDouble() >= 0.8)
                source = detected.GetProperty("language").GetString();
            var translated = Input.Text(first.GetProperty("translations")[0].GetProperty("text").GetString(), "translation");
            return new(translated, source, source is not null && !string.Equals(source, to, StringComparison.OrdinalIgnoreCase));
        }
        catch (Exception ex) when (ex is HttpRequestException or JsonException or KeyNotFoundException or InvalidOperationException or ChatException or OperationCanceledException)
        {
            return new(text, from, false);
        }
    }
    public static string ForAgent(string original, Translation translation, int maxLength = 8000)
    {
        if (!translation.Translated) return original;
        var combined = $"{translation.Text}\n[Translation from {translation.SourceLanguage}; original: {original}]";
        try { return Input.Text(combined, "translated message", maxLength); }
        catch (ChatException) { return original; }
    }
}
