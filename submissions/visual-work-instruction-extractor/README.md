# Visual Work Instruction Extractor

Use this skill when work instructions are stored in PDFs whose photos, diagrams, callouts, warnings, and step text need to remain connected. It works from rendered page evidence, so it can handle scanned, flattened, and mixed-layout documents without relying on embedded PDF image objects or fixed templates.

## What it produces

- Full-page PNG evidence for every processed page
- Evidence crops that retain labels, arrows, warnings, or nearby instruction text
- Optional clean photo or diagram crops when the association is unambiguous
- A normalized manifest containing steps, components, tools, materials, part numbers, warnings, provenance, and review status
- A human-readable summary and validated ZIP archive

The skill deliberately marks uncertain or safety-sensitive results for review instead of guessing. Every instruction retains a full-page fallback.

## Requirements

The skill can use native PDF and image capabilities supplied by the agent runtime. Its optional helper requires Python 3.10 or later. Rendering requires `pypdfium2` and `Pillow`; manifest validation and packaging do not.

Install the optional libraries with:

```text
python -m pip install pypdfium2 Pillow
```

## Example requests

- Extract the visual work instructions and instruction photos from this PDF.
- Turn this scanned maintenance guide into steps with safety warnings and evidence crops.
- Package the components, part numbers, tools, and photos from this work document for use by another agent.

## Privacy

Source documents and extracted images stay within approved runtime storage. The skill instructs the agent not to publish files, use unapproved external services, expose hidden metadata, or include unrelated personal data.