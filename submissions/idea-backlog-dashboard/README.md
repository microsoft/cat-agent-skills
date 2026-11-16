# Idea Backlog Dashboard

A portable, end-to-end package for collecting and tracking ideas on Power Platform:

**User → Copilot Studio agent → Dataverse `Idea` table → Power Apps dashboard**

## What you get

- **Dataverse**: script that idempotently creates an `IdeaBacklog` solution and an `Idea` table (title, description, status, priority, category, submitter, business value, status notes, source, conversation ID, completed date).
- **Copilot Studio agent**: instructions, topic and Dataverse "Add a new row" tool setup to capture ideas conversationally.
- **Power Apps canvas app**: dashboard with status counts, search and filter, an ideas gallery, and a detail screen where owners can update status and notes.
- **Import script and sample data** for seeding or bulk-loading ideas.

## Prerequisites

- A Dataverse environment with Copilot Studio and Power Apps
- A service principal and an existing publisher; set these environment variables: `DATAVERSE_ENV_URL`, `DATAVERSE_TENANT_ID`, `DATAVERSE_CLIENT_ID`, `DATAVERSE_CLIENT_SECRET`, `DATAVERSE_PUBLISHER_PREFIX`
- PowerShell 7

## Usage

Ask your agent, for example: *"Build an idea backlog dashboard with a Copilot Studio capture agent."* The skill walks through schema creation, agent setup, app creation, validation and sharing.

The Copilot Studio agent and canvas app are built in the maker portals following the included references; they are not generated automatically.
