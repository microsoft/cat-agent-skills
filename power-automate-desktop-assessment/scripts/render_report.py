from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re


MICROSOFT_LEARN_SOURCES = [
    "https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/error-handling",
    "https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/understand-limits",
    "https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/build-readable-flow-scripts",
    "https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/optimize-flow-performance",
    "https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/secure-your-data",
    "https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/monitor-automation",
]


def load_metrics(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict) or not isinstance(data.get("totals"), dict):
        raise ValueError(f"Invalid assessment metrics: {path}")
    return data


def markdown(value: object) -> str:
    text = " ".join(str(value if value is not None else "").splitlines())
    text = html.escape(text, quote=True).replace("\\", "\\\\")
    return re.sub(r"([`*_{}\[\]()#+!|])", r"\\\1", text)


def inline_code(value: object) -> str:
    text = " ".join(str(value if value is not None else "").splitlines())
    text = html.escape(text, quote=True).replace("`", "&#96;")
    return f"`{text}`"


def artifact_name(item: dict[str, object]) -> str:
    name = str(item.get("name") or Path(str(item.get("file") or "")).stem)
    return re.sub(r"\s+", " ", name).strip()


def finding(
    priority: str,
    title: str,
    artifact_type: str,
    technical_source: str,
    assessment_area: str,
    observed_condition: str,
    target_state: str,
    remediation: str,
    expected_impact: str,
    *,
    effort: str,
    owner: str,
) -> dict[str, str]:
    return {
        "priority": priority,
        "title": title,
        "artifactType": artifact_type,
        "technicalSource": technical_source,
        "assessmentArea": assessment_area,
        "observedCondition": observed_condition,
        "targetState": target_state,
        "remediation": remediation,
        "expectedImpact": expected_impact,
        "effort": effort,
        "owner": owner,
    }


def build_findings(metrics: dict[str, object]) -> list[dict[str, str]]:
    solution = metrics["solution"]
    workflows = metrics["workflows"]
    environment_variables = metrics["environmentVariables"]
    desktop_binaries = metrics.get("desktopBinaries") or []
    if not isinstance(solution, dict):
        raise ValueError("Metrics solution section must be an object")
    if not isinstance(workflows, list):
        raise ValueError("Metrics workflows section must be an array")
    if not isinstance(environment_variables, list):
        raise ValueError("Metrics environmentVariables section must be an array")
    if not isinstance(desktop_binaries, list):
        raise ValueError("Metrics desktopBinaries section must be an array")

    typed_workflows = [item for item in workflows if isinstance(item, dict)]
    findings: list[dict[str, str]] = []

    missing_dependencies = int(solution.get("missingDependencyCount") or 0)
    if missing_dependencies:
        findings.append(
            finding(
                "High",
                "Resolve missing dependencies [Solution Artifact]",
                "Solution-level artifacts",
                "solution.xml",
                "ALM / dependencies",
                f"solution.xml declares {missing_dependencies} missing dependencies.",
                "The release package resolves every required component and imports cleanly into a test environment.",
                "Resolve each dependency in the source environment and validate a clean import into a test environment.",
                "Reduces failed or incomplete imports and prevents missing-component runtime behavior.",
                effort="Medium",
                owner="Maker/Admin",
            )
        )

    large = [
        item for item in typed_workflows if int(item.get("actions") or 0) > 100
    ]
    if large:
        for item in large:
            name = artifact_name(item)
            findings.append(
                finding(
                    "High",
                    f"{name} [Cloud Flow]",
                    "Cloud Flows",
                    str(item.get("file") or ""),
                    "Maintainability / architecture",
                    f"{name} contains {item.get('actions')} actions.",
                    "The production flow has a focused responsibility, with reusable logic separated into governed child flows where appropriate.",
                    "Separate orchestration from reusable business, integration, and error-handling responsibilities using child flows where appropriate.",
                    "Reduces regression risk, review effort, and troubleshooting time.",
                    effort="High",
                    owner="Maker/Developer",
                )
            )

    nested = [
        item
        for item in typed_workflows
        if int(item.get("maxForeachDepth") or 0) > 1
    ]
    if nested:
        for item in nested:
            name = artifact_name(item)
            findings.append(
                finding(
                    "High",
                    f"{name} [Cloud Flow]",
                    "Cloud Flows",
                    str(item.get("file") or ""),
                    "Performance / platform limits",
                    f"{name} contains {item.get('foreach')} Foreach actions with a maximum nested depth of {item.get('maxForeachDepth')}.",
                    "The flow filters and shapes data before loops and avoids nested iteration where data operations or source-side queries can be used.",
                    "Filter at source, normalize arrays, use data operations, and batch independent work before entering loops.",
                    "Reduces action volume, duration, connector requests, and throttling exposure.",
                    effort="Medium",
                    owner="Maker/Developer",
                )
            )

    error_gaps = [
        item
        for item in typed_workflows
        if int(item.get("actions") or 0) > 10
        and int(item.get("scopes") or 0) == 0
        and int(item.get("runAfterNonSuccess") or 0) == 0
        and int(item.get("terminate") or 0) == 0
    ]
    if error_gaps:
        for item in error_gaps:
            name = artifact_name(item)
            findings.append(
                finding(
                    "High",
                    f"{name} [Cloud Flow]",
                    "Cloud Flows",
                    str(item.get("file") or ""),
                    "Reliability / error handling",
                    f"{name} has more than 10 actions and no detected Scope, non-success runAfter path, or Terminate action.",
                    "Critical paths use consistent Try/Catch scopes, non-success runAfter handling, bounded retry, contextual logging, and explicit terminal status.",
                    "Add Try/Catch scopes, failure and timeout runAfter paths, bounded retries, contextual logging, and explicit terminal behavior.",
                    "Improves diagnostic consistency and prevents ambiguous or apparently successful partial runs.",
                    effort="Medium",
                    owner="Maker/Developer",
                )
            )

    required_without_default = [
        item
        for item in environment_variables
        if isinstance(item, dict)
        and str(item.get("required") or "").lower() in {"1", "true"}
        and not bool(item.get("defaultValuePresent"))
    ]
    if required_without_default:
        for item in required_without_default:
            name = str(
                item.get("displayName")
                or item.get("schemaName")
                or "Environment variable"
            )
            findings.append(
                finding(
                    "Medium",
                    f"{name} [Environment Variable]",
                    "Environment Variables",
                    str(item.get("file") or ""),
                    "Configuration / deployment",
                    f"{name} is required and has no non-empty default.",
                    "The required setting is supplied and validated for each target environment before activation.",
                    "Provide the environment-specific value through the deployment process and document ownership and secret handling.",
                    "Prevents post-import failures caused by missing mandatory configuration.",
                    effort="Low",
                    owner="Maker/Admin",
                )
            )

    optional_without_default = [
        item
        for item in environment_variables
        if isinstance(item, dict)
        and str(item.get("required") or "").lower() in {"", "0", "false"}
        and not bool(item.get("defaultValuePresent"))
    ]
    if optional_without_default:
        for item in optional_without_default:
            name = str(
                item.get("displayName")
                or item.get("schemaName")
                or "Environment variable"
            )
            findings.append(
                finding(
                    "Observation",
                    f"{name} [Environment Variable]",
                    "Environment Variables",
                    str(item.get("file") or ""),
                    "Configuration / deployment",
                    f"{name} is optional and has no non-empty default.",
                    "Optional and mandatory settings are classified explicitly, with deployment validation for values needed by the target environment.",
                    "Confirm whether the setting is operationally mandatory and, if so, validate its value during deployment without embedding secrets in the solution.",
                    "Avoids false assumptions about optional settings while reducing configuration-related runtime failures.",
                    effort="Low",
                    owner="Maker/Admin",
                )
            )

    legacy_pattern = re.compile(r"(^|[/_-])(old|test|teste|unknown)([/_-]|$)", re.I)
    legacy = [
        item
        for item in typed_workflows
        if legacy_pattern.search(str(item.get("file") or ""))
    ]
    if legacy:
        for item in legacy:
            name = artifact_name(item)
            findings.append(
                finding(
                    "Medium",
                    f"{name} [Cloud Flow]",
                    "Cloud Flows",
                    str(item.get("file") or ""),
                    "ALM / release hygiene",
                    f"The {name} filename indicates an OLD, TEST, or Unknown artifact.",
                    "Release solutions contain only required, clearly named production components.",
                    "Confirm usage, remove the component if obsolete, or rename it with clear production intent.",
                    "Reduces release, ownership, and accidental activation risk.",
                    effort="Low",
                    owner="Maker/CoE",
                )
            )

    if str(solution.get("managed") or "") == "0":
        findings.append(
            finding(
                "Observation",
                "Confirm package type [Solution Artifact]",
                "Solution-level artifacts",
                "solution.xml",
                "ALM / package type",
                "The exported solution is unmanaged.",
                "The package type matches the documented ALM stage and target environment.",
                "Confirm the target environment and produce a managed release artifact when required by the ALM strategy.",
                "Avoids unintended unmanaged customization in controlled environments.",
                effort="Low",
                owner="Maker/Admin",
            )
        )

    module_names = sorted(
        {
            str(module_name)
            for item in desktop_binaries
            if isinstance(item, dict)
            for module_name in item.get("moduleNames", [])
        }
    )
    if {"UIAutomation", "WebAutomation"} & set(module_names):
        findings.append(
            finding(
                "Observation",
                "Desktop automation [Desktop Flow / PAD]",
                "Desktop Flow / PAD",
                ", ".join(
                    str(item.get("file") or "")
                    for item in desktop_binaries
                    if isinstance(item, dict)
                ),
                "Runtime / UI automation",
                "Desktop-flow metadata references UI or web automation modules, but package analysis does not include runtime, selector, or action-log evidence.",
                "UI and web automation have stable selectors, explicit waits and timeouts, tested session behavior, and actionable V2 logs.",
                "Review selectors, static-analysis results, machine prerequisites, V2 action logs, and attended/unattended test evidence.",
                "Reduces intermittent runtime failures and improves troubleshooting readiness.",
                effort="Medium",
                owner="Maker/Operations",
            )
        )

    return findings


def render_report(metrics: dict[str, object]) -> str:
    solution = metrics["solution"]
    totals = metrics["totals"]
    workflows = metrics["workflows"]
    connectors = metrics.get("connectors") or {}
    desktop_binaries = metrics.get("desktopBinaries") or []
    customizations = metrics.get("customizations") or {}
    if not isinstance(solution, dict) or not isinstance(totals, dict):
        raise ValueError("Metrics solution and totals sections must be objects")
    if not isinstance(workflows, list):
        raise ValueError("Metrics workflows section must be an array")
    if not isinstance(customizations, dict):
        raise ValueError("Metrics customizations section must be an object")

    findings = build_findings(metrics)
    priorities = {item["priority"] for item in findings}
    high_count = sum(item["priority"] == "High" for item in findings)
    if priorities & {"Critical", "High"}:
        overall_health = "Red"
    elif "Medium" in priorities:
        overall_health = "Amber"
    else:
        overall_health = "Green"
    confidence = "Medium"
    title = (
        str(solution.get("uniqueName") or "Power Automate Desktop")
        + " "
        + str(solution.get("version") or "")
    ).strip()

    lines = [
        f"# {markdown(title)} Assessment",
        "",
        "## Executive summary",
        "",
        f"**Overall health:** {overall_health}",
        f"**Assessment confidence:** {confidence} (static package analysis)",
        f"**Scope reviewed:** {totals.get('workflowCount', 0)} cloud workflows, "
        f"{totals.get('desktopBinaryJsonCount', 0)} desktop-flow artifacts, and "
        f"{totals.get('environmentVariableCount', 0)} environment variable definitions.",
        f"**Key conclusion:** {high_count} high-priority static-analysis findings require review before production sign-off.",
        "",
        "## Strengths",
        "",
        "- The solution package could be inventoried without modifying the source automation.",
        "- Metrics retain source filenames for traceability and omit configuration or secret values.",
        "- The assessment separates cloud workflow definitions from desktop-flow binary metadata.",
        "",
        "## Top risks",
        "",
        "| Priority | Severity | Area | Finding | Recommended action |",
        "|---:|---|---|---|---|",
    ]

    for index, item in enumerate(findings[:8], start=1):
        lines.append(
            f"| {index} | {markdown(item['priority'])} | "
            f"{markdown(item['assessmentArea'])} | "
            f"{markdown(item['observedCondition'])} | "
            f"{markdown(item['remediation'])} |"
        )
    if not findings:
        lines.append("| 1 | Observation | Static review | No threshold-based risks were detected. | Complete runtime and governance review. |")

    lines.extend(["", "## Detailed findings", ""])
    artifact_order = (
        "Cloud Flows",
        "Desktop Flow / PAD",
        "Environment Variables",
        "Solution-level artifacts",
    )
    for artifact_type in artifact_order:
        artifact_findings = [
            item for item in findings if item["artifactType"] == artifact_type
        ]
        if not artifact_findings:
            continue
        lines.extend([f"### {artifact_type}", ""])
        for item in artifact_findings:
            lines.extend(
                [
                    f"#### [{markdown(item['priority'])}] {markdown(item['title'])}",
                    "",
                    f"**Technical source:** {inline_code(item['technicalSource'])}",
                    f"**Assessment area:** {markdown(item['assessmentArea'])}",
                    f"**Observed condition:** {markdown(item['observedCondition'])}",
                    f"**Target state / best practice:** {markdown(item['targetState'])}",
                    f"**Recommended remediation:** {markdown(item['remediation'])}",
                    f"**Expected business/operational impact:** {markdown(item['expectedImpact'])}",
                    f"**Priority:** {markdown(item['priority'])}",
                    f"**Effort:** {markdown(item['effort'])}",
                    f"**Owner:** {markdown(item['owner'])}",
                    "",
                ]
            )

    roadmap_sections = (
        ("Quick wins (0-2 weeks)", "Low"),
        ("Stabilization (2-6 weeks)", "Medium"),
        ("Structural improvements (6+ weeks)", "High"),
    )
    lines.extend(["## Remediation roadmap", ""])
    for heading, effort in roadmap_sections:
        lines.extend([f"### {heading}"])
        effort_findings = [
            item for item in findings if item["effort"] == effort
        ]
        if effort_findings:
            lines.extend(
                f"- {markdown(item['remediation'])}" for item in effort_findings
            )
        else:
            lines.append("- No remediation was assigned to this horizon.")
        lines.append("")

    lines.extend(
        [
            "## Open questions and missing evidence",
            "",
            "- Business volume, SLA, observed runtime, and failure impact.",
            "- Cloud-flow run history and connector throttling evidence.",
            "- Desktop-flow V2 action logs, static-analysis output, and selector review.",
            "- Machine, connection, credential, DLP, licensing, and support ownership configuration.",
            "",
            "## Appendix: Inventory",
            "",
            "### Solution artifacts",
            "",
            f"- `solution.xml`: {solution.get('rootComponentCount', 0)} root component(s), "
            f"{solution.get('missingDependencyCount', 0)} missing dependency declaration(s).",
            f"- `customizations.xml`: "
            f"{'present' if customizations.get('present') else 'not present'}, "
            f"{customizations.get('size', 0)} byte(s), component counts "
            f"{markdown(customizations.get('componentCounts', {}))}.",
            "",
            "### Cloud workflows",
            "",
            "| Workflow | Actions | Foreach | Max depth | Non-success runAfter |",
            "|---|---:|---:|---:|---:|",
        ]
    )

    typed_workflows = [item for item in workflows if isinstance(item, dict)]
    for item in sorted(
        typed_workflows,
        key=lambda value: int(value.get("actions") or 0),
        reverse=True,
    ):
        lines.append(
            f"| {markdown(artifact_name(item))} | {item.get('actions', 0)} | "
            f"{item.get('foreach', 0)} | {item.get('maxForeachDepth', 0)} | "
            f"{item.get('runAfterNonSuccess', 0)} |"
        )

    lines.extend(["", "### Connectors", ""])
    if isinstance(connectors, dict) and connectors:
        for connector, count in sorted(connectors.items()):
            lines.append(
                f"- {inline_code(connector)}: referenced by {count} workflow(s)"
            )
    else:
        lines.append("- No cloud connector references were detected.")

    lines.extend(["", "### Desktop-flow artifacts", ""])
    if isinstance(desktop_binaries, list) and desktop_binaries:
        for item in desktop_binaries:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- {inline_code(item.get('file', ''))} "
                f"(screens: {item.get('screenCount', 0)}, images: {item.get('imageCount', 0)})"
            )
    else:
        lines.append("- No desktop-flow binary JSON artifacts were detected.")

    lines.extend(["", "### Microsoft Learn references", ""])
    lines.extend(f"- {source}" for source in MICROSOFT_LEARN_SOURCES)
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a portable Markdown assessment from metrics JSON."
    )
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    report = render_report(load_metrics(args.metrics))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(report)
    print(
        json.dumps(
            {
                "reportPath": str(args.output.resolve()),
                "characters": len(report),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
