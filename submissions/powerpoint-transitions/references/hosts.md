# Using the skill

The same package contains instructions and a Python standard-library editor. Installing the instructions does not grant file access, enable Python, publish an agent, or change permissions. A personal folder is local to the device; it is not a tenant-wide installation.

| Surface | How to make it available |
|---|---|
| [Microsoft 365 Copilot Chat](https://learn.microsoft.com/en-us/plugins/build-copilot-chat-skills) | Agents > More agents > Add dropdown > Upload skill. Select the ZIP with `SKILL.md` at its root. Requires a supported plan and tenant policy (documented for Premium, not Basic). |
| [Copilot Cowork](https://learn.microsoft.com/en-us/copilot/cowork/cowork-customize) | Plugins > Add > Upload. Choose the ZIP. Start a new conversation after updating it. |
| [Microsoft Copilot Code](https://learn.microsoft.com/en-us/copilot/code/use-code) | In a local project, open an extracted copy of the skill as a folder and attach your deck. Say: "Read SKILL.md and follow it for this file." In a session without access to the folder, use the portable prompt below. This is an explicit file workflow, not a claim of automatic skill registration. |
| [Copilot Autopilot](https://learn.microsoft.com/en-us/copilot/autopilot/plugins) | Plugins > Add > Upload skill; select the ZIP or skill folder. Where the Frontier preview is enabled, type `/` and select the skill. |
| [Microsoft Scout](https://learn.microsoft.com/en-us/microsoft-scout/use-microsoft-scout) | Place the skill in `~/.copilot/skills/powerpoint-transitions/`. Start a new conversation on that device. |
| [Microsoft Copilot Studio: Microsoft Copilot harness](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-add-existing) | Open an agent created with this harness. Build > Skills > Add skill > Upload a skill. Select the ZIP and test on a non-sensitive sample before publishing. This is not a legacy Bot Framework skill manifest. |
| [GitHub Copilot in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills) | Use the same personal skill folder as Scout. Start a fresh agent chat and select `/powerpoint-transitions` or describe the task. This is separate from Microsoft Copilot Code. |

**Try it:** Attach a deck and say "Give this presentation better transitions." The skill should pause and offer **Classic transitions only / Matched objects only / Both**. To skip the chooser, say: "Use matched objects only. Find the product photo and its caption across neighboring slides. Animate their move into the detail view and leave all other slide transitions as they are."

**Portable prompt** (when skill discovery or package upload isn't available):

> Before doing anything to the deck, ask me to choose **Classic transitions only**, **Matched objects only**, or **Both** and wait, unless I've already chosen. Classic means the existing Fade/Push/Wipe/None and intentional handpicked Morph workflow; don't scan for matches. Matched objects means compare neighboring slides for corresponding shapes, text boxes or pictures that move, resize or rotate. Use identity evidence such as a distinctive name, the same embedded picture or a unique text label. Skip uncertain pairs or ask; don't guess from color or position alone. Give each confirmed pair a unique shared `!!` name; apply one Morph / Objects on the destination (about 0.8 s). Leave transitions elsewhere untouched. In Both mode, choose Morph for matched moves and a classic transition only on other slide pairs when useful. Preserve content, existing animations and advance timings; respect reduced motion. If you can write and reopen a native `.pptx`, return an editable copy and list the changed objects and slides. Otherwise give exact PowerPoint steps and say no deck was edited.

For visual troubleshooting, see Microsoft's [Morph transition tips](https://support.microsoft.com/en-us/powerpoint/morph-transition-tips-and-tricks).
