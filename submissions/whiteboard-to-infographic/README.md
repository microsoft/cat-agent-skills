# Whiteboard to Infographic

Turn a photo of a hand-drawn whiteboard or a rough process/system sketch from a
discovery or working session into a polished, client-ready infographic. The
skill does the hard part - reading the handwriting correctly and choosing the
right structure - then builds a consistent, branded one-page layout you can put
straight in front of a client.

## What it does

Point the agent at a whiteboard photo (or a sketched diagram / captured session
notes) and ask to "clean it up," "make it presentable," or "turn it into an
infographic." It transcribes everything on the board, confirms its reading with
you *before* drawing anything, and builds one of two layouts:

- **Process rail** - a left-to-right numbered flow for sketches with a clear
  sequence (step 1 -> step 2 -> ...).
- **Network map** - a topology of locations, systems, or actors connected by
  labeled flows, for sketches with no single linear order.

The output is a polished single-slide PowerPoint (`.pptx`) infographic, returned
as a download link.

## What makes it different

It is faithful by design. It builds only what is on the board - it never invents
steps, fields, or connections to make the picture look complete, and it keeps
the client's exact terms and acronyms. Anything it can't read is surfaced as a
question, not silently dropped. It is not a chart generator: it works from a
sketch, not from a numeric dataset.

## How to use it

1. Add the skill to your Copilot Studio agent.
2. Upload a whiteboard photo - crop tightly; legible handwriting helps.
3. Review the transcription the agent sends back and correct any misreads.
4. Provide a color palette, or ask the skill to suggest one - the palette is
   client-specific and is not baked into the skill.
5. Download the generated `.pptx` and iterate as needed.

## Requirements

The infographic is generated natively inside the agent's Python container
(`python-pptx`) and returned as a downloadable file - no custom connectors,
external services, or tenant-specific infrastructure are required.

## Known limitations

Image input and file download don't currently work on the **Microsoft 365
Copilot channel**. An uploaded image appears to send but never reaches the
agent, and the agent can't return a file for download. Microsoft documents this
on the Microsoft 365 Copilot Extensibility known-issues list for custom engine
agents; there is no published ETA.

Use the **Copilot Studio test pane** or the **Teams channel**, where both the
image upload and the `.pptx` download work as expected.

## Tips

- Give it the messiest capture you have - the interpretation-first discipline is
  where it earns its keep.
- Use the accent "GAP" and "need details" flags to mark fit/gap items and open
  follow-ups; include the one-line legend it generates.
- Ask for a "detailed companion" version alongside the clean executive version
  when a working session produced a lot of margin notes.

## Author

Andy Zehr - [Andy Zehr | LinkedIn](https://www.linkedin.com/in/andyzehr)