# Podcast Script Generator

Turn a topic — or a pile of source material like a newsletter, a news digest, or
a set of articles — into a two-host podcast episode that actually sounds like
two people talking. You get a readable transcript, a multi-voice SSML document,
and optionally a narrated `.wav`.

## What you get

- **Two recurring hosts with distinct personalities.** *Nova* is the warm, quick
  lead host who asks the question you're thinking. *Miles* is the dry, precise
  analyst who supplies the numbers and the caveats. They talk to each other, not
  at the microphone — no narrator voice, no "welcome to the podcast".
- **Real editorial judgement on source material.** Feed it a digest and it
  parses out each distinct item, merges duplicates, throws away footers and
  unsubscribe boilerplate, ranks what's left by newsworthiness, gives the top
  4–6 full segments, and sweeps the rest into a rapid-fire round.
- **Conversational dialogue, not read-aloud prose.** Short lines, contractions,
  genuine reactions, one concrete analogy per complex idea, and a naive
  clarifying question whenever something needs unpacking.
- **TTS-ready output.** Numbers and acronyms are spelled out the way a
  synthesizer needs them, and the SSML uses one `<voice>` per turn with per-line
  prosody so the delivery never goes flat.

## Before you start

- **Copilot Studio** — this skill targets the Copilot Studio Python/Linux
  container and writes into `/app/created/`.
- **Azure Text-to-Speech connector** — the audio step calls the
  `ConverttexttospeechwithSSML` tool. Add it to your agent (Actions → Add an
  action → Azure Text to Speech) before asking for audio. Without it you still
  get the transcript and the SSML file; only the narration step is skipped.
- **Multi-voice SSML** — the default cast uses `en-US-AvaMultilingualNeural` and
  `en-US-AndrewMultilingualNeural`. Your Speech resource needs access to those
  neural voices.

## How to use it

Paste or point at your material and ask:

> Here's this week's AI newsletter. Make it a six-minute podcast and give me the
> audio.

> Turn these five articles into a Nova and Miles episode, short version.

Or skip the source material entirely and just give it a topic:

> Do a twelve-minute episode on the history of submarines.

The agent will parse and rank the material, write the transcript to
`/app/created/<slug>_Podcast_Script.txt` and the SSML to
`/app/created/<slug>_Podcast.ssml`, show you a segment-by-segment summary, then
offer to narrate it into `/app/created/<slug>_Podcast.wav`.

## Good to know

- **Length is a real target, not a suggestion.** Everything is budgeted at ~150
  spoken words per minute and the agent aims to land within 10 percent. Six
  minutes is roughly 900 words of dialogue.
- **It won't invent opinions.** Reactions to facts are fair game ("that number
  is wild"); made-up takes on people, companies, or politics are not. Unconfirmed
  claims get flagged out loud on air.
- **Two files, two audiences.** The `.txt` transcript carries `NOVA:` / `MILES:`
  labels so you can read along. The `.ssml` is the machine artifact — nothing
  but the SSML document, ready to hand straight to the TTS connector.
- **Long episodes and the 40k character cap.** The SSML is kept under 40,000
  characters. If an episode is too big for one synthesis call, the agent splits
  at a segment boundary and stitches the audio back together.
- **Customising the cast.** Ask for different voices, different names, or a
  single host and it'll adapt — the Nova/Miles pairing is just the default.
- **Non-English material.** Foreign names and phrases inside an English line get
  wrapped in a `<lang>` tag so they're pronounced properly. For a fully
  non-English episode, say so and specify matching neural voices.
