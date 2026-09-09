from __future__ import annotations

import binascii
import json
import stat
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

SUBMISSION_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SUBMISSION_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from cowork_plugin_utils import (  # noqa: E402
    CoworkPluginError,
    assert_outline_png_pixels,
    find_npx_command,
    inspect_zip,
    read_skill_metadata,
    temporary_workspace,
    validate_project,
)
from new_cowork_plugin_evals import generate_evaluations  # noqa: E402
from new_cowork_plugin_project import create_project  # noqa: E402
from set_cowork_oauth_reference import set_oauth_reference  # noqa: E402
from test_cowork_plugin_package import main as package_main  # noqa: E402


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def rgba_png(
    width: int,
    height: int,
    *,
    visible_pixel: tuple[int, int, int, int] = (255, 255, 255, 255),
    extra_zlib_data: bytes = b"",
    extra_scanline_data: bytes = b"",
) -> bytes:
    pixels = bytearray(width * height * 4)
    pixels[:4] = bytes(visible_pixel)
    rows = b"".join(
        b"\x00" + pixels[y * width * 4 : (y + 1) * width * 4]
        for y in range(height)
    )
    compressed = zlib.compress(rows + extra_scanline_data) + extra_zlib_data
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )


class WorkspaceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(
            prefix=".cowork-plugin-tests-", dir=Path.cwd()
        )
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()


class FrontmatterTests(WorkspaceTestCase):
    def test_parses_plain_single_double_literal_and_folded_values(self) -> None:
        descriptions = {
            "plain": ("Plain text # comment", "Plain text"),
            "single": ("'It''s quoted'", "It's quoted"),
            "double": ('"Line\\nvalue"', "Line\nvalue"),
            "literal": ("|\n  First line\n  second line", "First line\nsecond line"),
            "folded": (">\n  First line\n  second line", "First line second line"),
        }
        for label, (source, expected) in descriptions.items():
            with self.subTest(label=label):
                path = self.root / f"{label}.md"
                path.write_text(
                    f"---\nname: valid-name\ndescription: {source}\n---\n",
                    encoding="utf-8",
                )
                self.assertEqual(
                    read_skill_metadata(path), ("valid-name", expected)
                )

    def test_rejects_duplicate_frontmatter_fields(self) -> None:
        path = self.root / "SKILL.md"
        path.write_text(
            "---\nname: first\nname: second\ndescription: test\n---\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(CoworkPluginError, "exactly one name"):
            read_skill_metadata(path)

    def test_rejects_invalid_single_quoted_yaml(self) -> None:
        path = self.root / "invalid-single-quote.md"
        path.write_text(
            "---\n"
            "name: valid-name\n"
            "description: 'abc'def'\n"
            "---\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            CoworkPluginError, "invalid single-quoted YAML"
        ):
            read_skill_metadata(path)

    def test_rejects_typed_scalars_and_unsupported_yaml_constructs(self) -> None:
        unsupported = {
            "false": "false",
            "true": "true",
            "null": "null",
            "tilde": "~",
            "integer": "42",
            "leading-zero-integer": "0123",
            "float": "3.14",
            "trailing-dot-float": "1.",
            "exponent": "1e3",
            "date": "2026-09-09",
            "timestamp": "2026-09-09T02:06:43-04:00",
            "sequence": "[]",
            "mapping": "{}",
            "tag": "!!str tagged",
            "anchor": "&value anchored",
            "alias": "*value",
            "mapping-like": "foo: bar",
            "sequence-entry": "- item",
            "mapping-key": "? item",
            "reserved-at": "@value",
            "reserved-backtick": "`value",
            "comment-only": "# missing",
            "directive": "%YAML 1.2",
            "flow-comma": ",value",
        }
        for label, value in unsupported.items():
            with self.subTest(label=label):
                path = self.root / f"{label}.md"
                path.write_text(
                    f"---\nname: valid-name\ndescription: {value}\n---\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(CoworkPluginError, "must be"):
                    read_skill_metadata(path)


class TemporaryWorkspaceTests(WorkspaceTestCase):
    def test_uses_operating_system_temporary_directory(self) -> None:
        with patch.object(Path, "cwd", side_effect=PermissionError):
            with temporary_workspace(".cowork-workspace-test-") as workspace:
                workspace_path = Path(workspace)
                self.assertTrue(
                    workspace_path.parent.samefile(tempfile.gettempdir())
                )


class ToolLauncherTests(WorkspaceTestCase):
    def test_windows_npx_wrapper_is_replaced_with_node_argv(self) -> None:
        node_root = self.root / "node"
        node_root.mkdir()
        node = node_root / "node.exe"
        npx = node_root / "npx.cmd"
        npx_cli = node_root / "node_modules" / "npm" / "bin" / "npx-cli.js"
        node.write_bytes(b"")
        npx.write_bytes(b"")
        npx_cli.parent.mkdir(parents=True)
        npx_cli.write_bytes(b"")
        with patch(
            "cowork_plugin_utils.shutil.which",
            side_effect=lambda name: str(npx if name == "npx" else node),
        ):
            self.assertEqual(
                find_npx_command(),
                [str(node.resolve()), str(npx_cli.resolve())],
            )

    def test_windows_node_batch_launcher_is_rejected(self) -> None:
        node_root = self.root / "node"
        node_root.mkdir()
        node = node_root / "node.cmd"
        npx = node_root / "npx.cmd"
        node.write_bytes(b"")
        npx.write_bytes(b"")
        with patch(
            "cowork_plugin_utils.shutil.which",
            side_effect=lambda name: str(npx if name == "npx" else node),
        ):
            with self.assertRaisesRegex(
                CoworkPluginError, "native node executable"
            ):
                find_npx_command()


class PngValidationTests(WorkspaceTestCase):
    def test_accepts_strict_white_and_transparent_outline(self) -> None:
        path = self.root / "outline.png"
        path.write_bytes(rgba_png(32, 32))
        assert_outline_png_pixels(path)

    def test_rejects_non_white_visible_pixel(self) -> None:
        path = self.root / "outline.png"
        path.write_bytes(rgba_png(32, 32, visible_pixel=(254, 255, 255, 255)))
        with self.assertRaisesRegex(CoworkPluginError, "non-white"):
            assert_outline_png_pixels(path)

    def test_rejects_bad_crc_and_bytes_after_iend(self) -> None:
        valid = rgba_png(32, 32)
        bad_crc = bytearray(valid)
        bad_crc[29] ^= 1
        crc_path = self.root / "crc.png"
        crc_path.write_bytes(bad_crc)
        with self.assertRaisesRegex(CoworkPluginError, "invalid CRC"):
            assert_outline_png_pixels(crc_path)

        trailing_path = self.root / "trailing.png"
        trailing_path.write_bytes(valid + b"trailing")
        with self.assertRaisesRegex(CoworkPluginError, "after its IEND"):
            assert_outline_png_pixels(trailing_path)

    def test_bounded_zlib_rejects_overrun_and_trailing_stream_data(self) -> None:
        overrun = self.root / "overrun.png"
        overrun.write_bytes(rgba_png(32, 32, extra_scanline_data=b"x"))
        with self.assertRaisesRegex(CoworkPluginError, "unexpected decompressed"):
            assert_outline_png_pixels(overrun)

        trailing = self.root / "trailing-zlib.png"
        trailing.write_bytes(rgba_png(32, 32, extra_zlib_data=b"junk"))
        with self.assertRaisesRegex(CoworkPluginError, "trailing zlib"):
            assert_outline_png_pixels(trailing)


class ZipSafetyTests(WorkspaceTestCase):
    def write_zip(
        self,
        entries: list[tuple[str, bytes, int | None]],
        compression: int = zipfile.ZIP_STORED,
    ) -> Path:
        package = self.root / f"package-{len(list(self.root.glob('*.zip')))}.zip"
        with zipfile.ZipFile(package, "w") as archive:
            for name, content, mode in entries:
                info = zipfile.ZipInfo(name)
                info.compress_type = compression
                if mode is not None:
                    info.create_system = 3
                    info.external_attr = mode << 16
                archive.writestr(info, content)
        return package

    def inspect(self, package: Path) -> tuple[int, int]:
        target = self.root / f"extract-{len(list(self.root.glob('extract-*')))}"
        return inspect_zip(package, target)

    def test_accepts_rooted_package(self) -> None:
        package = self.write_zip([("manifest.json", b"{}", None)])
        self.assertEqual(self.inspect(package), (1, 2))

    def test_rejects_traversal_wrapper_duplicates_and_symlinks(self) -> None:
        cases = {
            "traversal": [
                ("manifest.json", b"{}", None),
                ("../escape", b"x", None),
            ],
            "wrapper": [("wrapper/manifest.json", b"{}", None)],
            "duplicate": [
                ("manifest.json", b"{}", None),
                ("MANIFEST.JSON", b"{}", None),
            ],
            "symlink": [
                ("manifest.json", b"{}", None),
                ("link", b"target", stat.S_IFLNK | 0o777),
            ],
        }
        for label, entries in cases.items():
            with self.subTest(label=label):
                package = self.write_zip(entries)
                with self.assertRaises(CoworkPluginError):
                    self.inspect(package)

    def test_rejects_ambiguous_and_absolute_paths(self) -> None:
        for unsafe in ("root//file", "folder./file", "/absolute", "C:/drive"):
            with self.subTest(path=unsafe):
                package = self.write_zip(
                    [
                        ("manifest.json", b"{}", None),
                        (unsafe, b"x", None),
                    ]
                )
                with self.assertRaises(CoworkPluginError):
                    self.inspect(package)

    def test_enforces_entry_and_expanded_size_limits(self) -> None:
        package = self.write_zip(
            [
                ("manifest.json", b"{}", None),
                ("extra.txt", b"x", None),
            ]
        )
        with self.assertRaisesRegex(CoworkPluginError, "maximum is 1"):
            inspect_zip(package, self.root / "entry-limit", max_entries=1)

        oversized = self.write_zip(
            [("manifest.json", b"x" * (1024 * 1024 + 1), None)]
        )
        with self.assertRaisesRegex(CoworkPluginError, "safety limit"):
            inspect_zip(
                oversized,
                self.root / "size-limit",
                max_extracted_bytes=1024 * 1024,
            )

    def test_rejects_unsupported_compression_before_extraction(self) -> None:
        packages = {
            "bzip2": self.write_zip(
                [("manifest.json", b"{}", None)], zipfile.ZIP_BZIP2
            ),
            "lzma": self.write_zip(
                [("manifest.json", b"{}", None)], zipfile.ZIP_LZMA
            ),
        }
        unknown = self.write_zip([("manifest.json", b"{}", None)])
        data = bytearray(unknown.read_bytes())
        local_header = data.index(b"PK\x03\x04")
        central_header = data.index(b"PK\x01\x02")
        struct.pack_into("<H", data, local_header + 8, 99)
        struct.pack_into("<H", data, central_header + 10, 99)
        unknown.write_bytes(data)
        packages["unknown"] = unknown

        for label, package in packages.items():
            with self.subTest(label=label):
                target = self.root / f"unsupported-{label}"
                with self.assertRaisesRegex(
                    CoworkPluginError, "unsupported compression"
                ):
                    inspect_zip(package, target)
                self.assertFalse(target.exists())

    def test_translates_corrupt_deflate_to_plugin_error(self) -> None:
        package = self.write_zip(
            [("manifest.json", b'{"value":"compress me"}', None)],
            zipfile.ZIP_DEFLATED,
        )
        data = bytearray(package.read_bytes())
        local_header = data.index(b"PK\x03\x04")
        name_length, extra_length = struct.unpack_from(
            "<HH", data, local_header + 26
        )
        compressed_start = local_header + 30 + name_length + extra_length
        data[compressed_start] ^= 0xFF
        package.write_bytes(data)

        with self.assertRaisesRegex(CoworkPluginError, "safely extracted"):
            self.inspect(package)


class WorkflowTests(WorkspaceTestCase):
    def create_valid_project(self) -> Path:
        color = self.root / "color-source.png"
        outline = self.root / "outline-source.png"
        color.write_bytes(rgba_png(192, 192))
        outline.write_bytes(rgba_png(32, 32))
        project = self.root / "project"
        create_project(
            project,
            plugin_name="Fixture",
            short_description="Fixture plugin",
            full_description="Fixture plugin for validation tests.",
            developer_name="Fixture Developer",
            website_url="https://example.com",
            privacy_url="https://example.com/privacy",
            terms_of_use_url="https://example.com/terms",
            skill_names=["review-helper"],
            skill_descriptions=["Review a fixture safely."],
            color_icon_path=color,
            outline_icon_path=outline,
        )
        return project

    def test_scaffold_validates_and_generates_schema_1_6_0_evals(self) -> None:
        project = self.create_valid_project()
        validation = validate_project(project)
        self.assertEqual(validation.skills, 1)
        result = generate_evaluations(project)
        document = json.loads(Path(result["output_path"]).read_text())
        self.assertEqual(document["schemaVersion"], "1.6.0")
        self.assertEqual(len(document["items"]), 4)

    def test_package_path_deeply_validates_packaged_content(self) -> None:
        project = self.create_valid_project()
        package_root = project / "appPackage"
        original_entries = {
            path.relative_to(package_root).as_posix(): path.read_bytes()
            for path in package_root.rglob("*")
            if path.is_file()
        }

        valid_package = self.root / "valid-package.zip"
        with zipfile.ZipFile(
            valid_package, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for name, content in original_entries.items():
                archive.writestr(name, content)
        result = validate_project(project, package_path=valid_package)
        self.assertTrue(result.package_checked)
        self.assertEqual(result.skills, 1)

        invalid_packages: dict[str, tuple[dict[str, bytes], str]] = {}

        missing_skill = original_entries.copy()
        del missing_skill["skills/review-helper/SKILL.md"]
        invalid_packages["skill"] = (
            missing_skill,
            "Skill folder is missing|missing SKILL.md",
        )

        corrupt_icon = original_entries.copy()
        corrupt_icon["color.png"] = b"not a png"
        invalid_packages["icon"] = (corrupt_icon, "not a PNG")

        missing_tool = original_entries.copy()
        manifest = json.loads(missing_tool["manifest.json"])
        manifest["agentConnectors"] = [
            {
                "id": "example",
                "displayName": "Example",
                "toolSource": {
                    "remoteMcpServer": {
                        "mcpServerUrl": "https://example.com/mcp",
                        "mcpToolDescription": {"file": "./tools/example.json"},
                    }
                },
            }
        ]
        missing_tool["manifest.json"] = json.dumps(manifest).encode()
        invalid_packages["connector-tool"] = (missing_tool, "tool file is missing")

        for label, (entries, error) in invalid_packages.items():
            with self.subTest(label=label):
                package = self.root / f"invalid-{label}.zip"
                with zipfile.ZipFile(
                    package, "w", compression=zipfile.ZIP_DEFLATED
                ) as archive:
                    for name, content in entries.items():
                        archive.writestr(name, content)
                with self.assertRaisesRegex(CoworkPluginError, error):
                    validate_project(project, package_path=package)

    def test_package_path_must_match_source_identity_and_registration(self) -> None:
        project = self.create_valid_project()
        package_root = project / "appPackage"
        original_entries = {
            path.relative_to(package_root).as_posix(): path.read_bytes()
            for path in package_root.rglob("*")
            if path.is_file()
        }
        mismatches = {
            "id": lambda manifest: manifest.update(
                {"id": "6d7f4fe0-a6f7-4b32-a587-255e89b2ed18"}
            ),
            "version": lambda manifest: manifest.update({"version": "2.0.0"}),
        }
        for field, mutate in mismatches.items():
            with self.subTest(field=field):
                entries = original_entries.copy()
                manifest = json.loads(entries["manifest.json"])
                mutate(manifest)
                entries["manifest.json"] = json.dumps(manifest).encode()
                package = self.root / f"mismatched-{field}.zip"
                with zipfile.ZipFile(
                    package, "w", compression=zipfile.ZIP_DEFLATED
                ) as archive:
                    for name, content in entries.items():
                        archive.writestr(name, content)
                with self.assertRaisesRegex(
                    CoworkPluginError,
                    f"manifest {field} does not match",
                ):
                    validate_project(project, package_path=package)

        entries = original_entries.copy()
        manifest = json.loads(entries["manifest.json"])
        manifest["agentSkills"] = [{"folder": "./skills/other-helper"}]
        entries["manifest.json"] = json.dumps(manifest).encode()
        entries["skills/other-helper/SKILL.md"] = (
            b"---\nname: other-helper\ndescription: Another valid skill.\n---\n"
        )
        package = self.root / "mismatched-agentSkills.zip"
        with zipfile.ZipFile(
            package, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
        with self.assertRaisesRegex(
            CoworkPluginError, "manifest agentSkills does not match"
        ):
            validate_project(project, package_path=package)

    def test_package_validation_cannot_switch_to_nested_app_package(self) -> None:
        project = self.create_valid_project()
        package_root = project / "appPackage"
        original_entries = {
            path.relative_to(package_root).as_posix(): path.read_bytes()
            for path in package_root.rglob("*")
            if path.is_file()
        }
        root_manifest = json.loads(original_entries["manifest.json"])
        del root_manifest["developer"]
        entries = original_entries | {
            "manifest.json": json.dumps(root_manifest).encode()
        }
        entries.update(
            {
                f"appPackage/{name}": content
                for name, content in original_entries.items()
            }
        )
        package = self.root / "nested-app-package-bypass.zip"
        with zipfile.ZipFile(
            package, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
        with self.assertRaisesRegex(CoworkPluginError, "developer must"):
            validate_project(project, package_path=package)

        with patch.object(
            sys,
            "argv",
            [
                "test_cowork_plugin_package.py",
                "--package-path",
                str(package),
                "--skip-toolkit-validation",
            ],
        ):
            with redirect_stderr(StringIO()):
                self.assertEqual(package_main(), 1)

    def test_scaffold_rejects_empty_required_manifest_text(self) -> None:
        color = self.root / "color-source.png"
        outline = self.root / "outline-source.png"
        color.write_bytes(rgba_png(192, 192))
        outline.write_bytes(rgba_png(32, 32))
        values = {
            "plugin_name": " ",
            "short_description": "",
            "full_description": "\t",
            "developer_name": "\n",
        }
        defaults = {
            "plugin_name": "Fixture",
            "short_description": "Fixture plugin",
            "full_description": "Fixture plugin for validation tests.",
            "developer_name": "Fixture Developer",
        }
        for field, invalid_value in values.items():
            with self.subTest(field=field):
                arguments = defaults | {field: invalid_value}
                with self.assertRaisesRegex(
                    CoworkPluginError, "must not be empty"
                ):
                    create_project(
                        self.root / f"invalid-{field}",
                        **arguments,
                        website_url="https://example.com",
                        privacy_url="https://example.com/privacy",
                        terms_of_use_url="https://example.com/terms",
                        skill_names=["review-helper"],
                        skill_descriptions=["Review a fixture safely."],
                        color_icon_path=color,
                        outline_icon_path=outline,
                        dry_run=True,
                    )

    def test_oauth_update_rejects_placeholder_and_bumps_version(self) -> None:
        project = self.create_valid_project()
        manifest_path = project / "appPackage" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["agentConnectors"] = [
            {
                "id": "example",
                "displayName": "Example",
                "toolSource": {
                    "remoteMcpServer": {
                        "mcpServerUrl": "https://example.com/mcp",
                        "mcpToolDescription": {"file": "./tools/example.json"},
                        "authorization": {
                            "type": "OAuthPluginVault",
                            "referenceId": "example-example-auth",
                        },
                    }
                },
            }
        ]
        tools = project / "appPackage" / "tools"
        tools.mkdir()
        (tools / "example.json").write_text(
            json.dumps(
                {
                    "tools": [
                        {
                            "name": "lookup",
                            "description": "Look up a record.",
                            "inputSchema": {"type": "object"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(CoworkPluginError, "placeholder"):
            validate_project(project)
        with self.assertRaisesRegex(CoworkPluginError, "placeholder"):
            set_oauth_reference(
                project, "example", "example-example-auth"
            )
        result = set_oauth_reference(
            project, "example", "registered-oauth-client-id"
        )
        self.assertEqual(result["version"], "1.0.1")
        validate_project(project)


if __name__ == "__main__":
    unittest.main()
