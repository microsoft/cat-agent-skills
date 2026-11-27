using System.Security.Cryptography;
using System.Text;

namespace CoworkSn;

public sealed class ChatService(SessionStore store, IServiceNowClient remote, TranslationService translator,
    BridgeOptions options, TimeProvider time)
{
    private DateTimeOffset Now => time.GetUtcNow();
    private string SystemAuthor => options.Demo.Enabled ? "Demo" : "system";
    private static string Fingerprint(string text) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text)));
    public static string RemoteMessageId(string sessionId, string clientMessageId) => "msg-" + Fingerprint(sessionId + ":" + clientMessageId);

    public ChatView Start(Owner owner, string summary, string requestId, string? originalText = null, string? language = null)
    {
        Input.Text(summary, nameof(summary), 4000);
        Input.Key(requestId, nameof(requestId));
        if (originalText is not null) Input.Text(originalText, nameof(originalText));
        Input.Language(language);
        var session = store.CreateDraft(owner, requestId, summary, originalText, language, Now);
        return store.View(session.Id, owner);
    }

    public ChatView Updates(Owner owner, string sessionId, long afterSequence = 0) => store.View(sessionId, owner, afterSequence);

    public async Task<ChatView> ConfirmAsync(Owner owner, string sessionId, string summary)
    {
        Input.Text(summary, nameof(summary), 4000);
        var opening = store.Update(sessionId, owner, tx =>
        {
            var s = tx.Session;
            if (tx.OperationState("open") is not null)
            {
                if (s.Summary != summary) throw new ChatException("already_confirmed", "A confirmed summary cannot be edited. Retry with the confirmed summary.", 409);
                return null;
            }
            if (s.Status != "draft") throw new ChatException("invalid_state", "Only a draft can be confirmed.", 409);
            tx.Reserve("open", Fingerprint(summary));
            s.Summary = summary;
            s.OpenedAt = Now;
            s.LastActivityAt = Now;
            s.Status = "starting";
            tx.Append("status", SystemAuthor, options.Demo.Enabled ? "Demo: opening a simulated support chat." : "Opening your approved support request.", Now);
            return s;
        });
        if (opening is null) return store.View(sessionId, owner);

        OpenChatResult result;
        try
        {
            // The assistant-written summary can differ from the employee's language.
            var translated = await translator.TranslateAsync(summary, options.Translator.AgentLanguage, null, CancellationToken.None);
            result = await remote.OpenAsync(opening, TranslationService.ForAgent(summary, translated, 4000), CancellationToken.None);
        }
        catch (Exception)
        {
            store.Update(sessionId, owner, tx =>
            {
                tx.Mark("open", "ambiguous");
                tx.Append("error", SystemAuthor,
                    "The opening result is unknown. The same request will not be sent twice. Support must reconcile the request using this session ID.", Now);
                return 0;
            });
            return store.View(sessionId, owner);
        }

        var needsClose = store.Update(sessionId, owner, tx =>
        {
            var s = tx.Session;
            tx.Mark("open", "succeeded");
            if (result.Unavailable)
            {
                if (!s.JoinAnnounced)
                    tx.Terminal("unavailable", result.Message ?? "No support representative is available. No chat was opened.", Now);
                else
                    tx.Append("error", SystemAuthor, "ServiceNow returned an inconsistent opening result; support must reconcile this session.", Now);
                return false;
            }
            if (s.InteractionNumber is not null && s.InteractionNumber != result.InteractionNumber)
            {
                tx.Mark("open", "ambiguous");
                tx.Append("error", SystemAuthor, "ServiceNow correlation mismatch; support must reconcile this session.", Now);
                return false;
            }
            s.ConversationId = result.ConversationId;
            s.InteractionNumber = result.InteractionNumber;
            if (s.Status == "starting")
            {
                s.Status = "waiting";
                tx.Append("status", SystemAuthor, options.Demo.Enabled ? "Demo: simulated support queue." : "Waiting for a support representative.", Now);
            }
            return s.Status == "closing";
        });
        if (needsClose) await TryCloseAsync(sessionId);
        if (options.Demo.Enabled)
            Receive(new("accepted", "cowork_mcp", sessionId, result.InteractionNumber, null, "Demo simulator", null, "demo-accepted"));
        return store.View(sessionId, owner);
    }

    public async Task<ChatView> SendAsync(Owner owner, string sessionId, string text, string clientMessageId)
    {
        Input.Text(text, nameof(text));
        Input.Key(clientMessageId, nameof(clientMessageId));
        var key = "client:" + clientMessageId;
        var pending = store.Update(sessionId, owner, tx =>
        {
            if (!tx.Reserve(key, "send:" + Fingerprint(text)))
            {
                RequireDeliveryConfirmation(tx, key);
                return null;
            }
            var s = tx.Session;
            if (s.Status is not ("connected" or "end_requested") || s.ConversationId is null)
                throw new ChatException("invalid_state", "Messages require an open, connected chat.", 409);
            return s;
        });
        if (pending is null) return store.View(sessionId, owner);
        Translation translation;
        bool sentTranslation;
        try
        {
            translation = await translator.TranslateAsync(text, options.Translator.AgentLanguage, null, CancellationToken.None);
            var outbound = TranslationService.ForAgent(text, translation);
            sentTranslation = translation.Translated && outbound != text;
            await remote.SendAsync(pending, outbound, RemoteMessageId(sessionId, clientMessageId), CancellationToken.None);
        }
        catch (RemoteChatClosedException)
        {
            AlreadyClosed(sessionId, owner, key);
            throw new ChatException("chat_closed_not_sent", "The chat is closed and this message was not sent. Your text has been retained in the panel.", 409);
        }
        catch (Exception)
        {
            AmbiguousMessage(sessionId, owner, key);
            throw DeliveryUnconfirmed();
        }
        store.Update(sessionId, owner, tx =>
        {
            tx.Mark(key, "succeeded");
            tx.Session.LastActivityAt = Now;
            if (translation.SourceLanguage is not null && text.Trim().Length >= 12)
                tx.Session.Language = translation.SourceLanguage;
            tx.Append("message", "user", text, Now, language: translation.SourceLanguage ?? pending.Language);
            if (sentTranslation)
                tx.Append("translation", SystemAuthor, translation.Text, Now, text, options.Translator.AgentLanguage);
            return 0;
        });
        if (options.Demo.Enabled)
            Receive(new("message", "cowork_mcp", sessionId, pending.InteractionNumber!,
                "Demo: your message was recorded by the simulator. No real agent or ServiceNow instance is involved.",
                "Demo simulator", null, "demo-message:" + Fingerprint(clientMessageId)));
        return store.View(sessionId, owner);
    }

    private void AmbiguousMessage(string sessionId, Owner owner, string key)
    {
        store.Update(sessionId, owner, tx =>
        {
            tx.Mark(key, "ambiguous");
            tx.Append("error", SystemAuthor,
                "Message delivery is unknown. It will not be resent automatically. Do not retry with a different message ID.", Now);
            return 0;
        });
    }

    private static ChatException DeliveryUnconfirmed() => new("delivery_unconfirmed",
        "Delivery is unconfirmed. Keep the same message ID; support must reconcile it before another send.", 409);

    private static void RequireDeliveryConfirmation(SessionTransaction tx, string key)
    {
        if (tx.OperationState(key) == "succeeded") return;
        if (tx.OperationState(key) == "not_sent_closed")
            throw new ChatException("chat_closed_not_sent", "The chat was closed before this message could be sent.", 409);
        throw DeliveryUnconfirmed();
    }

    private void AlreadyClosed(string sessionId, Owner owner, string key)
    {
        store.Update(sessionId, owner, tx =>
        {
            tx.Mark(key, "not_sent_closed");
            tx.Terminal("closed", "ServiceNow confirmed that this chat was already closed. The message was not sent.", Now);
            return 0;
        });
    }

    public async Task<ChatView> RequestEndAsync(Owner owner, string sessionId, string clientMessageId)
    {
        Input.Key(clientMessageId, nameof(clientMessageId));
        var key = "client:" + clientMessageId;
        var action = store.Update<(string Kind, ChatSession Session)>(sessionId, owner, tx =>
        {
            if (!tx.Reserve(key, "end"))
            {
                if (tx.OperationState(key) != "not_sent_closed") RequireDeliveryConfirmation(tx, key);
                return (Kind: "none", Session: tx.Session);
            }
            var s = tx.Session;
            if (s.Terminal || s.Status is "closing" or "end_requested")
            {
                if (s.Status == "end_requested") RequireDeliveryConfirmation(tx, "end_request");
                tx.Mark(key, "succeeded");
                return ("none", s);
            }
            if (s.Status == "draft")
            {
                tx.Terminal("closed", "Draft cancelled. No ServiceNow chat was opened.", Now);
                tx.Mark(key, "succeeded");
                return ("none", s);
            }
            if (s.Status is "waiting" or "starting")
            {
                BeginClose(tx, "The support request was cancelled.");
                tx.Mark(key, "succeeded");
                return ("close", s);
            }
            if (!tx.Reserve("end_request", "polite_close"))
            {
                RequireDeliveryConfirmation(tx, "end_request");
                return ("none", s);
            }
            s.Status = "end_requested";
            return ("send", s);
        });
        if (action.Kind == "close") await TryCloseAsync(sessionId);
        if (action.Kind == "send")
        {
            try
            {
                await remote.SendAsync(action.Session,
                    "The employee has asked to end this chat. Please close the conversation when you are finished. Thank you.",
                    RemoteMessageId(sessionId, clientMessageId), CancellationToken.None);
            }
            catch (RemoteChatClosedException)
            {
                AlreadyClosed(sessionId, owner, key);
                store.Update(sessionId, owner, tx => { tx.Mark("end_request", "not_sent_closed"); return 0; });
                return store.View(sessionId, owner);
            }
            catch (Exception)
            {
                AmbiguousMessage(sessionId, owner, key);
                store.Update(sessionId, owner, tx => { tx.Mark("end_request", "ambiguous"); return 0; });
                throw DeliveryUnconfirmed();
            }
            store.Update(sessionId, owner, tx =>
            {
                tx.Mark(key, "succeeded");
                tx.Mark("end_request", "succeeded");
                tx.Session.LastActivityAt = Now;
                tx.Append("status", SystemAuthor, options.Demo.Enabled
                    ? "Demo: the simulator received your end request."
                    : "The representative has been asked to close the chat. Only they close a connected chat, unless it times out.", Now);
                return 0;
            });
            if (options.Demo.Enabled)
                Receive(new("closed", "cowork_mcp", sessionId, action.Session.InteractionNumber!,
                    null, "Demo simulator", null, "demo-closed"));
        }
        return store.View(sessionId, owner);
    }

    /// <summary>Durable commit occurs before HTTP acknowledgement. No SDK callback or transient in-memory delivery.</summary>
    public void Receive(WebhookEvent e)
    {
        if (e.Bot != "cowork_mcp" || e.Event is not ("accepted" or "message" or "closed"))
            throw new ChatException("invalid_event", "The bot or event is not supported.");
        Input.SessionId(e.ClientSessionId);
        Input.Key(e.EventId, "event_id");
        Input.Key(e.InteractionNumber, "interaction_number");
        if (e.MessageSysId is not null) Input.Key(e.MessageSysId, "message_sys_id");
        if (e.Event == "message") Input.Text(e.Text, "text", maxJsonBytes: 48000);
        if (e.AgentName is not null && e.AgentName.Length > 200)
            throw new ChatException("invalid_argument", "agent_name must fit 200 characters.");
        store.Update(e.ClientSessionId, null, tx =>
        {
            var s = tx.Session;
            if (s.Status == "draft") throw new ChatException("not_opened", "This session has not been confirmed.", 409);
            if (s.InteractionNumber is not null && s.InteractionNumber != e.InteractionNumber)
                throw new ChatException("correlation_mismatch", "interaction_number does not match the session.", 409);
            if (!tx.RecordCallback("event:" + e.EventId)) return 0;
            if (e.Event == "message" && e.MessageSysId is not null && !tx.RecordCallback("message:" + e.MessageSysId)) return 0;
            var author = string.IsNullOrWhiteSpace(e.AgentName) ? "Support representative" : e.AgentName;
            if (s.Terminal)
            {
                if (e.Event == "message")
                    tx.Append("late_message", author, e.Text!, Now, language: options.Translator.AgentLanguage);
                return 0;
            }
            s.InteractionNumber ??= e.InteractionNumber;
            if (e.Event is "accepted" or "message")
            {
                s.AcceptedAt ??= Now;
                if (s.Status is not ("end_requested" or "closing")) s.Status = "connected";
                if (!s.JoinAnnounced)
                {
                    s.JoinAnnounced = true;
                    tx.Append("accepted", author, options.Demo.Enabled
                        ? "Demo: connected to a local simulator, not a real support representative."
                        : $"{author} joined the chat.", Now);
                }
            }
            if (e.Event == "message")
            {
                s.LastActivityAt = Now;
                // Persist source before ACK. Optional outbound translation never changes this original agent text.
                tx.Append("message", author, e.Text!, Now, language: options.Translator.AgentLanguage);
            }
            if (e.Event == "closed")
                tx.Terminal("closed", options.Demo.Enabled ? "Demo: the simulator ended the chat." : "The support conversation ended.", Now);
            return 0;
        });
    }

    private void BeginClose(SessionTransaction tx, string reason)
    {
        if (tx.Session.Terminal || tx.Session.Status == "closing") return;
        tx.Session.Status = "closing";
        tx.Session.CloseReason = reason;
        tx.Append("status", SystemAuthor, "Closing the ServiceNow conversation. Closure is not yet confirmed.", Now);
    }

    public async Task SweepAsync(CancellationToken ct = default)
    {
        foreach (var id in store.ActiveIds())
        {
            ct.ThrowIfCancellationRequested();
            var close = store.Update(id, null, tx =>
            {
                var s = tx.Session;
                if (s.Status == "draft")
                {
                    if (Now - s.CreatedAt > TimeSpan.FromMinutes(options.Timeouts.MaxChatDurationMinutes))
                        tx.Terminal("closed", "The unconfirmed draft expired. No ServiceNow chat was opened.", Now);
                    return false;
                }
                string? reason = null;
                if (s.OpenedAt is { } opened && Now - opened >= TimeSpan.FromMinutes(options.Timeouts.MaxChatDurationMinutes))
                    reason = "The maximum chat duration was reached.";
                else if (s.AcceptedAt is null && s.OpenedAt is { } start && Now - start >= TimeSpan.FromMinutes(options.Timeouts.AcceptanceMinutes))
                    reason = "No support representative accepted within the configured waiting period.";
                else if (s.AcceptedAt is not null && Now - s.LastActivityAt >= TimeSpan.FromMinutes(options.Timeouts.InactivityMinutes))
                    reason = "The chat reached the configured inactivity timeout.";
                if (reason is not null) BeginClose(tx, reason);
                return s.Status == "closing";
            });
            if (close) await TryCloseAsync(id);
        }
        store.Cleanup(Now.AddDays(-options.Storage.RetentionDays));
    }

    private async Task TryCloseAsync(string sessionId)
    {
        var closing = store.Update(sessionId, null, tx =>
        {
            var s = tx.Session;
            if (s.Terminal || s.Status != "closing" || s.ConversationId is null || s.CloseRetryAt > Now ||
                tx.OperationState("close") == "requires_reconciliation") return null;
            tx.Reserve("close", "close");
            // Longer than the bounded HTTP timeout; prevents another sweep overlapping this attempt.
            s.CloseRetryAt = Now.AddSeconds(Math.Max(60, options.Timeouts.CloseRetrySeconds));
            return s;
        });
        if (closing is null) return;
        try
        {
            await remote.CloseAsync(closing, "close-" + closing.Id, CancellationToken.None);
        }
        catch (RemoteCommandAmbiguousException)
        {
            store.Update(sessionId, null, tx =>
            {
                tx.Mark("close", "requires_reconciliation");
                tx.Append("error", SystemAuthor,
                    "ServiceNow reports an ambiguous prior close operation. Automatic retries are paused; support must reconcile the existing command key.", Now);
                return 0;
            });
            return;
        }
        catch (Exception)
        {
            store.Update(sessionId, null, tx =>
            {
                if (tx.OperationState("close") != "ambiguous")
                    tx.Append("error", SystemAuthor, "ServiceNow has not confirmed closure. The same close request will be retried; this session is retained.", Now);
                tx.Mark("close", "ambiguous");
                tx.Session.CloseRetryAt = Now.AddSeconds(options.Timeouts.CloseRetrySeconds);
                return 0;
            });
            return;
        }
        store.Update(sessionId, null, tx =>
        {
            tx.Mark("close", "succeeded");
            tx.Terminal("closed", (tx.Session.CloseReason ?? "The chat was ended.") + " Closure is confirmed.", Now);
            return 0;
        });
    }
}

public sealed class TimeoutWorker(ChatService service, BridgeOptions options, ILogger<TimeoutWorker> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(options.Timeouts.ScanSeconds));
        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            try { await service.SweepAsync(stoppingToken); }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { break; }
            catch (Exception) { logger.LogError("Live-chat timeout scan failed; durable sessions remain available for the next scan."); }
        }
    }
}
