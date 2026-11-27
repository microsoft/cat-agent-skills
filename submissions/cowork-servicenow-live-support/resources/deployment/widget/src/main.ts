import { App, type McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import {
  canSend, CLOSED_POLL_INTERVAL, definitelyNotSent, demoAllowed, eventPresentation, isTerminal, mergeSnapshot, nextCallDelay, parseDemoResult, parseToolResult,
  pollDelay, prepareMessage, SerialExecutor, shouldPoll, supportHeader,
  type ChatEvent, type ChatState, type PendingMessage, type Snapshot, type Status,
} from "./state.ts";
import "./styles.css";

const get = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const summaryInput = get<HTMLTextAreaElement>("summary-input");
const messageInput = get<HTMLTextAreaElement>("message-input");
const confirmButton = get<HTMLButtonElement>("confirm-button");
const sendButton = get<HTMLButtonElement>("send-button");
const endButton = get<HTMLButtonElement>("end-button");
const retryButton = get<HTMLButtonElement>("retry-button");
const returnButton = get<HTMLButtonElement>("return-button");
const expandButton = get<HTMLButtonElement>("expand-button");
const confirmEndButton = get<HTMLButtonElement>("confirm-end-button");
const endConfirmation = get<HTMLDialogElement>("end-confirmation");
const transcript = get<HTMLOListElement>("transcript");
const demo = demoAllowed(new URL(location.href), window.parent === window);
const app = new App({ name: "Cowork Human Support", version: "1.0.0" }, {});
const executor = new SerialExecutor();
const rateKey = "cowork-human-support:rate:v1";
let state: ChatState | undefined;
let pendingMessage: PendingMessage | undefined;
let pendingEndId: string | undefined;
let draftSummary = "";
let summaryDirty = false;
let ready = false;
let disposed = false;
let intersecting = true;
let polling = false;
let forcePoll = false;
let failures = 0;
let action: "confirm" | "send" | "end" | undefined;
let pollTimer: ReturnType<typeof setTimeout> | undefined;
let hostTimer: ReturnType<typeof setTimeout> | undefined;
let lastCalls: number[] = [];
let errorKind: "updates" | "action" | "host" | undefined;
let locale: string | undefined;
let timeZone: string | undefined;
let lastSync = "";
let storageAvailable = true;
let hostContext: McpUiHostContext = {};
const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
const visible = () => document.visibilityState !== "hidden" && intersecting;

const labels: Record<Status, string> = {
  draft: "Not shared yet", starting: "Requesting support", waiting: "Waiting for an agent",
  connected: "Support connected", end_requested: "End requested",
  closing: "Closing with support", closed: "Chat closed", unavailable: "Support unavailable", failed: "Support request failed",
};
const descriptions: Record<Status, string> = {
  draft: "",
  starting: "",
  waiting: "",
  connected: "",
  end_requested: "You can still message support until the service confirms closure.",
  closing: "Waiting for final messages and the service’s confirmation.",
  closed: "",
  unavailable: "Try again through Cowork or use your usual IT help channel.",
  failed: "Check the service notice below before trying again through Cowork.",
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The request failed. Please try again.";
}

function announce(message: string): void {
  get("announcements").textContent = message;
}

function storageRead(key: string): unknown {
  try {
    const value = sessionStorage.getItem(key);
    return value ? JSON.parse(value) : undefined;
  } catch {
    storageAvailable = false;
    return undefined;
  }
}

function storageWrite(key: string, value: unknown): void {
  try { sessionStorage.setItem(key, JSON.stringify(value)); }
  catch { storageAvailable = false; }
}

function sessionKey(): string {
  return `cowork-human-support:session:v1:${demo ? "demo:" : ""}${state?.sessionId}`;
}

function persist(): void {
  if (!state) return;
  storageWrite(sessionKey(), {
    draftSummary, summaryDirty, messageDraft: messageInput.value, pendingMessage, pendingEndId,
  });
}

function restore(): void {
  const saved = storageRead(sessionKey()) as Record<string, unknown> | undefined;
  if (!saved || typeof saved !== "object") return;
  if (typeof saved.draftSummary === "string" && saved.summaryDirty === true) {
    draftSummary = saved.draftSummary;
    summaryDirty = true;
  }
  if (typeof saved.messageDraft === "string") messageInput.value = saved.messageDraft;
  if (typeof saved.pendingEndId === "string") pendingEndId = saved.pendingEndId;
  const pending = saved.pendingMessage as Partial<PendingMessage> | undefined;
  if (pending && typeof pending.text === "string" && typeof pending.clientMessageId === "string") {
    pendingMessage = { text: pending.text, clientMessageId: pending.clientMessageId };
    messageInput.value = pending.text;
  }
}

async function reserveCall(): Promise<void> {
  while (!disposed) {
    const stored = storageRead(rateKey);
    const shared = Array.isArray(stored) ? stored.filter((value): value is number => typeof value === "number") : [];
    const now = Date.now();
    lastCalls = [...new Set([...shared, ...lastCalls])].filter(time => time > now - 60_000).sort((a, b) => a - b);
    const delay = nextCallDelay(lastCalls, now);
    if (!delay) {
      lastCalls.push(now);
      storageWrite(rateKey, lastCalls);
      return;
    }
    if (delay > 2_000) get("sync-status").textContent = "Pacing requests to stay within Cowork limits…";
    await wait(Math.min(delay, 1_000));
  }
  throw new Error("This support card has been closed.");
}

async function demoCall(name: string, args: Record<string, unknown>): Promise<unknown> {
  const response = await fetch(`/dev/tools/${encodeURIComponent(name)}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args), signal: AbortSignal.timeout(25_000),
    credentials: "same-origin", redirect: "error",
  });
  if (!response.ok) throw new Error(`Local demo service returned HTTP ${response.status}. No live fallback was used.`);
  return response.json();
}

function callTool(name: string, args: Record<string, unknown>, background = false): Promise<Snapshot> {
  return executor.run(async () => {
    if (disposed || (background && !visible())) throw new Error("Updates paused while the card is hidden.");
    await reserveCall();
    if (disposed || (background && !visible())) throw new Error("Updates paused while the card is hidden.");
    if (demo) return parseDemoResult(await demoCall(name, args));
    return parseToolResult(await app.callServerTool({ name, arguments: args }, { timeout: 25_000 }));
  });
}

function showError(message: string, kind: typeof errorKind = "action"): void {
  errorKind = kind;
  get("error-text").textContent = message;
  get("error-panel").hidden = false;
  retryButton.hidden = kind !== "updates";
  if (kind === "host" && !state) {
    get("status-text").textContent = "Support is not connected";
    get("loading").querySelector("h2")!.textContent = "We couldn’t open support";
    get("loading").querySelector("p")!.textContent = "No live agent connection has been assumed. See the error below for the next step.";
    get<HTMLElement>("loading").querySelector<HTMLElement>(".loading-mark")!.hidden = true;
  }
}

function clearError(kind?: typeof errorKind): void {
  if (kind && errorKind !== kind) return;
  errorKind = undefined;
  get("error-panel").hidden = true;
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  if (!Number.isFinite(date.getTime())) return timestamp;
  try { return new Intl.DateTimeFormat(locale, { hour: "numeric", minute: "2-digit", timeZone }).format(date); }
  catch { return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }); }
}

type EventNode = { element: HTMLLIElement; signature: string };
const eventNodes = new Map<HTMLOListElement, Map<string, EventNode>>();

function createEvent(event: ChatEvent, history = false): HTMLLIElement {
  const item = document.createElement("li");
  item.className = "event";
  item.dataset.presentation = history ? "technical" : eventPresentation(event);
  item.dataset.kind = event.author === "user" ? "user_message" : event.kind;
  const meta = document.createElement("div");
  meta.className = "event-meta";
  const author = document.createElement("span");
  author.className = "event-author";
  author.textContent = event.author === "user" ? "You" :
    event.author === "system" ? "Support service" : event.author || "Support service";
  meta.append(author);
  if (history) {
    const time = document.createElement("time");
    time.dateTime = event.timestamp;
    time.textContent = formatTime(event.timestamp);
    time.title = event.timestamp;
    meta.append(time);
  }
  const text = document.createElement("p");
  text.className = "event-text";
  text.textContent = event.text;
  item.append(meta, text);
  if (event.kind === "late_message") {
    const delayed = document.createElement("p");
    delayed.className = "translation-label";
    delayed.textContent = "Delayed delivery after chat closure";
    item.append(delayed);
  }
  if (event.originalText && event.originalText !== event.text) {
    const label = document.createElement("p");
    label.className = "translation-label";
    label.textContent = "Translated message";
    const details = document.createElement("details");
    details.className = "original";
    const summary = document.createElement("summary");
    summary.textContent = event.language ? `Show original (${event.language})` : "Show original";
    const original = document.createElement("p");
    original.textContent = event.originalText;
    details.append(summary, original);
    item.append(label, details);
  }
  return item;
}

function renderEventList(list: HTMLOListElement, events: ChatEvent[], history = false): boolean {
  let nodes = eventNodes.get(list);
  if (!nodes) {
    nodes = new Map();
    eventNodes.set(list, nodes);
  }
  let changed = false;
  const ids = new Set(events.map(event => event.id));
  for (const [id, node] of nodes) {
    if (!ids.has(id)) {
      node.element.remove();
      nodes.delete(id);
      changed = true;
    }
  }
  for (const [index, event] of events.entries()) {
    const signature = JSON.stringify([event, locale, timeZone]);
    let node = nodes.get(event.id);
    if (!node || node.signature !== signature) {
      const element = createEvent(event, history);
      node?.element.replaceWith(element);
      node = { element, signature };
      nodes.set(event.id, node);
      changed = true;
    }
    const position = list.children[index];
    if (position !== node.element) list.insertBefore(node.element, position ?? null);
  }
  return changed;
}

function renderEvents(): void {
  if (!state) return;
  const atBottom = transcript.scrollHeight - transcript.scrollTop - transcript.clientHeight < 64;
  const conversation = state.events.filter(event => eventPresentation(event) === "conversation");
  const attention = state.events.filter(event => eventPresentation(event) === "attention");
  const changed = renderEventList(transcript, conversation);
  renderEventList(get<HTMLOListElement>("attention-events"), [...attention].reverse());
  renderEventList(get<HTMLOListElement>("technical-events"), state.events, true);
  get("attention-panel").hidden = attention.length === 0;
  get("empty-transcript").hidden = conversation.length > 0;
  if (changed) {
    if (atBottom) scrollToLatest();
    else get("new-messages").hidden = false;
  }
}

function scrollToLatest(): void {
  transcript.scrollTop = transcript.scrollHeight;
  get("new-messages").hidden = true;
}

function render(): void {
  get("loading").hidden = !!state;
  get("review-panel").hidden = !state || state.status !== "draft";
  get("chat-panel").hidden = !state || state.status === "draft";
  if (!state) return;
  get("status-text").textContent = supportHeader(state);
  get("support-app").dataset.status = state.status;
  get("technical-status").textContent = labels[state.status];
  get("interaction-number").textContent = state.interactionNumber ?? "Not assigned";
  if (summaryInput.value !== draftSummary) summaryInput.value = draftSummary;
  summaryInput.disabled = action === "confirm";
  confirmButton.disabled = !ready || !!action || !draftSummary.trim();
  confirmButton.textContent = action === "confirm" ? "Requesting support…" : "Request support";
  get("summary-count").textContent = `${draftSummary.length.toLocaleString()} / 4,000`;
  get("connection-detail").textContent = descriptions[state.status];
  get("connection-detail").hidden = !descriptions[state.status];
  get("shared-summary-text").textContent = state.summary;
  const terminal = isTerminal(state.status);
  get("terminal-note").hidden = !terminal || !state.hasMore;
  get("terminal-note").textContent = "Loading the remaining conversation…";
  get("message-form").hidden = terminal && !pendingMessage && !messageInput.value;
  messageInput.disabled = !canSend(state.status) || action === "send" || !!pendingMessage;
  messageInput.placeholder = state.status === "waiting" || state.status === "starting"
    ? "You can message when support joins." : "Message IT support…";
  sendButton.disabled = !ready || !!action || (!canSend(state.status) && !pendingMessage) || !messageInput.value.trim();
  sendButton.textContent = action === "send" ? "Sending…" : pendingMessage ? "Retry send" : "Send";
  get("message-count").textContent = `${messageInput.value.length.toLocaleString()} / 4,000`;
  get("pending-note").hidden = !pendingMessage || action === "send";
  endButton.hidden = !pendingEndId && (state.status === "draft" || terminal || state.status === "closing" || state.status === "end_requested");
  endButton.disabled = !ready || !!action;
  endButton.textContent = pendingEndId ? "Retry end request" : "End";
  confirmEndButton.disabled = !!action;
  confirmEndButton.textContent = action === "end" ? "Requesting…" :
    state.status === "waiting" || state.status === "starting" ? "Cancel request" : "Request end";
  get<HTMLButtonElement>("keep-chat-button").disabled = !!action;
  retryButton.disabled = polling || !!action || !ready;
  returnButton.hidden = demo || !ready;
  if (!visible()) get("sync-status").textContent = "Updates paused while this card is hidden.";
  else if (terminal && !state.hasMore && !forcePoll) get("sync-status").textContent =
    state.status === "closed" && state.interactionNumber
      ? "Chat closed · Checking for delayed replies every 15 seconds while visible"
      : "Conversation complete · Updates stopped";
  else if (state.status === "draft" && !forcePoll) get("sync-status").textContent = "Private draft · Not sent to a human agent";
  else if (!failures) get("sync-status").textContent = lastSync ? `Updated ${lastSync} · Checks every 4 seconds while visible` : "Checking for support updates…";
  if (!storageAvailable && pendingMessage) {
    get("pending-note").textContent = "Delivery is unconfirmed. Retry here before closing this card; this host blocks saving the retry reference.";
  }
  renderEvents();
}

function applySnapshot(snapshot: Snapshot, fromPoll = false): void {
  if (disposed) return;
  const first = !state;
  const previousStatus = state?.status;
  const existing = new Set(state?.events.map(event => event.id) ?? []);
  state = mergeSnapshot(state, snapshot, fromPoll);
  if (!fromPoll) forcePoll = true;
  if (first) {
    draftSummary = snapshot.summary;
    restore();
  } else if (!summaryDirty && state.status === "draft") {
    draftSummary = snapshot.summary;
  }
  if (fromPoll) lastSync = formatTime(new Date().toISOString());
  render();
  const added = state.events.filter(event => !existing.has(event.id) && eventPresentation(event) !== "technical");
  if (previousStatus !== state.status) announce([supportHeader(state), ...added.filter(event => eventPresentation(event) === "attention").map(event => event.text)].join(". "));
  else if (added.length) announce(`${added.length} new support ${added.length === 1 ? "update" : "updates"}. ${added.at(-1)?.author}: ${added.at(-1)?.text}`);
  persist();
}

function schedulePoll(delay = pollDelay(failures)): void {
  clearTimeout(pollTimer);
  if (!ready || polling || action || !shouldPoll(state, visible(), disposed, forcePoll)) return;
  const interval = state?.status === "closed" && !state.hasMore && !forcePoll
    ? Math.max(delay, CLOSED_POLL_INTERVAL) : delay;
  pollTimer = setTimeout(() => void poll(), interval);
}

async function poll(): Promise<void> {
  if (polling || action || !ready || !shouldPoll(state, visible(), disposed, forcePoll)) return;
  polling = true;
  render();
  try {
    const snapshot = await callTool("get_live_chat_updates", {
      sessionId: state!.sessionId, afterSequence: state!.cursor,
    }, true);
    applySnapshot(snapshot, true);
    failures = 0;
    forcePoll = false;
    clearError("updates");
  } catch (error) {
    if (!disposed && visible()) {
      failures++;
      forcePoll = true;
      showError(`Support updates are interrupted. ${errorMessage(error)} Retrying in ${pollDelay(failures) / 1_000} seconds.`, "updates");
      get("sync-status").textContent = "Connection interrupted · No new messages are being assumed";
    }
  } finally {
    polling = false;
    if (!disposed) {
      render();
      // hasMore is drained one page per interval, including after terminal status. Never spin.
      schedulePoll();
    }
  }
}

function receiveInitialResult(result: unknown): void {
  try {
    const snapshot = parseToolResult(result);
    if (!state) applySnapshot(snapshot);
    else if (state.sessionId !== snapshot.sessionId) throw new Error("Cowork delivered a different support session. Reopen the card.");
    // Replayed host results may be old. Replay the server stream from cursor zero after each mount.
    forcePoll = true;
    clearError("host");
    clearTimeout(hostTimer);
    schedulePoll(0);
  } catch (error) {
    showError(errorMessage(error), "host");
  }
}

function applyHostContext(context: McpUiHostContext): void {
  hostContext = { ...hostContext, ...context };
  if (hostContext.theme === "dark" || hostContext.theme === "light") {
    document.documentElement.dataset.theme = hostContext.theme;
  }
  document.documentElement.dataset.display = hostContext.displayMode === "fullscreen" ? "fullscreen" : "inline";
  if (hostContext.locale) locale = hostContext.locale;
  if (hostContext.timeZone) timeZone = hostContext.timeZone;
  if (hostContext.displayMode) {
    expandButton.setAttribute("aria-label", hostContext.displayMode === "fullscreen" ? "Return support to inline view" : "Expand support to fullscreen");
  }
  if (hostContext.direction === "rtl" || hostContext.direction === "ltr") {
    document.documentElement.dir = hostContext.direction;
  }
  expandButton.hidden = demo || !ready || hostContext.availableDisplayModes?.includes("fullscreen") === false;
  renderEvents();
}

confirmButton.addEventListener("click", async () => {
  if (!state || state.status !== "draft" || action || !ready || !draftSummary.trim()) return;
  action = "confirm";
  clearTimeout(pollTimer);
  clearError();
  const reviewedSummary = draftSummary.trim();
  render();
  try {
    const snapshot = await callTool("confirm_live_chat", { sessionId: state.sessionId, summary: reviewedSummary });
    applySnapshot(snapshot);
    summaryDirty = false;
    if (snapshot.status === "draft") showError("The service did not confirm your support request. Your summary is still a draft.");
    else {
      announce(isTerminal(snapshot.status) ? supportHeader(snapshot) : "Request shared with IT support.");
      get("status-text").focus();
    }
  } catch (error) {
    showError(`Sharing could not be confirmed. ${errorMessage(error)} Your edited summary is preserved. Check updates before retrying if the connection was interrupted.`);
    forcePoll = true;
  } finally {
    action = undefined;
    persist();
    render();
    schedulePoll();
  }
});

summaryInput.addEventListener("input", () => {
  draftSummary = summaryInput.value;
  summaryDirty = true;
  persist();
  render();
});

sendButton.addEventListener("click", async () => {
  if (!state || action || !ready || (!canSend(state.status) && !pendingMessage)) return;
  try { pendingMessage = prepareMessage(pendingMessage, messageInput.value, () => crypto.randomUUID()); }
  catch (error) {
    get("send-error").textContent = errorMessage(error);
    get("send-error").hidden = false;
    return;
  }
  action = "send";
  clearTimeout(pollTimer);
  get("send-error").hidden = true;
  persist();
  render();
  try {
    const snapshot = await callTool("send_live_chat_message", { sessionId: state.sessionId, ...pendingMessage });
    applySnapshot(snapshot);
    pendingMessage = undefined;
    messageInput.value = "";
    announce("Your message was accepted by the support service.");
  } catch (error) {
    if (definitelyNotSent(error)) {
      pendingMessage = undefined;
      get("send-error").textContent = `The message was not sent. ${errorMessage(error)} Your text is preserved.`;
    } else {
      get("send-error").textContent = `Message delivery is unconfirmed. ${errorMessage(error)} Use Retry send; it reuses the same delivery reference.`;
    }
    get("send-error").hidden = false;
    forcePoll = true;
  } finally {
    action = undefined;
    persist();
    render();
    if (!pendingMessage && !messageInput.disabled) messageInput.focus();
    schedulePoll();
  }
});

messageInput.addEventListener("input", () => { persist(); render(); });
messageInput.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!sendButton.disabled) sendButton.click();
  }
});

endButton.addEventListener("click", () => {
  if (!state || action) return;
  const queued = state.status === "waiting" || state.status === "starting";
  get("end-confirm-title").textContent = queued ? "Cancel this support request?" : "Request the end of this chat?";
  get("end-confirm-description").textContent = queued
    ? "We’ll ask the support service to remove you from the queue. Your request is not cancelled until the service confirms."
    : "We’ll ask support to close the conversation. You can still message until the service confirms closure.";
  get<HTMLButtonElement>("keep-chat-button").textContent = queued ? "Keep waiting" : "Keep chatting";
  endConfirmation.showModal();
  get("end-confirm-title").focus();
});
get("keep-chat-button").addEventListener("click", () => {
  endConfirmation.close();
  endButton.focus();
});
endConfirmation.addEventListener("cancel", event => {
  if (action === "end") event.preventDefault();
});
confirmEndButton.addEventListener("click", async () => {
  if (!state || action || !ready) return;
  action = "end";
  pendingEndId ??= crypto.randomUUID();
  clearTimeout(pollTimer);
  clearError();
  persist();
  render();
  try {
    applySnapshot(await callTool("request_end_live_chat", { sessionId: state.sessionId, clientMessageId: pendingEndId }));
    pendingEndId = undefined;
    endConfirmation.close();
    announce("Your end request was received by the support service.");
    get("status-text").focus();
  } catch (error) {
    endConfirmation.close();
    showError(`The end request could not be confirmed. ${errorMessage(error)} Retry uses the same request reference.`);
    forcePoll = true;
  } finally {
    action = undefined;
    persist();
    render();
    schedulePoll();
  }
});

retryButton.addEventListener("click", () => {
  if (polling || action) return;
  forcePoll = true;
  schedulePoll(0);
});
returnButton.addEventListener("click", async () => {
  if (!ready || demo || returnButton.disabled) return;
  returnButton.disabled = true;
  try {
    await executor.run(async () => {
      await reserveCall();
      const result = await app.sendMessage({
        role: "user",
        content: [{ type: "text", text: "I want to continue with Copilot Cowork. Do not close my human support session or share its transcript." }],
      }, { timeout: 25_000 });
      if (result.isError) throw new Error("Cowork could not accept the return request.");
    });
    announce("Asked Copilot to continue. Your human chat was not closed or shared.");
  } catch (error) { showError(errorMessage(error)); }
  finally { returnButton.disabled = false; }
});
expandButton.addEventListener("click", async () => {
  if (!ready || demo || expandButton.disabled) return;
  expandButton.disabled = true;
  try {
    const result = await app.requestDisplayMode({
      mode: hostContext.displayMode === "fullscreen" ? "inline" : "fullscreen",
    });
    applyHostContext({ displayMode: result.mode });
  } catch (error) { showError(`Display mode could not be changed. ${errorMessage(error)}`); }
  finally { expandButton.disabled = false; }
});
get("new-messages").addEventListener("click", () => { scrollToLatest(); transcript.focus(); });
transcript.addEventListener("scroll", () => {
  if (transcript.scrollHeight - transcript.scrollTop - transcript.clientHeight < 64) get("new-messages").hidden = true;
});

function visibilityChanged(): void {
  clearTimeout(pollTimer);
  render();
  if (visible()) schedulePoll();
}
document.addEventListener("visibilitychange", visibilityChanged);
const observer = new IntersectionObserver(entries => {
  intersecting = entries.some(entry => entry.isIntersecting);
  visibilityChanged();
});
observer.observe(get("support-app"));

function teardown(): void {
  persist();
  disposed = true;
  clearTimeout(pollTimer);
  clearTimeout(hostTimer);
  observer.disconnect();
  document.removeEventListener("visibilitychange", visibilityChanged);
}
window.addEventListener("pagehide", teardown);
window.addEventListener("pageshow", event => {
  if (event.persisted) location.reload();
});

// Cowork can deliver the tool result during connect, so every handler is registered first.
app.ontoolinput = ({ arguments: args }) => {
  if (!state && typeof args?.summary === "string") draftSummary = args.summary;
};
app.ontoolresult = receiveInitialResult;
app.ontoolcancelled = () => showError("Cowork cancelled the support tool. No agent connection has been assumed. Ask Cowork to reopen human support.", "host");
app.onhostcontextchanged = applyHostContext;
app.onteardown = async () => { teardown(); return {}; };
app.onerror = error => {
  if (!disposed) showError(`The Cowork connection reported an error. ${errorMessage(error)}`, "host");
};

async function start(): Promise<void> {
  if (demo) {
    get("demo-banner").hidden = false;
    try {
      const response = await fetch("/dev/mode", { signal: AbortSignal.timeout(10_000), redirect: "error" });
      if (!response.ok) throw new Error("The loopback development mode endpoint is not enabled.");
      const mode = await response.json();
      if (mode.enabled !== true || mode.mode !== "demo") throw new Error("The server did not explicitly confirm demo mode.");
      ready = true;
      const stored = storageRead("cowork-human-support:demo-request");
      const requestId = typeof stored === "string" ? stored : crypto.randomUUID();
      storageWrite("cowork-human-support:demo-request", requestId);
      receiveInitialResult({ structuredContent: await callTool("start_live_chat", {
        summary: "I can’t connect to the company VPN. I’ve restarted my laptop and checked my internet connection, but the connection still times out. Please help me get connected.",
        language: "en", requestId,
      }) });
      schedulePoll(0);
    } catch (error) {
      ready = false;
      showError(`Demo unavailable. ${errorMessage(error)} No simulated or live fallback was started.`, "host");
    }
  } else {
    if (window.parent === window) {
      showError("Open this support card inside Copilot Cowork. Local testing requires an explicit loopback ?demo=1 URL and an enabled Development backend.", "host");
      get("sync-status").textContent = "Not connected to an MCP App host";
      return;
    }
    try {
      await app.connect(undefined, { timeout: 20_000 });
      if (disposed) return;
      ready = true;
      applyHostContext(app.getHostContext() ?? {});
      if (!state) hostTimer = setTimeout(() => {
        if (!state) showError("Cowork did not provide a support session. Reopen human support; the initial tool result may have failed or exceeded the host’s size limit.", "host");
      }, 20_000);
      schedulePoll(0);
    } catch (error) {
      showError(`Could not connect to Cowork. ${errorMessage(error)} Reopen this support card.`, "host");
    }
  }
  render();
}

void start();
