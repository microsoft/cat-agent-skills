using System.Net;
using System.Text.Json;
using CoworkSn;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.IdentityModel.Tokens;
using ModelContextProtocol.AspNetCore;
using ModelContextProtocol.AspNetCore.Authentication;

var builder = WebApplication.CreateBuilder(args);
var settings = builder.Configuration.Get<BridgeOptions>() ?? new BridgeOptions();
settings.Validate(builder.Environment, builder.Configuration);
builder.Services.AddSingleton(settings);
builder.Services.AddSingleton(TimeProvider.System);
builder.Services.AddSingleton<SessionStore>();
builder.Services.AddSingleton<ChatService>();
builder.Services.AddSingleton<TranslationService>();
builder.Services.AddSingleton<WidgetResource>();
builder.Services.AddHttpContextAccessor();
builder.Services.AddHostedService<TimeoutWorker>();
builder.Services.ConfigureHttpJsonOptions(o => o.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase);

// HTTP bodies and headers are never logged. These clients refuse redirects to avoid leaking OAuth credentials.
foreach (var name in new[] { "ServiceNow", "Translator" })
    builder.Services.AddHttpClient(name, client =>
    {
        client.Timeout = TimeSpan.FromSeconds(25);
        client.MaxResponseContentBufferSize = 256 * 1024;
    }).ConfigurePrimaryHttpMessageHandler(() => new HttpClientHandler { AllowAutoRedirect = false });

if (settings.Demo.Enabled)
{
    builder.WebHost.ConfigureKestrel(o => o.ListenLocalhost(settings.Demo.Port));
    builder.Services.AddSingleton<IServiceNowClient, DemoServiceNowClient>();
}
else
{
    if (settings.ServiceNow.Enabled) builder.Services.AddSingleton<IServiceNowClient, ServiceNowClient>();
    else builder.Services.AddSingleton<IServiceNowClient, DisconnectedServiceNowClient>();
    var authority = $"https://login.microsoftonline.com/{settings.Auth.TenantId}/v2.0";
    builder.Services.AddAuthentication(o =>
    {
        o.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
        o.DefaultChallengeScheme = McpAuthenticationDefaults.AuthenticationScheme;
        o.DefaultForbidScheme = JwtBearerDefaults.AuthenticationScheme;
    })
    .AddJwtBearer(JwtBearerDefaults.AuthenticationScheme, o => ConfigureJwt(o, authority, settings.Auth.UserAudience!))
    .AddJwtBearer("Webhook", o => ConfigureJwt(o, authority, settings.Auth.WebhookAudience!))
    .AddMcp(o =>
    {
        o.ResourceMetadataUri = new Uri(settings.PublicBaseUrl!.TrimEnd('/') + "/.well-known/oauth-protected-resource");
        o.ResourceMetadata = new()
        {
            Resource = settings.PublicBaseUrl.TrimEnd('/') + "/mcp",
            AuthorizationServers = { authority },
            ScopesSupported = [settings.Auth.DelegatedScope!],
            BearerMethodsSupported = ["header"],
            ResourceName = "Cowork ServiceNow live chat"
        };
    });
    builder.Services.Configure<ForwardedHeadersOptions>(o =>
    {
        o.ForwardedHeaders = ForwardedHeaders.XForwardedProto;
        o.KnownNetworks.Clear();
        o.KnownProxies.Clear();
        foreach (var ip in settings.TrustedProxyIps) o.KnownProxies.Add(IPAddress.Parse(ip));
        // Middleware is only installed when this allow-list is nonempty.
        o.ForwardLimit = 1;
    });
}

builder.Services.AddAuthorization(o =>
{
    if (!settings.Demo.Enabled)
    {
        o.AddPolicy("User", p => p.RequireAuthenticatedUser().RequireAssertion(context =>
        {
            try { Owner.FromPrincipal(context.User, settings.Auth); return true; }
            catch (ChatException) { return false; }
        }));
        o.AddPolicy("Webhook", p => p.AddAuthenticationSchemes("Webhook").RequireAuthenticatedUser()
            .RequireClaim("tid", settings.Auth.TenantId!)
            .RequireClaim("roles", AuthOptions.WebhookRole)
            .RequireAssertion(c => !c.User.HasClaim(x => x.Type == "scp") &&
                settings.Auth.AllowedWebhookCallers.Contains(
                    c.User.FindFirst("azp")?.Value ?? c.User.FindFirst("appid")?.Value ?? "", StringComparer.OrdinalIgnoreCase)));
    }
});
builder.Services.AddMcpServer()
    .WithHttpTransport(o => o.SessionMode = HttpServerSessionMode.Stateless)
    .WithTools<ChatTools>()
    .WithResources<WidgetResource>()
    .AddAuthorizationFilters();

var app = builder.Build();
if (!settings.Demo.Enabled && settings.TrustedProxyIps.Length > 0) app.UseForwardedHeaders();
app.Use(async (context, next) =>
{
    if (settings.Demo.Enabled)
    {
        if (!DemoSecurity.IsAllowed(context.Request, context.Connection.RemoteIpAddress, settings.Demo.Port))
        {
            context.Response.StatusCode = 403;
            return;
        }
    }
    else
    {
        var publicUri = new Uri(settings.PublicBaseUrl!);
        var expectedHost = new HostString(publicUri.Host, publicUri.Port);
        var requestPort = context.Request.Host.Port ?? (context.Request.IsHttps ? 443 : 80);
        if (!context.Request.IsHttps || !string.Equals(context.Request.Host.Host, expectedHost.Host, StringComparison.OrdinalIgnoreCase) ||
            requestPort != publicUri.Port ||
            (context.Request.Headers.Origin.Count > 0 &&
                context.Request.Headers.Origin.ToString() != publicUri.GetLeftPart(UriPartial.Authority)))
        {
            context.Response.StatusCode = 403;
            return;
        }
    }
    context.Response.Headers.CacheControl = "no-store";
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    if (context.Request.ContentLength > 64 * 1024)
    {
        context.Response.StatusCode = 413;
        return;
    }
    var limit = context.Features.Get<Microsoft.AspNetCore.Http.Features.IHttpMaxRequestBodySizeFeature>();
    if (limit is { IsReadOnly: false }) limit.MaxRequestBodySize = 64 * 1024;
    try { await next(context); }
    catch (ChatException ex)
    {
        context.Response.StatusCode = ex.HttpStatus;
        await context.Response.WriteAsJsonAsync(new { error = ex.Code, message = ex.Message });
    }
});
if (!settings.Demo.Enabled)
{
    app.UseAuthentication();
    app.UseAuthorization();
}

var mcp = app.MapMcp("/mcp");
app.MapGet("/privacy", () => Results.Text("Cowork SN private test pilot. Only the signed-in user's reviewed support summary and messages are used. Drafts and transcripts are stored in the pilot's local database; terminal sessions default to seven-day retention. ServiceNow receives data only when its integration is enabled and the user confirms sharing. No passwords should be entered into chat. Contact the pilot owner for access or deletion. No advertising or public transcript sharing."));
app.MapGet("/terms", () => Results.Text("Cowork SN is a custom test sample, not a Microsoft or ServiceNow product. No warranty, vendor support or service-level agreement is supplied. Access is restricted to the authorized pilot tester. Do not use for production or sensitive incidents. ServiceNow activation is separate from plugin installation."));
app.MapGet("/about", () => Results.Text("Cowork SN - review prototype. Human support appears in the embedded panel, not the main Cowork composer."));
if (!settings.Demo.Enabled) mcp.RequireAuthorization("User");
if (!settings.Demo.Enabled)
    app.MapPost("/api/livechat/sn", (WebhookEvent body, ChatService service) =>
    {
        service.Receive(body);
        return Results.Ok(new { ok = true });
    }).RequireAuthorization("Webhook");

if (settings.Demo.Enabled)
{
    // Browser harness only. Native MCP calls use the SAME ChatService. Never mapped in live mode.
    app.MapGet("/", (WidgetResource resource) => Results.Content(resource.Html(), "text/html"));
    app.MapGet("/dev/mode", () => Results.Json(new { enabled = true, mode = "demo" }));
    app.MapPost("/dev/tools/{name}", async (string name, JsonElement body, ChatService service) =>
    {
        string Required(string key) => body.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.String
            ? v.GetString()! : throw new ChatException("invalid_argument", $"{key} is required.");
        string? Optional(string key) => body.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
        var result = await ChatTools.Invoke(async () => name switch
        {
            "start_live_chat" => service.Start(Owner.Demo, Required("summary"), Required("requestId"), Optional("originalText"), Optional("language")),
            "confirm_live_chat" => await service.ConfirmAsync(Owner.Demo, Required("sessionId"), Required("summary")),
            "get_live_chat_updates" => service.Updates(Owner.Demo, Required("sessionId"), body.TryGetProperty("afterSequence", out var cursor) && cursor.TryGetInt32(out var n) ? n : 0),
            "send_live_chat_message" => await service.SendAsync(Owner.Demo, Required("sessionId"), Required("text"), Required("clientMessageId")),
            "request_end_live_chat" => await service.RequestEndAsync(Owner.Demo, Required("sessionId"), Required("clientMessageId")),
            _ => throw new ChatException("not_found", "Unknown tool.", 404)
        });
        return Results.Json(result, ChatJson.Options);
    });
}
app.Run();

static void ConfigureJwt(JwtBearerOptions options, string authority, string audience)
{
    options.Authority = authority;
    options.Audience = audience;
    options.MapInboundClaims = false;
    options.RequireHttpsMetadata = true;
    options.IncludeErrorDetails = false;
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true, ValidIssuer = authority, ValidateAudience = true, ValidAudience = audience,
        ValidateLifetime = true, ValidateIssuerSigningKey = true, RequireSignedTokens = true,
        RequireExpirationTime = true, ClockSkew = TimeSpan.FromMinutes(1),
        NameClaimType = "oid", RoleClaimType = "roles"
    };
}

public partial class Program;
