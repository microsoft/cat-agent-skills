using System.Net;
using System.Text.Json;
using CoworkSn;

namespace CoworkSn.Tests;

public sealed class RecordingHandler : HttpMessageHandler, IHttpClientFactory
{
    public List<(Uri Uri, string Body, string? Scheme, string? Parameter)> Requests { get; } = [];
    public Queue<(HttpStatusCode Status, string Body)> Responses { get; } = new();
    public HttpClient CreateClient(string name) => new(this, disposeHandler: false);
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        Requests.Add((request.RequestUri!, request.Content is null ? "" : await request.Content.ReadAsStringAsync(cancellationToken),
            request.Headers.Authorization?.Scheme, request.Headers.Authorization?.Parameter));
        var response = Responses.Dequeue();
        return new HttpResponseMessage(response.Status) { Content = new StringContent(response.Body) };
    }
}

public sealed class ServiceNowClientTests
{
    private static BridgeOptions Options() => new()
    {
        ServiceNow = new()
        {
            BaseUrl = "https://sn.example.invalid",
            OAuth = new() { TokenUrl = "https://oauth.example.invalid/token", ClientId = "own-client", ClientSecret = "fixture-only" }
        }
    };

    [Fact]
    public async Task UsesOwnClientCredentialsExactIsolatedPathsAndDurableIds()
    {
        using var handler = new RecordingHandler();
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"access_token":"test-token","expires_in":3600}"""));
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"result":{"conversation_sys_id":"remote-id","interaction_number":"INT001","unavailable":false}}"""));
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"result":{"sent":true,"closed":false}}"""));
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"result":{"closed":true}}"""));
        using var client = new ServiceNowClient(handler, Options());
        var session = new ChatSession { Id = Guid.NewGuid().ToString("N"), Email = "person@example.invalid", Language = "de" };
        var opened = await client.OpenAsync(session, "Approved summary", CancellationToken.None);
        session.ConversationId = opened.ConversationId;
        await client.SendAsync(session, "Hello", "client-message-1", CancellationToken.None);
        await client.CloseAsync(session, "close-" + session.Id, CancellationToken.None);
        Assert.Equal(4, handler.Requests.Count);
        Assert.Equal("oauth.example.invalid", handler.Requests[0].Uri.Host);
        Assert.Contains("grant_type=client_credentials", handler.Requests[0].Body);
        Assert.Contains("client_id=own-client", handler.Requests[0].Body);
        Assert.Null(handler.Requests[0].Scheme);
        foreach (var item in handler.Requests.Skip(1))
        {
            Assert.Equal("Bearer", item.Scheme);
            Assert.Equal("test-token", item.Parameter);
            Assert.StartsWith("/api/cowork_review/cowork_bridge/", item.Uri.AbsolutePath);
        }
        using var open = JsonDocument.Parse(handler.Requests[1].Body);
        Assert.Equal("cowork_mcp", open.RootElement.GetProperty("bot").GetString());
        Assert.Equal(session.Id, open.RootElement.GetProperty("client_session_id").GetString());
        Assert.Equal("person@example.invalid", open.RootElement.GetProperty("email").GetString());
        Assert.False(open.RootElement.TryGetProperty("upn", out _));
        using var send = JsonDocument.Parse(handler.Requests[2].Body);
        Assert.Equal("client-message-1", send.RootElement.GetProperty("client_message_id").GetString());
        using var close = JsonDocument.Parse(handler.Requests[3].Body);
        Assert.Equal("close-" + session.Id, close.RootElement.GetProperty("client_message_id").GetString());
    }

    [Fact]
    public async Task HttpFailureIsNotReportedAsSuccessfulClosure()
    {
        using var handler = new RecordingHandler();
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"access_token":"test-token","expires_in":3600}"""));
        handler.Responses.Enqueue((HttpStatusCode.ServiceUnavailable, """{"error":"failure"}"""));
        using var client = new ServiceNowClient(handler, Options());
        await Assert.ThrowsAsync<HttpRequestException>(() => client.CloseAsync(new ChatSession { ConversationId = "remote" }, "close", CancellationToken.None));
        Assert.Equal(2, handler.Requests.Count);
    }

    [Fact]
    public async Task ApplicationFailureIsNotSuccessfulMessage()
    {
        using var handler = new RecordingHandler();
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"access_token":"test-token","expires_in":3600}"""));
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"result":{"sent":false,"closed":false}}"""));
        using var client = new ServiceNowClient(handler, Options());
        await Assert.ThrowsAsync<HttpRequestException>(() => client.SendAsync(new ChatSession { ConversationId = "remote" }, "text", "key", CancellationToken.None));
    }

    [Theory]
    [InlineData("""{"result":{}}""")]
    [InlineData("""{"result":{"ok":true}}""")]
    [InlineData("""{"result":{"ok":true,"closed":false}}""")]
    public async Task BareHttp200IsNotProofOfClosure(string response)
    {
        using var handler = new RecordingHandler();
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"access_token":"test-token","expires_in":3600}"""));
        handler.Responses.Enqueue((HttpStatusCode.OK, response));
        using var client = new ServiceNowClient(handler, Options());
        await Assert.ThrowsAsync<HttpRequestException>(() => client.CloseAsync(new ChatSession { ConversationId = "remote" }, "key", CancellationToken.None));
    }

    [Fact]
    public async Task ServiceNow409IsDistinguishedFromRetryableCloseTransportErrors()
    {
        using var handler = new RecordingHandler();
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"access_token":"test-token","expires_in":3600}"""));
        handler.Responses.Enqueue((HttpStatusCode.Conflict, """{"error":{"code":"command_ambiguous"}}"""));
        using var client = new ServiceNowClient(handler, Options());
        await Assert.ThrowsAsync<RemoteCommandAmbiguousException>(() =>
            client.CloseAsync(new ChatSession { ConversationId = "remote" }, "close-01234567890123456789012345678901", CancellationToken.None));
    }

    [Fact]
    public async Task ExplicitClosedSendResponseIsNotAnAmbiguousNetworkFailure()
    {
        using var handler = new RecordingHandler();
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"access_token":"test-token","expires_in":3600}"""));
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"result":{"sent":false,"closed":true}}"""));
        using var client = new ServiceNowClient(handler, Options());
        await Assert.ThrowsAsync<RemoteChatClosedException>(() =>
            client.SendAsync(new ChatSession { ConversationId = "remote" }, "text", "msg-01234567890123456789", CancellationToken.None));
    }

    [Theory]
    [InlineData("""{"result":{}}""")]
    [InlineData("""{"result":{"sent":true}}""")]
    [InlineData("""{"result":{"closed":true}}""")]
    [InlineData("""{"result":{"sent":true,"closed":true}}""")]
    [InlineData("""{"result":{"sent":false,"closed":false}}""")]
    [InlineData("""{"result":{"sent":"true","closed":false}}""")]
    [InlineData("""{"result":{"sent":true,"closed":"false"}}""")]
    public async Task IncompleteOrContradictorySendBooleansAreNotProofOfDeliveryOrClosure(string response)
    {
        using var handler = new RecordingHandler();
        handler.Responses.Enqueue((HttpStatusCode.OK, """{"access_token":"test-token","expires_in":3600}"""));
        handler.Responses.Enqueue((HttpStatusCode.OK, response));
        using var client = new ServiceNowClient(handler, Options());
        await Assert.ThrowsAsync<HttpRequestException>(() =>
            client.SendAsync(new ChatSession { ConversationId = "remote" }, "text", "msg-01234567890123456789", CancellationToken.None));
    }

    [Fact]
    public async Task DisabledTranslationMakesNoNetworkCalls()
    {
        var translation = new TranslationService(new NoNetworkFactory(), new BridgeOptions());
        var result = await translation.TranslateAsync("Original words", "de", "en", CancellationToken.None);
        Assert.Equal("Original words", result.Text);
        Assert.False(result.Translated);
    }

    [Fact]
    public async Task TranslationPreservesSourceLabelAndFallsBackHonestly()
    {
        using var handler = new RecordingHandler();
        var options = Options();
        options.Translator.Enabled = true;
        options.Translator.Key = "test-key";
        handler.Responses.Enqueue((HttpStatusCode.OK, """[{"detectedLanguage":{"language":"de","score":0.99},"translations":[{"text":"Hello","to":"en"}]}]"""));
        var service = new TranslationService(handler, options);
        var result = await service.TranslateAsync("Hallo", "en", null, CancellationToken.None);
        Assert.True(result.Translated);
        Assert.Equal("de", result.SourceLanguage);
        Assert.Contains("original: Hallo", TranslationService.ForAgent("Hallo", result));
        handler.Responses.Enqueue((HttpStatusCode.ServiceUnavailable, "{}"));
        result = await service.TranslateAsync("Hallo", "en", "de", CancellationToken.None);
        Assert.False(result.Translated);
        Assert.Equal("Hallo", result.Text);
    }
}
