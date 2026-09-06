---
name: action-items-todo
description: >-
  Use this skill whenever the user asks to monitor, capture, or track action
  items directed at them across Microsoft Teams chats, meeting transcripts, and
  Outlook mail, and record them as Microsoft To Do tasks — e.g. "set up action
  item tracking", "monitor my action items", "capture asks into To Do", "scan
  for action items now", "what did people ask me to do". Run the SETUP wizard
  first when no config exists; it asks for the To Do list, scan frequency, and
  schedule, then creates the recurring automation. Also handles the follow-up
  commands "scan now", "status", "pause", "resume", and "reconfigure".
---

:: ACTION ITEMS TO MICROSOFT TO DO ::
Monitors Teams chats, meeting transcripts, and Outlook mail for action items EXPLICITLY directed at the user, and captures each one as a Microsoft To Do task with a due date, importance, and owner tagging. Microsoft To Do is the only task store this skill writes to.

Nothing about the user (name, email, list name, schedule, customer and workstream names) is hardcoded. Everything lives in the config file written by SETUP.

== FILES ==
Both live in the user's home directory, so write them with the platform's own separator and never hardcode a Windows path:
- CONFIG: <user home>/.scout/action-items-todo/config.json
- STATE (dedupe + last scan): <user home>/.scout/action-items-todo/state.json
Resolve <user home> at runtime (Node os.homedir(), $HOME, or %USERPROFILE% on Windows). Create the directory if missing. Write both files as UTF-8 JSON, atomically (temp file then rename). Always preserve unknown fields.

== CONFIG SCHEMA ==
{
  "version": 1,
  "identity": { "displayName": str, "mail": str, "upn": str, "aadId": str },
  "listName": str,                  // the Microsoft To Do list tasks are written to
  "frequency": str,                 // natural-language interval, e.g. "every 30 minutes"
  "schedule": "24/7" | "weekdays-allhours" | "workhours" | str,
  "timeZone": str,                  // IANA zone name, e.g. "Europe/Berlin"
  "language": "en",                 // task titles are always written in this language
  "owners": { "customers": [str], "workstreams": [str] },   // optional, may be empty
  "excludedChats": [str],           // chat/channel names to always ignore
  "notifyTeams": bool,              // send a Teams self-message when items are captured
  "automationId": str|null,
  "setupCompleted": ISO8601|null
}

== STATE SCHEMA ==
{ "last_scan": ISO8601,
  "seen": [ { "key": str, "title": str, "created": ISO8601, "source": "teams"|"transcript"|"email", "url": str|null } ] }
"key" is a stable hash of source + thread/message id. Keep the last 500 entries; drop older ones.

== SETUP (first run, or on demand) ==
Run SETUP automatically whenever CONFIG is missing or setupCompleted is null. Never run a scan before SETUP completes.

1. Call workiq_get_my_profile and fill identity. If it fails, say so and stop; the skill cannot target asks without knowing who the user is.
2. Read the machine time zone as an IANA name with a cross-platform runtime API: Intl.DateTimeFormat().resolvedOptions().timeZone, e.g. `node -p "Intl.DateTimeFormat().resolvedOptions().timeZone"`. Do NOT use PowerShell Get-TimeZone: on Windows it returns a Windows zone ID such as "W. Europe Standard Time", which is not an IANA name and will not match the format the rest of the skill expects. If the lookup fails, ask the user for their IANA zone rather than guessing.
3. Read the user's existing lists with workiq_list_task_lists, then ask QUESTION 1 with m_ask_user, free-text mode, inputHint "list name, e.g. Work":
   "Which Microsoft To Do list should captured action items go into?"
   Show the existing list names in the assistant message BEFORE the call so the user can pick one or name a new one. After the reply: if the list does not exist, confirm creation, then workiq_create_task_list.
4. Ask QUESTION 2 with m_ask_user, multiple choice, recommended index 1:
   "How often should I scan for new action items?"
   Answers: "Every 15 minutes" / "Every 30 minutes" / "Every hour" / "Every 2 hours".
   Store the matching natural-language interval in frequency.
5. Ask QUESTION 3 with m_ask_user, multiple choice, recommended index 0:
   "When should the scan run?"
   Answers:
     - "Around the clock, every day" (desc: best when you work across time zones) -> schedule "24/7"
     - "Around the clock, weekdays only" -> "weekdays-allhours"
     - "Working hours only, weekdays" (desc: 8am-6pm in your local time zone) -> "workhours"
     - "Let me describe it" -> free-text follow-up, stored verbatim.
6. Ask nothing else. Default the remaining config: language "en", owners empty, excludedChats empty, notifyTeams true.
7. Write CONFIG and an empty STATE with last_scan = now minus one frequency interval.
   Do NOT seed last_scan further back to "catch up". The first run would then backfill items that were already handled or already completed elsewhere, and create tasks for them. A short first window is correct.
8. Create the automation with m_create_automation, then store its id in automationId:
   - name: "Action Items to To Do"   // avoid > and < in the name; they get HTML-escaped in the automation list
   - schedule: derived from frequency + schedule (see SCHEDULE MAPPING)
   - teamsNotify: "auto"
   - prompt: "Load the action-items-todo skill with m_get_skill and run the SCAN procedure exactly as written. Output only the strict result format the skill defines."
9. Confirm back in one short block: list name, frequency, schedule, automation id, and how to change any of them ("run /action-items-todo setup again").

== SCHEDULE MAPPING ==
The scheduler parses a fixed set of forms. A minute interval CANNOT be combined with an hour window in natural language, so the working-hours case must use cron.
- "24/7"              -> "<frequency>"                e.g. "every 30 minutes"
- "weekdays-allhours" -> "<frequency> on weekdays"    e.g. "every 30 minutes on weekdays"
- "workhours"         -> cron, built from the interval:
                           every 15 minutes -> "cron: 0,15,30,45 8-17 * * 1-5"
                           every 30 minutes -> "cron: 0,30 8-17 * * 1-5"
                           every hour       -> "cron: 0 8-17 * * 1-5"
                           every 2 hours    -> "cron: 0 8,10,12,14,16 * * 1-5"
- custom              -> pass the user's phrasing through; if m_create_automation rejects it, show the supported_forms list it returns and ask the user to pick one.
All schedules run in machine-local time. Verify the automation was actually created: m_create_automation returns success:false with a supported_forms list when it cannot parse the schedule, and SETUP must not report success in that case.

== SCAN (what the automation runs) ==
Load CONFIG first. If it is missing, output AUTOMATION_ERROR|setup not completed and stop.
Scan window: from state.last_scan to now. If last_scan is missing or older than 24h, scan the trailing 24h.

Sources, all three every run:
(a) TEAMS CHATS — workiq_list_chats, then workiq_list_chat_messages on candidates.
(b) MEETING TRANSCRIPTS — workiq_list_meetings for meetings that ended inside the window, then workiq_list_meeting_transcripts and workiq_get_meeting_transcript. Transcripts for a recurring series come back out of order: filter transcripts[] by createdDateTime to the target meeting date, never take transcripts[0].
(c) OUTLOOK MAIL — workiq_list_emails on the Inbox for the window.

=== TEAMS RECENCY RULE (apply before targeting) ===
Do NOT use a chat's lastUpdatedDateTime or the default chat-list order to judge recency. Graph frequently fails to advance lastUpdatedDateTime on 1:1 chats, so a chat with a brand-new message can look a month stale.
- Rank and window chats by lastMessagePreview.date, which is authoritative.
- Always open any 1:1 chat where lastMessagePreview.date is later than viewpoint.lastMessageReadDateTime, or falls inside the scan window.
- Read the whole recent thread, not just the message naming the user. The ask often sits in a follow-up that does not repeat the name.

=== TARGETING RULE ===
An action item is anything asking the user to do, decide, respond, review, attend, prepare, or follow up. Soft and future-dated asks count ("when you have time, could you look at this?"). Urgency is NOT required.
Capture ONLY when the ask is specifically for the user:
- The activity names the user (display name, first name, or mail from identity) or uses a proper Teams @mention of them, OR the surrounding context clearly assigns the action to them.
- A 1:1 Teams chat always satisfies the context test: any genuine ask there is directed at the user even without their name.
- In a meeting transcript, capture only when someone assigns the item to the user by name, or the user is the clear owner from the immediately surrounding exchange. Do not capture the user's own statements about what they will do; this skill tracks asks TO the user.
- Do NOT capture generic group asks, broad team requests, messages addressed to "Everyone"/"Tutti"/a channel/a whole group, status updates, FYIs, newsletters, or notifications.
- Do NOT infer ownership from topic area, past participation, or the fact the user could help. There must be a specific ask.
- Skip any chat or channel named in config.excludedChats.

=== LANGUAGE RULE ===
Task titles and bodies are ALWAYS written in config.language (default English), regardless of the source language. Translate the gist into a clear, concise imperative title. Never copy foreign-language phrasing verbatim.

=== URGENCY -> IMPORTANCE ===
- high: incident, blocker, escalation, customer-impacting issue, explicit urgent/ASAP language, or a deadline inside the next two days.
- normal: a standard direct request with no specific deadline. This is the default.
- low: a soft, tentative, optional, or clearly far-future ask ("eventually", "no rush", "when you get a chance").

=== DUE DATE ===
- Explicit or clearly implied deadline ("by Friday", "before the review") -> that date, YYYY-MM-DD.
- Otherwise -> today's date in config.timeZone.
Always set a due date; never omit it.

=== OWNER TAGGING ===
To Do has no custom fields, so ownership goes in the task body as a metadata block above the summary, at most ONE line:
  Customer: <Name>
or
  Workstream: <Name>
Rules:
- If config.owners lists customers or workstreams, match against those exact names only, including obvious variants the thread supports.
- If config.owners is empty, you may infer a customer or project name that is stated plainly in the thread. Only use a name that actually appears in the source.
- Topic overlap is not ownership. Never invent a name.
- If a task touches both a customer and a workstream, prefer Customer.
- When the evidence is thin, leave the block off. An untagged task is easy to fix; a wrongly tagged one hides.

=== TASK BODY FORMAT ===
  [optional owner line]
  <one-sentence summary of the ask, in config.language>
  Source: <deep link to the Teams message / meeting / email, when available>

=== WRITE PROCEDURE, per captured item ===
1. Dedupe twice: check state.seen for the item key, and call workiq_list_tasks on config.listName for an open task with the same title. Skip if either matches.
2. workiq_create_task with list = config.listName, the English title, due, importance, and body.
3. If the list is missing, recreate it with workiq_create_task_list under the exact configured name and retry once.
4. Append the item to state.seen.
5. After all items, set state.last_scan = now and write STATE atomically. Write STATE even on a run with no items, so the window advances.

=== NOTIFICATION ===
If config.notifyTeams is true AND at least one task was created this run, send ONE Teams self-message listing each captured item: source, importance, owner (or "unassigned"), summary, link. Send nothing on a run that captured nothing.

=== OUTPUT FORMAT, STRICT ===
The final output is exactly one of these, with no preamble, narration, or progress commentary:
(A) one line per captured item:
    ACTION_ITEM|<source>|<importance>|<owner or ->|<summary>|<url>
(B) the single token:
    SILENT_NO_ACTION_ITEMS
(C) on a tool or permission failure:
    AUTOMATION_ERROR|<what was blocked and why>

Presentation rule for the assistant rendering the result: if the output is SILENT_NO_ACTION_ITEMS, or contains no ACTION_ITEM and no AUTOMATION_ERROR line, render a completely empty response. No heading, no acknowledgement, no "nothing found" message.

== ON-DEMAND COMMANDS ==
- "setup" / "reconfigure" -> re-run SETUP, keeping existing answers as the recommended defaults, then update the automation with m_update_automation instead of creating a duplicate.
- "scan now" -> run SCAN once, immediately, and report the items in a readable list rather than the strict format.
- "status" -> print the current config, last scan time, and the number of items captured in the last 7 days.
- "pause" / "resume" -> m_update_automation with enabled false/true.

== PRIVACY ==
Everything this skill writes stays in the user's own Microsoft To Do and their own Teams self-chat. It never sends a message to a third party, never forwards source content, and never posts to a group chat or channel.
