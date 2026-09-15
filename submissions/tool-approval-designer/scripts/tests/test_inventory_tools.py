"""Regression tests for scripts/inventory_tools.py.

Run from the skill root (the directory containing SKILL.md):

    python scripts/tests/test_inventory_tools.py
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_PATH = Path(__file__).parents[1] / "inventory_tools.py"
SUBMISSION_ROOT = SCRIPT_PATH.parents[1]
SPEC = importlib.util.spec_from_file_location("inventory_tools", SCRIPT_PATH)
assert SPEC and SPEC.loader
inventory_tools = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = inventory_tools
SPEC.loader.exec_module(inventory_tools)


def scan(source: str, filename: str = "memory.py"):
    return inventory_tools.scan_python(source, filename)


def only(source: str):
    records, _ = scan(source)
    assert len(records) == 1, f"expected exactly one tool, got {len(records)}"
    return records[0]


def categories(record) -> set[str]:
    return {signal.category for signal in record.signals}


class DecoratorDetectionTests(unittest.TestCase):
    def test_bare_decorator(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Return a heartbeat.'''\n"
            "    return 'ok'\n"
        )
        self.assertEqual(record.name, "ping")
        self.assertEqual(record.language, "python")
        self.assertEqual(record.detection, "parsed")

    def test_called_decorator_without_arguments(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool()\n"
            "def ping() -> str:\n"
            "    '''Return a heartbeat.'''\n"
            "    return 'ok'\n"
        )
        self.assertEqual(record.name, "ping")
        self.assertFalse(record.approval_mode_explicit)

    def test_aliased_import(self):
        record = only(
            "from agent_framework import tool as af_tool\n"
            "@af_tool(approval_mode='always_require')\n"
            "def ping() -> str:\n"
            "    '''Return a heartbeat.'''\n"
            "    return 'ok'\n"
        )
        self.assertTrue(record.gated)

    def test_module_qualified_decorator(self):
        record = only(
            "import agent_framework\n"
            "@agent_framework.tool\n"
            "def ping() -> str:\n"
            "    '''Return a heartbeat.'''\n"
            "    return 'ok'\n"
        )
        self.assertEqual(record.name, "ping")

    def test_aliased_module_decorator(self):
        record = only(
            "import agent_framework as af\n"
            "@af.tool(approval_mode='always_require')\n"
            "def ping() -> str:\n"
            "    '''Return a heartbeat.'''\n"
            "    return 'ok'\n"
        )
        self.assertTrue(record.gated)

    def test_unrelated_decorator_is_ignored(self):
        records, _ = scan(
            "import functools\n"
            "@functools.cache\n"
            "def ping() -> str:\n"
            "    return 'ok'\n"
        )
        self.assertEqual(records, [])

    def test_unrelated_module_attribute_is_ignored(self):
        records, _ = scan(
            "import fastapi\n"
            "app = fastapi.FastAPI()\n"
            "@app.get('/ping')\n"
            "def ping() -> str:\n"
            "    return 'ok'\n"
        )
        self.assertEqual(records, [])

    def test_async_tool_is_detected(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool(approval_mode='always_require')\n"
            "async def ping() -> str:\n"
            "    '''Return a heartbeat.'''\n"
            "    return 'ok'\n"
        )
        self.assertTrue(record.gated)

    def test_method_inside_class_is_detected(self):
        record = only(
            "from agent_framework import tool\n"
            "class Toolbox:\n"
            "    @tool\n"
            "    def ping(self) -> str:\n"
            "        '''Return a heartbeat.'''\n"
            "        return 'ok'\n"
        )
        self.assertEqual(record.name, "ping")

    def test_stacked_decorators_yield_one_record(self):
        records, _ = scan(
            "import functools\n"
            "from agent_framework import tool\n"
            "@functools.wraps(print)\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Return a heartbeat.'''\n"
            "    return 'ok'\n"
        )
        self.assertEqual(len(records), 1)

    def test_multiple_tools_in_one_module(self):
        records, _ = scan(
            "from agent_framework import tool\n"
            "@tool\n"
            "def one() -> str:\n"
            "    '''First.'''\n"
            "    return ''\n"
            "@tool\n"
            "def two() -> str:\n"
            "    '''Second.'''\n"
            "    return ''\n"
        )
        self.assertEqual([record.name for record in records], ["one", "two"])


class ToolProvenanceTests(unittest.TestCase):
    """A '@tool' from another library is not an Agent Framework tool."""

    def test_foreign_tool_import_is_not_inventoried(self):
        records, notes = scan(
            "from langchain_core.tools import tool\n"
            "@tool\n"
            "def send_email(to: str) -> str:\n"
            "    '''Send an email.'''\n"
            "    return ''\n"
        )
        self.assertEqual(records, [])
        self.assertEqual(len(notes), 1)
        self.assertIn("langchain_core.tools", notes[0])
        self.assertIn("not agent_framework", notes[0])

    def test_aliased_foreign_tool_import_is_not_inventoried(self):
        records, _ = scan(
            "from langchain_core.tools import tool as lc_tool\n"
            "@lc_tool(approval_mode='always_require')\n"
            "def send_email(to: str) -> str:\n"
            "    '''Send an email.'''\n"
            "    return ''\n"
        )
        self.assertEqual(records, [])

    def test_locally_defined_tool_decorator_is_not_inventoried(self):
        records, notes = scan(
            "def tool(fn):\n"
            "    return fn\n"
            "@tool\n"
            "def send_email(to: str) -> str:\n"
            "    '''Send an email.'''\n"
            "    return ''\n"
        )
        self.assertEqual(records, [])
        self.assertIn("a definition in this file", notes[0])

    def test_skip_note_counts_agree_with_the_number_skipped(self):
        _, notes = scan(
            "from langchain_core.tools import tool\n"
            "@tool\n"
            "def one() -> str:\n"
            "    '''First.'''\n"
            "    return ''\n"
            "@tool\n"
            "def two() -> str:\n"
            "    '''Second.'''\n"
            "    return ''\n"
        )
        self.assertIn("2 decorated functions", notes[0])

    def test_single_skip_note_is_singular(self):
        _, notes = scan(
            "from langchain_core.tools import tool\n"
            "@tool\n"
            "def one() -> str:\n"
            "    '''First.'''\n"
            "    return ''\n"
        )
        self.assertIn("1 decorated function", notes[0])
        self.assertNotIn("1 decorated functions", notes[0])

    def test_untraceable_tool_is_kept_but_marked_best_effort(self):
        record = only(
            "@tool\n"
            "def send_email(to: str) -> str:\n"
            "    '''Send an email.'''\n"
            "    return ''\n"
        )
        self.assertEqual(record.name, "send_email")
        self.assertEqual(record.detection, "best-effort")
        self.assertTrue(
            any("could not be traced" in note for note in record.notes),
            record.notes,
        )

    def test_traced_import_is_parsed_not_best_effort(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def send_email(to: str) -> str:\n"
            "    '''Send an email.'''\n"
            "    return ''\n"
        )
        self.assertEqual(record.detection, "parsed")
        self.assertEqual(record.notes, [])

    def test_submodule_import_is_traced(self):
        record = only(
            "from agent_framework.tools import tool\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return ''\n"
        )
        self.assertEqual(record.detection, "parsed")

    def test_star_import_is_traced(self):
        record = only(
            "from agent_framework import *\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return ''\n"
        )
        self.assertEqual(record.detection, "parsed")

    def test_foreign_star_import_does_not_trace(self):
        record = only(
            "from langchain_core.tools import *\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return ''\n"
        )
        self.assertEqual(record.detection, "best-effort")

    def test_a_foreign_import_does_not_suppress_a_real_one(self):
        records, _ = scan(
            "from langchain_core.tools import tool as lc_tool\n"
            "from agent_framework import tool\n"
            "@lc_tool\n"
            "def foreign() -> str:\n"
            "    '''Not ours.'''\n"
            "    return ''\n"
            "@tool\n"
            "def ours() -> str:\n"
            "    '''Ours.'''\n"
            "    return ''\n"
        )
        self.assertEqual([record.name for record in records], ["ours"])

    def test_module_qualified_decorator_needs_the_module_name(self):
        records, _ = scan(
            "import langchain as agents\n"
            "@agents.tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return ''\n"
        )
        self.assertEqual(records, [])

    def test_imported_module_qualified_decorator_is_confirmed(self):
        record = only(
            "import agent_framework\n"
            "@agent_framework.tool(approval_mode='always_require')\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return ''\n"
        )
        self.assertEqual(record.detection, "parsed")
        self.assertEqual(record.notes, [])

    def test_module_qualified_decorator_without_the_import_is_best_effort(self):
        """Naming the framework is not the same as importing it."""
        record = only(
            "@agent_framework.tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return ''\n"
        )
        self.assertEqual(record.detection, "best-effort")
        self.assertEqual(len(record.notes), 1)
        self.assertIn("could not be traced", record.notes[0])

    def test_untraceable_tools_count_as_best_effort(self):
        inventory = inventory_tools.Inventory(root=".", tools=[], notes=[])
        inventory.tools.extend(
            only(
                "@tool\n"
                "def ping() -> str:\n"
                "    '''Heartbeat.'''\n"
                "    return ''\n"
            )
            for _ in range(1)
        )
        self.assertEqual(inventory.counts()["best_effort"], 1)


class ApprovalModeTests(unittest.TestCase):
    def mode(self, decorator: str):
        return only(
            "from agent_framework import tool\n"
            f"{decorator}\n"
            "def ping() -> str:\n"
            "    '''Return a heartbeat.'''\n"
            "    return 'ok'\n"
        )

    def test_always_require_is_gated(self):
        record = self.mode("@tool(approval_mode='always_require')")
        self.assertEqual(record.approval_mode, "always_require")
        self.assertTrue(record.approval_mode_explicit)
        self.assertTrue(record.gated)

    def test_never_require_is_not_gated(self):
        record = self.mode("@tool(approval_mode='never_require')")
        self.assertEqual(record.approval_mode, "never_require")
        self.assertTrue(record.approval_mode_explicit)
        self.assertFalse(record.gated)

    def test_absent_mode_defaults_to_never_require(self):
        record = self.mode("@tool")
        self.assertEqual(record.approval_mode, "never_require")
        self.assertFalse(record.approval_mode_explicit)
        self.assertFalse(record.gated)

    def test_conditional_is_gated_but_annotated(self):
        record = self.mode("@tool(approval_mode='conditional')")
        self.assertTrue(record.gated)
        self.assertTrue(any("conditional" in note for note in record.notes))

    def test_dynamic_mode_is_reported_as_unreadable(self):
        record = self.mode("@tool(approval_mode=CHOSEN_MODE)")
        self.assertEqual(record.approval_mode, inventory_tools.DYNAMIC_APPROVAL_MODE)
        self.assertTrue(record.approval_mode_explicit)
        self.assertFalse(record.gated)
        self.assertTrue(any("statically" in note for note in record.notes))

    def test_undocumented_mode_is_flagged(self):
        record = self.mode("@tool(approval_mode='sometimes')")
        self.assertTrue(any("documented modes" in note for note in record.notes))

    def test_name_keyword_overrides_function_name(self):
        record = self.mode("@tool(name='heartbeat')")
        self.assertEqual(record.name, "heartbeat")
        self.assertEqual(record.function, "ping")

    def test_non_string_name_falls_back_to_function_name(self):
        record = self.mode("@tool(name=NAME_CONSTANT)")
        self.assertEqual(record.name, "ping")


class WriteSignalTests(unittest.TestCase):
    def test_body_call_to_write_verb(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def act(payload: str) -> str:\n"
            "    '''Do a thing.'''\n"
            "    return client.create_record(payload)\n"
        )
        self.assertEqual(record.proposed_write, "write")

    def test_http_write_method(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def act(payload: str) -> str:\n"
            "    '''Do a thing.'''\n"
            "    return requests.put(URL, json=payload)\n"
        )
        self.assertEqual(record.proposed_write, "write")

    def test_file_opened_for_writing(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def act(path: str) -> str:\n"
            "    '''Do a thing.'''\n"
            "    handle = open(path, 'w')\n"
            "    return path\n"
        )
        self.assertEqual(record.proposed_write, "write")

    def test_file_opened_for_reading_is_not_a_write(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def fetch(path: str) -> str:\n"
            "    '''Read a stored value.'''\n"
            "    handle = open(path, 'r')\n"
            "    return path\n"
        )
        self.assertEqual(record.proposed_write, "read")

    def test_write_capable_mode_permutations_are_all_writes(self):
        """Modes are order-independent flags, not a fixed vocabulary."""
        for mode in (
            "w", "a", "x", "wb", "ab", "xb", "wt", "at",
            "wb+", "w+b", "w+", "a+", "ab+", "a+b",
            "r+", "rb+", "r+b", "x+b", "xb+",
        ):
            with self.subTest(mode=mode):
                record = only(
                    "from agent_framework import tool\n"
                    "@tool\n"
                    "def act(path: str) -> str:\n"
                    "    '''Do a thing.'''\n"
                    f"    handle = open(path, {mode!r})\n"
                    "    return path\n"
                )
                self.assertEqual(record.proposed_write, "write")

    def test_read_only_mode_permutations_are_not_writes(self):
        for mode in ("r", "rb", "rt", "br"):
            with self.subTest(mode=mode):
                record = only(
                    "from agent_framework import tool\n"
                    "@tool\n"
                    "def fetch(path: str) -> str:\n"
                    "    '''Read a stored value.'''\n"
                    f"    handle = open(path, {mode!r})\n"
                    "    return path\n"
                )
                self.assertEqual(record.proposed_write, "read")

    def test_keyword_mode_argument_is_honoured(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def act(path: str) -> str:\n"
            "    '''Do a thing.'''\n"
            "    handle = open(path, mode='a+b')\n"
            "    return path\n"
        )
        self.assertEqual(record.proposed_write, "write")

    def test_runtime_mode_is_surfaced_not_downgraded(self):
        """An unresolvable mode must not silently become read-only."""
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def act(path: str, mode: str) -> str:\n"
            "    '''Do a thing.'''\n"
            "    handle = open(path, mode)\n"
            "    return path\n"
        )
        self.assertEqual(record.proposed_write, "write")
        self.assertTrue(
            any("computed at runtime" in signal.evidence for signal in record.signals)
        )

    def test_open_evidence_names_the_mode_it_found(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def act(path: str) -> str:\n"
            "    '''Do a thing.'''\n"
            "    handle = open(path, 'rb+')\n"
            "    return path\n"
        )
        self.assertTrue(
            any("'rb+'" in signal.evidence for signal in record.signals)
        )

    def test_data_modifying_sql_literal(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def act(row_id: str) -> str:\n"
            "    '''Do a thing.'''\n"
            "    return run('DELETE FROM invoices WHERE id = ?', row_id)\n"
        )
        self.assertEqual(record.proposed_write, "write")

    def test_select_sql_literal_is_not_a_write(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def fetch(row_id: str) -> str:\n"
            "    '''Read a row.'''\n"
            "    return run('SELECT total FROM invoices WHERE id = ?', row_id)\n"
        )
        self.assertEqual(record.proposed_write, "read")

    def test_pure_read_has_no_write_signal(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def fetch(row_id: str) -> str:\n"
            "    '''Look up a stored value by identifier.'''\n"
            "    return cache.get(row_id)\n"
        )
        self.assertEqual(record.proposed_write, "read")

    def test_stdlib_close_call_is_not_a_write(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def fetch(path: str) -> str:\n"
            "    '''Look up a stored value.'''\n"
            "    handle = open(path)\n"
            "    body = handle.read()\n"
            "    handle.close()\n"
            "    return body\n"
        )
        self.assertEqual(record.proposed_write, "read")

    def test_noun_order_in_docstring_is_not_a_write(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def search_orders(query: str) -> str:\n"
            "    '''Search order history and return matching orders.'''\n"
            "    return index.query(query)\n"
        )
        self.assertEqual(record.proposed_write, "read")

    def test_write_verb_in_tool_name(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def cancel_booking(booking_id: str) -> str:\n"
            "    '''Stop a reservation.'''\n"
            "    return backend.run(booking_id)\n"
        )
        self.assertEqual(record.proposed_write, "write")


class ExternalSignalTests(unittest.TestCase):
    def test_external_term_in_name(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def send_invoice(to: str) -> str:\n"
            "    '''Deliver a document.'''\n"
            "    return gateway.post(to)\n"
        )
        self.assertEqual(record.proposed_visibility, "external")

    def test_external_term_in_docstring(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def dispatch(body: str) -> str:\n"
            "    '''Publish the note to the customer portal.'''\n"
            "    return gateway.post(body)\n"
        )
        self.assertEqual(record.proposed_visibility, "external")

    def test_internal_tool_is_not_external(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def add_internal_note(body: str) -> str:\n"
            "    '''Create a note colleagues can edit.'''\n"
            "    return store.save(body)\n"
        )
        self.assertEqual(record.proposed_visibility, "internal-or-unknown")

    def test_external_read_is_annotated(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def lookup_customer(customer_id: str) -> str:\n"
            "    '''Look up a customer record.'''\n"
            "    return store.get(customer_id)\n"
        )
        self.assertEqual(record.proposed_write, "read")
        self.assertTrue(any("only reads" in note for note in record.notes))


class BlastRadiusTests(unittest.TestCase):
    def test_collection_annotation(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def notify(targets: list[str]) -> str:\n"
            "    '''Send a note.'''\n"
            "    return str(targets)\n"
        )
        self.assertEqual(record.proposed_blast, "many")

    def test_collection_parameter_name(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def notify(recipients) -> str:\n"
            "    '''Send a note.'''\n"
            "    return str(recipients)\n"
        )
        self.assertEqual(record.proposed_blast, "many")

    def test_suffixed_parameter_name(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def notify(ticket_ids) -> str:\n"
            "    '''Send a note.'''\n"
            "    return str(ticket_ids)\n"
        )
        self.assertEqual(record.proposed_blast, "many")

    def test_bulk_term_in_name(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def bulk_update(target: str) -> str:\n"
            "    '''Change a value.'''\n"
            "    return target\n"
        )
        self.assertEqual(record.proposed_blast, "many")

    def test_write_inside_loop(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def process(rows) -> str:\n"
            "    '''Handle rows.'''\n"
            "    for row in rows:\n"
            "        store.save(row)\n"
            "    return 'done'\n"
        )
        self.assertEqual(record.proposed_blast, "many")
        self.assertIn(
            "writes inside a loop",
            [signal.evidence for signal in record.signals],
        )

    def test_single_target_is_one(self):
        record = only(
            "from agent_framework import tool\n"
            "@tool\n"
            "def update_record(record_id: str) -> str:\n"
            "    '''Change one stored value.'''\n"
            "    return record_id\n"
        )
        self.assertEqual(record.proposed_blast, "one")


class GoDetectionTests(unittest.TestCase):
    def test_wrapped_tool_is_gated(self):
        records, _ = inventory_tools.scan_go(
            'approvedWeatherTool := tool.ApprovalRequiredFunc(weatherTool)\n', "main.go"
        )
        gated = {record.name: record.gated for record in records}
        self.assertTrue(gated["weatherTool"])

    def test_unwrapped_binding_is_ungated(self):
        records, _ = inventory_tools.scan_go(
            "weatherTool := tool.NewFunc(getWeather)\n"
            "deleteTool := tool.NewFunc(deleteFile)\n"
            "approved := tool.ApprovalRequiredFunc(weatherTool)\n",
            "main.go",
        )
        gated = {record.name: record.gated for record in records}
        self.assertTrue(gated["weatherTool"])
        self.assertFalse(gated["deleteTool"])

    def test_go_records_are_best_effort_and_annotated(self):
        records, _ = inventory_tools.scan_go(
            "weatherTool := tool.NewFunc(getWeather)\n", "main.go"
        )
        self.assertEqual(records[0].detection, "best-effort")
        self.assertTrue(any("best-effort" in note for note in records[0].notes))

    def test_unrelated_go_code_yields_nothing(self):
        records, _ = inventory_tools.scan_go(
            "client := http.NewClient()\nfmt.Println(client)\n", "main.go"
        )
        self.assertEqual(records, [])

    def test_binding_line_points_at_the_declaration(self):
        records, _ = inventory_tools.scan_go(
            "package main\n"
            "\n"
            "weatherTool := tool.NewFunc(getWeather)\n"
            "\n"
            "approved := tool.ApprovalRequiredFunc(weatherTool)\n",
            "main.go",
        )
        record = next(r for r in records if r.name == "weatherTool")
        self.assertEqual(record.line, 3)

    def test_binding_line_survives_a_blank_line_above_it(self):
        """The pattern's leading '^\\s*' must not be counted as the line."""
        records, _ = inventory_tools.scan_go(
            "package main\n\n\n\nrefundTool := tool.NewFunc(issueRefund)\n",
            "main.go",
        )
        self.assertEqual(records[0].line, 5)

    def test_wrapped_only_tool_points_at_the_approval_call(self):
        """A tool declared elsewhere must not be reported at line 0."""
        records, _ = inventory_tools.scan_go(
            "package main\n"
            "\n"
            "func main() {\n"
            "\tagent.Run(tool.ApprovalRequiredFunc(weatherTool))\n"
            "}\n",
            "main.go",
        )
        record = next(r for r in records if r.name == "weatherTool")
        self.assertEqual(record.line, 4)
        self.assertTrue(
            any("declaration was not found" in note for note in record.notes)
        )

    def test_no_go_record_is_ever_emitted_at_line_zero(self):
        records, _ = inventory_tools.scan_go(
            "weatherTool := tool.NewFunc(getWeather)\n"
            "agent.Run(tool.ApprovalRequiredFunc(refundTool))\n",
            "main.go",
        )
        self.assertEqual(len(records), 2)
        self.assertTrue(all(record.line > 0 for record in records))


class FileHandlingTests(unittest.TestCase):
    def build(self, files: dict[str, str], **kwargs):
        directory = Path(tempfile.mkdtemp())
        for name, body in files.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return directory, inventory_tools.build_inventory(
            directory, kwargs.get("languages", {"python", "go"}), kwargs.get("include_tests", False)
        )

    def test_unparseable_python_is_noted_not_fatal(self):
        _, inventory = self.build({"broken.py": "def oops(:\n"})
        self.assertEqual(inventory.tools, [])
        self.assertTrue(any("could not be parsed" in note for note in inventory.notes))

    def test_non_utf8_file_is_noted_not_fatal(self):
        directory = Path(tempfile.mkdtemp())
        (directory / "binary.py").write_bytes(b"\xff\xfe\x00bad bytes\n")
        inventory = inventory_tools.build_inventory(directory, {"python"}, False)
        self.assertTrue(any("could not be read" in note for note in inventory.notes))

    def test_utf8_bom_file_is_parsed_not_skipped(self):
        """CPython accepts a BOM in source, so the inventory must too."""
        directory = Path(tempfile.mkdtemp())
        body = (
            "from agent_framework import tool\n"
            "@tool(approval_mode='always_require')\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return 'ok'\n"
        )
        (directory / "bom.py").write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
        inventory = inventory_tools.build_inventory(directory, {"python"}, False)
        self.assertEqual([record.name for record in inventory.tools], ["ping"])
        self.assertTrue(inventory.tools[0].gated)
        self.assertEqual(inventory.notes, [])

    def test_test_files_are_skipped_by_default(self):
        body = (
            "from agent_framework import tool\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return 'ok'\n"
        )
        _, inventory = self.build({"test_thing.py": body})
        self.assertEqual(inventory.tools, [])

    def test_test_files_are_included_on_request(self):
        body = (
            "from agent_framework import tool\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return 'ok'\n"
        )
        _, inventory = self.build({"test_thing.py": body}, include_tests=True)
        self.assertEqual(len(inventory.tools), 1)

    TOOL_BODY = (
        "from agent_framework import tool\n"
        "@tool\n"
        "def ping() -> str:\n"
        "    '''Heartbeat.'''\n"
        "    return 'ok'\n"
    )

    def scan_under_ancestor(self, ancestor: str):
        """Build tool.py inside <tmp>/<ancestor>/repo and scan repo itself."""
        directory = Path(tempfile.mkdtemp())
        repo = directory / ancestor / "repo"
        repo.mkdir(parents=True)
        (repo / "tool.py").write_text(self.TOOL_BODY, encoding="utf-8")
        return inventory_tools.build_inventory(repo, {"python"}, False)

    def test_a_skipped_name_above_root_does_not_empty_the_inventory(self):
        """Only names at or below root are ours to judge.

        Testing whole paths against SKIP_DIRECTORIES inspects the ancestors too,
        so a repo checked out under a directory called build, dist, env or venv
        would report zero tools. That failure is silent and looks like "this
        codebase has no tools", which is the worst possible way to be wrong.
        """
        for ancestor in ("build", "dist", "env", "venv", "node_modules", ".git"):
            with self.subTest(ancestor=ancestor):
                inventory = self.scan_under_ancestor(ancestor)
                self.assertEqual(
                    [record.name for record in inventory.tools],
                    ["ping"],
                    f"a parent directory named {ancestor} emptied the inventory",
                )

    def test_a_tests_directory_above_root_does_not_empty_the_inventory(self):
        inventory = self.scan_under_ancestor("tests")
        self.assertEqual([record.name for record in inventory.tools], ["ping"])

    def test_a_root_named_tests_is_scanned_as_an_explicit_request(self):
        """Naming a directory is as explicit as naming a file."""
        directory = Path(tempfile.mkdtemp())
        root = directory / "tests"
        root.mkdir()
        (root / "tool.py").write_text(self.TOOL_BODY, encoding="utf-8")
        inventory = inventory_tools.build_inventory(root, {"python"}, False)
        self.assertEqual([record.name for record in inventory.tools], ["ping"])

    def test_a_tests_directory_below_root_is_still_pruned(self):
        _, inventory = self.build({"tests/tool.py": self.TOOL_BODY})
        self.assertEqual(inventory.tools, [])

    def test_an_explicitly_named_test_file_is_read(self):
        """Pointing at a file is an explicit request, not a directory sweep."""
        body = (
            "from agent_framework import tool\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return 'ok'\n"
        )
        directory = Path(tempfile.mkdtemp())
        (directory / "tests").mkdir()
        path = directory / "tests" / "test_thing.py"
        path.write_text(body, encoding="utf-8")
        inventory = inventory_tools.build_inventory(path, {"python"}, False)
        self.assertEqual([record.name for record in inventory.tools], ["ping"])

    def test_an_explicit_file_the_inventory_cannot_read_is_noted(self):
        directory = Path(tempfile.mkdtemp())
        path = directory / "README.md"
        path.write_text("not source\n", encoding="utf-8")
        inventory = inventory_tools.build_inventory(path, {"python"}, False)
        self.assertEqual(inventory.tools, [])
        self.assertTrue(
            any("does not read" in note for note in inventory.notes)
        )

    def test_vendor_directories_are_skipped(self):
        body = (
            "from agent_framework import tool\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return 'ok'\n"
        )
        _, inventory = self.build({"node_modules/pkg/thing.py": body})
        self.assertEqual(inventory.tools, [])

    def test_vendor_directories_are_pruned_not_just_filtered(self):
        """Skipping must happen during traversal, not after walking everything."""
        body = (
            "from agent_framework import tool\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return 'ok'\n"
        )
        directory, _ = self.build(
            {
                "app.py": body,
                "node_modules/pkg/lib/deep/vendored.py": body,
                ".git/objects/pack/thing.py": body,
            }
        )
        visited: list[str] = []
        real_walk = inventory_tools.os.walk

        def recording_walk(top, *args, **kwargs):
            for entry in real_walk(top, *args, **kwargs):
                visited.append(entry[0])
                yield entry

        with mock.patch.object(inventory_tools.os, "walk", recording_walk):
            inventory = inventory_tools.build_inventory(directory, {"python"}, False)

        self.assertEqual([record.name for record in inventory.tools], ["ping"])
        self.assertTrue(visited, "the walker was never called")
        for skipped in ("node_modules", ".git"):
            self.assertFalse(
                any(skipped in entry for entry in visited),
                f"{skipped} was traversed rather than pruned",
            )

    def test_language_filter_excludes_go(self):
        directory, _ = self.build({"main.go": "t := tool.NewFunc(f)\n"})
        inventory = inventory_tools.build_inventory(directory, {"python"}, False)
        self.assertEqual(inventory.tools, [])

    def test_sources_are_posix_relative_paths(self):
        body = (
            "from agent_framework import tool\n"
            "@tool\n"
            "def ping() -> str:\n"
            "    '''Heartbeat.'''\n"
            "    return 'ok'\n"
        )
        _, inventory = self.build({"pkg/agent.py": body})
        self.assertEqual(inventory.tools[0].source, "pkg/agent.py")


class OutputAndExitCodeTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = inventory_tools.main(argv)
        return code, buffer.getvalue()

    def test_json_output_shape(self):
        code, out = self.run_cli(["assets/samples", "--format", "json"])
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(payload["inventory"], inventory_tools.INVENTORY_NAME)
        self.assertEqual(payload["version"], inventory_tools.INVENTORY_VERSION)
        for key in ("root", "counts", "tools", "notes", "disclaimer"):
            self.assertIn(key, payload)
        first = payload["tools"][0]
        for key in (
            "name",
            "language",
            "detection",
            "approval_mode",
            "approval_mode_explicit",
            "gated",
            "proposed_write",
            "proposed_visibility",
            "proposed_blast",
            "signals",
            "notes",
        ):
            self.assertIn(key, first)

    def test_table_output_carries_the_honesty_footer(self):
        _, out = self.run_cli(["assets/samples"])
        self.assertIn("Signals are advisory evidence, not verdicts.", out)

    def test_clean_run_exits_zero(self):
        code, _ = self.run_cli(["assets/samples"])
        self.assertEqual(code, 0)

    def test_fail_on_ungated_write_exits_one(self):
        code, _ = self.run_cli(["assets/samples", "--fail-on", "ungated-write"])
        self.assertEqual(code, 1)

    def test_fail_on_ungated_write_external_exits_one(self):
        code, _ = self.run_cli(["assets/samples", "--fail-on", "ungated-write-external"])
        self.assertEqual(code, 1)

    def test_missing_path_exits_two(self):
        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            code = inventory_tools.main(["does/not/exist"])
        self.assertEqual(code, 2)
        self.assertIn("Path not found", buffer.getvalue())

    def test_gate_does_not_trigger_on_a_fully_gated_corpus(self):
        directory = Path(tempfile.mkdtemp())
        (directory / "agent.py").write_text(
            "from agent_framework import tool\n"
            "@tool(approval_mode='always_require')\n"
            "def send_customer_email(to: str) -> str:\n"
            "    '''Send an email to a customer.'''\n"
            "    return to\n",
            encoding="utf-8",
        )
        code, _ = self.run_cli([directory.as_posix(), "--fail-on", "ungated-write"])
        self.assertEqual(code, 0)


class SummaryAgreementTests(unittest.TestCase):
    """The summary block must read correctly at a count of one and above one.

    A count of exactly one is the case that regresses, because the plural form is
    the one written first and the singular is the afterthought.
    """

    def render(self, files: dict[str, str]) -> str:
        directory = Path(tempfile.mkdtemp())
        for name, body in files.items():
            (directory / name).write_text(body, encoding="utf-8")
        inventory = inventory_tools.build_inventory(directory, {"python", "go"}, False)
        return inventory_tools.render_table(inventory)

    ONE_UNGATED_EXTERNAL_WRITE = (
        "from agent_framework import tool\n"
        "@tool\n"
        "def send_customer_email(to: str, body: str) -> str:\n"
        "    '''Send an email to a customer.'''\n"
        "    return to\n"
    )

    TWO_UNGATED_EXTERNAL_WRITES = ONE_UNGATED_EXTERNAL_WRITE + (
        "@tool\n"
        "def publish_customer_notice(recipient: str) -> str:\n"
        "    '''Publish a notice to a customer.'''\n"
        "    return recipient\n"
    )

    # The clause that regressed: 'of which 1 also look externally visible.'

    def test_singular_external_clause_uses_looks(self):
        out = self.render({"agent.py": self.ONE_UNGATED_EXTERNAL_WRITE})
        self.assertIn("of which 1 also looks externally visible.", out)
        self.assertNotIn("also look externally visible", out)

    def test_plural_external_clause_uses_look(self):
        out = self.render({"agent.py": self.TWO_UNGATED_EXTERNAL_WRITES})
        self.assertIn("of which 2 also look externally visible.", out)
        self.assertNotIn("also looks externally", out)

    def test_zero_external_clause_uses_look(self):
        out = self.render(
            {
                "agent.py": (
                    "from agent_framework import tool\n"
                    "@tool\n"
                    "def write_internal_log(entry: str) -> str:\n"
                    "    '''Append an entry to the internal log.'''\n"
                    "    return entry\n"
                )
            }
        )
        self.assertIn("of which 0 also look externally visible.", out)

    # The sibling clauses in the same block.

    def test_singular_ungated_tool_noun(self):
        out = self.render({"agent.py": self.ONE_UNGATED_EXTERNAL_WRITE})
        self.assertIn("Needs a ruling: 1 ungated tool with a write signal,", out)

    def test_plural_ungated_tool_noun(self):
        out = self.render({"agent.py": self.TWO_UNGATED_EXTERNAL_WRITES})
        self.assertIn("Needs a ruling: 2 ungated tools with a write signal,", out)

    def test_singular_tool_count_line(self):
        out = self.render({"agent.py": self.ONE_UNGATED_EXTERNAL_WRITE})
        self.assertIn("1 tool: 0 gated, 1 ungated.", out)
        self.assertNotIn("1 tools:", out)

    def test_plural_tool_count_line(self):
        out = self.render({"agent.py": self.TWO_UNGATED_EXTERNAL_WRITES})
        self.assertIn("2 tools: 0 gated, 2 ungated.", out)

    def test_singular_signal_nouns(self):
        out = self.render({"agent.py": self.ONE_UNGATED_EXTERNAL_WRITE})
        self.assertIn("1 write signal,", out)
        self.assertIn("1 external-visibility signal,", out)
        self.assertIn("0 blast-radius signals.", out)

    def test_plural_signal_nouns(self):
        out = self.render({"agent.py": self.TWO_UNGATED_EXTERNAL_WRITES})
        self.assertIn("2 write signals,", out)
        self.assertIn("2 external-visibility signals,", out)

    def test_singular_attention_header(self):
        out = self.render({"agent.py": self.ONE_UNGATED_EXTERNAL_WRITE})
        self.assertIn("Ungated tool with a write signal:", out)

    def test_plural_attention_header(self):
        out = self.render({"agent.py": self.TWO_UNGATED_EXTERNAL_WRITES})
        self.assertIn("Ungated tools with a write signal:", out)

    def test_singular_best_effort_line(self):
        out = self.render(
            {
                "agent.go": (
                    "package main\n"
                    "func main() {\n"
                    "\tagent.Run(tool.ApprovalRequiredFunc(weatherTool))\n"
                    "}\n"
                )
            }
        )
        self.assertIn("1 entry is a best-effort match and may be incomplete.", out)
        self.assertNotIn("1 entries", out)

    def test_plural_best_effort_line(self):
        out = self.render(
            {
                "agent.go": (
                    "package main\n"
                    "func main() {\n"
                    "\tagent.Run(tool.ApprovalRequiredFunc(weatherTool))\n"
                    "\tagent.Run(tool.ApprovalRequiredFunc(refundTool))\n"
                    "}\n"
                )
            }
        )
        self.assertIn("2 entries are best-effort matches and may be incomplete.", out)

    def test_empty_corpus_summary_is_singularly_correct(self):
        out = self.render({"notes.py": "x = 1\n"})
        self.assertIn("(no tools found)", out)
        self.assertIn("0 tools: 0 gated, 0 ungated.", out)
        self.assertIn("Needs a ruling: 0 ungated tools with a write signal,", out)

    # The helpers themselves.

    def test_quantify_helper(self):
        self.assertEqual(inventory_tools.quantify(0, "tool"), "0 tools")
        self.assertEqual(inventory_tools.quantify(1, "tool"), "1 tool")
        self.assertEqual(inventory_tools.quantify(2, "tool"), "2 tools")
        self.assertEqual(inventory_tools.quantify(1, "entry", "entries"), "1 entry")
        self.assertEqual(inventory_tools.quantify(3, "entry", "entries"), "3 entries")

    def test_agree_helper(self):
        self.assertEqual(inventory_tools.agree(1, "looks", "look"), "looks")
        self.assertEqual(inventory_tools.agree(0, "looks", "look"), "look")
        self.assertEqual(inventory_tools.agree(2, "looks", "look"), "look")


class ShippedFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = inventory_tools.build_inventory(
            SUBMISSION_ROOT / "assets" / "samples", {"python"}, False
        )
        cls.by_name = {record.name: record for record in cls.inventory.tools}

    def test_fixture_contains_the_expected_tools(self):
        self.assertEqual(
            sorted(self.by_name),
            [
                "close_tickets",
                "draft_internal_note",
                "issue_refund",
                "lookup_customer",
                "purge_export_files",
                "search_orders",
                "send_customer_email",
                "update_subscription",
            ],
        )

    def test_fixture_read_tools_are_not_flagged_as_writes(self):
        self.assertEqual(self.by_name["lookup_customer"].proposed_write, "read")
        self.assertEqual(self.by_name["search_orders"].proposed_write, "read")

    def test_fixture_exposes_an_ungated_irreversible_external_tool(self):
        record = self.by_name["send_customer_email"]
        self.assertFalse(record.gated)
        self.assertEqual(record.proposed_write, "write")
        self.assertEqual(record.proposed_visibility, "external")
        self.assertTrue(record.needs_urgent_attention)

    def test_fixture_bulk_tool_shows_blast_radius(self):
        record = self.by_name["close_tickets"]
        self.assertTrue(record.gated)
        self.assertEqual(record.proposed_blast, "many")

    def test_fixture_conditional_tool_is_annotated(self):
        record = self.by_name["update_subscription"]
        self.assertEqual(record.approval_mode, "conditional")
        self.assertTrue(any("conditional" in note for note in record.notes))

    def test_fixture_renamed_tool_uses_the_declared_name(self):
        record = self.by_name["purge_export_files"]
        self.assertEqual(record.function, "purge_exports")
        self.assertEqual(record.proposed_write, "write")

    def test_fixture_counts(self):
        counts = self.inventory.counts()
        self.assertEqual(counts["tools"], 8)
        self.assertEqual(counts["gated"], 3)
        self.assertEqual(counts["ungated_write_external"], 1)


def count_test_methods(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


class DocumentedCountTests(unittest.TestCase):
    """The README states exact test counts, so make them unable to drift.

    A hardcoded number in prose is a claim about the code that nothing enforces.
    It went stale twice during review, which is the whole argument for asserting
    it rather than remembering to update it.
    """

    def readme(self) -> str:
        return (SUBMISSION_ROOT / "README.md").read_text(encoding="utf-8")

    def assert_documented(self, pattern: str, path: Path, label: str) -> None:
        match = re.search(pattern, self.readme())
        self.assertIsNotNone(
            match, f"README no longer states the {label} test count as {pattern!r}."
        )
        self.assertEqual(
            int(match.group(1)),
            count_test_methods(path),
            f"README claims a stale {label} test count. Update the number in "
            "README.md to match this suite.",
        )

    def test_readme_states_this_suites_count(self):
        self.assert_documented(r"(\d+) tests covering", Path(__file__), "inventory")

    def test_readme_states_the_renderer_suites_count(self):
        self.assert_documented(
            r"A further (\d+) cover",
            Path(__file__).with_name("test_approval_renderer.py"),
            "renderer",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
