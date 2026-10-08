#!/usr/bin/env python3
"""Template: a real approval loop with a working deny path.

Microsoft Agent Framework's documented sample loop contains, verbatim:

    user_approval = True  # Replace with actual user input

That line is the seam this template closes. Everything below is the documented
control flow with three things added that the docs leave to the maker:

1. the approval value comes from a decision function, never a constant;
2. the request is rendered through ``approval_renderer`` so a human can judge it;
3. a denial is handled deliberately instead of dead-ending or silently retrying.

Requires ``agent_framework``, and expects ``approval_renderer.py`` to sit beside it:
the import below is a sibling import, so copy both templates into the same package
or adjust the import to wherever you put the renderer. Adapt the marked sections;
keep the shape.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Protocol

from agent_framework import Message

from approval_renderer import render_approval_request

# ---------------------------------------------------------------------------
# 1. The decision function
#
# Anything that returns a real boolean from a real human. A console prompt, a
# web request, an Adaptive Card response, a queued task. The only forbidden
# implementation is one that returns a constant.
# ---------------------------------------------------------------------------


class ApprovalDecider(Protocol):
    def __call__(self, request_text: str, tool_name: str) -> bool: ...


def console_decider(request_text: str, tool_name: str) -> bool:
    print(request_text)
    answer = input("Approve? (y/N): ").strip().lower()
    return answer in {"y", "yes"}


def rejecting_decider(request_text: str, tool_name: str) -> bool:
    """Safe default for tests and unattended runs. Never approves."""
    return False


# ---------------------------------------------------------------------------
# 2. Argument normalisation
#
# ``function_call.arguments`` may arrive as a mapping or as a JSON string.
# Normalise once so the renderer always receives a mapping.
# ---------------------------------------------------------------------------


def as_mapping(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return {"arguments": arguments}
        return parsed if isinstance(parsed, dict) else {"arguments": parsed}
    return {"arguments": arguments}


# ---------------------------------------------------------------------------
# 3. The loop
# ---------------------------------------------------------------------------


async def run_with_approvals(
    query: str,
    agent: Any,
    decide: ApprovalDecider = rejecting_decider,
    on_denied: Callable[[str, dict[str, Any]], None] | None = None,
    max_rounds: int = 10,
) -> Any:
    """Run the agent, pausing for a real decision on every gated tool call.

    Without a session, each round must carry the original query, the assistant
    message holding the approval request, and the approval response.
    """
    result = await agent.run(query)
    rounds = 0

    while result.user_input_requests:
        rounds += 1
        if rounds > max_rounds:
            # A loop that will not settle is a design fault, not a runtime blip.
            # Stop and surface it rather than approving to escape.
            raise RuntimeError(
                f"Approval loop exceeded {max_rounds} rounds. Check for a tool the "
                "agent retries after denial."
            )

        new_inputs: list[Any] = [query]

        for user_input_needed in result.user_input_requests:
            if user_input_needed.function_call is None:
                continue

            tool_name = user_input_needed.function_call.name
            arguments = as_mapping(user_input_needed.function_call.arguments)
            request_text = render_approval_request(tool_name, arguments)

            approved = decide(request_text, tool_name)

            new_inputs.append(
                Message(role="assistant", contents=[user_input_needed])
            )
            new_inputs.append(
                Message(
                    role="user",
                    contents=[user_input_needed.to_function_approval_response(approved)],
                )
            )

            if not approved:
                if on_denied is not None:
                    on_denied(tool_name, arguments)
                # The framework's approval response carries a boolean only. To
                # tell the agent *why*, and what to do next, add an ordinary
                # user message. Keep it factual; it becomes model context.
                new_inputs.append(
                    Message(
                        role="user",
                        contents=[
                            f"The {tool_name} call was denied by a human reviewer. "
                            "Do not attempt it again in this conversation. Tell me "
                            "what you were going to do, and continue with the parts "
                            "of the task that do not need it."
                        ],
                    )
                )

        result = await agent.run(new_inputs)

    return result


# ---------------------------------------------------------------------------
# 4. Required agent instructions
#
# Code alone cannot produce good denial behaviour, because what the agent does
# after a rejection is a model decision. Add this to the agent's instructions
# for every gated tool, and verify it by actually denying during testing.
# ---------------------------------------------------------------------------

DENIAL_INSTRUCTIONS = """\
When a tool call is denied:

- Do not call the same tool again with the same arguments in this conversation.
- Do not silently substitute a different tool to achieve the same effect.
- Tell the user plainly what you were going to do and that it was declined.
- Continue with any part of the task that does not depend on the declined action.
- If nothing useful remains, say so and stop. Do not invent a partial result.
"""
