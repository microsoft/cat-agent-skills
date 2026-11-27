using System.IdentityModel.Tokens.Jwt;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text.Json;
using CoworkSn;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.IdentityModel.Protocols.OpenIdConnect;
using Microsoft.IdentityModel.Protocols;
using Microsoft.IdentityModel.Tokens;

namespace CoworkSn.Tests;

public sealed class LoopbackFilter : IStartupFilter
{
    public Action<IApplicationBuilder> Configure(Action<IApplicationBuilder> next) => app =>
    {
        app.Use((context, continuation) =>
        {
            context.Connection.RemoteIpAddress = IPAddress.Loopback;
            return continuation(context);
        });
        next(app);
    };
}

public sealed class AppFactory : WebApplicationFactory<Program>
{
    private readonly bool _demo;
    private readonly string _directory = Path.GetFullPath(Path.Combine("data", "http-test-" + Guid.NewGuid().ToString("N")));
    private readonly RSA _rsa = RSA.Create(2048);
    public const string Tenant = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
    public const string WebhookCaller = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb";
    public const string UserAudience = "api://cowork-tests-user";
    public const string WebhookAudience = "api://cowork-tests-webhook";
    public AppFactory(bool demo = true) => _demo = demo;

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment(_demo ? "Development" : "Production");
        var values = new Dictionary<string, string?>
        {
            ["Demo:Enabled"] = _demo.ToString(),
            ["Demo:Port"] = "5078",
            ["Storage:DatabasePath"] = Path.Combine(_directory, "session.db"),
            ["WidgetPath"] = Path.Combine(_directory, "widget.html"),
            ["PublicBaseUrl"] = "https://cowork.example.invalid",
            ["Auth:TenantId"] = Tenant,
            ["Auth:UserAudience"] = UserAudience,
            ["Auth:WebhookAudience"] = WebhookAudience,
            ["Auth:DelegatedScope"] = UserAudience + "/" + AuthOptions.UserScope,
            ["Auth:EmailClaim"] = "preferred_username",
            ["Auth:AllowedEmailDomains:0"] = "example.invalid",
            ["Auth:AllowedWebhookCallers:0"] = WebhookCaller,
            ["ServiceNow:BaseUrl"] = "https://sn.example.invalid",
            ["ServiceNow:OAuth:TokenUrl"] = "https://sn.example.invalid/oauth_token.do",
            ["ServiceNow:OAuth:ClientId"] = "test-only",
            ["ServiceNow:OAuth:ClientSecret"] = "nonsecret-test-fixture"
        };
        Directory.CreateDirectory(_directory);
        File.WriteAllText(Path.Combine(_directory, "widget.html"), "<!doctype html><html><body>Test widget</body></html>");
        foreach (var pair in values) builder.UseSetting(pair.Key, pair.Value);
        builder.ConfigureAppConfiguration((_, c) => c.AddInMemoryCollection(values));
        builder.ConfigureTestServices(services =>
        {
            services.AddSingleton<IStartupFilter, LoopbackFilter>();
            services.RemoveAll<IServiceNowClient>();
            services.AddSingleton<IServiceNowClient, FakeRemote>();
            foreach (var scheme in new[] { JwtBearerDefaults.AuthenticationScheme, "Webhook" })
                services.PostConfigure<JwtBearerOptions>(scheme, o =>
                {
                    o.Configuration = new OpenIdConnectConfiguration
                    {
                        Issuer = $"https://login.microsoftonline.com/{Tenant}/v2.0",
                        SigningKeys = { new RsaSecurityKey(_rsa) { KeyId = "test-key" } }
                    };
                    o.ConfigurationManager = new StaticConfigurationManager<OpenIdConnectConfiguration>(o.Configuration);
                });
        });
    }

    public HttpClient Client() => CreateClient(new WebApplicationFactoryClientOptions
    {
        BaseAddress = new Uri(_demo ? "http://localhost:5078" : "https://cowork.example.invalid"),
        AllowAutoRedirect = false
    });

    public string Token(bool webhook = false, bool wrongAudience = false, bool role = true,
        string user = "cccccccc-cccc-cccc-cccc-cccccccccccc", string? scope = AuthOptions.UserScope,
        string caller = WebhookCaller)
    {
        var claims = new List<Claim> { new("tid", Tenant), new("oid", user), new("preferred_username", "person@example.invalid") };
        if (webhook)
        {
            claims.Add(new("azp", caller));
            if (role) claims.Add(new("roles", AuthOptions.WebhookRole));
        }
        else if (scope is not null) claims.Add(new("scp", scope));
        var jwt = new JwtSecurityToken(
            $"https://login.microsoftonline.com/{Tenant}/v2.0",
            wrongAudience ? "wrong-audience" : webhook ? WebhookAudience : UserAudience,
            claims, DateTime.UtcNow.AddMinutes(-1), DateTime.UtcNow.AddMinutes(10),
            new SigningCredentials(new RsaSecurityKey(_rsa) { KeyId = "test-key" }, SecurityAlgorithms.RsaSha256));
        return new JwtSecurityTokenHandler().WriteToken(jwt);
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);
        if (disposing)
        {
            _rsa.Dispose();
            if (Directory.Exists(_directory)) Directory.Delete(_directory, true);
        }
    }
}

public sealed class HttpContractTests
{
    private static async Task<JsonElement> Rpc(HttpClient client, string method, object? parameters = null)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post, "/mcp")
        {
            Content = JsonContent.Create(new { jsonrpc = "2.0", id = 1, method, @params = parameters ?? new { } })
        };
        request.Headers.Accept.ParseAdd("application/json");
        request.Headers.Accept.ParseAdd("text/event-stream");
        request.Headers.Add("MCP-Protocol-Version", "2025-11-25");
        using var response = await client.SendAsync(request);
        var text = await response.Content.ReadAsStringAsync();
        Assert.True(response.IsSuccessStatusCode, $"HTTP {(int)response.StatusCode}: {text}");
        var json = text.StartsWith("event:") || text.StartsWith("data:")
            ? string.Join("", text.Split('\n').Where(x => x.StartsWith("data:")).Select(x => x[5..].Trim()))
            : text;
        using var document = JsonDocument.Parse(json);
        Assert.False(document.RootElement.TryGetProperty("error", out _), json);
        return document.RootElement.GetProperty("result").Clone();
    }

    [Fact]
    public async Task OfficialMcpDiscoveryPublishesAppMetadataAndBoundedSchemas()
    {
        using var factory = new AppFactory();
        using var client = factory.Client();
        var result = await Rpc(client, "tools/list");
        var tools = result.GetProperty("tools").EnumerateArray().ToArray();
        Assert.Equal(5, tools.Length);
        foreach (var tool in tools)
        {
            var visibility = tool.GetProperty("_meta").GetProperty("ui").GetProperty("visibility").EnumerateArray().Select(x => x.GetString()).ToArray();
            if (tool.GetProperty("name").GetString() == "start_live_chat")
            {
                Assert.Equal(new[] { "model", "app" }, visibility);
                Assert.Equal(ChatTools.ResourceUri, tool.GetProperty("_meta").GetProperty("ui").GetProperty("resourceUri").GetString());
                Assert.Equal(128, tool.GetProperty("inputSchema").GetProperty("properties").GetProperty("requestId").GetProperty("maxLength").GetInt32());
            }
            else Assert.Equal(new[] { "app" }, visibility);
        }
    }

    [Fact]
    public async Task OfficialMcpResourceAndToolResultsMatchWidgetContract()
    {
        using var factory = new AppFactory();
        using var client = factory.Client();
        var resources = await Rpc(client, "resources/list");
        Assert.Contains(resources.GetProperty("resources").EnumerateArray(), r => r.GetProperty("uri").GetString() == ChatTools.ResourceUri);
        var read = await Rpc(client, "resources/read", new { uri = ChatTools.ResourceUri });
        var resource = read.GetProperty("contents")[0];
        Assert.Equal(WidgetResource.MimeType, resource.GetProperty("mimeType").GetString());
        Assert.Contains("Test widget", resource.GetProperty("text").GetString());
        var call = await Rpc(client, "tools/call", new { name = "start_live_chat", arguments = new { summary = "Help", requestId = "http-request" } });
        var view = call.GetProperty("structuredContent");
        Assert.Equal("draft", view.GetProperty("status").GetString());
        Assert.True(view.TryGetProperty("sessionId", out _));
        Assert.Equal(JsonValueKind.Null, view.GetProperty("interactionNumber").ValueKind);
        Assert.True(view.TryGetProperty("events", out _));
        Assert.True(view.TryGetProperty("hasMore", out _));
        Assert.True(view.TryGetProperty("nextCursor", out _));
        Assert.Equal("text", call.GetProperty("content")[0].GetProperty("type").GetString());
        var remote = (FakeRemote)factory.Services.GetRequiredService<IServiceNowClient>();
        Assert.Equal(0, remote.Opens);
    }

    [Fact]
    public async Task DemoBrowserEndpointUsesSameCoreAndRejectsForeignOriginsAndHosts()
    {
        using var factory = new AppFactory();
        using var client = factory.Client();
        var mode = await client.GetFromJsonAsync<JsonElement>("/dev/mode");
        Assert.True(mode.GetProperty("enabled").GetBoolean());
        Assert.Equal("demo", mode.GetProperty("mode").GetString());
        var response = await client.PostAsJsonAsync("/dev/tools/start_live_chat", new { summary = "Demo problem", requestId = "demo-test" });
        response.EnsureSuccessStatusCode();
        var envelope = await response.Content.ReadFromJsonAsync<JsonElement>();
        var view = envelope.GetProperty("structuredContent").Deserialize<ChatView>(ChatJson.Options)!;
        Assert.Equal("draft", view.Status);
        Assert.Equal("text", envelope.GetProperty("content")[0].GetProperty("type").GetString());
        var invalid = await client.PostAsJsonAsync("/dev/tools/start_live_chat", new { summary = "", requestId = "invalid" });
        Assert.True((await invalid.Content.ReadFromJsonAsync<JsonElement>()).GetProperty("isError").GetBoolean());
        using var foreign = new HttpRequestMessage(HttpMethod.Post, "/dev/tools/start_live_chat")
        {
            Content = JsonContent.Create(new { summary = "Demo problem", requestId = "foreign" })
        };
        foreign.Headers.Add("Origin", "https://evil.example");
        Assert.Equal(HttpStatusCode.Forbidden, (await client.SendAsync(foreign)).StatusCode);
        using var host = new HttpRequestMessage(HttpMethod.Get, "/");
        host.Headers.Host = "evil.example:5078";
        Assert.Equal(HttpStatusCode.Forbidden, (await client.SendAsync(host)).StatusCode);
        using var forwarded = new HttpRequestMessage(HttpMethod.Get, "/");
        forwarded.Headers.Add("X-Forwarded-For", "127.0.0.1");
        Assert.Equal(HttpStatusCode.Forbidden, (await client.SendAsync(forwarded)).StatusCode);
    }

    [Fact]
    public async Task ProductionRequiresJwtAndSuppliesOfficialOAuthResourceChallenge()
    {
        using var factory = new AppFactory(false);
        using var client = factory.Client();
        using var unauthorized = await client.PostAsJsonAsync("/mcp", new { });
        Assert.Equal(HttpStatusCode.Unauthorized, unauthorized.StatusCode);
        Assert.Contains("resource_metadata", unauthorized.Headers.WwwAuthenticate.ToString());
        using var metadata = await client.GetAsync("/.well-known/oauth-protected-resource");
        metadata.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await metadata.Content.ReadAsStringAsync());
        Assert.Equal("https://cowork.example.invalid/mcp", document.RootElement.GetProperty("resource").GetString());
        Assert.Equal(HttpStatusCode.NotFound, (await client.PostAsJsonAsync("/dev/tools/start_live_chat", new { })).StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync("/dev/mode")).StatusCode);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token());
        Assert.Equal(5, (await Rpc(client, "tools/list")).GetProperty("tools").GetArrayLength());
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token(wrongAudience: true));
        Assert.Equal(HttpStatusCode.Unauthorized, (await client.PostAsJsonAsync("/mcp", new { })).StatusCode);
    }

    [Fact]
    public async Task UserScopeAndWebhookAppRoleAudiencesAreNotInterchangeable()
    {
        using var factory = new AppFactory(false);
        using var client = factory.Client();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token(scope: "Other.Scope"));
        Assert.Equal(HttpStatusCode.Forbidden, (await client.PostAsJsonAsync("/mcp", new { })).StatusCode);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token(webhook: true));
        Assert.Equal(HttpStatusCode.Unauthorized, (await client.PostAsJsonAsync("/mcp", new { })).StatusCode);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token());
        Assert.Equal(HttpStatusCode.Unauthorized, (await client.PostAsJsonAsync("/api/livechat/sn", new { })).StatusCode);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token(webhook: true, role: false));
        Assert.Equal(HttpStatusCode.Forbidden, (await client.PostAsJsonAsync("/api/livechat/sn", new { })).StatusCode);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token(webhook: true, caller: Guid.NewGuid().ToString()));
        Assert.Equal(HttpStatusCode.Forbidden, (await client.PostAsJsonAsync("/api/livechat/sn", new { })).StatusCode);
    }

    [Fact]
    public async Task ProductionWebhookCommitsBeforeAckAndUserCannotReadOthersSession()
    {
        using var factory = new AppFactory(false);
        using var client = factory.Client();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token());
        var start = await Rpc(client, "tools/call", new { name = "start_live_chat", arguments = new { summary = "Help", requestId = "owner-test" } });
        var id = start.GetProperty("structuredContent").GetProperty("sessionId").GetString()!;
        await Rpc(client, "tools/call", new { name = "confirm_live_chat", arguments = new { sessionId = id, summary = "Help" } });
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token(webhook: true));
        var e = Fixture.Event(id, "message", "http-callback", "An agent message", "message-id");
        Assert.Equal(HttpStatusCode.OK, (await client.PostAsJsonAsync("/api/livechat/sn", e)).StatusCode);
        Assert.Equal(HttpStatusCode.OK, (await client.PostAsJsonAsync("/api/livechat/sn", e)).StatusCode);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token());
        var updates = await Rpc(client, "tools/call", new { name = "get_live_chat_updates", arguments = new { sessionId = id, afterSequence = 0 } });
        Assert.Single(updates.GetProperty("structuredContent").GetProperty("events").EnumerateArray(), x => x.GetProperty("kind").GetString() == "message");
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", factory.Token(user: "dddddddd-dddd-dddd-dddd-dddddddddddd"));
        var denied = await Rpc(client, "tools/call", new { name = "get_live_chat_updates", arguments = new { sessionId = id } });
        Assert.True(denied.GetProperty("isError").GetBoolean());
        Assert.DoesNotContain("An agent message", denied.ToString());
    }
}
