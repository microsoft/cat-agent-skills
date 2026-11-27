using CoworkSn;

namespace CoworkSn.Tests;

public sealed class DisconnectedPilotTests
{
    [Fact]
    public async Task AuthenticatedDisconnectedPilotDoesNotSimulateOrSendServiceNowTraffic()
    {
        var client = new DisconnectedServiceNowClient();
        var session = new ChatSession();
        var result = await client.OpenAsync(session, "Approved synthetic summary", CancellationToken.None);
        Assert.True(result.Unavailable);
        Assert.Empty(result.ConversationId);
        Assert.Contains("not connected", result.Message);
        await Assert.ThrowsAsync<ChatException>(() => client.SendAsync(session, "text", "id", CancellationToken.None));
        await Assert.ThrowsAsync<ChatException>(() => client.CloseAsync(session, "id", CancellationToken.None));
    }
}
