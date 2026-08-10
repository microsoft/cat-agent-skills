# Business OS

Business OS is a practical operating system for Copilot Studio. It gives agents a consistent way to approach real business work, including problem solving, decision making, project planning, process improvement, incident handling, governance, and turning repeatable work into reusable skills.

## Why use Business OS instead of a standard Copilot experience?

A standard Copilot experience can answer questions and complete tasks using the prompt, instructions, knowledge, and context it has available. Business OS adds a structured way of working on top of that.

It helps the agent clarify the outcome before jumping into an answer, choose an appropriate level of structure for the task, work through problems and decisions consistently, and produce outputs that are easier to act on and reuse.

This is useful when you want Copilot Studio agents to do more than generate a good one-off response. Business OS is designed for repeatable business work where the quality of the approach matters as much as the final answer.

## Before you start

Business OS is designed for Microsoft Copilot Studio Agent Skills. It does not require external services or accounts by default.

For organisation-specific use, you can add your own policies, approval rules, terminology, structures, and ways of working through the Company DNA approach included in the skill. The skill is designed not to invent this information when it has not been provided.

## How to use it

Use Business OS for requests where the agent needs to do more than provide a simple factual answer or rewrite a short piece of text.

For example:

- "We have three options for replacing this process. Help me decide which one to choose."
- "This project keeps slipping. Work out what is going wrong and what we should do next."
- "Turn this idea into a practical project plan."
- "Map this process and show me where it can be improved."
- "Help me handle this business incident and make sure we capture what we learn."
- "We keep doing this task manually. Assess whether it should become an Agent Skill."

The skill first identifies the outcome, classifies the type of work, and chooses a proportionate approach. Simple work stays simple. More complex or higher-risk work can use the included decision, problem-solving, process, project, incident, communication, governance, and skill-generation guidance.

## What is included

The main `SKILL.md` acts as a lightweight router. Supporting material is only used when it is relevant to the task.

The package includes:

- Work classification and response sizing
- Decision support
- Problem solving and root-cause analysis
- Process design and improvement
- Project planning
- Incident handling and learning
- Business communications and meeting outputs
- Governance, evidence, confidence, and quality checks
- Company-specific context through Company DNA
- Reusable templates for common business outputs
- A Skill Generator for assessing and drafting new reusable skills

## Good to know

Business OS is intentionally broad, but it should not override a more specific installed skill that is better suited to the task. It is designed to route work sensibly and only load the guidance that is needed.

It does not assume that an action has been completed just because it was recommended or drafted. It separates facts from assumptions, avoids inventing organisation-specific rules, and states clearly when something still needs human approval or verification.

Any organisation-specific policies, approval thresholds, systems, or terminology need to be supplied by the organisation.

## Author

Created by Matthew James Davis.

More Agent Skills and resources: https://agentskillslibrary.ai
