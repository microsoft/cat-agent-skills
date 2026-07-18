# Knowledge Source Router

Point your Copilot Studio agent at the **right** knowledge source for each user —
by region — so answers are locally accurate instead of one-size-fits-all.

## Why use this?

Lots of information depends on where someone is: benefits, pricing, policies,
legal and compliance rules, support hours, what products are even available. If
your agent searches one big pile of knowledge, a user in Germany can easily get
an answer meant for someone in the US.

The clever part is that in Copilot Studio you don't need custom code to fix this
— you can guide the agent, in plain instructions, on **where** to look. This
skill is exactly that guidance: before the agent searches its knowledge, it first
decides *which* source fits the user's region (Americas, EMEA, APAC, or a Global
fallback) and searches only there. Same question, right answer for the right
place.

## What you provide

The skill handles the routing. The one thing it needs from you is a way to know
**where the user is**. That can be as simple or as rich as you like:

- **Just ask** — have the agent ask the user their country or region.
- **Look it up** — call a tool that returns it, such as a "get profile" action
  that reports the signed-in user's country, or any similar source of location.

Once the agent knows the user's location, this skill maps it to the correct
knowledge source and searches that one.

## The regions it routes to

| Source | For users in... |
| --- | --- |
| Global | Anywhere — content that's the same everywhere (the fallback) |
| Americas | US, Canada, Mexico, Central & South America |
| EMEA | Europe, the Middle East, and Africa |
| APAC | Asia, Australia, and the Pacific |

Adapt these to match however your own knowledge is organized.

## Requirements

Built for **Copilot Studio**, where an agent can be steered to specific knowledge
sources through instructions. You supply the region-specific sources and a way to
determine the user's location; the skill does the routing.
