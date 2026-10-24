# Convention catalog

The rules `scripts/hve_core_workspace_audit.py` evaluates, what each means, and where the fix lives. They approximate the conventions HVE Core documents in `docs/contributing/ai-artifacts-common.md`, `docs/contributing/{custom-agents,prompts,instructions,skills}.md`, `docs/customization/*.md`, `docs/architecture/ai-artifacts.md`, `docs/getting-started/{install,troubleshooting}.md`, the `hve-builder.instructions.md` file, and the frontmatter schema reference inside the `hve-artifact-authoring` skill, as of HVE Core 3.2.2. They are not HVE Core's own lint (`npm run lint:frontmatter`, `lint:md`, `lint:md-links`, `lint:models`, `validate:skills`, `plugin:validate`), which runs only inside an HVE Core clone or fork; say so whenever a user asks whether the repository "passes".

Severity is a review heuristic for ordering work, not a Microsoft rating and not a compliance verdict: **high** means no host loads the artifact or finds it by name; **medium** means it loads but misbehaves silently, one host drops it, or the workspace carries a setup gap; **low** means convention or portability; **info** means a fact to know, not a defect. Where current VS Code behavior has moved past what HVE Core documents (model lists, prompt `agent:` versus `mode`, deprecated location settings, Claude-format agents), the rule says so and keys its severity to the stricter host.

Artifacts whose path under `.github/` matches a file HVE Core ships are "copies" and exempt from the per-artifact rules by default, because upstream maintains them and the host validates them there. `--include-hve-copies` audits them anyway, which is useful after local edits. A rule is listed as not evaluated when the workspace lacks the file it needs or the run was single-file; that says nothing about conformance. Symbolic links are never followed, whether they stand in for `.github`, a type folder, a skill or `scripts/` folder, or an artifact file, because they can point outside the workspace; the report header lists every link skipped, and `--file` refuses a link.

Three sources feed these rules, and the text says which applies: **HVE Core's own documentation** (the default); **VS Code's agent customization documentation** for custom agents, agent skills, custom instructions, and prompt files, as read in October 2026, for statements marked "current VS Code" (model lists, prompt `agent:`, Claude-format agents, `.claude/skills` and `.agents/skills`, `AGENTS.md`, deprecated `chat.*Locations` settings, `context: fork`, silent failure of badly named skills, `agents: "*"`); and the **Agent Skills specification** at agentskills.io for `name` and `description` limits, `compatibility`, `metadata`, and `allowed-tools`. HVE Core's repository does not mention the VS Code or Agent Skills items; when the two disagree, the rule keys its severity to the stricter host and says so.

The frontmatter parser supports the YAML that Copilot artifacts use: `key: value`, quoted and multi-line plain scalars, `|` and `>` block scalars, inline and block lists, nested maps, `- key: value` list items, and trailing `# comments` outside quotes. Anchors, aliases, tags, and flow mappings are not supported and report as FM1.

## Frontmatter fields by type

From HVE Core's schema reference (`hve-artifact-authoring/references/frontmatter-schemas.md`) with the contributing guides' constraints. `description` is required everywhere and must not carry an attribution suffix. Omit optional fields rather than leaving them empty.

| Type | Required | Optional | Never |
| --- | --- | --- | --- |
| Agent | `name` (schema reference; the contributing guide calls it optional and VS Code defaults to the file name, but handoffs and `agents:` resolve by it), `description` (one sentence, 10 to 200 characters) | `argument-hint`, `agents` (names, `*`, or `[]`; needs the `agent` tool), `tools` (user-managed, read before write; omitted means full access), `model` (one scalar string from the model catalog; VS Code accepts an ordered list but the Copilot CLI and HVE Core's lint do not), `handoffs` (`label` and `agent` required; `prompt`, `send`, `model` optional; VS Code 1.106 or later), `user-invocable` (false for subagents), `disable-model-invocation` (true for orchestrators and side-effect agents), `target` (`vscode` or `github-copilot`), `mcp-servers` (only with `target: github-copilot`), `hooks` (preview) | `infer` (deprecated), `applyTo` |
| Prompt | `description` | `name` (slash-command name), `agent` (`ask`, `agent`, `plan`, or a custom agent's `name:`; current VS Code routes on this), `argument-hint`, `model` (scalar or ordered fallback list; the only type where a list is valid), `tools` (overrides the agent's), `mode` (legacy; HVE Core's checklist still lists it, VS Code no longer documents it), `disable-model-invocation`, `category`, `version`, `author`, `lastUpdated` | `applyTo` |
| Instruction | `description`, `applyTo` (glob or comma-separated globs from the repository root; required for pattern attachment; current VS Code can load a file on demand from its description alone) | `name`, `version` (semver), `author`, `lastUpdated` (ISO date) | `tools`, `model`, `agent`, `handoffs`, `agents`, `mcp-servers` |
| Skill | `name` (lowercase kebab-case, at most 64 characters, equal to the folder name), `description` (one to three sentences; the Agent Skills specification caps it at 1,024 characters) | `argument-hint` (required arguments first), `license` (SPDX; set when third-party content is included; noncommercial qualifiers exclude the skill from the plugin), `user-invocable` (default true), `disable-model-invocation` (default false; true for high-cost or niche skills), `compatibility` (at most 500 characters), `metadata` (string-to-string map: `authors`, `spec_version`, `last_updated`, and so on), `allowed-tools` (Agent Skills spec, experimental), `context: fork` (VS Code, experimental: run in a subagent) | `tools`, `model`, `agent`, `handoffs`, `applyTo`, `agents`, `mcp-servers` |

Model names must use the VS Code display name with the `(copilot)` suffix and appear in HVE Core's `scripts/linting/model-catalog.json` with `ga` or `preview` status; the script does not validate names, only the shape. VS Code also reads Claude-format agents under `.claude/agents` and skills under `.claude/skills` and `.agents/skills`; the script inventories those skills but applies HVE Core's packaging rules only to `.github`.

## Frontmatter (FM)

**FM1 Frontmatter missing or unparseable.** No `---` block at the top, an unclosed block, or YAML the parser cannot read. High. *Why:* without parseable frontmatter the host has no name or description to route on, and HVE Core's frontmatter lint fails. *Verify:* open the file; the detail names the line. *Fix:* a `---` line, `key: value` pairs, a closing `---`, then the body.

**FM2 Description missing.** `description` absent or empty. High. *Why:* Copilot decides when to load a skill and when to suggest an agent from the description; HVE Core routes parents to subagents on it. *Fix:* one sentence that says what the artifact does and when it applies, in the words users type.

**FM3 Description length.** Agent, prompt, or instruction description outside 10 to 200 characters; skill description over 1,024. Low. *Why:* HVE Core's contribution standard; long descriptions cost context on every turn and short ones do not route. *Fix:* trim or extend.

**FM4 Field that belongs to another artifact type.** `applyTo` on anything but an instruction; `tools`, `model`, `agent`, `handoffs`, `agents`, or `mcp-servers` on a skill or instruction. Medium. *Why:* HVE Core's lint rejects cross-type fields, and skills must stay portable across hosts. *Fix:* remove the field; put behavior that needs tools into an agent.

**FM5 Field not in the schema reference.** Any key outside HVE Core's schema reference plus the host fields the catalog table lists (`allowed-tools` and `context` for skills). Info. *Why:* the host may accept it (VS Code adds fields over time), but neither HVE Core's schema nor the documented host fields know it. *Verify:* the current VS Code customization documentation. *Fix:* none required.

**FM6 Deprecated infer field.** `infer` on an agent. Low. *Fix:* replace with `user-invocable` and `disable-model-invocation`.

## Agents (AG)

**AG1 Agent without a name.** Medium. *Why:* handoffs, `agents:` allowlists, and prompts' `agent:` resolve by `name:`; HVE Core's schema reference lists it as required even though the contributing guide allows the filename to stand in. *Fix:* add a display name.

**AG2 Model given as a list.** `model` is a YAML array. Medium; treat as high when anyone on the team uses the Copilot CLI. *Why:* current VS Code tries the entries in order, but the Copilot CLI rejects array-form model values and drops the agent entirely, and HVE Core's frontmatter lint rejects it; arrays are accepted everywhere only in prompt files. *Fix:* one scalar string, or omit `model` to inherit the session or picker selection.

**AG3 Subagent allowlist without the agent tool.** `agents:` lists names or is `"*"` (current VS Code's "any agent" form), `tools:` is declared, and it contains neither `agent` nor a wildcard. Medium. *Why:* dispatch needs the `agent` tool; the allowlist is inert without it. *Fix:* add `agent` to `tools`, or drop `agents:`.

**AG4 Subagent visible in the picker.** File under a `subagents/` folder without `user-invocable: false`. Medium. *Why:* the subagent appears to users as a selectable agent and can be run outside its parent's protocol. *Fix:* `user-invocable: false`.

**AG5 Handoff entry without label or agent.** Medium. *Why:* VS Code needs both to render the transition. *Fix:* `label` and `agent`; `prompt` and `send` are optional.

**AG6 Handoff or subagent target not found.** A handoff `agent` or an `agents:` entry matches neither a `name:` value nor a file stem (file name without `.agent.md`) of any workspace or HVE Core agent. Low (the target may live in another source). *Why both forms:* HVE Core's own agents target by `name:`; its contributing guide describes the field as the file stem. *Verify:* the picker, or the extension's agent list. *Fix:* match one of the two forms exactly.

**AG7 Agent name duplicates an HVE Core agent.** A local agent not at the HVE Core path uses an HVE Core agent's name. Low. *Why:* with the extension, plugin, or a clone present, two entries appear and the user cannot tell which ran; the troubleshooting guide's "duplicate components" case. *Fix:* rename, or keep one source.

**AG8 Read-only agent with unrestricted tools.** No `tools:` while the description or title says read-only, review, or audit. Low, heuristic. *Why:* omitting `tools` grants full access including edits and terminal. *Fix:* list read-oriented tools (`read`, `search`, `web`) only.

## Prompts (PR)

**PR1 Prompt delegates to an unknown agent.** `agent:` is neither a built-in value (`ask`, `agent`, `plan`) nor a workspace or HVE Core agent name. Low. *Fix:* use the agent's `name:` value.

**PR2 Prompt without a target agent.** No `agent:`; or a legacy `mode:` without `agent:`. Info. *Why:* current VS Code routes prompt files with `agent:` and no longer documents `mode`; without it the prompt runs in whichever agent is current. HVE Core's prompt checklist predates the change and still lists `mode`. *Fix:* add `agent: agent`, `agent: plan`, or the custom agent's name.

## Instructions (IN)

**IN1 Instruction without applyTo.** Low when the file has a description, Medium when it has neither. *Why:* without `applyTo` the file never attaches by file pattern. Current VS Code can still load it on demand when its description matches the task, and an agent or skill can load it with `#file:`; with neither field, only a manual attachment loads it. The customization guide calls `applyTo` "strongly recommended" and the contributing guide mandatory for auto-applied files. HVE Core itself ships three such files on purpose (`commit-message`, `git-merge`, `diff-computation`), loaded by the Git skills and the Code Review agent. *Verify:* whether an agent or skill references the file. *Fix:* add globs, or confirm the reference.

**IN2 Pattern matches the repository root only.** A pattern with no `/` and no `**` (`*.py`). Low. *Why:* HVE Core's guide says patterns that match only the root "cause failures". A deliberate root-only target such as `package.json` is fine. *Fix:* prefix with `**/` unless the root match is intended.

**IN3 Pattern applies globally.** `**`, `**/*`, or `*`. Low. *Why:* the file attaches to every edit; repository-wide rules belong in `copilot-instructions.md`, which loads once per interaction and wins conflicts. *Fix:* narrow, or move.

**IN4 Files sharing one applyTo pattern.** Two or more local instruction files declare an identical pattern. Info. *Why:* stacking is additive and conflicts are resolved by specificity, which identical patterns do not provide; same-specificity conflicts are for the artifact owner to resolve by pull request. *Verify:* read both for contradictions. *Fix:* keep them consistent or merge.

**IN5 Pattern also used by an HVE Core instruction.** A local (non-copy) pattern equals one HVE Core ships (`**/*.py`, `**/*.md`, and so on). Info. *Why:* with HVE Core present both files attach; the more specific pattern wins conflicts, and duplicated rules waste context. *Fix:* keep organization additions, remove restatements; `/hve-builder mode=refactor` consolidates.

## Skills (SK)

**SK1 Skill name does not match its folder.** Also fires when `name` is missing, blank, or not a string. High. *Why:* the folder name is the skill's identity for discovery and `copilot-skill:` references; HVE Core's `validate:skills` rejects the mismatch, and a skill without a name cannot be found by one. *Fix:* make them equal.

**SK2 Name not lowercase kebab-case.** Also fires above 64 characters. Medium. *Why:* the Agent Skills specification allows only `a-z`, `0-9`, and single hyphens up to 64 characters, and VS Code's agent skills documentation says a skill with invalid characters, dots, colons, slashes, or a namespace prefix fails to load silently. *Fix:* lowercase letters, digits, single hyphens.

**SK3 Unrecognised folder inside a skill.** Anything other than `scripts`, `references`, `assets`, `templates`, `examples`, `tests`. Low. *Why:* HVE Core's skill validation allows only those; other hosts may bundle stray folders into the agent's context. *Fix:* move the content.

**SK4 Scripts with external surface and no SECURITY.md.** Scripts under `scripts/` contain, outside comment lines and lines that define search patterns, network calls (`curl`, `wget`, `Invoke-WebRequest`, `requests.`, `urllib.request`, `httpx`, `fetch(`, sockets), subprocess launches (`subprocess.`, `os.system`, `Start-Process`, `child_process`), or credential handling (`api_key`, `client_secret`, `access_token`, `password`, `bearer`, `Authorization:`, Azure credential classes, `keyring`) and the skill root has no `SECURITY.md`. Medium, keyword heuristic. *Why:* HVE Core requires a per-skill STRIDE security model when a skill with an executable runtime performs network egress, handles credentials, starts subprocesses, or parses untrusted content. *Verify:* read the scripts; a comment, a string constant, or a scanner that looks for secrets can trigger the keyword, and HVE Core's own `adr-author` and `data-catalog` skills trip it that way. *Fix:* add `SECURITY.md` from HVE Core's template (`## Bucket Bn` trust buckets, STRIDE categories and Risk Rating as H3), or remove the surface.

**SK5 Scripts folder without a PowerShell script.** Info. *Why:* HVE Core's own contribution rule requires at least one `.ps1` when `scripts/` exists, except Python skills packaging modules; irrelevant for a repository-local skill.

**SK6 Skill body navigates by workspace-root .github path.** The body (outside code fences) references a concrete `.github/agents/...`, `.github/skills/...` file path; globs, placeholders, and folder mentions ending in `/` are skipped. Low. *Why:* distributable artifacts must not depend on the installation path; refer to other artifacts by name and to bundled files by skill-relative paths. `.github/` may remain in examples and placeholder text. *Fix:* relative paths and names.

## Layout and packaging (LY)

**LY1 Artifacts at the root of a .github type folder.** Aggregated per type. Info. *Why:* HVE Core treats them as repository-specific and excludes them from plugin membership and packaging. Fine for repository-only artifacts. *Fix:* move distributable ones under `.github/<type>/<package-id>/`.

**LY2 Package folder not in kebab-case.** Low. *Why:* package ids must be unique, lowercase, kebab-case; they organise membership but are not separate marketplace products.

**LY3 plugin.json membership drift.** Members listed but missing on disk (Medium); package-scoped artifacts not listed (Low), except skills whose `license` carries a noncommercial qualifier, which HVE Core excludes on purpose. Evaluated only when a root `plugin.json` exists (HVE Core forks and plugin repositories). *Fix:* `npm run plugin:sync` then `npm run plugin:validate`.

**LY4 Deprecated artifact without a replacement note.** File under `.github/deprecated/` whose frontmatter or first lines name no replacement. Low. *Why:* HVE Core's deprecation path is notice, move to `.github/deprecated/`, sync, then removal after the transition. *Fix:* add the note.

**LY5 Artifact file outside the naming convention.** A `.md` under `.github/prompts/` or `instructions/` without the `.prompt.md` or `.instructions.md` suffix (README excluded), a `skill.md` in the wrong case, or a `SKILL.md` with no skill folder: Medium, because no host discovers them. A `.md` under `.github/agents/` without `.agent.md`: Low, because current VS Code loads any `.md` there as a Claude-format agent, but it sits outside HVE Core's naming convention, is excluded from packaging, and is not an agent for hosts that key on the suffix. *Fix:* rename.

## Workspace (WS)

**WS1 .copilot-tracking not ignored by git.** The folder exists and no `.gitignore` rule covers it (Medium); no rule yet and the folder is absent (Info). *Why:* every install method ends with adding `.copilot-tracking/` to `.gitignore`; the folder holds research, plans, change logs, and planner state, and HVE Core's lint exempts it only because it is never committed. *Verify:* `git check-ignore .copilot-tracking` on the user's machine. *Fix:* the one line.

**WS2 More than one HVE Core source.** The extension is recommended in `.vscode/extensions.json` and the workspace also carries a clone, submodule, git-ignored folder, workspace file, `.hve-tracking.json`, or copied artifacts (Medium); two local sources (Low). *Why:* the same agents and skills load twice, appear as duplicates, and behave unpredictably; the troubleshooting guide says to use one source per workspace. *Verify:* which source the user intends; compare copied files with `.hve-tracking.json` before deleting. *Fix:* keep the extension for managed content or the copied selection for version-controlled files; uninstalling the extension does not remove repository files.

**WS3 .hve-tracking.json out of date.** Schema version other than 2 (Low), or recorded paths missing on disk (Medium). *Fix:* re-run `hve-core-installer`, which validates or offers an upgrade.

**WS4 Chat location setting points to a missing folder.** An enabled entry in `chat.agentFilesLocations`, `chat.modeFilesLocations`, `chat.instructionsFilesLocations`, `chat.agentSkillsLocations`, `chat.promptFilesLocations`, or `chat.hookFilesLocations` in `.vscode/settings.json` does not exist. Low. *Why:* the "Copilot not discovering customizations" case; multi-root setups must also open the `.code-workspace` file. Current VS Code marks these settings deprecated and reads them only in Local harness sessions; HVE Core's clone-based install methods and its own `.vscode/settings.json` still rely on them, and monorepos now use `chat.useCustomizationsInParentRepositories`. *Fix:* correct the path or remove the entry.

**WS5 MCP-dependent agents without .vscode/mcp.json.** Agents declare `mcp-servers` or tool entries such as `microsoft-docs/*` and the workspace has no `.vscode/mcp.json`. Info. *Why:* MCP is optional; the agent reports the tool unavailable. *Fix:* create the file from the MCP configuration guide, at the workspace root, keeping only the servers used.

**WS6 No copilot-instructions.md.** Info; the detail says whether `AGENTS.md` exists instead, which current VS Code reads when `chat.useAgentsMdFile` is on. *Why:* HVE Core's adoption guide and conflict policy center on `copilot-instructions.md`.

**WS7 copilot-instructions.md over the soft threshold.** More lines than `--global-lines` (default 200); also evaluated when `--file` points at a `copilot-instructions.md`. Low, heuristic; HVE Core sets no numeric limit and warns against inventing one, so present it as a prompt to review. *Why:* the file loads on every interaction; the customization guide warns against sprawl. *Fix:* keep cross-cutting rules, move path-specific ones to `applyTo` files.

**WS8 HVE Core source detected.** One Info finding per source (extension recommendation, clone with version, submodule, git-ignored folder, multi-root workspace file, `.hve-tracking.json`, copied artifacts), or one saying none is visible. A user-level extension install and a CLI plugin cannot be seen.

## Body content (CT)

**CT1 No H1 heading.** Low. *Why:* every HVE Core artifact body starts with an H1 matching its purpose; markdownlint requires it.

**CT2 XML-style block tags unbalanced or duplicated.** `<!-- <tag> -->` without `<!-- </tag> -->`, or a tag name used twice. Low. *Why:* HVE Core's tools extract examples from these blocks; tags must match exactly, sit on their own lines, and be unique per file.

**CT3 Fenced code block without a language.** Low. *Why:* markdownlint MD040 in HVE Core's configuration.

**CT4 Relative link target missing.** A `[text](path)` link in prose (fenced code blocks are skipped) whose target does not exist next to the file. Targets that look like placeholders (`{var}`, `<path>`, `path/to/file.ext`, `url`) are skipped. Medium. *Why:* the artifact promises a reference, template, or script that is not there; HVE Core's link lint fails. *Fix:* fix the path or add the file.

**CT5 Trailing whitespace or missing final newline.** Info. *Why:* file-format checks in HVE Core's review checklists.

## Where fixes live

The script's remediation plan groups findings under these control names, in this order.

| Control (as printed) | Rules | Where |
| --- | --- | --- |
| Artifact discovery (file names and locations) | SK1, LY2, LY5 | File and folder names |
| Frontmatter of the artifact | FM1 to FM4, FM6, AG1 to AG6, AG8, PR1, IN1 to IN3, SK2 | The artifact's frontmatter block; `/hve-builder mode=improve` applies corrections inside an HVE Core-enabled workspace |
| Install source choice | AG7, WS2, WS3 | `.vscode/extensions.json`, cloned or copied folders, `.hve-tracking.json`, the `hve-core-installer` skill |
| .gitignore | WS1 | Root `.gitignore` |
| .vscode settings and MCP | WS4, WS5 | `.vscode/settings.json`, `.vscode/mcp.json` |
| plugin.json membership | LY3 | `npm run plugin:sync`, `npm run plugin:validate` in the fork |
| Skill folder | SK3, SK4 | The skill's folders and `SECURITY.md` |
| Body content | SK6, LY4, WS7, CT1 to CT4 | The Markdown body |
| Facts to carry forward | FM5, PR2, IN4, IN5, SK5, LY1, WS6, WS8, CT5 | Nothing to change unless the user wants distribution or HVE Core contribution |
