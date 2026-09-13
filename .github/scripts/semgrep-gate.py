"""Fail the build when Semgrep reports high-severity findings.

Reads a SARIF file and exits non-zero if any result maps to a rule whose
severity is `error` (Semgrep's ERROR level, i.e. high severity).

Semgrep does not put a `level` on each SARIF result -- it carries severity on
the rule definition under `tool.driver.rules[].defaultConfiguration.level`, so
results have to be joined back to their rule. A filter on `result.level` alone
silently matches nothing.

Usage: python semgrep-gate.py semgrep.sarif
"""

import collections
import json
import sys

HIGH = "error"


def rule_levels(run):
    driver = run.get("tool", {}).get("driver", {})
    return {
        rule["id"]: rule.get("defaultConfiguration", {}).get("level", "none")
        for rule in driver.get("rules", [])
        if "id" in rule
    }


def finding_location(result):
    locations = result.get("locations") or []
    if not locations:
        return "<unknown>", 0
    physical = locations[0].get("physicalLocation", {})
    uri = physical.get("artifactLocation", {}).get("uri", "<unknown>")
    line = physical.get("region", {}).get("startLine", 0)
    return uri, line


def main(path):
    try:
        with open(path, encoding="utf-8") as handle:
            sarif = json.load(handle)
    except FileNotFoundError:
        print(f"::error::SARIF file not found: {path}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"::error::SARIF file is not valid JSON: {exc}")
        return 1

    by_level = collections.Counter()
    high_findings = []

    for run in sarif.get("runs", []):
        levels = rule_levels(run)
        for result in run.get("results", []):
            rule_id = result.get("ruleId", "<unknown>")
            # Prefer an explicit result level if a future Semgrep starts emitting
            # one; otherwise fall back to the rule's configured severity.
            level = result.get("level") or levels.get(rule_id, "none")
            by_level[level] += 1
            if level == HIGH:
                uri, line = finding_location(result)
                message = result.get("message", {}).get("text", "").strip()
                high_findings.append((uri, line, rule_id, message))

    total = sum(by_level.values())
    summary = ", ".join(f"{lvl}={n}" for lvl, n in sorted(by_level.items())) or "none"
    print(f"Semgrep findings: {total} ({summary})")

    if not high_findings:
        print("No high-severity findings. Gate passed.")
        return 0

    print()
    print(f"{len(high_findings)} high-severity finding(s) blocking this build:")
    for uri, line, rule_id, message in high_findings:
        print(f"\n  {uri}:{line}")
        print(f"    rule: {rule_id}")
        if message:
            first_line = message.splitlines()[0]
            print(f"    {first_line}")
        # Surface it as a GitHub annotation on the offending line too.
        print(f"::error file={uri},line={line},title=Semgrep {rule_id}::{message}")

    return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
