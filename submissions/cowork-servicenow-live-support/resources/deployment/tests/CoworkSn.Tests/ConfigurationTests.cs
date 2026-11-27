using System.Net;
using System.Security.Claims;
using CoworkSn;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;

namespace CoworkSn.Tests;

public sealed class ConfigurationTests
{
    [Fact]
    public void ServiceNowIsDisabledByDefault()
    {
        Assert.False(new BridgeOptions().ServiceNow.Enabled);
    }

    [Fact]
    public void ProductionIsFailClosedWithoutConfiguration()
    {
        Assert.Throws<InvalidOperationException>(() => new BridgeOptions().Validate(
            new TestEnvironment { EnvironmentName = "Production" }, new ConfigurationBuilder().Build()));
    }

    [Fact]
    public void DemoRequiresExplicitFlagDevelopmentAndLoopbackBindings()
    {
        var config = new ConfigurationBuilder().Build();
        var options = new BridgeOptions { Demo = new() { Enabled = true } };
        options.Validate(new TestEnvironment(), config);
        Assert.Throws<InvalidOperationException>(() => options.Validate(new TestEnvironment { EnvironmentName = "Production" }, config));
        var remote = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?> { ["urls"] = "http://0.0.0.0:5078" }).Build();
        Assert.Throws<InvalidOperationException>(() => options.Validate(new TestEnvironment(), remote));
        var endpoints = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?> { ["Kestrel:Endpoints:Remote:Url"] = "http://0.0.0.0:9000" }).Build();
        Assert.Throws<InvalidOperationException>(() => options.Validate(new TestEnvironment(), endpoints));
        options.Translator.Enabled = true;
        Assert.Throws<InvalidOperationException>(() => options.Validate(new TestEnvironment(), config));
    }

    [Theory]
    [InlineData("127.0.0.1", "localhost:5078", null, true)]
    [InlineData("::1", "[::1]:5078", "http://[::1]:5078", true)]
    [InlineData("192.168.0.2", "localhost:5078", null, false)]
    [InlineData("127.0.0.1", "evil.example:5078", null, false)]
    [InlineData("127.0.0.1", "localhost:5078", "null", false)]
    [InlineData("127.0.0.1", "localhost:5078", "https://evil.example", false)]
    [InlineData("127.0.0.1", "localhost:9999", null, false)]
    public void DemoChecksRemoteIpHostAndOrigin(string ip, string host, string? origin, bool expected)
    {
        var context = new DefaultHttpContext();
        context.Request.Scheme = "http";
        context.Request.Host = new HostString(host);
        if (origin is not null) context.Request.Headers.Origin = origin;
        Assert.Equal(expected, DemoSecurity.IsAllowed(context.Request, IPAddress.Parse(ip), 5078));
        Assert.False(DemoSecurity.IsAllowed(context.Request, null, 5078));
    }

    [Fact]
    public void InputLimitsAndIdentityMappingAreEnforced()
    {
        Assert.Throws<ChatException>(() => Input.Key(new string('x', 129), "requestId"));
        Assert.Throws<ChatException>(() => Input.Text(new string('x', 8001), "text"));
        Assert.Throws<ChatException>(() => Input.Language("../../secret"));
        var options = new AuthOptions
        {
            TenantId = AppFactory.Tenant, EmailClaim = "preferred_username", AllowedEmailDomains = ["example.invalid"]
        };
        var claims = new[]
        {
            new Claim("tid", AppFactory.Tenant), new Claim("oid", Guid.NewGuid().ToString()),
            new Claim("preferred_username", "user@example.invalid"), new Claim("scp", AuthOptions.UserScope)
        };
        Assert.Equal("user@example.invalid", Owner.FromPrincipal(new ClaimsPrincipal(new ClaimsIdentity(claims, "JWT")), options).Email);
        Assert.Throws<ChatException>(() => Owner.FromPrincipal(new ClaimsPrincipal(new ClaimsIdentity(claims)), options));
        options.AllowedEmailDomains = ["another.example"];
        Assert.Throws<ChatException>(() => Owner.FromPrincipal(new ClaimsPrincipal(new ClaimsIdentity(claims, "JWT")), options));
    }
}
