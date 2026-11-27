using System.Text.Json;
using CoworkSn;

namespace CoworkSn.Tests;

public sealed class ChatServiceTests
{
    [Fact]
    public void DraftHasNoRemoteEffectsAndRequestIdIsOwnerBound()
    {
        using var f = new Fixture();
        var first = f.Draft();
        var second = f.Draft();
        var bob = f.Service.Start(f.Bob, "A test issue", "request-1");
        Assert.Equal("draft", first.Status);
        Assert.Empty(first.Events);
        Assert.Equal(first.SessionId, second.SessionId);
        Assert.NotEqual(first.SessionId, bob.SessionId);
        Assert.Equal(0, f.Remote.Opens + f.Remote.Sends + f.Remote.Closes);
        Assert.Throws<ChatException>(() => f.Service.Start(f.Alice, "Changed", "request-1"));
    }

    [Fact]
    public async Task EverySessionOperationChecksOwner()
    {
        using var f = new Fixture();
        var draft = f.Draft();
        Assert.Equal(404, Assert.Throws<ChatException>(() => f.Service.Updates(f.Bob, draft.SessionId)).HttpStatus);
        Assert.Equal(404, Assert.Throws<ChatException>(() => f.Service.Updates(f.Alice with { TenantId = "another-tenant" }, draft.SessionId)).HttpStatus);
        await Assert.ThrowsAsync<ChatException>(() => f.Service.ConfirmAsync(f.Bob, draft.SessionId, "summary"));
        await Assert.ThrowsAsync<ChatException>(() => f.Service.SendAsync(f.Bob, draft.SessionId, "text", "msg-1"));
        await Assert.ThrowsAsync<ChatException>(() => f.Service.RequestEndAsync(f.Bob, draft.SessionId, "end-1"));
        Assert.Equal(0, f.Remote.Opens + f.Remote.Sends + f.Remote.Closes);
    }

    [Fact]
    public async Task ConfirmIsIdempotentAndCallbackCanArriveBeforeOpenReturns()
    {
        using var f = new Fixture();
        var draft = f.Draft();
        f.Remote.BeforeOpenReturns = s =>
        {
            f.Service.Receive(Fixture.Event(s.Id, "message", "first-message", "Hello", "sn-message"));
            f.Service.Receive(Fixture.Event(s.Id, "accepted", "late-accepted"));
            return Task.CompletedTask;
        };
        var first = await f.Service.ConfirmAsync(f.Alice, draft.SessionId, "Edited and approved");
        var repeated = await f.Service.ConfirmAsync(f.Alice, draft.SessionId, "Edited and approved");
        Assert.Equal("connected", first.Status);
        Assert.Equal("Edited and approved", repeated.Summary);
        Assert.Equal(1, f.Remote.Opens);
        Assert.Single(first.Events, e => e.Kind == "accepted");
        Assert.Single(first.Events, e => e.Kind == "message");
        await Assert.ThrowsAsync<ChatException>(() => f.Service.ConfirmAsync(f.Alice, draft.SessionId, "Another edit"));
    }

    [Fact]
    public async Task ParallelConfirmAndSendsReserveBeforeNetwork()
    {
        using var f = new Fixture();
        var draft = f.Draft();
        var entered = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var release = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        f.Remote.BeforeOpenReturns = async _ => { entered.SetResult(); await release.Task; };
        var first = f.Service.ConfirmAsync(f.Alice, draft.SessionId, draft.Summary);
        await entered.Task;
        var retry = await f.Service.ConfirmAsync(f.Alice, draft.SessionId, draft.Summary);
        Assert.Equal("starting", retry.Status);
        release.SetResult();
        await first;
        Assert.Equal(1, f.Remote.Opens);
        f.Service.Receive(Fixture.Event(draft.SessionId, "accepted", "joined"));
        await Task.WhenAll(Enumerable.Range(0, 8).Select(_ => f.Service.SendAsync(f.Alice, draft.SessionId, "Hi", "same-id")));
        Assert.Equal(1, f.Remote.Sends);
    }

    [Fact]
    public async Task SendDedupRejectsChangedPayloadAndAmbiguousSendsAreNotRetried()
    {
        using var f = new Fixture();
        var connected = await f.Connected();
        await f.Service.SendAsync(f.Alice, connected.SessionId, "Hello", "message-1");
        await f.Service.SendAsync(f.Alice, connected.SessionId, "Hello", "message-1");
        await Assert.ThrowsAsync<ChatException>(() => f.Service.SendAsync(f.Alice, connected.SessionId, "Changed", "message-1"));
        f.Remote.FailSend = true;
        await Assert.ThrowsAsync<ChatException>(() => f.Service.SendAsync(f.Alice, connected.SessionId, "Another", "message-2"));
        await Assert.ThrowsAsync<ChatException>(() => f.Service.SendAsync(f.Alice, connected.SessionId, "Another", "message-2"));
        Assert.Equal(2, f.Remote.Sends);
        Assert.Equal("ambiguous", f.Store.Update(connected.SessionId, f.Alice, tx => tx.OperationState("client:message-2")));
    }

    [Fact]
    public async Task AmbiguousOpeningIsRetainedAndNeverBlindlyReopened()
    {
        using var f = new Fixture();
        f.Remote.FailOpen = true;
        var draft = f.Draft();
        var result = await f.Service.ConfirmAsync(f.Alice, draft.SessionId, draft.Summary);
        Assert.Equal("starting", result.Status);
        await f.Service.ConfirmAsync(f.Alice, draft.SessionId, draft.Summary);
        f.Clock.Advance(TimeSpan.FromDays(20));
        await f.Service.SweepAsync();
        Assert.Equal("closing", f.Service.Updates(f.Alice, draft.SessionId).Status);
        Assert.Contains(draft.SessionId, f.Store.ActiveIds());
        Assert.Equal(1, f.Remote.Opens);
        Assert.Equal(0, f.Remote.Closes);
    }

    [Fact]
    public async Task CallbackDedupOrderingAndLateAcceptedNeverReopensClosed()
    {
        using var f = new Fixture();
        var waiting = await f.Waiting();
        var message = Fixture.Event(waiting.SessionId, "message", "event-1", "Hello", "message-1");
        f.Service.Receive(message);
        f.Service.Receive(message);
        f.Service.Receive(message with { EventId = "event-2" });
        f.Service.Receive(Fixture.Event(waiting.SessionId, "closed", "closed"));
        f.Service.Receive(Fixture.Event(waiting.SessionId, "accepted", "late-join"));
        var late = Fixture.Event(waiting.SessionId, "message", "late-message", "A delayed reply");
        f.Service.Receive(late);
        f.Service.Receive(late);
        var all = f.Service.Updates(f.Alice, waiting.SessionId);
        Assert.Equal("closed", all.Status);
        Assert.Single(all.Events, e => e.Kind == "accepted");
        Assert.Single(all.Events, e => e.Kind == "message");
        Assert.Single(all.Events, e => e.Kind == "closed");
        var tail = f.Service.Updates(f.Alice, waiting.SessionId, all.NextCursor);
        Assert.Single(tail.Events, e => e.Kind == "late_message" && e.Text == "A delayed reply");
        Assert.Equal(Enumerable.Range(1, all.Events.Count).Select(x => (long)x), all.Events.Select(e => e.Sequence));
    }

    [Fact]
    public async Task EarlyClosedCallbackSurvivesOpenResponse()
    {
        using var f = new Fixture();
        f.Remote.BeforeOpenReturns = s => { f.Service.Receive(Fixture.Event(s.Id, "closed", "early-close")); return Task.CompletedTask; };
        var result = await f.Waiting();
        Assert.Equal("closed", result.Status);
        Assert.Contains(result.Events, x => x.Kind == "closed");
    }

    [Fact]
    public async Task InvalidCallbacksAreRejected()
    {
        using var f = new Fixture();
        var waiting = await f.Waiting();
        var e = Fixture.Event(waiting.SessionId, "accepted", "event");
        Assert.Throws<ChatException>(() => f.Service.Receive(e with { Bot = "agents_sdk_skill" }));
        Assert.Throws<ChatException>(() => f.Service.Receive(e with { Event = "surprise" }));
        Assert.Throws<ChatException>(() => f.Service.Receive(e with { EventId = "" }));
        Assert.Throws<ChatException>(() => f.Service.Receive(e with { ClientSessionId = Guid.NewGuid().ToString("N") }));
        Assert.Throws<ChatException>(() => f.Service.Receive(e with { InteractionNumber = "another" }));
    }

    [Fact]
    public async Task DraftCancelsLocallyWaitingClosesAndConnectedOnlyRequestsClosure()
    {
        using var draftFixture = new Fixture();
        var draft = draftFixture.Draft();
        Assert.Equal("closed", (await draftFixture.Service.RequestEndAsync(draftFixture.Alice, draft.SessionId, "end")).Status);
        Assert.Equal(0, draftFixture.Remote.Closes);
        using var waitingFixture = new Fixture();
        var waiting = await waitingFixture.Waiting();
        Assert.Equal("closed", (await waitingFixture.Service.RequestEndAsync(waitingFixture.Alice, waiting.SessionId, "end")).Status);
        Assert.Equal(1, waitingFixture.Remote.Closes);
        using var connectedFixture = new Fixture();
        var connected = await connectedFixture.Connected();
        var end = await connectedFixture.Service.RequestEndAsync(connectedFixture.Alice, connected.SessionId, "end");
        await connectedFixture.Service.RequestEndAsync(connectedFixture.Alice, connected.SessionId, "another-end");
        Assert.Equal("end_requested", end.Status);
        Assert.Equal(1, connectedFixture.Remote.Sends);
        Assert.Equal(0, connectedFixture.Remote.Closes);
    }

    [Fact]
    public async Task CloseFailureRetainsSessionRetriesSameKeyAndRetainsTerminalDelta()
    {
        using var f = new Fixture();
        var waiting = await f.Waiting();
        var cursor = waiting.NextCursor;
        f.Remote.FailClose = true;
        f.Clock.Advance(TimeSpan.FromMinutes(6));
        await f.Service.SweepAsync();
        Assert.Equal("closing", f.Service.Updates(f.Alice, waiting.SessionId).Status);
        Assert.Contains(waiting.SessionId, f.Store.ActiveIds());
        f.Remote.FailClose = false;
        f.Clock.Advance(TimeSpan.FromMinutes(1));
        await f.Service.SweepAsync();
        var delta = f.Service.Updates(f.Alice, waiting.SessionId, cursor);
        Assert.Equal("closed", delta.Status);
        Assert.Contains(delta.Events, x => x.Kind == "closed");
        Assert.Equal(f.Remote.CloseKeys[0], f.Remote.CloseKeys[1]);
        await f.Service.SweepAsync();
        Assert.Equal("closed", f.Service.Updates(f.Alice, waiting.SessionId).Status);
        f.Clock.Advance(TimeSpan.FromDays(8));
        await f.Service.SweepAsync();
        Assert.Throws<ChatException>(() => f.Service.Updates(f.Alice, waiting.SessionId));
    }

    [Fact]
    public async Task PollsAndAcceptedRetriesDoNotExtendIdleTimeout()
    {
        using var f = new Fixture();
        var connected = await f.Connected();
        f.Clock.Advance(TimeSpan.FromMinutes(14));
        f.Service.Updates(f.Alice, connected.SessionId);
        f.Service.Receive(Fixture.Event(connected.SessionId, "accepted", "join-retry-different-id"));
        f.Clock.Advance(TimeSpan.FromMinutes(2));
        await f.Service.SweepAsync();
        Assert.Equal("closed", f.Service.Updates(f.Alice, connected.SessionId).Status);
    }

    [Fact]
    public async Task DeltasAreBoundedAndCursorAllowsAllEventsToBeRead()
    {
        using var f = new Fixture();
        var connected = await f.Connected();
        for (var i = 0; i < 14; i++)
            f.Service.Receive(Fixture.Event(connected.SessionId, "message", $"msg-{i}", new string('x', 8000)));
        long cursor = 0;
        var sequences = new List<long>();
        ChatView view;
        do
        {
            view = f.Service.Updates(f.Alice, connected.SessionId, cursor);
            Assert.InRange(view.Events.Count, 1, 5);
            Assert.True(JsonSerializer.SerializeToUtf8Bytes(view, ChatJson.Options).Length < 64 * 1024);
            sequences.AddRange(view.Events.Select(x => x.Sequence));
            cursor = view.NextCursor;
        } while (view.HasMore);
        Assert.Equal(17, sequences.Count);
        Assert.Equal(17, sequences.Distinct().Count());
    }

    [Fact]
    public async Task DurableStoreSurvivesRecreationAndPreservesIdempotency()
    {
        using var f = new Fixture();
        var connected = await f.Connected();
        await f.Service.SendAsync(f.Alice, connected.SessionId, "Hello", "sent");
        var reopened = new SessionStore(f.Options, new TestEnvironment());
        var service = new ChatService(reopened, f.Remote, new TranslationService(new NoNetworkFactory(), f.Options), f.Options, f.Clock);
        await service.SendAsync(f.Alice, connected.SessionId, "Hello", "sent");
        Assert.Equal(1, f.Remote.Sends);
        Assert.Contains(service.Updates(f.Alice, connected.SessionId).Events, x => x.Text == "Hello");
    }

    [Fact]
    public async Task EndRequestedDuringOpeningClosesAfterRemoteIdArrives()
    {
        using var f = new Fixture();
        var draft = f.Draft();
        var entered = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var release = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        f.Remote.BeforeOpenReturns = async _ => { entered.SetResult(); await release.Task; };
        var opening = f.Service.ConfirmAsync(f.Alice, draft.SessionId, draft.Summary);
        await entered.Task;
        var closing = await f.Service.RequestEndAsync(f.Alice, draft.SessionId, "early-cancel");
        Assert.Equal("closing", closing.Status);
        Assert.Equal(0, f.Remote.Closes);
        release.SetResult();
        Assert.Equal("closed", (await opening).Status);
        Assert.Equal(1, f.Remote.Closes);
    }

    [Fact]
    public async Task UnavailableIsTerminalAndIncludesRetainedReason()
    {
        using var f = new Fixture();
        f.Remote.Unavailable = true;
        var result = await f.Waiting();
        Assert.Equal("unavailable", result.Status);
        Assert.Contains(result.Events, e => e.Kind == "unavailable");
        Assert.DoesNotContain(result.SessionId, f.Store.ActiveIds());
    }

    [Fact]
    public async Task PendingOperationAfterCrashIsNotReplayed()
    {
        using var f = new Fixture();
        var draft = f.Draft();
        f.Store.Update(draft.SessionId, f.Alice, tx =>
        {
            tx.Session.Status = "starting";
            tx.Reserve("open", "crash-marker");
            return 0;
        });
        var restored = new SessionStore(f.Options, new TestEnvironment());
        var service = new ChatService(restored, f.Remote, new TranslationService(new NoNetworkFactory(), f.Options), f.Options, f.Clock);
        var result = await service.ConfirmAsync(f.Alice, draft.SessionId, draft.Summary);
        Assert.Equal("starting", result.Status);
        Assert.Equal(0, f.Remote.Opens);
    }

    [Fact]
    public async Task WireMessageIdsAreBoundedStableAndSessionScoped()
    {
        using var f = new Fixture();
        var first = await f.Connected();
        const string callerId = "id:with.period_under";
        await f.Service.SendAsync(f.Alice, first.SessionId, "hello", callerId);
        await f.Service.SendAsync(f.Alice, first.SessionId, "hello", callerId);
        var second = f.Draft("second");
        await f.Service.ConfirmAsync(f.Alice, second.SessionId, second.Summary);
        f.Service.Receive(Fixture.Event(second.SessionId, "accepted", "join-second"));
        await f.Service.SendAsync(f.Alice, second.SessionId, "hello", callerId);
        Assert.Equal(2, f.Remote.Sends);
        Assert.NotEqual(f.Remote.SendKeys[0], f.Remote.SendKeys[1]);
        Assert.All(f.Remote.SendKeys, key =>
        {
            Assert.InRange(key.Length, 16, 80);
            Assert.Matches("^[A-Za-z0-9-]+$", key);
        });
        Assert.Equal(f.Remote.SendKeys[0], ChatService.RemoteMessageId(first.SessionId, callerId));
    }

    [Fact]
    public async Task AmbiguousCloseLedgerPausesRetriesWithoutLosingSession()
    {
        using var f = new Fixture();
        var waiting = await f.Waiting();
        f.Remote.AmbiguousClose = true;
        f.Clock.Advance(TimeSpan.FromMinutes(6));
        await f.Service.SweepAsync();
        Assert.Equal("closing", f.Service.Updates(f.Alice, waiting.SessionId).Status);
        Assert.Equal("requires_reconciliation", f.Store.Update(waiting.SessionId, f.Alice, tx => tx.OperationState("close")));
        f.Clock.Advance(TimeSpan.FromHours(1));
        await f.Service.SweepAsync();
        Assert.Equal(1, f.Remote.Closes);
        Assert.Equal("close-" + waiting.SessionId, f.Remote.CloseKeys.Single());
        Assert.Matches("^[A-Za-z0-9-]{16,80}$", f.Remote.CloseKeys.Single());
        f.Service.Receive(Fixture.Event(waiting.SessionId, "closed", "reconciled"));
        Assert.Equal("closed", f.Service.Updates(f.Alice, waiting.SessionId).Status);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ExplicitAlreadyClosedResponseClosesWithoutClaimingMessageDelivery(bool endRequest)
    {
        using var f = new Fixture();
        var connected = await f.Connected();
        f.Remote.AlreadyClosed = true;
        if (endRequest)
            await f.Service.RequestEndAsync(f.Alice, connected.SessionId, "already-closed");
        else
            await Assert.ThrowsAsync<ChatException>(() => f.Service.SendAsync(f.Alice, connected.SessionId, "Do not claim this was sent", "already-closed"));
        var result = f.Service.Updates(f.Alice, connected.SessionId);
        Assert.Equal("closed", result.Status);
        Assert.Contains(result.Events, e => e.Kind == "closed" && e.Text.Contains("not sent"));
        Assert.DoesNotContain(result.Events, e => e.Kind == "message" && e.Author == "user");
        Assert.Equal("not_sent_closed", f.Store.Update(connected.SessionId, f.Alice, tx => tx.OperationState("client:already-closed")));
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UncertainMutationAndRetryReturnMcpErrorsInsteadOfSuccess(bool endRequest)
    {
        using var f = new Fixture();
        var connected = await f.Connected();
        f.Remote.FailSend = true;
        Task<ChatView> Send() => endRequest
            ? f.Service.RequestEndAsync(f.Alice, connected.SessionId, "uncertain")
            : f.Service.SendAsync(f.Alice, connected.SessionId, "Keep this draft", "uncertain");
        var first = await ChatTools.Invoke(Send);
        var retry = await ChatTools.Invoke(Send);
        Assert.True(first.IsError);
        Assert.True(retry.IsError);
        Assert.Equal(1, f.Remote.Sends);
        Assert.DoesNotContain(f.Service.Updates(f.Alice, connected.SessionId).Events, e => e.Author == "user");
    }

    [Fact]
    public void TranslatedSummaryFallsBackToApprovedOriginalWhenCombinedTextExceedsBridgeLimit()
    {
        var original = new string('a', 3000);
        var translation = new Translation(new string('b', 3000), "fr", true);
        Assert.Equal(original, TranslationService.ForAgent(original, translation, 4000));
    }

    [Fact]
    public async Task UnassignedClosureAcceptsBlankNameAndRecoversAnAmbiguousOpening()
    {
        using var f = new Fixture();
        f.Remote.FailOpen = true;
        var draft = f.Draft();
        await f.Service.ConfirmAsync(f.Alice, draft.SessionId, draft.Summary);
        f.Service.Receive(Fixture.Event(draft.SessionId, "closed", "queue-cancelled") with { AgentName = "" });
        Assert.Equal("closed", f.Service.Updates(f.Alice, draft.SessionId).Status);
    }

    [Fact]
    public async Task FullLengthUnicodeCallbacksAndAgentNamesRemainCompleteAndFitMcpPages()
    {
        using var f = new Fixture();
        var draft = f.Service.Start(f.Alice, new string('a', 4000), "unicode");
        await f.Service.ConfirmAsync(f.Alice, draft.SessionId, draft.Summary);
        var text = new string('\u4e2d', 8000);
        var author = new string('\u540d', 200);
        f.Service.Receive(Fixture.Event(draft.SessionId, "message", "unicode-message", text) with { AgentName = author });
        long cursor = 0;
        var all = new List<ChatEvent>();
        ChatView page;
        do
        {
            page = f.Service.Updates(f.Alice, draft.SessionId, cursor);
            Assert.True(page.NextCursor > cursor);
            Assert.True(JsonSerializer.SerializeToUtf8Bytes(ChatTools.Result(page), ChatJson.Options).Length < 64 * 1024);
            all.AddRange(page.Events);
            cursor = page.NextCursor;
        } while (page.HasMore);
        Assert.Contains(all, e => e.Kind == "message" && e.Text == text && e.Author == author);
    }

    [Fact]
    public async Task LateRepliesRemainRetrievableAfterClosureWithoutReopeningTheSession()
    {
        using var f = new Fixture();
        var chat = await f.Connected();
        f.Service.Receive(Fixture.Event(chat.SessionId, "closed", "closed-first"));
        var closed = f.Service.Updates(f.Alice, chat.SessionId);
        var retry = Fixture.Event(chat.SessionId, "message", "earlier-message-retry", "The final solution", "sn-final-message");
        f.Service.Receive(retry);
        f.Service.Receive(retry);
        var delta = f.Service.Updates(f.Alice, chat.SessionId, closed.NextCursor);
        Assert.Equal("closed", delta.Status);
        Assert.Single(delta.Events);
        Assert.Equal("late_message", delta.Events[0].Kind);
        Assert.Equal("The final solution", delta.Events[0].Text);
    }
}
