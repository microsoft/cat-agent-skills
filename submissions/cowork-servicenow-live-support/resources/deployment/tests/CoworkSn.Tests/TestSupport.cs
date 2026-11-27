using System.Net;
using CoworkSn;
using Microsoft.Extensions.FileProviders;
using Microsoft.Extensions.Hosting;

namespace CoworkSn.Tests;

public sealed class TestEnvironment : IHostEnvironment
{
    public string EnvironmentName { get; set; } = "Development";
    public string ApplicationName { get; set; } = "CoworkSn";
    public string ContentRootPath { get; set; } = Directory.GetCurrentDirectory();
    public IFileProvider ContentRootFileProvider { get; set; } = new NullFileProvider();
}

public sealed class TestClock : TimeProvider
{
    private DateTimeOffset _now = new(2026, 10, 16, 12, 0, 0, TimeSpan.Zero);
    public override DateTimeOffset GetUtcNow() => _now;
    public void Advance(TimeSpan amount) => _now += amount;
}

public sealed class FakeRemote : IServiceNowClient
{
    public int Opens;
    public int Sends;
    public int Closes;
    public bool FailOpen;
    public bool FailSend;
    public bool FailClose;
    public bool AmbiguousClose;
    public bool AlreadyClosed;
    public bool Unavailable;
    public Func<ChatSession, Task>? BeforeOpenReturns;
    public List<string> CloseKeys { get; } = [];
    public List<string> SendKeys { get; } = [];
    public Task<OpenChatResult> OpenAsync(ChatSession session, string summary, CancellationToken cancellationToken) => Open(session);
    private async Task<OpenChatResult> Open(ChatSession session)
    {
        Interlocked.Increment(ref Opens);
        if (BeforeOpenReturns is not null) await BeforeOpenReturns(session);
        if (FailOpen) throw new HttpRequestException("Test ambiguous opening failure");
        return new("remote-" + session.Id, "INT001", Unavailable);
    }
    public Task SendAsync(ChatSession session, string text, string clientMessageId, CancellationToken cancellationToken)
    {
        Interlocked.Increment(ref Sends);
        SendKeys.Add(clientMessageId);
        if (AlreadyClosed) throw new RemoteChatClosedException();
        if (FailSend) throw new HttpRequestException("Test ambiguous send failure");
        return Task.CompletedTask;
    }
    public Task CloseAsync(ChatSession session, string clientMessageId, CancellationToken cancellationToken)
    {
        Interlocked.Increment(ref Closes);
        CloseKeys.Add(clientMessageId);
        if (AmbiguousClose) throw new RemoteCommandAmbiguousException();
        if (FailClose) throw new HttpRequestException("Test ambiguous close failure");
        return Task.CompletedTask;
    }
}

public sealed class NoNetworkFactory : IHttpClientFactory
{
    public HttpClient CreateClient(string name) => new(new DenyNetwork());
    private sealed class DenyNetwork : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) =>
            throw new InvalidOperationException("Unexpected network traffic during a test.");
    }
}

public sealed class Fixture : IDisposable
{
    private readonly string _directory = Path.GetFullPath(Path.Combine("data", "test-" + Guid.NewGuid().ToString("N")));
    public BridgeOptions Options { get; } = new();
    public TestClock Clock { get; } = new();
    public FakeRemote Remote { get; } = new();
    public SessionStore Store { get; }
    public ChatService Service { get; }
    public Owner Alice { get; } = new("tenant", "alice", "alice@example.invalid");
    public Owner Bob { get; } = new("tenant", "bob", "bob@example.invalid");
    public Fixture()
    {
        Options.Storage.DatabasePath = Path.Combine(_directory, "sessions.db");
        Store = new SessionStore(Options, new TestEnvironment());
        Service = new ChatService(Store, Remote, new TranslationService(new NoNetworkFactory(), Options), Options, Clock);
    }
    public ChatView Draft(string requestId = "request-1") => Service.Start(Alice, "A test issue", requestId);
    public async Task<ChatView> Waiting()
    {
        var draft = Draft();
        return await Service.ConfirmAsync(Alice, draft.SessionId, draft.Summary);
    }
    public async Task<ChatView> Connected()
    {
        var waiting = await Waiting();
        Service.Receive(Event(waiting.SessionId, "accepted", "accepted-1"));
        return Service.Updates(Alice, waiting.SessionId);
    }
    public static WebhookEvent Event(string id, string kind, string eventId, string? text = null, string? messageId = null) =>
        new(kind, "cowork_mcp", id, "INT001", text, "Agent", messageId, eventId);
    public void Dispose() { if (Directory.Exists(_directory)) Directory.Delete(_directory, true); }
}
