# Chunking Guidance for Copilot Studio Knowledge

Good chunks are self-contained, focused, and easy to retrieve.

## Recommended structure

- Use clear H1/H2/H3 headings.
- Keep each section focused on one question, policy, procedure, product, or scenario.
- Put the direct answer before background detail.
- Include required context in the same section as the answer.
- Prefer FAQ sections for high-volume questions.
- Keep tables simple and add short text summaries before or after complex tables.

## Content splitting guidance

Split content when:

- A page covers multiple unrelated departments, products, or policies.
- A document exceeds roughly 1,500-2,000 words and has multiple intents.
- A section requires different permissions from the rest of the file.
- A procedure mixes static explanation with live workflow steps.
- A page has multiple regional variants.

Do not split content when:

- The sections need each other to answer correctly.
- Splitting would remove definitions, eligibility criteria, or exceptions from the answer.
- The content is already a short, focused FAQ or article.

## Anti-patterns

- Long policy PDFs with no headings.
- "Contact support" answers without direct criteria.
- Mixed public and manager-only content in one page.
- Huge troubleshooting articles with many unrelated symptoms.
- Images that contain important text but no accessible text alternative.
- Tables with no surrounding explanation.

## Chunk review checklist

- Can a user question retrieve this section without needing unrelated sections?
- Does the section state who it applies to?
- Does it include exceptions and effective dates?
- Does it point to an action when the user must do something?
- Is the language clear enough for the agent to quote or summarize?
