# Scheduling the regulation monitor

The core skill has no schedule of its own — it just runs. To put it on a
cadence, wire it to a scheduler on your platform.

## Scout

Create a Scout automation. In natural language:

> Every Monday at 8am, run "regulation-monitor" for profile `<profile-name>`.

Or via the built-in automation tool:

```
name: Regulation Monitor — <profile-name>
schedule: every Monday at 8am
prompt: |
  Run the regulation-monitor skill for profile "<profile-name>".
  Load the profile's config.json, sweep the window since the last run,
  build the dashboard, and email the digest to the user per the
  delivery block. Send silently if no items were found.
teamsNotify: auto
```

Scout will keep the recurrence, invoke the skill, and post the summary
according to the automation's Teams notification policy.

## Copilot Studio

Create a scheduled agent in Copilot Studio pointed at the skill. In the
agent's schedule, choose the same cadence as the profile
(`cadence: weekly` → weekly). The agent's prompt is identical to the Scout
automation prompt above.

## Cowork

Cowork tasks can run on a schedule. Create a recurring task:

- Task name: `Regulation Monitor — <profile-name>`
- Recurrence: match the profile's cadence
- Instructions: the same prompt as above, pointed at the skill.

## What the schedule should NOT do

- **Do not reconfigure the profile from the schedule.** Setup is an
  interactive step. If the profile is missing or stale, the scheduled run
  should send a short heads-up to the user and stop, not silently rebuild.
- **Do not add external email recipients from the schedule.** The pre-
  authorized recipient is the user themselves. Any other recipient requires
  an interactive confirmation.
- **Do not chain the monitor into downstream action.** This skill monitors;
  it does not take a filing position or trigger a workflow. Keep the
  scheduled job single-purpose.
