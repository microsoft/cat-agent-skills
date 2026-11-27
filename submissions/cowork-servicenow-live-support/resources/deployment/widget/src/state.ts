export const STATUSES = [
  "draft", "starting", "waiting", "connected", "end_requested",
  "closing", "closed", "unavailable", "failed",
] as const;
export type Status = typeof STATUSES[number];
export type ChatEvent = {
  id: string;
  sequence: number;
  kind: string;
  author: string;
  text: string;
  timestamp: string;
  originalText?: string;
  language?: string;
};
export type Snapshot = {
  sessionId: string;
  status: Status;
  summary: string;
  interactionNumber: string | null;
  events: ChatEvent[];
  nextCursor: number;
  hasMore: boolean;
};
export type ChatState = Snapshot & { cursor: number };
export type PendingMessage = { clientMessageId: string; text: string };
export const POLL_INTERVAL = 4_000;
export const CLOSED_POLL_INTERVAL = 15_000;
export const MAX_CALLS_PER_MINUTE = 40;
export const MIN_CALL_GAP = 1_500;
export const MAX_TEXT_LENGTH = 4_000;

export class ToolError extends Error {
  readonly code: string;
  constructor(message: string) {
    super(message);
    this.name = "ToolError";
    this.code = message.match(/^([a-z_]+):/)?.[1] ?? "unknown";
  }
}

export function definitelyNotSent(error: unknown): boolean {
  return error instanceof ToolError &&
    ["invalid_argument", "invalid_state", "not_found", "chat_closed_not_sent"].includes(error.code);
}

function object(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function integer(value: unknown): value is number {
  return Number.isSafeInteger(value) && (value as number) >= 0;
}

export function parseSnapshot(value: unknown): Snapshot {
  if (!object(value) || typeof value.sessionId !== "string" || !value.sessionId ||
      !STATUSES.includes(value.status as Status) || typeof value.summary !== "string" ||
      !(value.interactionNumber == null || typeof value.interactionNumber === "string") ||
      !Array.isArray(value.events) || !integer(value.nextCursor) || typeof value.hasMore !== "boolean") {
    throw new Error("The support service returned an invalid session. Please retry.");
  }
  const events = value.events.map((event: unknown): ChatEvent => {
    if (!object(event) || typeof event.id !== "string" || !event.id || !integer(event.sequence) ||
        typeof event.kind !== "string" || typeof event.author !== "string" ||
        typeof event.text !== "string" || typeof event.timestamp !== "string" ||
        (event.originalText != null && typeof event.originalText !== "string") ||
        (event.language != null && typeof event.language !== "string")) {
      throw new Error("The support service returned an invalid transcript event. Please retry.");
    }
    return {
      ...event,
      originalText: typeof event.originalText === "string" ? event.originalText : undefined,
      language: typeof event.language === "string" ? event.language : undefined,
    } as ChatEvent;
  });
  return { ...value, interactionNumber: value.interactionNumber ?? null, events } as Snapshot;
}

export function parseToolResult(result: unknown): Snapshot {
  if (!object(result)) throw new Error("The support service returned no result.");
  const content = Array.isArray(result.content) ? result.content : [];
  const texts = content.filter((item): item is { type: string; text: string } =>
    object(item) && item.type === "text" && typeof item.text === "string");
  if (result.isError) {
    const error = object(result.structuredContent) ? result.structuredContent : {};
    throw new ToolError(typeof error.message === "string" ? error.message :
      texts.map(item => item.text).join("\n") || "The support service could not complete this request.");
  }
  if (result.structuredContent !== undefined) return parseSnapshot(result.structuredContent);
  for (const { text } of texts) {
    try { return parseSnapshot(JSON.parse(text)); } catch { /* Try the next text block. */ }
  }
  throw new Error("The support service returned no readable session data. Please retry.");
}

export function parseDemoResult(result: unknown): Snapshot {
  if (object(result) && !result.isError && typeof result.sessionId === "string") {
    return parseSnapshot(result);
  }
  return parseToolResult(result);
}

export function mergeEvents(existing: readonly ChatEvent[], incoming: readonly ChatEvent[]): ChatEvent[] {
  const byId = new Map(existing.map(event => [event.id, event]));
  for (const event of incoming) byId.set(event.id, event);
  const bySequence = new Map<number, ChatEvent>();
  for (const event of byId.values()) bySequence.set(event.sequence, event);
  return [...bySequence.values()].sort((a, b) => a.sequence - b.sequence);
}

export function mergeSnapshot(current: ChatState | undefined, snapshot: Snapshot, isPoll: boolean): ChatState {
  if (current && current.sessionId !== snapshot.sessionId) {
    throw new Error("The support service returned a different session. Reopen this support card.");
  }
  // Mutation results can contain only a recent page. Only the ordered poll stream advances the cursor.
  const cursor = current?.cursor ?? 0;
  if (isPoll && snapshot.hasMore && snapshot.nextCursor <= cursor) {
    throw new Error("Transcript updates stopped advancing. Retrying without skipping messages.");
  }
  return {
    ...snapshot,
    events: mergeEvents(current?.events ?? [], snapshot.events),
    cursor: isPoll ? Math.max(cursor, snapshot.nextCursor) : cursor,
  };
}

export function isTerminal(status: Status): boolean {
  return status === "closed" || status === "unavailable" || status === "failed";
}

export type EventPresentation = "conversation" | "technical" | "attention";

export function eventPresentation(event: ChatEvent): EventPresentation {
  if (["error", "unavailable", "translation"].includes(event.kind)) return "attention";
  if (["status", "accepted", "closed"].includes(event.kind)) return "technical";
  if (event.kind === "late_message") return "conversation";
  if (event.kind === "message" && event.author && event.author !== "system") return "conversation";
  // Unknown service updates stay visible rather than concealing a possible next step.
  return "attention";
}

export function supportHeader(state: Pick<Snapshot, "status" | "events">): string {
  const labels: Record<Status, string> = {
    draft: "IT support",
    starting: "Requesting support",
    waiting: "Waiting for support",
    connected: "IT support",
    end_requested: "End requested",
    closing: "Support is closing the chat",
    closed: "Chat ended",
    unavailable: "Support unavailable",
    failed: "Support request failed",
  };
  if (state.status !== "connected") return labels[state.status];
  const agent = [...state.events].reverse().find(event =>
    ["message", "accepted"].includes(event.kind) &&
    event.author.trim() && !["user", "system"].includes(event.author));
  return agent ? `${agent.author} · IT support` : labels.connected;
}

export function canSend(status: Status): boolean {
  return status === "connected" || status === "end_requested";
}

export function shouldPoll(state: ChatState | undefined, visible: boolean, disposed: boolean, force = false): boolean {
  return !disposed && visible && !!state &&
    (force || state.hasMore || (state.status === "closed" && state.interactionNumber !== null) ||
      (state.status !== "draft" && !isTerminal(state.status)));
}

export function pollDelay(failures: number): number {
  return Math.min(60_000, POLL_INTERVAL * 2 ** Math.min(Math.max(failures, 0), 4));
}

export function nextCallDelay(timestamps: readonly number[], now: number): number {
  const recent = timestamps.filter(time => time > now - 60_000 && time <= now);
  const gap = recent.length ? Math.max(0, recent[recent.length - 1] + MIN_CALL_GAP - now) : 0;
  const budget = recent.length >= MAX_CALLS_PER_MINUTE ? recent[recent.length - MAX_CALLS_PER_MINUTE] + 60_001 - now : 0;
  return Math.max(gap, budget, 0);
}

export function prepareMessage(pending: PendingMessage | undefined, text: string, createId: () => string): PendingMessage {
  const trimmed = text.trim();
  if (!trimmed || trimmed.length > MAX_TEXT_LENGTH) throw new Error(`Enter a message of 1–${MAX_TEXT_LENGTH.toLocaleString()} characters.`);
  if (pending && pending.text !== trimmed) {
    throw new Error("Retry the unconfirmed message first. Editing it could create a duplicate delivery.");
  }
  return pending ?? { clientMessageId: createId(), text: trimmed };
}

export class SerialExecutor {
  private tail: Promise<unknown> = Promise.resolve();

  run<T>(operation: () => Promise<T>): Promise<T> {
    const result = this.tail.then(operation);
    this.tail = result.catch(() => undefined);
    return result;
  }
}

export function demoAllowed(url: URL, isTopLevel: boolean): boolean {
  return isTopLevel && url.searchParams.get("demo") === "1" &&
    (url.protocol === "http:" || url.protocol === "https:") &&
    ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
}
