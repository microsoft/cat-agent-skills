#!/usr/bin/env python3
"""Template: argument-aware approval request renderer.

Microsoft Agent Framework hands you the function call name and its arguments and
stops. Rendering the request a human actually reads is left to the maker, and the
framework's own generic form is ``Approve tool call transfer_money?`` -- a
question nobody can answer responsibly, because it shows none of the values that
make the action safe or unsafe.

This module turns a raw function call into a request that satisfies the approval
request contract in ``references/surfaces-and-contracts.md``: action, target,
consequence, scale, reversibility, decision.

Adapt the ``APPROVAL_SPECS`` table for the agent you are designing. Keep the
renderer. It is standard library only and can be unit tested without a model.

    python assets/templates/approval_renderer.py     # prints worked examples
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

# Values never shown in an approval request, whatever the tool declares. A gated
# tool that takes one of these is a separate finding: report it.
ALWAYS_REDACT = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "client_secret",
        "connection_string",
        "credential",
        "password",
        "private_key",
        "refresh_token",
        "secret",
        "token",
    }
)

MAX_VALUE_CHARACTERS = 120


@dataclass(frozen=True)
class ApprovalSpec:
    """How one gated tool describes itself to the person deciding."""

    action: str
    """The verb in the user's language, not the function name."""

    target: str
    """A format string over the call arguments, e.g. '{to}'."""

    consequence: str
    """The specific irreversible or external effect, stated plainly."""

    reversibility: str
    """Who can undo this, or that nobody can."""

    scale_argument: str | None = None
    """Argument holding a collection, when the blast radius is 'many'."""

    detail_arguments: tuple[str, ...] = ()
    """Extra arguments worth showing verbatim, in display order."""

    redact: frozenset[str] = field(default_factory=frozenset)
    """Argument names to mask in addition to ALWAYS_REDACT."""


# ---------------------------------------------------------------------------
# Replace this table. One entry per gated tool, matching the decision record.
# ---------------------------------------------------------------------------

APPROVAL_SPECS: dict[str, ApprovalSpec] = {
    "send_customer_email": ApprovalSpec(
        action="Send an email to a customer",
        target="{to}",
        consequence="The customer receives this message. A sent email cannot be recalled.",
        reversibility="Nobody. Once delivered it cannot be withdrawn.",
        detail_arguments=("subject", "body"),
    ),
    "issue_refund": ApprovalSpec(
        action="Refund a customer order",
        target="order {order_id}",
        consequence="Money leaves the company account and reaches the customer's payment method.",
        reversibility="Finance only, by raising a new charge. Not reversible by you.",
        detail_arguments=("amount", "currency"),
    ),
    "close_tickets": ApprovalSpec(
        action="Close support tickets and notify each requester",
        target="{resolution}",
        consequence="Every listed requester receives a closure notice.",
        reversibility="Anyone can reopen a ticket, but the notification cannot be recalled.",
        scale_argument="ticket_ids",
    ),
}


def mask(name: str, value: Any, extra_redactions: frozenset[str]) -> str:
    """Mask secrets, and shorten long values without hiding their size.

    Both sides of the comparison are lowercased. A spec that declares
    ``redact={"ApiKey"}`` must still mask an argument called ``apiKey``:
    this is the boundary that keeps a secret out of an approval request, so
    it cannot depend on the author matching the caller's capitalisation.
    """
    lowered = name.lower()
    if lowered in ALWAYS_REDACT:
        return "[redacted]"
    if lowered in {redaction.lower() for redaction in extra_redactions}:
        return "[redacted]"
    text = str(value)
    if len(text) <= MAX_VALUE_CHARACTERS:
        return text
    return f"{text[:MAX_VALUE_CHARACTERS]}... [{len(text)} characters total]"


def count_of(value: Any) -> int | None:
    if isinstance(value, (list, tuple, set, frozenset)):
        return len(value)
    return None


def render_approval_request(
    tool_name: str,
    arguments: Mapping[str, Any],
    specs: Mapping[str, ApprovalSpec] | None = None,
) -> str:
    """Render one approval request. Never returns a bare tool name."""
    table = APPROVAL_SPECS if specs is None else specs
    spec = table.get(tool_name)

    if spec is None:
        # A gated tool with no spec is a gap in the design, not a reason to
        # render nothing. Say so, and still show the values.
        shown = "\n".join(
            f"  {name}: {mask(name, value, frozenset())}"
            for name, value in arguments.items()
        )
        return (
            f"Approval needed: {tool_name}\n"
            f"{shown}\n"
            "\nNo approval wording is defined for this tool, so its consequence and "
            "reversibility are unstated. Do not approve until someone adds them."
        )

    try:
        target = spec.target.format(**arguments)
    except (KeyError, IndexError):
        target = "(target could not be resolved from the call arguments)"

    lines = [f"{spec.action}: {target}"]

    if spec.scale_argument is not None:
        total = count_of(arguments.get(spec.scale_argument))
        if total is not None:
            lines.append(f"Scale: {total} items affected by this single approval.")
        else:
            lines.append(
                f"Scale: unknown, {spec.scale_argument!r} was not a collection."
            )

    for name in spec.detail_arguments:
        if name in arguments:
            lines.append(f"{name}: {mask(name, arguments[name], spec.redact)}")

    lines.append(f"Consequence: {spec.consequence}")
    lines.append(f"Reversible by: {spec.reversibility}")
    lines.append("Approve to run it now. Deny to stop it and continue without it.")
    return "\n".join(lines)


def _demo() -> None:
    examples = [
        (
            "send_customer_email",
            {
                "to": "hans.jensen@contoso.example",
                "subject": "Your order has shipped",
                "body": "Hi Hans, your order left our warehouse this morning.",
            },
        ),
        (
            "close_tickets",
            {"ticket_ids": ["T-1001", "T-1002", "T-1003"], "resolution": "duplicate"},
        ),
        ("transfer_money", {"from_account": "1234567890", "amount": 500.0}),
    ]
    for tool_name, arguments in examples:
        print(f"--- {tool_name} ---")
        print(render_approval_request(tool_name, arguments))
        print()


if __name__ == "__main__":
    _demo()
