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
CAPSULE_RE = re.compile(r"rci-capsule:v1:([A-Za-z0-9+/=]+)")
GENERATED_BEGIN = "<!-- toaster:generated:begin -->"
GENERATED_END = "<!-- toaster:generated:end -->"
GENERATED_RE = re.compile(
    r"\n?<!-- toaster:generated:begin -->.*?<!-- toaster:generated:end -->\n?", re.S)
GENERATED_PERFORM_MARK = "# toaster:generated-perform"
DET_FENCE = re.compile(
    r"(`{3,})python[ \t]*(?:#[ \t]*rapp:deterministic)?[ \t]*\n(.*?)\1", re.S)
PARAM_FENCE = re.compile(r"##+\s*Parameters\s*\n+```json\s*\n(.*?)```", re.S | re.I)
SYSCTX_SEC = re.compile(r"##+\s*System Context\s*\n+(.*?)(?=\n##+\s|\Z)", re.S | re.I)
TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
FORMATS = ("agent", "skill")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _gz(b: bytes) -> bytes:
    # mtime=0 keeps the gzip header deterministic — without it two conversions
    # of the same bytes in different seconds emit different capsules.
    return gzip.compress(b, 9, mtime=0)


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
    payload = json.dumps({k: v for k, v in rci.items() if not k.startswith("_")},
                         sort_keys=True, separators=(",", ":")).encode()
    return "rci-capsule:v1:" + base64.b64encode(_gz(payload)).decode()


def unpack_capsule(text: str):
    # LAST match, deliberately: a converted agent's own source (with its old
    # trailing capsule) can ride inside this artifact, and the capsule this
    # file carries is always appended after it. First-match read the stale
    # passenger instead of the ledger -- found by round-tripping an upstream
    # cartridge that embedded its history.
    ms = CAPSULE_RE.findall(text)
    if not ms:
        return None
    try:
        return json.loads(gzip.decompress(base64.b64decode(ms[-1])))
    except Exception:
        return None


def strip_capsules(b: bytes) -> bytes:
    """Every capsule removed -- the content two ledger-bearing artifacts share."""
    t = re.sub(r"<!--\s*rci-capsule:v1:[A-Za-z0-9+/=]+\s*-->", "",
               b.decode("utf-8", "replace"))
    t = re.sub(r"#\s*rci-capsule:v1:[A-Za-z0-9+/=]+", "", t)
    return t.encode()


# The sentence only THIS tool writes into its inline projection; its presence
# means the python fence claims to be the complete vaulted agent, so the two
# are checkable against each other.
INLINE_MARK = ("deterministic implementation is a RAPP single-file agent, "
               "linked beside this file")


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
    text = raw.decode("utf-8", "replace").lstrip("\ufeff")
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
    if not (isinstance(params, dict) and params.get("type") == "object"):
        if params is not None:
            print(f"[WARN] metadata['parameters'] is not a JSON-Schema object in "
                  f"{filename}", file=sys.stderr)
        params = {"type": "object", "properties": {}, "required": []}

    # The FILE always defines the capability; a capsule is ledger (provenance,
    # vault, host extras), never an override. A synthesized agent has no way
    # to vault itself, so a capsule-trusting reader would ignore every edit
    # made to the file afterwards -- the exact drift this tool exists to stop.
    rci["name"] = name if isinstance(name, str) else cls.name
    rci["slug"] = _kebab(manifest.get("display_name") or "") or rci.get("slug") \
        or _kebab(rci["name"])
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

    preserve(rci, "agent", raw, filename)
    rci.setdefault("provenance", []).append(f"read:agent:{os.path.basename(filename)}")
    rci["_read_fmt"] = "agent"
    return rci


# ---------------------------------------------------------------- skill (read)

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
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            if val.startswith("|"):
                fm[key] = "\n".join(block).strip()
            else:
                # folded: blank lines separate paragraphs, which stay newlines
                paras, cur = [], []
                for b in block:
                    if b:
                        cur.append(b)
                    elif cur:
                        paras.append(" ".join(cur))
                        cur = []
                if cur:
                    paras.append(" ".join(cur))
                fm[key] = "\n".join(paras)
            continue
        if val.startswith(("[", "{", '"')):
            try:
                fm[key] = json.loads(val)
            except Exception:
                fm[key] = val.strip('"').strip("'")
        else:
            fm[key] = val.strip("'")
        i += 1
    return fm, body


def read_skill(raw: bytes, filename: str) -> dict:
    text = raw.decode("utf-8", "replace")
    got = _capsule_or_reparse(raw, filename, "skill")
    cap = got[1] if got and got[0] == "ok" else None
    rci = cap if cap else (got[1] if got else blank_rci())

    fm, body = split_frontmatter(text)
    body = GENERATED_RE.sub("", body)      # drop what a tool wrote, keep authored text
    body = re.sub(r"<!--\s*rci-capsule:v1:[A-Za-z0-9+/=]+\s*-->", "", body)
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
            except Exception:
                pass
        dm = DET_FENCE.search(body)
        if dm:
            rci["impl"] = {"lang": "python",
                           "perform_body": textwrap.dedent(dm.group(2)).strip()}
        sm = SYSCTX_SEC.search(body)
        if sm:
            rci["system_context"] = sm.group(1).strip()

    for k in ("metadata",):
        if isinstance(fm.get(k), dict):
            rci.setdefault("platform", {}).update(fm[k])

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
    if rci.get("version") and rci["version"] != "1.0.0":
        pairs.append(("version", rci["version"]))
    for k in ("author", "license"):
        if rci.get(k):
            pairs.append((k, rci[k]))
    if rci.get("tags"):
        pairs.append(("tags", rci["tags"]))

    body = (rci.get("instructions") or "").strip()
    out = [emit_frontmatter(pairs), "\n", body, "\n"]

    params = rci.get("parameters") or {}
    if params.get("properties") and not PARAM_FENCE.search(body):
        out += [f"\n{GENERATED_BEGIN}\n"
                "\n## Parameters\n\nThe typed contract this capability answers to "
                "(JSON Schema — the deterministic layer):\n\n```json\n",
                json.dumps(params, indent=2),
                f"\n```\n\n{GENERATED_END}\n"]

    source = restore(rci, "agent")
    if source is not None:
        code = source.decode("utf-8", "replace")
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
                "Use its output verbatim — do not reason out the answer yourself and "
                "do not paraphrase the result. On a host without code execution, "
                "treat the Parameters schema and the code below as the exact "
                "specification and never paraphrase a step. Never edit inside the "
                "generated markers; a toaster-equipped host can instead restore the "
                "original file checksum-verified with "
                "`toast.py convert SKILL.md --to agent`.\n\n"
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

    cls = _pascal(name)
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
    return ((rci.get("preserved", {}).get("agent") or {}).get("filename")
            or agent_filename(rci))


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
    return os.path.join(d, "SKILL.md" if fmt == "skill" else agent_filename(rci))


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
    if os.path.abspath(out_path) == os.path.abspath(a.path):
        raise SystemExit("[FAIL] refusing to overwrite the source file with a "
                         "different format -- pass -o with another path")
    if os.path.exists(out_path) and not a.force:
        raise SystemExit(f"[FAIL] {out_path} exists -- pass -o or --force")
    parent = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(parent, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(out_bytes)
    mode = "RESTORED (byte-exact)" if restored else "SYNTHESISED"
    print(f"{src_fmt} -> {a.to}: {mode}  {out_path}  sha256 {_sha(out_bytes)[:16]}")

    if a.to == "skill":
        # The projection ships as a PAIR: the self-sufficient SKILL.md plus a
        # linked python file that literally IS the agent.py, so a host with
        # execution (Copilot Studio's sandbox) calls the real implementation
        # first-party instead of re-deriving it from the fence.
        src_bytes = restore(rci, "agent")
        if src_bytes is not None:
            side = os.path.join(os.path.dirname(os.path.abspath(out_path)),
                                linked_agent_name(rci))
            if os.path.abspath(side) == os.path.abspath(a.path):
                print(f"  linked agent: {side} (the source file itself)")
            else:
                if os.path.exists(side) and not a.force \
                        and open(side, "rb").read() != src_bytes:
                    raise SystemExit(f"[FAIL] {side} exists with different "
                                     "content -- pass --force to overwrite")
                with open(side, "wb") as f:
                    f.write(src_bytes)
                print(f"  linked agent: {side}  sha256 {_sha(src_bytes)[:16]} "
                      "(byte-exact copy of the source)")
    return 0


def cmd_roundtrip(a) -> int:
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
    if src_fmt == "skill" and not unpack_capsule(original.decode("utf-8", "replace")):
        if not a.allow_raw:
            print("RAW BREAD -- this SKILL.md carries no capsule, so a byte-exact "
                  "return trip does not exist yet. Convert it to an agent first "
                  "(that emission carries the capsule), or pass --allow-raw to "
                  "measure capability-level fidelity only.")
            return 2

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        if src_fmt == "agent":
            rci = load(a.path, src_fmt)
            mid_path = os.path.join(td, "SKILL.md")
            with open(mid_path, "wb") as f:
                f.write(render(rci, "skill"))
            back = render(load(mid_path, "skill"), "agent")
            ok = back == original
            print(f"agent -> skill -> agent: "
                  f"{'IDENTICAL' if ok else 'DRIFT'}  ({len(original)}B -> {len(back)}B)")
            if not ok:
                print(f"  sha in  {_sha(original)[:16]}\n  sha out {_sha(back)[:16]}")
                return 1
            prev = open(mid_path, "rb").read()
            for cycle in range(max(1, a.cycles)):
                again = render(load(mid_path, "skill"), "skill")
                if again != prev:
                    print(f"  FIXED-POINT DRIFT at cycle {cycle + 1}: "
                          f"{_sha(prev)[:16]} -> {_sha(again)[:16]}")
                    return 1
                with open(mid_path, "wb") as f:  # feed each cycle its own output
                    f.write(again)
                prev = again
            print(f"  projection fixed point holds over {max(1, a.cycles)} cycles")
            return 0

        rci = load(a.path, "skill")
        vault = rci.get("preserved", {}).get("agent")
        if not vault:
            print("no vaulted agent in the capsule -- conversion to agent "
                  "would be a SYNTHESIS (capability-level, not byte-level)")
            return 0 if a.allow_raw else 2
        restored = restore(rci, "agent")  # raises on checksum mismatch
        print(f"vaulted agent restores byte-exact: {vault['filename']}  "
              f"sha256 {_sha(restored)[:16]} (checksum verified)")

        # Tamper check -- the verdict that must be able to fire: when this
        # tool's inline projection is present, the visible python fence and
        # the vaulted agent are claims about the same bytes.
        text = original.decode("utf-8", "replace")
        if INLINE_MARK in text:
            m = DET_FENCE.search(text)
            shown = m.group(2).rstrip("\n") if m else None
            truth = restored.decode("utf-8", "replace").rstrip("\n")
            if shown is None or shown != truth:
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


SAMPLE_AGENT = '''"""Sample cartridge used by selftest. Echoes its arguments."""

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
        skill_path = os.path.join(td, "SKILL.md")
        with open(skill_path, "wb") as f:
            f.write(write_skill(rci))
        rci2 = load(skill_path, "skill")
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

        # 4. Raw bread must be refused by the oracle.
        raw_path = os.path.join(td, "RAW.md")
        with open(raw_path, "w") as f:
            f.write("---\nname: raw-bread\ndescription: no capsule here\n---\n\nProse.\n")
        if cmd_roundtrip(argparse.Namespace(path=raw_path, cycles=1,
                                            allow_raw=False)) != 2:
            failures.append("raw bread was not refused")

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
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
