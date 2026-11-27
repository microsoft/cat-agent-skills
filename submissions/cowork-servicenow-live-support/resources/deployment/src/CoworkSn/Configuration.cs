using System.Net;
using System.Net.Mail;
using System.Security.Claims;

namespace CoworkSn;

/// <summary>
/// Deploy exactly one process against a persistent, local SQLite volume (not an SMB/NFS share).
/// Back up the database plus its WAL consistently. Never expire active or ambiguous sessions.
/// Environment variables use double underscores, e.g. Demo__Enabled and Auth__TenantId.
/// Production requires HTTPS or a trusted proxy preserving Host and setting X-Forwarded-Proto.
/// Supply secrets through environment variables or dotnet user-secrets; never appsettings files.
/// </summary>
public sealed class BridgeOptions
{
    public DemoOptions Demo { get; set; } = new();
    public AuthOptions Auth { get; set; } = new();
    public ServiceNowOptions ServiceNow { get; set; } = new();
    public TranslatorOptions Translator { get; set; } = new();
    public StorageOptions Storage { get; set; } = new();
    public TimeoutOptions Timeouts { get; set; } = new();
    public string? PublicBaseUrl { get; set; }
    public string? WidgetPath { get; set; }
    public string[] TrustedProxyIps { get; set; } = [];

    public void Validate(IHostEnvironment environment, IConfiguration configuration)
    {
        if (new[] { Timeouts.AcceptanceMinutes, Timeouts.InactivityMinutes, Timeouts.MaxChatDurationMinutes, Storage.RetentionDays }
                .Any(x => !double.IsFinite(x)) ||
            Timeouts.AcceptanceMinutes <= 0 || Timeouts.InactivityMinutes <= 0 ||
            Timeouts.MaxChatDurationMinutes < Math.Max(Timeouts.AcceptanceMinutes, Timeouts.InactivityMinutes) ||
            Storage.RetentionDays * 1440 <= Timeouts.MaxChatDurationMinutes ||
            Timeouts.ScanSeconds < 1 || Timeouts.CloseRetrySeconds < 1)
            throw new InvalidOperationException("Invalid Timeouts or Storage:RetentionDays; retention must exceed maximum chat duration.");
        if (Demo.Enabled)
        {
            if (!environment.IsDevelopment())
                throw new InvalidOperationException("Demo:Enabled requires the Development environment.");
            if (Demo.Port is < 1024 or > 65535 || configuration.GetSection("Kestrel:Endpoints").Exists())
                throw new InvalidOperationException("Demo uses its own loopback listener; Kestrel:Endpoints is not allowed.");
            foreach (var url in (configuration["urls"] ?? "").Split(';', StringSplitOptions.RemoveEmptyEntries))
                if (!Uri.TryCreate(url, UriKind.Absolute, out var uri) || !uri.IsLoopback)
                    throw new InvalidOperationException("Demo cannot use a non-loopback URL.");
            if (Translator.Enabled)
                throw new InvalidOperationException("Demo never permits external translation.");
            return;
        }
        RequireHttps(PublicBaseUrl, nameof(PublicBaseUrl), rootOnly: true);
        if (!Guid.TryParse(Auth.TenantId, out _) || string.IsNullOrWhiteSpace(Auth.UserAudience) ||
            string.IsNullOrWhiteSpace(Auth.WebhookAudience) || Auth.UserAudience == Auth.WebhookAudience ||
            string.IsNullOrWhiteSpace(Auth.DelegatedScope) || !Auth.DelegatedScope.EndsWith("/" + AuthOptions.UserScope, StringComparison.Ordinal) ||
            Auth.AllowedWebhookCallers.Length == 0 || Auth.AllowedWebhookCallers.Any(x => !Guid.TryParse(x, out _)) ||
            Auth.EmailClaim is not ("preferred_username" or "email") || Auth.AllowedEmailDomains.Length == 0 ||
            Auth.AllowedEmailDomains.Any(x => x.Contains('@') || Uri.CheckHostName(x) != UriHostNameType.Dns))
            throw new InvalidOperationException("Configure Auth tenant, separate audiences, webhook callers, EmailClaim and AllowedEmailDomains.");
        if (ServiceNow.Enabled)
        {
            RequireHttps(ServiceNow.BaseUrl, "ServiceNow:BaseUrl", rootOnly: true);
            RequireHttps(ServiceNow.OAuth.TokenUrl, "ServiceNow:OAuth:TokenUrl");
            if (string.IsNullOrWhiteSpace(ServiceNow.OAuth.ClientId) || string.IsNullOrWhiteSpace(ServiceNow.OAuth.ClientSecret))
                throw new InvalidOperationException("ServiceNow OAuth client credentials are required; Basic authentication is unsupported.");
        }
        if (Translator.Enabled)
        {
            RequireHttps(Translator.Endpoint, "Translator:Endpoint", rootOnly: true);
            if (string.IsNullOrWhiteSpace(Translator.Key))
                throw new InvalidOperationException("Translator:Key is required when translation is explicitly enabled.");
        }
        foreach (var proxy in TrustedProxyIps)
            if (!IPAddress.TryParse(proxy, out _)) throw new InvalidOperationException("TrustedProxyIps must contain IP addresses.");
    }

    private static void RequireHttps(string? value, string name, bool rootOnly = false)
    {
        if (!Uri.TryCreate(value, UriKind.Absolute, out var uri) || uri.Scheme != "https" ||
            uri.UserInfo.Length > 0 || uri.Query.Length > 0 || uri.Fragment.Length > 0 ||
            (rootOnly && uri.AbsolutePath != "/"))
            throw new InvalidOperationException($"{name} must be an absolute HTTPS URL{(rootOnly ? " without a path" : "")}.");
    }
}

public sealed class DemoOptions { public bool Enabled { get; set; } public int Port { get; set; } = 5078; }
public sealed class AuthOptions
{
    public string? TenantId { get; set; }
    public string? UserAudience { get; set; }
    public string? WebhookAudience { get; set; }
    public string? DelegatedScope { get; set; }
    public string? EmailClaim { get; set; }
    public string[] AllowedEmailDomains { get; set; } = [];
    public string[] AllowedWebhookCallers { get; set; } = [];
    public const string UserScope = "LiveChat.Access";
    public const string WebhookRole = "LiveChat.Webhook";
}
public sealed class ServiceNowOptions
{
    public bool Enabled { get; set; }
    public string? BaseUrl { get; set; }
    public OAuthOptions OAuth { get; set; } = new();
}
public sealed class OAuthOptions
{
    public string? TokenUrl { get; set; }
    public string? ClientId { get; set; }
    public string? ClientSecret { get; set; }
}
public sealed class TranslatorOptions
{
    public bool Enabled { get; set; }
    public string Endpoint { get; set; } = "https://api.cognitive.microsofttranslator.com";
    public string? Key { get; set; }
    public string? Region { get; set; }
    public string AgentLanguage { get; set; } = "en";
}
public sealed class StorageOptions
{
    public string DatabasePath { get; set; } = "data\\cowork-sn.db";
    public double RetentionDays { get; set; } = 7;
}
public sealed class TimeoutOptions
{
    public double AcceptanceMinutes { get; set; } = 5;
    public double InactivityMinutes { get; set; } = 15;
    public double MaxChatDurationMinutes { get; set; } = 120;
    public int ScanSeconds { get; set; } = 30;
    public int CloseRetrySeconds { get; set; } = 30;
}

public sealed record Owner(string TenantId, string UserId, string Email)
{
    public static readonly Owner Demo = new("11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222", "demo@example.invalid");

    public static Owner FromPrincipal(ClaimsPrincipal user, AuthOptions options)
    {
        var tenant = user.FindFirst("tid")?.Value;
        var id = user.FindFirst("oid")?.Value;
        var email = options.EmailClaim is null ? null : user.FindFirst(options.EmailClaim)?.Value;
        if (user.Identity?.IsAuthenticated != true || !Guid.TryParse(tenant, out _) || !Guid.TryParse(id, out _) ||
            !string.Equals(tenant, options.TenantId, StringComparison.OrdinalIgnoreCase) ||
            !user.FindAll("scp").SelectMany(x => x.Value.Split(' ')).Contains(AuthOptions.UserScope) ||
            email is null || !MailAddress.TryCreate(email, out var address) || address.Address != email ||
            !options.AllowedEmailDomains.Contains(address.Host, StringComparer.OrdinalIgnoreCase))
            throw new ChatException("identity_not_mapped", "A validated delegated user identity and configured email mapping are required.", 403);
        return new Owner(tenant!.ToLowerInvariant(), id!.ToLowerInvariant(), email);
    }
}

public static class DemoSecurity
{
    public static bool IsAllowed(HttpRequest request, IPAddress? remoteAddress, int port)
    {
        var host = request.Host.Host.Trim('[', ']');
        if (remoteAddress is null || !IPAddress.IsLoopback(remoteAddress) || request.Host.Port != port ||
            !(host.Equals("localhost", StringComparison.OrdinalIgnoreCase) ||
              (IPAddress.TryParse(host, out var ip) && IPAddress.IsLoopback(ip))) ||
            request.Headers.ContainsKey("Forwarded") || request.Headers.ContainsKey("X-Forwarded-Host") ||
            request.Headers.ContainsKey("X-Forwarded-Proto") || request.Headers.ContainsKey("X-Forwarded-For") ||
            request.Headers["Sec-Fetch-Site"] == "cross-site")
            return false;
        var origin = request.Headers.Origin;
        return origin.Count == 0 || (origin.Count == 1 &&
            string.Equals(origin[0], $"{request.Scheme}://{request.Host}", StringComparison.OrdinalIgnoreCase));
    }
}
