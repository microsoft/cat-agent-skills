# The RAPP single-file agent contract

A RAPP agent is **one file = one class = one `metadata` dict = one `perform()`
method**. That is the entire contract. It is what makes the cartridge portable:
the same file runs on a laptop brainstem, on Azure Functions, and behind a
Copilot Studio agent without modification.

## Required structure

```python
from agents.basic_agent import BasicAgent

class MyAgent(BasicAgent):
    def __init__(self):
        self.name = "MyAgent"
        self.metadata = {
            "name": self.name,
            "description": "Tells the model exactly when to invoke this agent.",
            "parameters": {                      # OpenAI function-calling JSON Schema
                "type": "object",
                "properties": {
                    "topic": {"type": "string",
                              "description": "Self-sufficient; the caller sees only this."}
                },
                "required": ["topic"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:          # MUST return a string
        return "result the model will read back"
```

A class-attribute style (no `__init__`; `name` and `metadata` as class
attributes) also loads. Optional surfaces: `system_context(self) -> str | None`
(text injected into the system prompt each turn) and a module-level
`__manifest__` dict (`{"schema": "rapp-agent/1.0", "name", "version",
"display_name", "description", "author", "tags", "requires_env", ...}`) that
registries read by AST without executing the file.

## Portability shim

So the file runs with or without a brainstem, open with:

```python
try:
    from agents.basic_agent import BasicAgent
except ImportError:  # running OUTSIDE a brainstem -- stay executable anyway.
    class BasicAgent:
        def __init__(self, name=None, metadata=None):
            if name:
                self.name = name
            if metadata:
                self.metadata = metadata
        def perform(self, **kwargs):
            return "Not implemented."
        def system_context(self):
            return None
        def to_tool(self):
            return {"type": "function", "function": {
                "name": self.name,
                "description": self.metadata.get("description", ""),
                "parameters": self.metadata.get("parameters", {})}}
```

and close with a standalone entry point:

```python
if __name__ == "__main__":
    _a = sys.argv[1:]
    if _a and _a[0] == "--tool":
        print(json.dumps(MyAgent().to_tool(), indent=2))
    else:
        _raw = _a[0] if _a else (sys.stdin.read().strip() or "{}")
        print(MyAgent().perform(**json.loads(_raw)))
```

## Rules the loader actually enforces

| Rule | Why it exists |
|------|---------------|
| Filename ends `_agent.py`, snake_case, no dashes | Auto-discovery globs for it. |
| `self.name` matches `^[a-zA-Z0-9_-]+$` | Non-tool-safe names are quarantined at load. |
| `metadata["parameters"]` is a dict with `"type": "object"` | It is passed to the model as the function-calling schema. |
| `perform()` returns a `str`, always | The tool layer serializes the return value; anything else breaks the turn. |
| No-argument constructor | The loader instantiates every agent class it finds. |
| No network calls in `__init__()` | Constructors run at load time for every request. |
| Secrets via `os.environ.get()`, declared in `__manifest__["requires_env"]` | A reader can see what an agent needs without running it. Never hardcode. |
| Missing env vars degrade gracefully (return an explanatory string) | A crash takes out the request; a message does not. |
| No sibling imports (agents never import other agents) | Each file must work dropped into `agents/` alone. |

Conventionally `perform()` returns `json.dumps({"status": "success" | "error",
...})` so callers can branch without parsing prose.

## Canonical homes

- Conversion spec: `rapp-capability-interchange/1.0` — reference implementation
  and normative text at <https://github.com/kody-w/rapp-toaster>.
- The RAPP platform (brainstem runtime, agent examples):
  <https://github.com/kody-w/RAPP>.
- Portable toasted skills and launchpad agents:
  <https://github.com/kody-w/rapp-skills>.
