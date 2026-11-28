# PowerPoint Transitions

Make a product photo grow from a sidebar into a detail view, carry its label along with it, or use a short fade when a chapter ends. The output is a **new, editable `.pptx`** with native PowerPoint effects, not a video.

## Try it in Cowork

Upload the complete skill ZIP through **Plugins > Add > Upload** (called **Customize** in some clients). Start a fresh task, select the installed skill, attach a copy of a `.pptx`, and say: **"Give this deck better transitions."** The skill asks which mode you want unless you've already specified one:

| Mode | What happens |
|---|---|
| Classic transitions only | Apply a handpicked Fade, Push, Wipe, None, or single-object Morph without scanning for matches. |
| Matched objects only | Compare adjacent slides for moving, resizing, or rotating pictures and shapes. Use Morph on selected pairs; leave transitions elsewhere alone. |
| Both | Use matched-object Morph where appropriate and classic transitions at other destinations. |

For a first run, try **"Matched objects only. Follow the product photo and its caption; skip ambiguous matches. Return an editable copy."** Start Slide Show on the slide **before** the change to see the motion.

## What it needs

The bundled Python 3.9+ editor uses only the standard library, makes no network requests, and refuses to overwrite an existing output. The host needs access to the attached deck and the bundled script, plus a way to return binary files. PowerPoint's own transition controls can be used if the host exposes them. Without a file writer the skill returns a **plan only**; an installation or text response does not prove a deck was edited.

The matcher looks for identity evidence such as a unique text label or identical embedded picture. It doesn't guess between repeated icons, find separate objects inside one screenshot, or add animations that run within a slide. Use **None** for zero motion. The skill preserves existing advance settings on edits.

## Tested in Cowork

On November 28, 2026, Cowork imported the CAT-generated ZIP, invoked the installed custom skill on a synthetic four-slide presentation, and offered all three modes before making changes. With **Matched objects only**, it returned a new `.pptx`. The input and output package-content fingerprints computed in Cowork matched an independent local run of the packaged editor. The picture and its caption were bound separately across slides 1–3, slides 2 and 3 received an 800 ms native Morph with Fade fallback, and slide 4 was unchanged. This verifies file delivery and structure; it is not a visual playback test in Cowork.

The author also reports testing in Copilot in PowerPoint. Cowork is the only CAT host claimed for this submission; Copilot Studio and Scout have not been validated with this package.

## Reproduce the local checks

The [source and four regression tests](https://github.com/OfirGavish/copilot-skills/tree/34c22d77bc5cd038cae3546445e420bf677ef1cc/.github/skills/powerpoint-transitions) include a synthetic four-slide fixture. Tests cover one-to-one matching, ambiguous and static objects, consecutive Morph transitions, mode isolation, hidden slides, and unchanged package parts. Test-only fixture creation requires `python-pptx` and Pillow; the installed editor does not.

In that fixture, the first two slide changes each have two eligible pairs: a picture moves and resizes, and a box labeled **Forecast** moves and rotates. In matched-only mode, slide 4 should remain unchanged. Testing Copilot in PowerPoint or rendering the deck locally is separate from verifying skill activation, execution and file delivery in a CAT host.
