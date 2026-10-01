# Eye.Art Polyphemus for Copilot Studio

Polyphemus is Eye.Art's hosted image workflow router. Connect the MCP endpoint to a Copilot Studio agent, then add this skill so the agent knows when to create, edit, or retrieve images and how to keep follow-up turns grounded in the source image and conversation.

## Setup

1. In Copilot Studio, add a custom Model Context Protocol server using `https://eye.art/api/eye-mcp` with no authentication. The custom MCP server flow is documented by Microsoft as a preview feature.
2. Review the discovered tools and enable the Eye.Art actions the agent needs.
3. Upload `SKILL.md` to the agent's Skills section.
4. Test a simple generation and a follow-up edit in Preview. Confirm the activity trace shows the Eye.Art tool call and inspect the returned status before showing an image.

This gallery entry is a community-contributed skill, not a Microsoft or Eye.Art integration certification. The gallery skill itself does not install the MCP server.

## What it can do

- Generate and edit images through one chat-oriented endpoint.
- Keep related turns connected with a `conversationId` and use source images for focused edits.
- Route requests for artist-guided images, small illustrations, webpage-matched art, editable SVG, and supported motion.
- Return asynchronous job identifiers for longer generations so the agent can poll for completion.

Eye.Art is free to try without a key, subject to an anonymous rate limit of 20 generations per hour per caller network identity. Prompts, images, and conversation history may be retained for up to 30 days for service history and debugging. Do not send sensitive references without the user's direction.
