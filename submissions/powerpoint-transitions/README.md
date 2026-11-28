# PowerPoint Transitions

Make a product photo grow from a sidebar into a detail view, carry its label along with it, or use a short fade when a chapter ends. The output is a **new, editable `.pptx`** with native PowerPoint effects, not a video.

**[Download the installable ZIP for Cowork and Copilot Studio (v1.0.1)](https://github.com/OfirGavish/cat-agent-skills/releases/download/powerpoint-transitions-v1.0.1/powerpoint-transitions.zip)** from the author's release. Upload this file **as is**. Do not use GitHub's **Code > Download ZIP** or the release's **Source code (zip)**: those download the repository, not the skill.

## Try it in Cowork

Upload the complete skill ZIP through **Plugins > Add > Upload** (called **Customize** in some clients). Start a fresh task, select the installed skill, attach a copy of a `.pptx`, and say: **"Give this deck better transitions."** The skill asks which mode you want unless you've already specified one:

| Mode | What happens |
|---|---|
| Classic transitions only | Apply a handpicked Fade, Push, Wipe, None, or single-object Morph without scanning for matches. |
| Matched objects only | Compare adjacent slides for moving, resizing, or rotating pictures and shapes. Use Morph on selected pairs; leave transitions elsewhere alone. |
| Both | Use matched-object Morph where appropriate and classic transitions at other destinations. |

For a first run, try **"Matched objects only. Follow the product photo and its caption; skip ambiguous matches. Return an editable copy."** Start Slide Show on the slide **before** the change to see the motion.

## Try it in Copilot Studio

Open an unpublished agent using the Microsoft Copilot harness. In **Build > Skills > Add skill > Upload a skill**, upload the whole ZIP. In a fresh **Preview** chat, attach a copy of your deck and ask for better transitions without specifying a mode. Choose **Matched objects only** to reproduce the test below. Publishing the agent is not required.

## Other installation options

The two CAT targets are [Cowork](https://learn.microsoft.com/en-us/copilot/cowork/cowork-customize) and [Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-add-existing). The following are other ways to provide the instructions, not additional CAT host test results:

| Surface | How to use the skill |
|---|---|
| [Microsoft 365 Copilot Chat](https://learn.microsoft.com/en-us/plugins/build-copilot-chat-skills) | Where your plan and tenant permit personal skills, open **Agents > More agents > Add > Upload skill** and choose the ZIP. |
| [Microsoft Copilot Code](https://learn.microsoft.com/en-us/copilot/code/use-code) | Open an extracted copy of the skill as a local project, attach the deck, and ask Code to follow `SKILL.md`. This is a file workflow, not automatic skill registration. |
| [Copilot Autopilot](https://learn.microsoft.com/en-us/copilot/autopilot/plugins) | Where enabled, use **Plugins > Add > Upload skill**, then select the skill in the conversation. |
| [Microsoft Scout](https://learn.microsoft.com/en-us/microsoft-scout/use-microsoft-scout) or [GitHub Copilot in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills) | Extract the contents to `~/.copilot/skills/powerpoint-transitions/` so `SKILL.md` sits directly inside it. Start a new conversation on that device. This is a personal installation, not tenant-wide deployment. |

**If your host cannot install a skill**, paste this prompt instead. It can produce a plan but does not install the Python editor:

> Ask me to choose Classic transitions only, Matched objects only, or Both. Use one native transition per destination slide; pair objects only when their identity is clear, not just because their positions or colors are similar. Keep the original file and its slide-advance settings. If you can write and reopen an editable `.pptx`, return a new copy and list the changed slide pairs. Otherwise give exact PowerPoint steps and say that no deck was edited.

If Morph appears as a fade, start Slide Show on the *preceding* slide and check the shape names on both slides. See Microsoft's [Morph transition tips](https://support.microsoft.com/en-us/powerpoint/morph-transition-tips-and-tricks) for viewer compatibility and matching behavior.

## What it needs

The bundled Python 3.9+ editor uses only the standard library, makes no network requests, and refuses to overwrite an existing output. The host needs access to the attached deck and the bundled script, plus a way to return binary files. PowerPoint's own transition controls can be used if the host exposes them. Without a file writer the skill returns a **plan only**; an installation or text response does not prove a deck was edited.

The matcher looks for identity evidence such as a unique text label or identical embedded picture. It doesn't guess between repeated icons, find separate objects inside one screenshot, or add animations that run within a slide. Use **None** for zero motion. The skill preserves existing advance settings on edits.

## Tested in Cowork

On November 28, 2026, Cowork imported the CAT-generated ZIP, invoked the installed custom skill on a synthetic four-slide presentation, and offered all three modes before making changes. With **Matched objects only**, it returned a new `.pptx`. The input and output package-content fingerprints computed in Cowork matched an independent local run of the packaged editor. The picture and its caption were bound separately across slides 1–3, slides 2 and 3 received an 800 ms native Morph with Fade fallback, and slide 4 was unchanged. This verifies file delivery and structure; it is not a visual playback test in Cowork.

## Tested in Copilot Studio

On November 28, 2026, an unpublished Microsoft Copilot-harness agent in Studio Preview offered all three modes as a chat question. With **Matched objects only**, it returned a PowerPoint attachment. In a read-only follow-up, Studio fingerprinted its input and returned deck: both matched the Cowork and independent local results. The hash of the installed Python helper also matched the file in the submitted ZIP. Only the first three slide XML parts changed: slide 1 received object names, slides 2 and 3 received names and Morph, and slide 4 stayed untouched.

The first Preview debug step displayed **Skill incomplete**. The test did not treat that label, or the agent's text response, as proof either way: it checked the attachment's contents and installed helper. Visual playback in Studio was not tested. Classic and Both modes have local coverage, not end-to-end coverage in these two hosts.

The author also reports testing in Copilot in PowerPoint. Scout and regular Microsoft 365 Copilot Chat are not claimed as live-tested hosts here.

The live tests above used v1.0.0. Version 1.0.1 moves installation help and sample prompts out of the agent bundle; the Python editor and motion workflow are unchanged.

## Reproduce the local checks

The [source and four regression tests](https://github.com/OfirGavish/copilot-skills/tree/34c22d77bc5cd038cae3546445e420bf677ef1cc/.github/skills/powerpoint-transitions) include a synthetic four-slide fixture. Tests cover one-to-one matching, ambiguous and static objects, consecutive Morph transitions, mode isolation, hidden slides, and unchanged package parts. Test-only fixture creation requires `python-pptx` and Pillow; the installed editor does not.

In that fixture, the first two slide changes each have two eligible pairs: a picture moves and resizes, and a box labeled **Forecast** moves and rotates. In matched-only mode, slide 4 should remain unchanged. Testing Copilot in PowerPoint or rendering the deck locally is separate from verifying skill activation, execution and file delivery in a CAT host.
