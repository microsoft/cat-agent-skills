#!/usr/bin/env python3
"""HelloRapp -- a minimal, complete RAPP single-file agent cartridge.

One file = one class = one metadata dict = one perform() method. Drop it into a
brainstem's agents/ directory and it hot-loads; run it standalone with python3;
or toast it into a single-file Agent Skill:

    python3 ../scripts/toast.py convert hello_rapp_agent.py --to skill -o SKILL.md
"""

import json
import sys

try:
    from agents.basic_agent import BasicAgent
except ImportError:  # running OUTSIDE a brainstem -- stay executable anyway.
    class BasicAgent:  # noqa: D101 - minimal stand-in, same contract
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

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@cat-agent-skills/hello_rapp",
    "version": "1.0.0",
    "display_name": "HelloRapp",
    "description": "Greets a person by name and reports the host surface "
                   "running the cartridge.",
    "author": "CAT Agent Skills gallery",
    "tags": ["demo", "hello"],
}


class HelloRapp(BasicAgent):
    def __init__(self):
        self.name = "HelloRapp"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "person": {"type": "string",
                               "description": "Name of the person to greet."},
                    "host": {"type": "string",
                             "description": "Optional label for the host surface "
                                            "running this cartridge."},
                },
                "required": ["person"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        person = str(kwargs.get("person", "")).strip()
        if not person:
            return json.dumps({"status": "error", "message": "No person given."})
        host = str(kwargs.get("host", "")).strip() or f"python {sys.version.split()[0]}"
        return json.dumps({"status": "success",
                           "greeting": f"Hello, {person}!",
                           "host": host})


if __name__ == "__main__":
    #     python3 hello_rapp_agent.py '{"person": "Ada"}'
    #     echo '{"person": "Ada"}' | python3 hello_rapp_agent.py
    #     python3 hello_rapp_agent.py --tool     # emit the JSON tool contract
    _a = sys.argv[1:]
    if _a and _a[0] == "--tool":
        print(json.dumps(HelloRapp().to_tool(), indent=2))
    else:
        _raw = _a[0] if _a else (sys.stdin.read().strip() or "{}")
        print(HelloRapp().perform(**json.loads(_raw)))
