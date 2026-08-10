#!/usr/bin/env python3
"""toast.py — deterministic converter between RAPP single-file agents and Agent Skills.

Implements rapp-capability-interchange/1.0 (the RCI capsule) for two formats:

  agent   a RAPP single-file agent cartridge (*_agent.py) — the canonical form
  skill   a single-file SKILL.md Agent Skill — a PROJECTION of the agent

The projection carries the canonical record inside itself as an RCI capsule
(`rci-capsule:v1:` + base64(gzip(JSON))), whose `preserved` map vaults the
byte-exact original with a sha256. Converting back is therefore a
checksum-verified RESTORE, never a re-render: nothing is translated, so
nothing can drift.

Spec + reference implementation: https://github.com/kody-w/rapp-toaster
(Apache-2.0; capsule/vault mechanics follow it so artifacts interoperate).
This file is stdlib-only, offline, Python 3.9+. Agent files are parsed with
`ast` and NEVER imported or executed.

Commands:
    python3 toast.py convert <path> --to skill|agent [-o OUT] [--force]
    python3 toast.py roundtrip <agent.py|SKILL.md> [--cycles N] [--allow-raw]
    python3 toast.py inspect <path>
    python3 toast.py selftest
"""

import argparse
import ast
import base64
import gzip
import hashlib
import json
import os
import re
import sys
import textwrap

RCI_VERSION = "1.0"
SPEC = "rapp-capability-interchange/1.0"
CAPSULE_COMMENT_RE = re.compile(
    r"<!--[ \t]*rci-capsule:v1:([^<\r\n]*?)[ \t]*-->"
    r"|^[ \t]*#[ \t]*rci-capsule:v1:([^\s]+)[ \t]*$",
    re.M,
)
GENERATED_BEGIN = "<!-- toaster:generated:begin -->"
GENERATED_END = "<!-- toaster:generated:end -->"
GENERATED_BLOCK_RE = re.compile(
    r"^<!-- toaster:generated:begin -->[ \t]*\n"
    r"(.*?)"
    r"^<!-- toaster:generated:end -->[ \t]*$",
    re.S | re.M,
)
GENERATED_RE = re.compile(
    r"\n?^<!-- toaster:generated:begin -->[ \t]*\n.*?"
    r"^<!-- toaster:generated:end -->[ \t]*$\n?",
    re.S | re.M,
)
GENERATED_PERFORM_MARK = "# toaster:generated-perform"
DET_FENCE = re.compile(
    r"(`{3,})python[ \t]*#[ \t]*rapp:deterministic[ \t]*\n(.*?)\1",
    re.S,
)
PARAM_FENCE = re.compile(r"##+\s*Parameters\s*\n+```json\s*\n(.*?)```", re.S | re.I)
SYSCTX_SEC = re.compile(r"##+\s*System Context\s*\n+(.*?)(?=\n##+\s|\Z)", re.S | re.I)
TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
FORMATS = ("agent", "skill")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _gz(b: bytes) -> bytes:
    # mtime=0 keeps the gzip header deterministic — without it two conversions
    # of the same bytes in different seconds emit different capsules. Python
    # versions have emitted different gzip OS bytes even with mtime=0, so pin
    # that header byte too.
    out = bytearray(gzip.compress(b, 9, mtime=0))
    if len(out) >= 10:
        out[9] = 255  # RFC 1952: unknown OS; stable on every supported host.
    return bytes(out)


def blank_rci() -> dict:
    return {
        "rci": RCI_VERSION,
        "name": "",             # tool name as the model calls it
        "slug": "",             # filesystem / skill identity (kebab-case)
        "version": "1.0.0",
        "description": "",      # routing + trigger text
        "parameters": {"type": "object", "properties": {}, "required": []},
        "instructions": "",     # the procedural layer (markdown)
        "system_context": None,
        "impl": None,
        "author": None,
        "tags": [],
        "license": None,
        "examples": [],
        "platform": {},         # host-specific extras we must not lose
        "preserved": {},        # fmt -> {"sha256","b64","filename"}
        "provenance": [],       # conversion trail
    }


def preserve(rci: dict, fmt: str, raw: bytes, filename: str) -> None:
    """Vault the byte-exact original so a later conversion can restore it."""
    rci.setdefault("preserved", {})[fmt] = {
        "sha256": _sha(raw),
        "b64": base64.b64encode(_gz(raw)).decode(),
        "filename": os.path.basename(filename),
    }


def restore(rci: dict, fmt: str):
    p = rci.get("preserved", {}).get(fmt)
    if not p:
        return None
    raw = gzip.decompress(base64.b64decode(p["b64"]))
    if _sha(raw) != p["sha256"]:
        raise ValueError(f"preserved {fmt} payload failed its checksum")
    return raw


def pack_capsule(rci: dict) -> str:
    # Underscore keys are in-process state (e.g. which format was read) and
    # never travel.
    _validate_rci_fields(rci)
    payload = json.dumps({k: v for k, v in rci.items() if not k.startswith("_")},
                         sort_keys=True, separators=(",", ":")).encode()
    return "rci-capsule:v1:" + base64.b64encode(_gz(payload)).decode()


def _safe_agent_filename(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9_]+_agent\.py", value
    ):
        raise ValueError(
            "vaulted agent filename must be a basename ending _agent.py"
        )
    if value != os.path.basename(value) or ".." in value:
        raise ValueError("vaulted agent filename is not path-safe")
    return value


def _validate_parameters(value):
    if not isinstance(value, dict) or value.get("type") != "object":
        raise ValueError("parameters must be a JSON-Schema object")
    if not isinstance(value.get("properties", {}), dict):
        raise ValueError("parameters.properties must be an object")
    required = value.get("required", [])
    if not isinstance(required, list) \
            or not all(isinstance(item, str) for item in required):
        raise ValueError("parameters.required must be a list of strings")
    return value


def _validate_rci_fields(value):
    if not isinstance(value, dict):
        raise ValueError("RCI record must be an object")
    for key in ("name", "slug", "version", "description", "instructions"):
        if not isinstance(value.get(key, ""), str):
            raise ValueError(f"RCI {key} must be a string")
    for key in ("system_context", "author", "license"):
        if value.get(key) is not None and not isinstance(value.get(key), str):
            raise ValueError(f"RCI {key} must be a string or null")
    for key in ("tags", "examples"):
        if not isinstance(value.get(key, []), list):
            raise ValueError(f"RCI {key} must be a list")
    if not all(isinstance(tag, str) for tag in value.get("tags", [])):
        raise ValueError("RCI tags must contain strings")
    if not all(isinstance(example, dict) for example in value.get("examples", [])):
        raise ValueError("RCI examples must contain objects")
    _validate_parameters(
        value.get("parameters")
        or {"type": "object", "properties": {}, "required": []}
    )
    platform = value.get("platform", {})
    if not isinstance(platform, dict):
        raise ValueError("RCI platform must be an object")
    if platform.get("metadata") is not None \
            and not isinstance(platform.get("metadata"), dict):
        raise ValueError("RCI platform.metadata must be an object")
    if platform.get("claude") is not None:
        if not isinstance(platform.get("claude"), dict):
            raise ValueError("RCI platform.claude must be an object")
        allowed = platform["claude"].get("allowed-tools")
        if allowed is not None and not isinstance(allowed, (str, list)):
            raise ValueError(
                "RCI platform.claude.allowed-tools must be a string or list"
            )
    if platform.get("compatibility") is not None \
            and not isinstance(platform.get("compatibility"), str):
        raise ValueError("RCI platform.compatibility must be a string")
    if platform.get("disable-model-invocation") is not None \
            and not isinstance(platform.get("disable-model-invocation"), bool):
        raise ValueError(
            "RCI platform.disable-model-invocation must be a boolean"
        )
    impl = value.get("impl")
    if impl is not None:
        if not isinstance(impl, dict):
            raise ValueError("RCI impl must be an object or null")
        for key in ("perform", "perform_body", "system_context"):
            if impl.get(key) is not None and not isinstance(impl.get(key), str):
                raise ValueError(f"RCI impl.{key} must be a string")
        if impl.get("steps") is not None and not isinstance(impl.get("steps"), list):
            raise ValueError("RCI impl.steps must be a list")
    if not isinstance(value.get("provenance", []), list):
        raise ValueError("RCI provenance must be a list")
    return value


def _validate_capsule(value):
    _validate_rci_fields(value)
    if value.get("rci") != RCI_VERSION:
        raise ValueError("capsule is not an RCI 1.0 object")
    preserved = value.get("preserved", {})
    if not isinstance(preserved, dict):
        raise ValueError("capsule preserved field must be an object")
    for fmt, entry in preserved.items():
        if fmt not in FORMATS or not isinstance(entry, dict):
            raise ValueError("capsule preserved entry is invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
            raise ValueError("capsule preserved checksum is invalid")
        if not isinstance(entry.get("b64"), str):
            raise ValueError("capsule preserved payload is invalid")
        if not isinstance(entry.get("filename"), str):
            raise ValueError("capsule preserved filename is invalid")
    return value


def unpack_capsule(text: str):
    # LAST match, deliberately: a converted agent's own source (with its old
    # trailing capsule) can ride inside this artifact, and the capsule this
    # file carries is always appended after it. First-match read the stale
    # passenger instead of the ledger -- found by round-tripping an upstream
    # cartridge that embedded its history.
    matches = CAPSULE_COMMENT_RE.findall(text)
    if not matches:
        return None
    payload = next(part for part in matches[-1] if part).strip()
    if not re.fullmatch(r"[A-Za-z0-9+/=]+", payload):
        raise ValueError("malformed rci-capsule:v1 payload")
    try:
        decoded = json.loads(gzip.decompress(base64.b64decode(payload)))
    except Exception as exc:
        raise ValueError("malformed rci-capsule:v1 payload") from exc
    return _validate_capsule(decoded)


def strip_capsules(b: bytes) -> bytes:
    """Every capsule removed -- the content two ledger-bearing artifacts share."""
    t = CAPSULE_COMMENT_RE.sub("", b.decode("utf-8"))
    return t.encode()


def _kebab(s: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", s or "")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "capability"


def _snake(s: str) -> str:
    return _kebab(s).replace("-", "_")


def _pascal(s: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9]+", s or "") and s[:1].isupper():
        return s  # already a PascalCase-ish identifier — keep the author's casing
    return "".join(w.capitalize() for w in re.split(r"[^a-zA-Z0-9]+", s or "") if w) or "Capability"


def _class_identifier(s: str) -> str:
    """Return a valid Python class identifier without changing the tool name."""
    name = _pascal(s)
    if not re.match(r"^[A-Za-z_]", name):
        name = "Agent" + name
    return name


def _generated_agent_fences(text: str) -> list[str]:
    """Return deterministic Python fences inside generated regions only."""
    found = []
    for block in GENERATED_BLOCK_RE.findall(text):
        found.extend(match.group(2) for match in DET_FENCE.finditer(block))
    return found


def _generated_markers_are_top_level(text: str) -> bool:
    """Reject generated markers hidden inside Markdown fences or HTML comments."""
    in_fence = None
    fence_len = 0
    in_html = False
    for line in text.splitlines():
        marker = line.rstrip()
        if marker in (GENERATED_BEGIN, GENERATED_END):
            if in_fence or in_html or line != marker:
                return False
            continue

        if in_fence:
            close = re.match(r"^ {0,3}([`~]{3,})[ \t]*$", line)
            if close and close.group(1)[0] == in_fence \
                    and len(close.group(1)) >= fence_len:
                in_fence = None
                fence_len = 0
            continue

        if in_html:
            if "-->" in line:
                in_html = False
            continue

        fence = re.match(r"^ {0,3}([`~]{3,})", line)
        if fence:
            in_fence = fence.group(1)[0]
            fence_len = len(fence.group(1))
            continue

        start = line.find("<!--")
        if start != -1 and "-->" not in line[start + 4:]:
            in_html = True
    return True


def _capsule_or_reparse(raw: bytes, filename: str, fmt: str):
    """The file in hand outranks its capsule.

    A capsule whose own-format vault entry no longer matches the current bytes
    was written for an EARLIER version of this file -- trusting it would emit
    stale content (found by round-tripping upstream example agents that had
    evolved past their embedded capsules). Reparse from the file itself, drop
    the stale vault, and keep only the provenance trail.
    """
    text = raw.decode("utf-8", "replace")
    if fmt == "skill":
        # Generated regions may quote a whole agent -- capsule and all. Only a
        # capsule OUTSIDE them belongs to this file.
        text = GENERATED_RE.sub("", text)
    cap = unpack_capsule(text)
    if not cap:
        return None
    entry = (cap.get("preserved") or {}).get(fmt)
    if entry and entry.get("sha256") != _sha(raw):
        stale = blank_rci()
        stale["provenance"] = list(cap.get("provenance") or []) + [
            f"capsule:stale:reparsed:{os.path.basename(filename)}"]
        return ("stale", stale)
    return ("ok", cap)


# ---------------------------------------------------------------- agent (read)

class _Unevaluable(Exception):
    pass


def _eval_node(node, env):
    """Evaluate the literal subset RAPP metadata actually uses. No execution."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Dict):
        return {_eval_node(k, env): _eval_node(v, env)
                for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.List):
        return [_eval_node(e, env) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(e, env) for e in node.elts)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
            and node.value.id == "self":
        if node.attr in env:
            return env[node.attr]
        raise _Unevaluable(f"self.{node.attr}")
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise _Unevaluable(node.id)
    if isinstance(node, ast.Subscript):
        container = _eval_node(node.value, env)
        idx = node.slice
        if isinstance(idx, ast.Constant):
            return container[idx.value]
        raise _Unevaluable("subscript")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand, env)
    raise _Unevaluable(type(node).__name__)


def _class_candidates(tree):
    out = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name == "BasicAgent":
            continue
        bases = [getattr(b, "id", getattr(b, "attr", "")) for b in node.bases]
        has_perform = any(isinstance(n, ast.FunctionDef) and n.name == "perform"
                          for n in node.body)
        if has_perform or any("Agent" in (b or "") for b in bases):
            out.append((node, has_perform))
    # Prefer a class that actually defines perform(); the duck-typed contract
    # is the shape, not the ancestor (each project vendors its own BasicAgent).
    out.sort(key=lambda t: not t[1])
    return [n for n, _ in out]


def read_agent(raw: bytes, filename: str) -> dict:
    try:
        text = raw.decode("utf-8").lstrip("\ufeff")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{filename}: agent source must be UTF-8 for an Agent Skill projection"
        ) from exc
    got = _capsule_or_reparse(raw, filename, "agent")
    cap = got[1] if got and got[0] == "ok" else None
    rci = cap if cap else (got[1] if got else blank_rci())

    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        raise SystemExit(f"[FAIL] {filename}: not parseable Python "
                         f"({e.msg} at line {e.lineno})")
    env = {}
    for node in tree.body:  # module-level literals: __manifest__, STEPS, INSTRUCTIONS
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            try:
                env[node.targets[0].id] = _eval_node(node.value, env)
            except _Unevaluable:
                pass

    classes = _class_candidates(tree)
    if not classes:
        raise SystemExit(f"[FAIL] {filename}: no agent class found "
                         "(need a class with a perform() method)")
    cls = classes[0]

    self_env = dict(env)
    for node in cls.body:  # class-attribute style: name/metadata as class attrs
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            try:
                self_env[node.targets[0].id] = _eval_node(node.value, self_env)
            except _Unevaluable:
                pass
    perform_src = sysctx_src = None
    for node in cls.body:
        if isinstance(node, ast.FunctionDef):
            if node.name == "perform":
                perform_src = ast.get_source_segment(text, node)
            elif node.name == "system_context":
                sysctx_src = ast.get_source_segment(text, node)
            elif node.name == "__init__":
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                            and isinstance(stmt.targets[0], ast.Attribute) \
                            and isinstance(stmt.targets[0].value, ast.Name) \
                            and stmt.targets[0].value.id == "self":
                        try:
                            self_env[stmt.targets[0].attr] = _eval_node(stmt.value, self_env)
                        except _Unevaluable:
                            pass

    manifest = env.get("__manifest__") if isinstance(env.get("__manifest__"), dict) else {}
    metadata = self_env.get("metadata") if isinstance(self_env.get("metadata"), dict) else {}
    name = self_env.get("name") or metadata.get("name") or cls.name
    if not (isinstance(name, str) and TOOL_NAME_RE.match(name)):
        print(f"[WARN] tool name {name!r} is not tool-safe "
              "(^[a-zA-Z0-9_-]+$) — the brainstem loader would quarantine it",
              file=sys.stderr)

    params = metadata.get("parameters")
    if params is None:
        params = {"type": "object", "properties": {}, "required": []}
    else:
        _validate_parameters(params)

    # The FILE always defines the capability; a capsule is ledger (provenance,
    # vault, host extras), never an override. A synthesized agent has no way
    # to vault itself, so a capsule-trusting reader would ignore every edit
    # made to the file afterwards -- the exact drift this tool exists to stop.
    rci["name"] = name if isinstance(name, str) else cls.name
    display_name = manifest.get("display_name")
    rci["slug"] = (_kebab(display_name) if display_name else None) \
        or rci.get("slug") or _kebab(rci["name"])
    rci["description"] = (metadata.get("description")
                          or manifest.get("description")
                          or rci.get("description", ""))
    rci["parameters"] = params
    # Launchpad agents carry the full source prose as a module-level
    # INSTRUCTIONS literal; plain agents document themselves in the docstring.
    rci["instructions"] = (env.get("INSTRUCTIONS")
                           if isinstance(env.get("INSTRUCTIONS"), str)
                           else None) or ast.get_docstring(tree) or rci["description"]
    if manifest.get("version"):
        rci["version"] = manifest["version"]
    if manifest.get("author"):
        rci["author"] = manifest["author"]
    if manifest.get("tags"):
        rci["tags"] = list(manifest["tags"])
    rci["impl"] = {"lang": "python", "class": cls.name, "perform": perform_src,
                   **({"system_context": sysctx_src} if sysctx_src else {})}
    if isinstance(env.get("STEPS"), list) and env["STEPS"]:
        rci["impl"]["steps"] = env["STEPS"]

    _validate_rci_fields(rci)
    preserve(rci, "agent", raw, filename)
    rci.setdefault("provenance", []).append(f"read:agent:{os.path.basename(filename)}")
    rci["_read_fmt"] = "agent"
    return rci


# ---------------------------------------------------------------- skill (read)

def _yaml_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except Exception:
            return value[1:-1]
    if value in ("true", "false", "null") \
            or re.fullmatch(r"-?(?:0|[1-9]\d*)(?:\.\d+)?", value):
        return json.loads(value)
    if value.startswith(("[", "{")):
        try:
            return json.loads(value)
        except Exception:
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                return [] if not inner else [
                    _yaml_scalar(part) for part in inner.split(",")
                ]
    return value


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _next_indented_line(lines, start: int):
    for index in range(start, len(lines)):
        if lines[index].strip():
            return index, _indent_of(lines[index])
    return None, None


def _read_block_scalar(lines, start: int, parent_indent: int, style: str):
    block = []
    i = start
    while i < len(lines):
        line = lines[i]
        if line.strip() and _indent_of(line) <= parent_indent:
            break
        block.append(line.strip())
        i += 1
    if style.startswith("|"):
        return "\n".join(block).strip(), i
    paragraphs, current = [], []
    for value in block:
        if value:
            current.append(value)
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(paragraphs), i


def _parse_yaml_node(lines, start: int, indent: int):
    first, _ = _next_indented_line(lines, start)
    is_list = first is not None and lines[first][indent:].startswith("- ")
    out = [] if is_list else {}
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        current = _indent_of(line)
        if current < indent:
            break
        if current > indent:
            raise ValueError("unsupported YAML indentation in frontmatter")
        token = line[indent:]
        if is_list:
            if not token.startswith("- "):
                break
            value = token[2:].strip()
            i += 1
            if value:
                out.append(_yaml_scalar(value))
                continue
            child_index, child_indent = _next_indented_line(lines, i)
            if child_index is None or child_indent <= indent:
                out.append(None)
                continue
            child, i = _parse_yaml_node(lines, child_index, child_indent)
            out.append(child)
            continue

        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", token)
        if not match:
            raise ValueError(f"unsupported YAML frontmatter line: {token}")
        key, value = match.group(1), match.group(2).strip()
        i += 1
        if value in (">", ">-", "|", "|-"):
            out[key], i = _read_block_scalar(lines, i, indent, value)
            continue
        if value:
            out[key] = _yaml_scalar(value)
            continue
        child_index, child_indent = _next_indented_line(lines, i)
        if child_index is None or child_indent <= indent:
            out[key] = {}
            continue
        child, i = _parse_yaml_node(lines, child_index, child_indent)
        out[key] = child
    return out, i


def split_frontmatter(text: str):
    m = re.match(r"---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm, body = {}, m.group(2)
    lines = m.group(1).split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not km:
            i += 1
            continue
        key, val = km.group(1), km.group(2).strip()
        if val in (">", ">-", "|", "|-"):  # block scalar: consume indented lines
            fm[key], i = _read_block_scalar(lines, i + 1, 0, val)
            continue
        if not val:
            child_index, child_indent = _next_indented_line(lines, i + 1)
            if child_index is not None and child_indent > 0:
                fm[key], i = _parse_yaml_node(lines, child_index, child_indent)
                continue
            fm[key] = {}
        else:
            fm[key] = _yaml_scalar(val)
        i += 1
    return fm, body


def read_skill(raw: bytes, filename: str) -> dict:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{filename}: SKILL.md must be UTF-8") from exc
    got = _capsule_or_reparse(raw, filename, "skill")
    cap = got[1] if got and got[0] == "ok" else None
    has_generated_markers = GENERATED_BEGIN in text or GENERATED_END in text
    if has_generated_markers and not _generated_markers_are_top_level(text):
        raise ValueError(
            "generated skill markers must be top-level Markdown blocks"
        )
    if has_generated_markers and not cap:
        raise ValueError(
            "generated skill content requires a valid current capsule"
        )
    rci = cap if cap else (got[1] if got else blank_rci())

    fm, body = split_frontmatter(text)
    body = GENERATED_RE.sub("", body)      # drop what a tool wrote, keep authored text
    body = CAPSULE_COMMENT_RE.sub("", body)
    body = re.sub(r"<!--\s*-->\s*$", "", body).rstrip() + "\n"

    # Authored surfaces always come from the CURRENT file; the capsule keeps
    # only what the markdown cannot show (vault, parameters, impl, platform).
    if fm.get("name"):
        rci["slug"] = fm["name"]
    elif not rci.get("slug"):
        rci["slug"] = _kebab(os.path.basename(os.path.dirname(os.path.abspath(filename))))
    if not rci.get("name"):
        rci["name"] = _pascal(rci["slug"])
    if fm.get("description"):
        rci["description"] = fm["description"]
    for k in ("version", "author", "license"):
        if fm.get(k):
            rci[k] = fm[k]
    if isinstance(fm.get("tags"), list):
        rci["tags"] = fm["tags"]
    rci["instructions"] = body.strip()
    if not cap:
        pm = PARAM_FENCE.search(body)
        if pm:
            try:
                rci["parameters"] = json.loads(pm.group(1))
            except Exception as exc:
                raise ValueError(
                    "Parameters fence is not valid JSON"
                ) from exc
            _validate_parameters(rci["parameters"])
        dm = DET_FENCE.search(body)
        if dm:
            rci["impl"] = {"lang": "python",
                           "perform_body": textwrap.dedent(dm.group(2)).strip()}
        sm = SYSCTX_SEC.search(body)
        if sm:
            rci["system_context"] = sm.group(1).strip()

    platform = rci.setdefault("platform", {})
    for key in ("compatibility", "disable-model-invocation"):
        if key in fm:
            platform[key] = fm[key]
    if "allowed-tools" in fm:
        platform.setdefault("claude", {})["allowed-tools"] = fm["allowed-tools"]
    if isinstance(fm.get("metadata"), dict):
        metadata = dict(fm["metadata"])
        for key in ("version", "author", "tags"):
            if key in metadata:
                rci[key] = metadata.pop(key)
        if metadata:
            platform["metadata"] = metadata

    _validate_rci_fields(rci)
    if cap and (cap.get("preserved") or {}).get("agent"):
        # Generated regions are deterministic output, not editable prose.
        # Regenerate them from the current authored surfaces + vaulted agent
        # and compare every byte, including commands, parameters, and code.
        expected_rci = json.loads(json.dumps(rci))
        expected = write_skill(expected_rci).decode("utf-8")
        current_blocks = GENERATED_BLOCK_RE.findall(text)
        expected_blocks = GENERATED_BLOCK_RE.findall(expected)
        if current_blocks != expected_blocks:
            raise ValueError(
                "generated skill regions do not match the checksum-verified "
                "projection"
            )

    preserve(rci, "skill", raw, filename)
    rci.setdefault("provenance", []).append(f"read:skill:{os.path.basename(filename)}")
    rci["_read_fmt"] = "skill"
    return rci


# --------------------------------------------------------------- skill (write)

def emit_frontmatter(pairs) -> str:
    # json.dumps output is valid YAML for strings (double-quoted scalar) and
    # lists (flow sequence) alike.
    out = ["---"] + [f"{k}: {json.dumps(v)}" for k, v in pairs] + ["---"]
    return "\n".join(out) + "\n"


def _fence_for(code: str) -> str:
    runs = re.findall(r"`+", code)
    longest = max((len(r) for r in runs), default=0)
    return "`" * max(3, longest + 1)


def write_skill(rci: dict) -> bytes:
    _validate_rci_fields(rci)
    # The skill is the PROJECTION: restore only when this very skill was the
    # source (the fixed-point path). Converting an agent always projects the
    # file in hand -- an heirloom skill vaulted generations ago must neither
    # be resurrected nor travel on (found by round-tripping a launchpad agent
    # whose capsule vaulted the SKILL.md that predated it).
    if rci.get("_read_fmt") == "skill":
        exact = restore(rci, "skill")
        if exact is not None:
            return exact  # byte-for-byte original — zero loss, not a re-render
    rci.get("preserved", {}).pop("skill", None)

    pairs = [("name", rci.get("slug") or _kebab(rci["name"])),
             ("description", rci.get("description", ""))]
    if rci.get("license"):
        pairs.append(("license", rci["license"]))
    platform = rci.get("platform") or {}
    if "compatibility" in platform:
        pairs.append(("compatibility", platform["compatibility"]))
    claude = platform.get("claude") or {}
    if "allowed-tools" in claude:
        pairs.append(("allowed-tools", claude["allowed-tools"]))
    if "disable-model-invocation" in platform:
        pairs.append(
            ("disable-model-invocation", platform["disable-model-invocation"])
        )
    metadata = dict(platform.get("metadata") or {})
    if rci.get("version") and rci["version"] != "1.0.0":
        metadata["version"] = rci["version"]
    if rci.get("author"):
        metadata["author"] = rci["author"]
    if rci.get("tags"):
        metadata["tags"] = rci["tags"]
    if metadata:
        pairs.append(("metadata", metadata))

    body = (rci.get("instructions") or "").strip()
    out = [emit_frontmatter(pairs), "\n", body, "\n"]

    params = rci.get("parameters") or {}
    authored_params = PARAM_FENCE.search(body)
    if authored_params:
        try:
            documented = json.loads(authored_params.group(1))
        except Exception as exc:
            raise ValueError("authored Parameters fence is not valid JSON") from exc
        if documented != params:
            raise ValueError(
                "authored Parameters fence conflicts with the agent tool schema"
            )
    if params.get("properties") and not authored_params:
        out += [f"\n{GENERATED_BEGIN}\n"
                "\n## Parameters\n\nThe typed contract this capability answers to "
                "(JSON Schema — the deterministic layer):\n\n```json\n",
                json.dumps(params, indent=2, sort_keys=True),
                f"\n```\n\n{GENERATED_END}\n"]

    source = restore(rci, "agent")
    if source is not None:
        try:
            code = source.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "vaulted agent must be UTF-8 for an Agent Skill projection"
            ) from exc
        if GENERATED_BEGIN in code or GENERATED_END in code:
            raise ValueError("agent source contains reserved generated-marker text")
        fence = _fence_for(code)
        fn = linked_agent_name(rci)
        cap_prev = rci.get("preserved", {}).get("agent", {}).get("sha256", "")[:16]
        out += [f"\n{GENERATED_BEGIN}\n"
                "\n## Run this — do not improvise\n\n"
                "This capability's deterministic implementation is a RAPP "
                f"single-file agent, linked beside this file as `{fn}` and "
                f"embedded as the fenced Python below (sha256 {cap_prev}…; a "
                "byte-exact copy is also vaulted in the capsule comment at the "
                "end of this file). On a host with sandbox execution, run the "
                "linked file directly — if it is missing, write the fence "
                f"contents verbatim to `{fn}` first:\n\n"
                "```bash\n"
                f"python3 {fn} '{{\"key\": \"value\"}}'      # arguments as one JSON object\n"
                f"echo '{{\"key\": \"value\"}}' | python3 {fn}   # or on stdin\n"
                f"python3 {fn} --tool                      # emit the JSON tool contract\n"
                "```\n\n"
                "Treat stdout as a tool result. If it reports missing or unresolved "
                "inputs, stop and collect them. If it returns `steps`, execute those "
                "steps in order exactly as returned; if it returns `instructions`, "
                "follow them with the supplied inputs. Otherwise use the result "
                "verbatim. Do not invent behavior beyond that output. On a host "
                "without code execution, "
                "treat the Parameters schema and the code below as the exact "
                "specification and never paraphrase a step. Never edit inside the "
                "generated markers; a converter-equipped host can instead restore "
                "the original file checksum-verified with the installed "
                "`rapp-agent-converter/scripts/toast.py convert SKILL.md --to agent`."
                "\n\n"
                f"{fence}python  # rapp:deterministic\n{code}"
                + ("" if code.endswith("\n") else "\n")
                + f"{fence}\n\n{GENERATED_END}\n"]
    elif (rci.get("impl") or {}).get("perform_body"):
        code = rci["impl"]["perform_body"]
        fence = _fence_for(code)
        out += [f"\n{GENERATED_BEGIN}\n"
                "\n## Deterministic implementation\n\nRun this instead of "
                "improvising when the inputs are well-formed:\n\n"
                f"{fence}python  # rapp:deterministic\n{code.strip()}\n{fence}\n"
                f"\n{GENERATED_END}\n"]

    if rci.get("examples"):
        out.append("\n## Examples\n\n")
        for ex in rci["examples"]:
            out.append(f"- **in:** {ex.get('input', '')}\n  **out:** {ex.get('output', '')}\n")

    out.append(f"\n<!-- {pack_capsule(rci)} -->\n")
    return "".join(out).encode()


# --------------------------------------------------------------- agent (write)

def _py_literal(value, indent: int) -> str:
    """JSON-ish value -> Python source. Rewrites true/false/null outside strings."""
    text = json.dumps(value, indent=2)
    out, in_str, esc = [], False, False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        for tok, rep in (("true", "True"), ("false", "False"), ("null", "None")):
            if text.startswith(tok, i):
                out.append(rep)
                i += len(tok)
                break
        else:
            out.append(ch)
            i += 1
    return textwrap.indent("".join(out), " " * indent).lstrip()


AGENT_TEMPLATE = '''"""{docstring}"""

import json
import re
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
            return {{"type": "function", "function": {{
                "name": self.name,
                "description": self.metadata.get("description", ""),
                "parameters": self.metadata.get("parameters", {{}})}}}}

# The procedural layer, verbatim from the source capability.
INSTRUCTIONS = {instructions!r}

# Ordered commands lifted verbatim from the capability's own documentation.
STEPS = {steps}


class {cls}(BasicAgent):
    def __init__(self):
        self.name = {name!r}
        self.metadata = {metadata}
        super().__init__(name=self.name, metadata=self.metadata)

{perform}

if __name__ == "__main__":
    #     echo '{{"arg": "value"}}' | python3 {filename}
    #     python3 {filename} '{{"arg": "value"}}'
    #     python3 {filename} --tool          # emit the JSON tool contract
    _a = sys.argv[1:]
    if _a and _a[0] == "--tool":
        print(json.dumps({cls}().to_tool(), indent=2))
    else:
        _raw = _a[0] if _a else (sys.stdin.read().strip() or "{{}}")
        print({cls}().perform(**json.loads(_raw)))

# {capsule}
'''

STEP_PERFORM = f"""    def perform(self, **kwargs):  {GENERATED_PERFORM_MARK}
        missing = [k for k in self.metadata["parameters"].get("required", [])
                   if k not in kwargs]
        if missing:
            return json.dumps({{"status": "error", "missing_required": missing}}, indent=2)
        resolved, unresolved = [], set()
        for step in STEPS:
            cmd = step["cmd"] if isinstance(step, dict) else str(step)
            for key, value in kwargs.items():
                for token in ("<" + key.replace("_", "-") + ">", "<" + key + ">",
                              "{{{{" + key + "}}}}", "$" + key.upper()):
                    cmd = cmd.replace(token, str(value))
            for leftover in re.findall(r"<[a-zA-Z][a-zA-Z0-9 _.-]{{1,40}}>", cmd):
                unresolved.add(leftover)
            resolved.append(cmd)
        return json.dumps({{"status": "ok", "steps": resolved,
                           "unresolved_placeholders": sorted(unresolved),
                           "note": "Resolved deterministically by the agent; "
                                   "run in order. Nothing was executed here."}}, indent=2)"""

DEFAULT_PERFORM = f"""    def perform(self, **kwargs):  {GENERATED_PERFORM_MARK}
        return json.dumps({{"status": "ok", "instructions": INSTRUCTIONS,
                           "inputs": kwargs,
                           "note": "Prose-only capability: follow INSTRUCTIONS "
                                   "with the given inputs."}}, indent=2)"""


def write_agent(rci: dict) -> bytes:
    _validate_rci_fields(rci)
    # The agent is the HOME format: a vaulted agent is the implementation of
    # record, so restoring it is always right. (An agent file that evolved
    # past its own capsule is caught at read time and reparsed fresh.)
    exact = restore(rci, "agent")
    if exact is not None:
        return exact  # byte-for-byte original -- zero loss, not a re-render

    impl = rci.get("impl") or {}
    if impl.get("steps") and not impl.get("perform") and not impl.get("perform_body"):
        perform = STEP_PERFORM
    elif impl.get("perform"):
        perform = impl["perform"]
        if not perform.startswith("    "):
            perform = textwrap.indent(perform, "    ")
    elif impl.get("perform_body"):
        perform = ("    def perform(self, **kwargs):\n"
                   + textwrap.indent(impl["perform_body"], "        "))
    else:
        perform = DEFAULT_PERFORM

    name = rci.get("name") or _pascal(rci.get("slug") or "capability")
    if not TOOL_NAME_RE.match(name):
        name = _pascal(_kebab(name))
    metadata = {
        "name": name,
        "description": rci.get("description", ""),
        "parameters": rci.get("parameters") or
        {"type": "object", "properties": {}, "required": []},
    }
    doc = (rci.get("description") or name).replace('"""', "'''")
    doc = (f"{name} -- {doc}\n\nGenerated by the rapp skill from "
           f"{rci.get('slug') or name}. The RCI capsule at the bottom of this file "
           f"carries the full original; `toast.py convert` restores it byte-exact.")

    cls = _class_identifier(name)
    cls = cls if cls.endswith("Agent") else cls + "Agent"
    src = AGENT_TEMPLATE.format(
        docstring=doc,
        instructions=rci.get("instructions", ""),
        steps=_py_literal(impl.get("steps") or [], 0),
        cls=cls,
        name=name,
        metadata=_py_literal(metadata, 8),
        perform=perform,
        filename=agent_filename(rci),
        capsule=pack_capsule(rci),
    )
    compile(src, agent_filename(rci), "exec")  # syntax gate only -- never executed
    return src.encode()


def agent_filename(rci: dict) -> str:
    return f"{_snake(rci.get('slug') or rci.get('name') or 'capability')}_agent.py"


def linked_agent_name(rci: dict) -> str:
    """The sidecar name the projection links to — the vaulted original's own
    filename when known, so the link and the restore always agree."""
    vaulted = (rci.get("preserved", {}).get("agent") or {}).get("filename")
    return _safe_agent_filename(vaulted or agent_filename(rci))


# ------------------------------------------------------------------------ I/O

def detect(path: str) -> str:
    if path.endswith(".py"):
        return "agent"
    if path.endswith(".md"):
        return "skill"
    raise SystemExit(f"[FAIL] cannot detect format of {path} (expected .py or .md)")


def load(path: str, fmt: str) -> dict:
    raw = open(path, "rb").read()
    return read_agent(raw, path) if fmt == "agent" else read_skill(raw, path)


def render(rci: dict, fmt: str) -> bytes:
    return write_agent(rci) if fmt == "agent" else write_skill(rci)


def default_out(rci: dict, fmt: str, src_path: str) -> str:
    d = os.path.dirname(os.path.abspath(src_path))
    return os.path.join(
        d,
        "SKILL.md" if fmt == "skill" else linked_agent_name(rci),
    )


def _same_target(left: str, right: str) -> bool:
    if os.path.normcase(os.path.realpath(left)) == \
            os.path.normcase(os.path.realpath(right)):
        return True
    try:
        return os.path.exists(left) and os.path.exists(right) \
            and os.path.samefile(left, right)
    except OSError:
        return False


def cmd_convert(a) -> int:
    src_fmt = a.from_fmt or detect(a.path)
    if a.to == src_fmt:
        raise SystemExit(f"[FAIL] source already is format {src_fmt!r}")
    rci = load(a.path, src_fmt)
    # Only the home format restores across a conversion; the projection is
    # always freshly synthesized from the file in hand.
    restored = a.to == "agent" and rci.get("preserved", {}).get("agent") is not None
    if not restored:
        rci.setdefault("provenance", []).append(f"convert:{src_fmt}->{a.to}")
    out_bytes = render(rci, a.to)
    out_path = a.out or default_out(rci, a.to, a.path)
    if _same_target(out_path, a.path):
        raise SystemExit("[FAIL] refusing to overwrite the source file with a "
                         "different format -- pass -o with another path")

    side = side_bytes = None
    if a.to == "skill":
        side_bytes = restore(rci, "agent")
        if side_bytes is not None:
            side = os.path.join(
                os.path.dirname(os.path.abspath(out_path)),
                linked_agent_name(rci),
            )
            if _same_target(out_path, side):
                raise SystemExit(
                    "[FAIL] SKILL.md and linked-agent destinations resolve "
                    "to the same file"
                )

    # Preflight the complete pair before writing either artifact. A conflicting
    # linked file must not leave behind a SKILL.md that tells hosts to run it.
    for target, data in ((out_path, out_bytes), (side, side_bytes)):
        if not target or data is None \
                or os.path.abspath(target) == os.path.abspath(a.path):
            continue
        if os.path.exists(target) and not a.force \
                and open(target, "rb").read() != data:
            raise SystemExit(
                f"[FAIL] {target} exists with different content "
                "-- pass -o or --force"
            )

    already_present = False
    if os.path.exists(out_path) and not a.force:
        already_present = True
    parent = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(parent, exist_ok=True)

    # Write the linked implementation first. If the later SKILL.md write fails,
    # the residue is a valid standalone agent rather than a broken instruction
    # file pointing at hostile or unrelated bytes.
    if side and side_bytes is not None \
            and os.path.abspath(side) != os.path.abspath(a.path):
        os.makedirs(os.path.dirname(os.path.abspath(side)), exist_ok=True)
        if a.force or not os.path.exists(side):
            with open(side, "wb") as f:
                f.write(side_bytes)

    if not already_present:
        with open(out_path, "wb") as f:
            f.write(out_bytes)
    mode = "RESTORED (byte-exact)" if restored else "SYNTHESISED"
    suffix = " (already present, byte-identical)" if already_present else ""
    print(f"{src_fmt} -> {a.to}: {mode}  {out_path}  "
          f"sha256 {_sha(out_bytes)[:16]}{suffix}")

    if a.to == "skill":
        # The projection ships as a PAIR: the self-sufficient SKILL.md plus a
        # linked python file that literally IS the agent.py, so a host with
        # execution (Copilot Studio's sandbox) calls the real implementation
        # first-party instead of re-deriving it from the fence.
        src_bytes = side_bytes
        if src_bytes is not None and side:
            if os.path.abspath(side) == os.path.abspath(a.path):
                print(f"  linked agent: {side} (the source file itself)")
            else:
                print(f"  linked agent: {side}  sha256 {_sha(src_bytes)[:16]} "
                      "(byte-exact copy of the source)")
    return 0


def cmd_roundtrip(a) -> int:
    try:
        return _cmd_roundtrip(a)
    except (ValueError, OSError) as exc:
        print(f"[FAIL] {exc}")
        return 1


def _cmd_roundtrip(a) -> int:
    """Prove fidelity for the given artifact. Exit 0 only on hard evidence.

    agent input: agent -> skill -> agent must return the exact original bytes,
    and the emitted projection must be a fixed point over --cycles (a single
    round trip cannot see slow drift).

    toasted-skill input: the file must be its own fixed point, and the vaulted
    agent must restore checksum-verified. (Byte-comparing skill -> agent ->
    skill instead would measure the capsule's append-only ledger growing --
    the ledger working, not fidelity lost.)
    """
    src_fmt = detect(a.path)
    original = open(a.path, "rb").read()
    raw_skill = (
        src_fmt == "skill"
        and not unpack_capsule(original.decode("utf-8", "replace"))
    )
    if raw_skill:
        if not a.allow_raw:
            print("RAW BREAD -- this SKILL.md carries no capsule, so a byte-exact "
                  "return trip does not exist yet. Convert it to an agent first "
                  "(that emission carries the capsule), or pass --allow-raw to "
                  "measure capability-level fidelity only.")
            return 2
        first_agent = write_agent(read_skill(original, a.path))
        projection = write_skill(read_agent(first_agent, "synthesised_agent.py"))
        second_agent = write_agent(read_skill(projection, "SKILL.md"))
        ok = first_agent == second_agent
        print("raw skill -> agent -> skill -> agent: "
              f"{'STABLE' if ok else 'DRIFT'}  "
              f"({len(first_agent)}B -> {len(second_agent)}B)")
        if not ok:
            print(f"  sha first  {_sha(first_agent)[:16]}\n"
                  f"  sha second {_sha(second_agent)[:16]}")
            return 1
        for cycle in range(max(1, a.cycles)):
            cycle_agent = write_agent(read_skill(projection, "SKILL.md"))
            cycle_skill = write_skill(
                read_agent(cycle_agent, "synthesised_agent.py")
            )
            if cycle_agent != first_agent or cycle_skill != projection:
                print(f"  CAPABILITY DRIFT at cycle {cycle + 1}")
                return 1
            projection = cycle_skill
        print(f"  synthesised capability fixed point holds over "
              f"{max(1, a.cycles)} cycles")
        return 0

    if src_fmt == "agent":
        projection = write_skill(read_agent(original, a.path))
        back = write_agent(read_skill(projection, "SKILL.md"))
        ok = back == original
        print(f"agent -> skill -> agent: "
              f"{'IDENTICAL' if ok else 'DRIFT'}  ({len(original)}B -> {len(back)}B)")
        if not ok:
            print(f"  sha in  {_sha(original)[:16]}\n  sha out {_sha(back)[:16]}")
            return 1
        for cycle in range(max(1, a.cycles)):
            cycle_agent = write_agent(read_skill(projection, "SKILL.md"))
            cycle_skill = write_skill(read_agent(cycle_agent, a.path))
            if cycle_agent != original:
                print(f"  AGENT DRIFT at cycle {cycle + 1}: "
                      f"{_sha(original)[:16]} -> {_sha(cycle_agent)[:16]}")
                return 1
            if cycle_skill != projection:
                print(f"  PROJECTION DRIFT at cycle {cycle + 1}: "
                      f"{_sha(projection)[:16]} -> {_sha(cycle_skill)[:16]}")
                return 1
            projection = cycle_skill
        print(f"  projection fixed point holds over {max(1, a.cycles)} cycles")
        return 0

    rci = load(a.path, "skill")
    vault = rci.get("preserved", {}).get("agent")
    if not vault:
        print("no vaulted agent in the capsule -- conversion to agent "
              "would be a SYNTHESIS (capability-level, not byte-level)")
        return 2
    restored = restore(rci, "agent")  # raises on checksum mismatch
    print(f"vaulted agent restores byte-exact: {vault['filename']}  "
          f"sha256 {_sha(restored)[:16]} (checksum verified)")

    # The visible implementation and the vaulted bytes are two claims about
    # the same agent. Locate the fence structurally inside generated regions;
    # authored example fences and mutable prose cannot disable this check.
    text = original.decode("utf-8", "replace")
    fences = _generated_agent_fences(text)
    if len(fences) != 1:
        print("  INLINE DRIFT: expected exactly one generated deterministic "
              f"Python fence, found {len(fences)}")
        return 1
    shown = fences[0].rstrip("\n")
    truth = restored.decode("utf-8", "replace").rstrip("\n")
    if shown != truth:
        print("  INLINE DRIFT: the fenced Python no longer matches the "
              "vaulted implementation -- the file was edited inside "
              "the generated markers")
        return 1
    print("  inline python matches the vaulted agent")
    return 0


def cmd_inspect(a) -> int:
    fmt = detect(a.path)
    rci = load(a.path, fmt)
    preserved = rci.get("preserved", {})
    print(json.dumps({
        "spec": SPEC,
        "format": fmt,
        "capsule": bool(unpack_capsule(open(a.path, "rb").read().decode("utf-8", "replace"))),
        "name": rci.get("name"),
        "slug": rci.get("slug"),
        "version": rci.get("version"),
        "parameters": len((rci.get("parameters") or {}).get("properties", {})),
        "preserved": {k: v["sha256"][:16] for k, v in preserved.items()},
        "provenance": rci.get("provenance", []),
    }, indent=2))
    return 0


SAMPLE_AGENT = '''"""Sample cartridge used by selftest. Echoes its arguments.

An authored example fence must not be mistaken for the generated implementation:

```python
print("documentation only")
```
"""

from agents.basic_agent import BasicAgent
import json


class EchoAgent(BasicAgent):
    def __init__(self):
        self.name = "Echo"
        self.metadata = {
            "name": self.name,
            "description": "Echoes the given text back, uppercased on request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to echo."},
                    "shout": {"type": "boolean", "description": "Uppercase it.",
                              "default": False},
                },
                "required": ["text"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        text = kwargs.get("text", "")
        if kwargs.get("shout"):
            text = text.upper()
        return json.dumps({"status": "success", "echo": text})
'''


def cmd_selftest(_a) -> int:
    """Every verdict must be able to fire, or the oracle proves nothing."""
    import tempfile
    failures = []
    gzip_probe = _gz(b"rapp-agent-converter-determinism-v1")
    if _sha(gzip_probe) != \
            "dd13d986790e5029a2058b7865a01e8a0f1b7f774246aaf02a63e2bca7347aff":
        failures.append("gzip capsule bytes vary on this Python/runtime")
    with tempfile.TemporaryDirectory() as td:
        agent_path = os.path.join(td, "echo_agent.py")
        with open(agent_path, "wb") as f:
            f.write(SAMPLE_AGENT.encode())

        # 1. MATCH must fire: the round trip is byte-identical.
        ns = argparse.Namespace(path=agent_path, cycles=3, allow_raw=False)
        if cmd_roundtrip(ns) != 0:
            failures.append("round trip on the sample agent was not IDENTICAL")

        # 2. DIFFER must fire: corrupt the restored payload -> checksum refusal.
        rci = load(agent_path, "agent")
        if rci.get("slug") != "echo":
            failures.append("agent without display_name projected as the wrong slug")
        skill_path = os.path.join(td, "SKILL.md")
        with open(skill_path, "wb") as f:
            f.write(write_skill(rci))
        rci2 = load(skill_path, "skill")
        if os.path.basename(default_out(rci2, "agent", skill_path)) != "echo_agent.py":
            failures.append("restore default ignored the vaulted agent filename")
        rci2["preserved"]["agent"]["sha256"] = "0" * 64
        try:
            write_agent(rci2)
            failures.append("corrupted capsule checksum was NOT refused")
        except ValueError:
            print("corruption probe: checksum refusal fired as designed")

        # 3. INLINE DRIFT must fire: tamper with the code inside the fence.
        tampered = open(skill_path, "rb").read().replace(b'"echo": text',
                                                         b'"echo": "HACKED"')
        tam_path = os.path.join(td, "TAMPERED.md")
        with open(tam_path, "wb") as f:
            f.write(tampered)
        if cmd_roundtrip(argparse.Namespace(path=tam_path, cycles=1,
                                            allow_raw=False)) != 1:
            failures.append("in-fence tampering was NOT detected")
        else:
            print("tamper probe: inline drift detection fired as designed")

        command_tampered = open(skill_path, "rb").read().replace(
            b"python3 echo_agent.py", b"python3 attacker_payload.py", 1
        )
        command_path = os.path.join(td, "COMMAND_TAMPERED.md")
        with open(command_path, "wb") as f:
            f.write(command_tampered)
        if cmd_roundtrip(argparse.Namespace(path=command_path, cycles=1,
                                            allow_raw=False)) != 1:
            failures.append("generated command tampering was NOT detected")

        wrapped = open(skill_path, "rb").read()
        wrapped = wrapped.replace(
            GENERATED_BEGIN.encode(),
            b"`````\n" + GENERATED_BEGIN.encode(),
            1,
        )
        last_end = wrapped.rfind(GENERATED_END.encode())
        wrapped = (
            wrapped[:last_end]
            + GENERATED_END.encode()
            + b"\n`````"
            + wrapped[last_end + len(GENERATED_END):]
        )
        wrapped_path = os.path.join(td, "WRAPPED.md")
        with open(wrapped_path, "wb") as f:
            f.write(wrapped)
        if cmd_roundtrip(argparse.Namespace(path=wrapped_path, cycles=1,
                                            allow_raw=False)) != 1:
            failures.append("generated regions hidden in a fence were accepted")

        # Changing prose must not disable the structural inline check.
        reworded = open(skill_path, "rb").read().replace(
            b"deterministic implementation is a RAPP single-file agent",
            b"implementation travels as linked Python",
        ).replace(b'"echo": text', b'"echo": "HACKED"')
        reworded_path = os.path.join(td, "REWORDED.md")
        with open(reworded_path, "wb") as f:
            f.write(reworded)
        if cmd_roundtrip(argparse.Namespace(path=reworded_path, cycles=1,
                                            allow_raw=False)) != 1:
            failures.append("rewording prose disabled inline drift detection")

        # 4. Raw bread must be refused by the oracle.
        raw_path = os.path.join(td, "RAW.md")
        with open(raw_path, "w") as f:
            f.write("---\nname: raw-bread\ndescription: no capsule here\n---\n\n"
                    "Documents `rci-capsule:v1:` as syntax.\n\n"
                    "```python\nprint('documentation only')\n```\n")
        if cmd_roundtrip(argparse.Namespace(path=raw_path, cycles=1,
                                            allow_raw=False)) != 2:
            failures.append("raw bread was not refused")
        if cmd_roundtrip(argparse.Namespace(path=raw_path, cycles=2,
                                            allow_raw=True)) != 0:
            failures.append("raw capability fixed point was not verified")
        if (load(raw_path, "skill").get("impl") or {}).get("perform_body"):
            failures.append("ordinary Python example became executable behavior")

        numeric_path = os.path.join(td, "NUMERIC.md")
        with open(numeric_path, "w") as f:
            f.write("---\nname: 123-tool\ndescription: numeric slug\n---\n\nProse.\n")
        try:
            numeric_agent = write_agent(load(numeric_path, "skill"))
            compile(numeric_agent, "123_tool_agent.py", "exec")
        except SyntaxError:
            failures.append("numeric-leading skill name generated invalid Python")

        metadata_path = os.path.join(td, "METADATA.md")
        with open(metadata_path, "w") as f:
            f.write(
                "---\n"
                "name: metadata-skill\n"
                "description: block metadata\n"
                "allowed-tools: Read, Bash\n"
                "metadata:\n"
                "  author: Kody\n"
                "  version: \"2.0.0\"\n"
                "  tags:\n"
                "    - conversion\n"
                "    - rapp\n"
                "  custom:\n"
                "    owner: scout\n"
                "    changelog: >-\n"
                "      first release\n"
                "      keeps fidelity\n"
                "---\n\nProse.\n"
            )
        metadata_rci = load(metadata_path, "skill")
        if metadata_rci.get("author") != "Kody" \
                or metadata_rci.get("version") != "2.0.0" \
                or metadata_rci.get("tags") != ["conversion", "rapp"] \
                or metadata_rci.get("platform", {}).get("metadata", {}) \
                .get("custom", {}).get("owner") != "scout" \
                or metadata_rci.get("platform", {}).get("metadata", {}) \
                .get("custom", {}).get("changelog") \
                != "first release keeps fidelity":
            failures.append("block-form metadata was not preserved")

        traversing = load(agent_path, "agent")
        traversing["preserved"]["agent"]["filename"] = "../../escape_agent.py"
        try:
            linked_agent_name(traversing)
            failures.append("vaulted filename path traversal was accepted")
        except ValueError:
            pass

        bad_shape = base64.b64encode(_gz(json.dumps([]).encode())).decode()
        shaped_path = os.path.join(td, "BAD_SHAPE.md")
        with open(shaped_path, "w") as f:
            f.write(f"---\nname: bad\ndescription: bad\n---\n\n"
                    f"<!-- rci-capsule:v1:{bad_shape} -->\n")
        try:
            load(shaped_path, "skill")
            failures.append("non-object capsule shape was accepted")
        except ValueError:
            pass

        bad_impl = load(agent_path, "agent")
        bad_impl["impl"] = "not-an-object"
        bad_impl_payload = base64.b64encode(
            _gz(
                json.dumps(
                    {k: v for k, v in bad_impl.items()
                     if not k.startswith("_")},
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            )
        ).decode()
        bad_impl_path = os.path.join(td, "BAD_IMPL.md")
        with open(bad_impl_path, "w") as f:
            f.write(
                "---\nname: bad-impl\ndescription: bad\n---\n\n"
                f"<!-- rci-capsule:v1:{bad_impl_payload} -->\n"
            )
        try:
            load(bad_impl_path, "skill")
            failures.append("capsule with invalid impl type was accepted")
        except ValueError:
            pass

        bad_platform = load(agent_path, "agent")
        bad_platform["platform"] = {"metadata": [1]}
        try:
            write_skill(bad_platform)
            failures.append("invalid nested platform metadata was accepted")
        except ValueError:
            pass

        conflict_agent = SAMPLE_AGENT.replace(
            '\n"""\n\nfrom agents.basic_agent',
            '\n\n## Parameters\n\n```json\n'
            '{"type":"object","properties":{"wrong":{"type":"string"}},'
            '"required":["wrong"]}\n```\n'
            '"""\n\nfrom agents.basic_agent',
        )
        conflict_rci = read_agent(conflict_agent.encode(), "conflict_agent.py")
        try:
            write_skill(conflict_rci)
            failures.append("conflicting authored Parameters fence was accepted")
        except ValueError:
            pass

        invalid_params_path = os.path.join(td, "INVALID_PARAMS.md")
        with open(invalid_params_path, "w") as f:
            f.write(
                "---\nname: invalid-params\ndescription: bad schema\n---\n\n"
                "## Parameters\n\n```json\n"
                '{"type":"array","items":{"type":"string"}}\n'
                "```\n"
            )
        try:
            load(invalid_params_path, "skill")
            failures.append("non-object parameter schema was accepted")
        except ValueError:
            pass

        alias_dir = os.path.join(td, "alias")
        os.makedirs(alias_dir)
        try:
            cmd_convert(
                argparse.Namespace(
                    path=agent_path,
                    from_fmt=None,
                    to="skill",
                    out=os.path.join(alias_dir, "echo_agent.py"),
                    force=False,
                )
            )
            failures.append("pair destinations resolving to one file were accepted")
        except SystemExit:
            pass

        latin1_path = os.path.join(td, "latin1_agent.py")
        with open(latin1_path, "wb") as f:
            f.write(
                b"# -*- coding: latin-1 -*-\n"
                b"class LatinAgent:\n"
                b"    def perform(self, **kwargs):\n"
                b"        return 'caf" + bytes([0xE9]) + b"'\n"
            )
        try:
            load(latin1_path, "agent")
            failures.append("non-UTF-8 agent was accepted for projection")
        except ValueError:
            pass

        # 5. A synthesized launchpad agent must be valid Python (compile gate
        #    inside write_agent), and edits to it must be HONORED on the next
        #    projection -- the file outranks its capsule.
        rci3 = load(raw_path, "skill")
        agent2_path = os.path.join(td, "raw_bread_agent.py")
        with open(agent2_path, "wb") as f:
            f.write(write_agent(rci3))
        edited = open(agent2_path, "rb").read().replace(b"no capsule here",
                                                        b"EDITED DESCRIPTION")
        with open(agent2_path, "wb") as f:
            f.write(edited)
        reskill = write_skill(load(agent2_path, "agent"))
        if b"EDITED DESCRIPTION" not in reskill.split(b"<!--")[0]:
            failures.append("edit to a synthesized agent was IGNORED on re-projection")
        else:
            print("edit-honored probe: file outranks capsule as designed")

    print("SELFTEST " + ("FAIL:\n  - " + "\n  - ".join(failures) if failures else "PASS"))
    return 1 if failures else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="toast.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("convert", help="convert between agent.py and SKILL.md")
    c.add_argument("path")
    c.add_argument("--to", required=True, choices=FORMATS)
    c.add_argument("--from", dest="from_fmt", choices=FORMATS)
    c.add_argument("-o", "--out")
    c.add_argument("--force", action="store_true")
    c.set_defaults(fn=cmd_convert)

    r = sub.add_parser("roundtrip", help="prove the conversion is byte-identical")
    r.add_argument("path")
    r.add_argument("--cycles", type=int, default=3)
    r.add_argument("--allow-raw", action="store_true")
    r.set_defaults(fn=cmd_roundtrip)

    i = sub.add_parser("inspect", help="show capsule status and identity")
    i.add_argument("path")
    i.set_defaults(fn=cmd_inspect)

    s = sub.add_parser("selftest", help="prove every verdict can fire")
    s.set_defaults(fn=cmd_selftest)

    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except (ValueError, OSError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
