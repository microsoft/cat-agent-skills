# Copilot Studio agent: Idea Capture

## Create
1. Copilot Studio (same environment) > Create > New agent, name **Idea Capture Assistant**.
2. Paste the instructions below into *Instructions*.
3. Add the topic from this file (Topics > Add > From blank > open code editor, paste YAML), or rely on generative orchestration with the tool.
4. Tools > Add a tool > Dataverse > **Add a new row** > table **Ideas**. Name it `Save idea`. Description: "Saves a captured idea to the Idea Backlog." Set inputs: Title, Description, Submitted By, Submitter Email, Business Value, Category, Priority = fill dynamically (model); Status = fixed `New`; Source = fixed `Copilot Studio`; Conversation Id = `System.Conversation.Id`.
5. Test, then Publish and add a channel (Teams / website). Share with users.

## Instructions
```
You help employees submit ideas for improvement. Greet briefly, then collect:
1. Title (short), 2. Description, 3. Business value (why it matters),
4. Category (Process, Product, Technology, Customer Experience, Other),
5. Priority (Low, Medium, High), 6. The user's name and email.
Ask one question at a time; skip anything the user already gave. Summarise the idea and ask for confirmation,
then call the "Save idea" tool with Status = New. After saving, thank the user and tell them it will appear
in the Idea Backlog app with status New. Never invent values. If the user wants to submit another idea, repeat.
Do not discuss topics unrelated to idea capture.
```

## Topic (YAML, adjust to your tool's action id)
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    triggerQueries:
      - I have an idea
      - Submit an idea
      - Suggest an improvement
  actions:
    - kind: Question
      id: q_title
      variable: Topic.Title
      prompt: What is a short title for your idea?
      entity: StringPrebuiltEntity
    - kind: Question
      id: q_desc
      variable: Topic.Description
      prompt: Please describe your idea.
      entity: StringPrebuiltEntity
    - kind: Question
      id: q_value
      variable: Topic.BusinessValue
      prompt: What benefit or value would it bring?
      entity: StringPrebuiltEntity
    - kind: Question
      id: q_cat
      variable: Topic.Category
      prompt: Which category fits best?
      entity:
        kind: EmbeddedEntity
        definition:
          kind: ClosedListEntity
          items:
            - { id: Process, displayName: Process }
            - { id: Product, displayName: Product }
            - { id: Technology, displayName: Technology }
            - { id: CustomerExperience, displayName: Customer Experience }
            - { id: Other, displayName: Other }
    - kind: SendMessage
      id: confirm
      message: "Saving your idea \"{Topic.Title}\". Thank you! It will show as New in the Idea Backlog app."
```
Link the *Add a new row* tool node (Add a tool node after `confirm`) mapping the Topic variables to the columns above.

## Bulk/offline capture
Export transcripts or collect ideas into JSON matching `assets/sample-ideas.json`, then run `scripts/Import-Ideas.ps1`.
