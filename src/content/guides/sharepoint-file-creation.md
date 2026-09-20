# SharePoint File Creation

Generate files in a Copilot Studio session and upload them to SharePoint without
passing raw file bytes through the model. Use this workflow instead of reading
binary file content into the model, converting files to base64, or passing raw
bytes through connector arguments.

This skill gives an agent a fixed, safety-focused workflow:

1. Generate the complete requested file in Copilot Studio's `/app/created/`
   directory.
2. Measure the final file with the filesystem API and stop before upload if it
   is empty or 4,000,000 bytes or larger.
3. Pass the file path directly to the configured SharePoint **Create file**
   action so the connector resolves the file server-side.
4. Report the SharePoint destination, measured pre-upload size, and upload
   result.

## Why the path and size rules matter

The workflow is based on connector testing in Copilot Studio:

- `/app/created/<filename>` is the confirmed path-reference mechanism for the
  Create file action. Passing a path outside that directory can upload the
  literal path text instead of the intended file bytes.
- Uploads begin failing around the tool layer's 4 MiB inline-upload boundary.
  The skill uses a conservative 4,000,000-byte gate because the complete range
  immediately below 4 MiB has not been verified.

These are empirical, environment-specific findings rather than documented
SharePoint limits. SharePoint itself supports larger files; this skill addresses
the current inline connector/tool behavior available to the agent.

## Before adding the skill

Configure a SharePoint **Create file** action for the agent. Fix the site and
folder in the action when every upload should use the same destination, or
leave them available as inputs when the destination must vary.

Review Section 0 of `SKILL.md` and replace or extend the generic content-sourcing
rules when the agent must use a particular template, knowledge source, report
structure, schema, or style guide. The upload and size-gating sections should
remain unchanged.

## Boundaries

- It does not automatically truncate or split oversized output.
- It stops on permission, DLP, authentication, ambiguous-result, size, or
  integrity errors rather than silently retrying.
- The raw sandbox path stays internal during normal use.
