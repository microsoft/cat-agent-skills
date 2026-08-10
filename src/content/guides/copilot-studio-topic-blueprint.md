# Copilot Studio Topic Blueprint

Describe an agent in a sentence, get a build-ready plan back. This skill takes a
one or two line use case and returns a structured Microsoft Copilot Studio
blueprint you can implement directly, no blank-page phase.

## How to use it

Give the agent a use case, for example:

> "An HR agent for employees that answers policy questions from our SharePoint
> handbook and can open a leave request in our HR system."

You get back eight sections:

1. **Recommendation** - agent type and orchestration mode, with the reason.
2. **Topics** - 3 to 7 topics, each with a generative "use when" description and
   its ordered nodes.
3. **Tools and actions** - connectors and flows with typed inputs, outputs, and
   failure paths.
4. **Knowledge** - what to attach and when knowledge should answer.
5. **Variables** - the global variables and their types.
6. **Welcome experience** - paste-ready Adaptive Card JSON with 3 starter prompts.
7. **Security and cost** - authentication mode, DLP notes, and Copilot Credits
   cost drivers.
8. **First test plan** - 5 utterances and the topic or tool each should trigger.

## Good to know

- It designs and specifies; it never builds in your tenant.
- It stays grounded in Microsoft Learn and will not invent product features,
  menu paths, or limits. When behavior is product-dependent, it points you to
  the relevant guidance instead of guessing.
- Pair it with the **Copilot Studio Test Planner** skill once your agent exists,
  to turn it into a runnable test suite.
