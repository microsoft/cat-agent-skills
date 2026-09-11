"""Synthetic agent tools used to demonstrate and test the inventory script.

Nothing here talks to a real system. Every body is a stub. The module exists so
that a run of the inventory has a known corpus, and so the workflow can be
demonstrated end to end without pointing at a customer codebase.

The set is deliberately uneven. It contains a tool that is correctly ungated, a
tool that is correctly gated, a tool that is irreversible and externally visible
but ungated, a bulk operation whose per-call gate multiplies into a clicking
exercise, and a tool whose gating logic is hidden behind ``conditional``.

This module is read statically with ``ast`` and is never imported or executed by
the inventory script or its tests. Importing it directly requires the
``agent_framework`` package; nothing in this submission needs that to run.
"""

from __future__ import annotations

from typing import Annotated

from agent_framework import tool


@tool
def lookup_customer(
    customer_id: Annotated[str, "The customer record identifier"],
) -> str:
    """Look up a customer record by identifier."""
    return f"Customer {customer_id}: Contoso Ltd, tier Gold, open tickets 2."


@tool
def search_orders(
    query: Annotated[str, "Free-text search over order history"],
) -> str:
    """Search order history and return matching orders."""
    return f"3 orders match {query!r}."


@tool
def draft_internal_note(
    ticket_id: Annotated[str, "Ticket the note belongs to"],
    body: Annotated[str, "Note text, visible to colleagues only"],
) -> str:
    """Create an internal note on a ticket. Colleagues can edit or delete it."""
    return f"Internal note saved on {ticket_id} ({len(body)} characters)."


@tool
def send_customer_email(
    to: Annotated[str, "Customer email address"],
    subject: Annotated[str, "Subject line"],
    body: Annotated[str, "Message body"],
) -> str:
    """Send an email to a customer from the shared support mailbox."""
    return f"Email sent to {to} with subject {subject!r}."


@tool(approval_mode="always_require")
def issue_refund(
    order_id: Annotated[str, "Order to refund"],
    amount: Annotated[float, "Refund amount"],
    currency: Annotated[str, "ISO currency code"] = "DKK",
) -> str:
    """Refund a customer order to the original payment method."""
    return f"Refunded {amount} {currency} against order {order_id}."


@tool(approval_mode="always_require")
def close_tickets(
    ticket_ids: Annotated[list[str], "Tickets to close"],
    resolution: Annotated[str, "Resolution code"],
) -> str:
    """Close each ticket in the list and notify its requester."""
    closed = []
    for ticket_id in ticket_ids:
        closed.append(ticket_id)
    return f"Closed {len(closed)} tickets as {resolution}."


@tool(approval_mode="conditional")
def update_subscription(
    subscription_id: Annotated[str, "Subscription to change"],
    new_plan: Annotated[str, "Target plan code"],
) -> str:
    """Update a subscription to a different plan."""
    return f"Subscription {subscription_id} moved to {new_plan}."


@tool(name="purge_export_files")
def purge_exports(
    older_than_days: Annotated[int, "Delete exports older than this many days"],
) -> str:
    """Permanently delete generated export files from the staging share."""
    return f"Purged exports older than {older_than_days} days."
