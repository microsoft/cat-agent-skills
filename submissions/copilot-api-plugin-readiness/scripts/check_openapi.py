#!/usr/bin/env python3
"""Check an OpenAPI description, and optionally an API plugin manifest, against
the constraints Microsoft documents for API plugins in Microsoft 365 Copilot
declarative agents.

Usage:
    python check_openapi.py openapi.json [--manifest ai-plugin.json]

YAML input needs PyYAML. JSON needs nothing beyond the standard library.
Prints a Markdown table of findings and exits 1 if any BLOCKER was found.
"""

import argparse
import json
import re
import sys

NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
METHODS = ("get", "put", "post", "delete", "patch", "head", "options", "trace")
POLY = ("oneOf", "allOf", "anyOf")
SRC_KNOWN = "known-issues#api-plugins"
SRC_GUIDE = "openapi-document-guidance"
SRC_AUTH = "plugin-authentication"
SRC_KEY = "plugin-authentication-api-key"
SRC_MANIFEST = "plugin-manifest-2.4"

findings = []


def add(verdict, check, where, evidence, source):
    findings.append((verdict, check, where, evidence, source))


def load(path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError:
            sys.exit("This file is not JSON and PyYAML is not installed.")
        return yaml.safe_load(text)


def resolve(doc, node, seen):
    """Follow a local $ref. Returns (node, cycle_name or None, refs seen so far)."""
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return node, None, seen
        if ref in seen:
            return None, ref, seen
        seen = seen | {ref}
        target = doc
        for part in ref[2:].split("/"):
            target = target.get(part.replace("~1", "/").replace("~0", "~"), {}) if isinstance(target, dict) else {}
        node = target
    return node, None, seen


def walk_schema(doc, schema, seen, report, depth=0):
    """Yield problems in a schema: polymorphism, cycles, and object nesting depth."""
    schema, cycle, seen = resolve(doc, schema, seen)
    if cycle:
        report("cycle", cycle)
        return
    if not isinstance(schema, dict):
        return
    for key in POLY:
        if key in schema:
            report("poly", key)
    is_object = schema.get("type") == "object" or "properties" in schema
    if is_object and depth >= 1:
        report("nested", depth)
    child_seen = seen
    for prop in (schema.get("properties") or {}).values():
        walk_schema(doc, prop, child_seen, report, depth + (1 if is_object else 0))
    extra = schema.get("additionalProperties")
    if isinstance(extra, dict):
        walk_schema(doc, extra, child_seen, report, depth + (1 if is_object else 0))
    if "items" in schema:
        walk_schema(doc, schema["items"], child_seen, report, depth)
    for key in POLY:
        for sub in schema.get(key) or []:
            walk_schema(doc, sub, child_seen, report, depth)


def check_schemas(doc, op_name, label, schema, request_side):
    reported = set()

    def report(kind, detail):
        if (kind, str(detail)) in reported:
            return
        reported.add((kind, str(detail)))
        if kind == "cycle":
            add("BLOCKER", "Circular reference", op_name, f"{label} reaches {detail} again", SRC_KNOWN)
        elif kind == "poly":
            add("BLOCKER", "Polymorphic schema", op_name, f"{label} uses {detail}; flatten it", SRC_KNOWN)
        elif kind == "nested" and request_side:
            add("BLOCKER", "Nested object in request", op_name, f"{label} has an object inside an object", SRC_KNOWN)

    walk_schema(doc, schema, set(), report)


def path_items(doc):
    """Yield (path, item) with local Path Item references resolved."""
    for path, item in (doc.get("paths") or {}).items():
        item, _, _ = resolve(doc, item, set())
        if isinstance(item, dict):
            yield path, item


def referenced_schemes(doc):
    """Names of security schemes that some operation's effective requirement uses."""
    names = set()
    global_security = doc.get("security") or []
    for _, item in path_items(doc):
        for method in METHODS:
            op = item.get(method)
            if isinstance(op, dict):
                for requirement in op.get("security", global_security) or []:
                    names.update(requirement)
    return names


def check_openapi(doc):
    swagger2 = "swagger" in doc
    version = doc.get("swagger") or doc.get("openapi") or "missing"
    add("INFO", "Document version", "document", f"{'swagger' if swagger2 else 'openapi'} {version}", SRC_GUIDE)

    info = doc.get("info") or {}
    if not (info.get("description") or "").strip():
        add("FIX", "info.description", "document", "missing; it becomes the plugin description", SRC_GUIDE)
    else:
        add("PASS", "info.description", "document", info["description"][:80], SRC_GUIDE)

    if swagger2:
        if not doc.get("host"):
            add("FIX", "Server URL", "document", "no host; Copilot needs the base URL", SRC_KEY)
    elif not doc.get("servers"):
        add("FIX", "Server URL", "document", "no servers entry; an API key registration's base URL must match one", SRC_KEY)

    schemes = (doc.get("components") or {}).get("securitySchemes") or doc.get("securityDefinitions") or {}
    kinds = {}
    used_schemes = referenced_schemes(doc)
    for name, scheme in schemes.items():
        scheme, _, _ = resolve(doc, scheme, set())
        stype = (scheme or {}).get("type")
        where = f"securityScheme {name}"
        if name not in used_schemes:
            add("INFO", "Security scheme", where, "declared but no operation requires it, so it is not checked", SRC_AUTH)
            continue
        if stype == "apiKey":
            location = scheme.get("in")
            kinds[name] = "apikey"
            if location == "cookie":
                add("BLOCKER", "API key placement", where, "key in a cookie is not supported", SRC_KNOWN)
            else:
                add("WATCH", "API key placement", where,
                    f"key in {location} '{scheme.get('name')}': the API key article supports it, the known issues article says it is not supported. Test it, or send the key as a bearer token",
                    f"{SRC_KEY}, {SRC_KNOWN}")
        elif stype == "http":
            if (scheme.get("scheme") or "").lower() == "bearer":
                kinds[name] = "bearer"
                add("PASS", "Bearer token", where, "http bearer, supported with ApiKeyPluginVault", SRC_KEY)
            else:
                kinds[name] = "other"
                add("BLOCKER", "Unsupported scheme", where, f"http {scheme.get('scheme')} is not a supported scheme", SRC_AUTH)
        elif stype == "oauth2":
            kinds[name] = "oauth"
            flows = scheme.get("flows") or {scheme.get("flow"): {}}
            bad = [f for f in flows if f not in ("authorizationCode", "accessCode")]
            if bad:
                add("BLOCKER", "OAuth grant", where, f"flow(s) {', '.join(map(str, bad))}; only authorization code (with or without PKCE) is supported", SRC_KNOWN)
            else:
                add("PASS", "OAuth grant", where, "authorization code", SRC_AUTH)
        elif stype == "basic":
            kinds[name] = "other"
            add("BLOCKER", "Unsupported scheme", where, "basic authentication is not a supported scheme", SRC_AUTH)
        else:
            kinds[name] = "other"
            add("UNKNOWN", "Security scheme", where, f"type {stype} is not covered by the documented schemes", SRC_AUTH)

    global_security = doc.get("security")
    operation_ids = {}
    for path, item in path_items(doc):
        shared_params = item.get("parameters") or []
        for method in METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            label = f"{method.upper()} {path}"
            op_id = op.get("operationId")
            if not op_id:
                add("BLOCKER", "operationId", label, "missing; a plugin function must match an operationId", SRC_MANIFEST)
            else:
                operation_ids.setdefault(op_id, []).append(label)
                if not NAME_RE.match(op_id):
                    add("BLOCKER", "operationId shape", label, f"'{op_id}' does not match ^[A-Za-z0-9_]+$, so no function name can equal it", SRC_MANIFEST)
            if not (op.get("description") or op.get("summary")):
                add("FIX", "Operation description", label, "no summary or description to route on", SRC_GUIDE)

            for param in shared_params + (op.get("parameters") or []):
                param, _, _ = resolve(doc, param, set())
                if not isinstance(param, dict):
                    continue
                pname = param.get("name")
                if param.get("in") == "body":
                    check_schemas(doc, label, "body", param.get("schema"), True)
                    continue
                if not param.get("description"):
                    add("FIX", "Parameter description", label, f"parameter '{pname}' has no description", SRC_GUIDE)
                if "schema" in param:
                    check_schemas(doc, label, f"parameter '{pname}'", param["schema"], True)

            body, _, _ = resolve(doc, op.get("requestBody"), set())
            for media in ((body or {}).get("content") or {}).values():
                check_schemas(doc, label, "request body", media.get("schema"), True)

            responses = op.get("responses") or {}
            if not responses:
                add("FIX", "Responses", label, "no responses defined", SRC_GUIDE)
            for code, response in responses.items():
                response, _, _ = resolve(doc, response, set())
                if not isinstance(response, dict):
                    continue
                if not response.get("description"):
                    add("FIX", "Response description", label, f"response {code} has no description", SRC_GUIDE)
                schemas = [m.get("schema") for m in (response.get("content") or {}).values()]
                if "schema" in response:
                    schemas.append(response["schema"])
                for schema in schemas:
                    check_schemas(doc, label, f"response {code}", schema, False)

            security = op.get("security", global_security) or []
            for requirement in security:
                used = {kinds.get(n) for n in requirement}
                if "oauth" in used and "bearer" in used:
                    add("BLOCKER", "Dual authentication", label, "OAuth and a bearer token required together on one endpoint", SRC_KNOWN)

    for op_id, labels in operation_ids.items():
        if len(labels) > 1:
            add("BLOCKER", "Duplicate operationId", ", ".join(labels), f"'{op_id}' is used more than once", SRC_MANIFEST)
    return {op_id: labels[0] for op_id, labels in operation_ids.items()}


def long_strings(node, path=""):
    if isinstance(node, str) and len(node) > 4096:
        yield path, len(node)
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from long_strings(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from long_strings(value, f"{path}[{index}]")


def check_manifest(manifest, operations):
    functions = manifest.get("functions") or []
    runtimes = manifest.get("runtimes") or []
    for runtime in runtimes:
        auth_type = (runtime.get("auth") or {}).get("type")
        if auth_type not in ("None", "OAuthPluginVault", "ApiKeyPluginVault"):
            add("BLOCKER", "Runtime auth type", f"runtime {runtime.get('type')}", f"'{auth_type}' is not one of None, OAuthPluginVault, ApiKeyPluginVault", SRC_MANIFEST)
        elif auth_type != "None" and not (runtime.get("auth") or {}).get("reference_id"):
            add("FIX", "Auth config reference", f"runtime {runtime.get('type')}", f"{auth_type} with no reference_id", SRC_MANIFEST)

    openapi_runtimes = [r for r in runtimes if r.get("type") == "OpenApi"]
    bound_to_openapi = set()
    for runtime in openapi_runtimes:
        listed = runtime.get("run_for_functions")
        if not listed or "*" in listed:
            bound_to_openapi = {f.get("name", "") for f in functions}
            break
        bound_to_openapi.update(listed)

    for function in functions:
        name = function.get("name", "")
        where = f"function {name}"
        if not NAME_RE.match(name):
            add("BLOCKER", "Function name", where, "does not match ^[A-Za-z0-9_]+$", SRC_MANIFEST)
        if name in bound_to_openapi and name not in operations:
            add("BLOCKER", "Function binding", where, "no operationId with this name in the OpenAPI description", SRC_MANIFEST)
        capabilities = function.get("capabilities") or {}
        confirmation = capabilities.get("confirmation") or {}
        if confirmation.get("isNonConsequential") and operations.get(name, "").split(" ")[0] not in ("GET", ""):
            add("FIX", "isNonConsequential", where, "set on a non-GET operation, where it has no effect", SRC_MANIFEST)
        semantics = capabilities.get("response_semantics")
        if isinstance(semantics, list) and len(semantics) > 1:
            add("BLOCKER", "Response semantics", where, "more than one response semantics object", SRC_KNOWN)
        template = json.dumps((semantics or {}).get("static_template", {})) if isinstance(semantics, dict) else ""
        for action in ("Action.OpenUrl", "Action.ToggleVisibility"):
            if action in template:
                add("FIX", "Card action", where, f"{action} in response semantics is not supported", SRC_KNOWN)

    for path, length in long_strings(manifest):
        add("WATCH", "String length", path, f"{length} characters; manifest strings should stay under 4K", SRC_MANIFEST)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("openapi")
    parser.add_argument("--manifest")
    args = parser.parse_args()

    operations = check_openapi(load(args.openapi))
    if args.manifest:
        check_manifest(load(args.manifest), operations)

    order = {"BLOCKER": 0, "FIX": 1, "WATCH": 2, "UNKNOWN": 3, "PASS": 4, "INFO": 5}
    print("| Verdict | Check | Where | Evidence | Source |")
    print("|---|---|---|---|---|")
    for verdict, check, where, evidence, source in sorted(findings, key=lambda f: order[f[0]]):
        print(f"| {verdict} | {check} | {where} | {evidence} | {source} |")
    blockers = sum(1 for f in findings if f[0] == "BLOCKER")
    print(f"\n{blockers} blocker(s), {len(findings)} finding(s).")
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
