"""Summarise Checkov's github_actions results and gate the build on them.

Writes a Markdown report to $GITHUB_STEP_SUMMARY (falling back to stdout) and
exits non-zero if any *blocking* check failed.

Why an explicit blocking list instead of `--hard-fail-on CRITICAL`:
open-source Checkov does not attach severities to findings. Every result comes
back with `severity: null` unless you supply a Bridgecrew/Prisma API key, so a
severity threshold matches nothing and would pass silently no matter what broke.
The checks are therefore triaged here, by ID.

Blocking checks are the ones describing an actual security misconfiguration in
the workflow. The non-blocking ones are supply-chain maturity items (cosign
signing, SBOM attestation, SLSA build-parameter rules) -- worth reporting, but
not worth failing a build over at this stage. Move an ID between the two sets to
change what blocks.

Usage: python checkov-gate.py <results_json.json> [path-prefix]
"""

import json
import os
import sys

BLOCKING = {
    "CKV_GHA_1": "ACTIONS_ALLOW_UNSECURE_COMMANDS enabled",
    "CKV_GHA_2": "run command vulnerable to shell injection",
    "CKV_GHA_3": "suspicious use of curl with secrets",
    "CKV_GHA_4": "suspicious use of netcat with an IP address",
    "CKV2_GHA_1": "top-level permissions set to write-all",
}

NON_BLOCKING_NOTE = (
    "Reported but not blocking: cosign signing/SBOM attestation and SLSA "
    "build-parameter checks (`CKV_GHA_5`, `CKV_GHA_6`, `CKV_GHA_7`)."
)


def load_runs(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    # Checkov emits a list when several frameworks ran, a dict for just one.
    return data if isinstance(data, list) else [data]


def location(check, prefix):
    # Checkov reports paths relative to the scanned root, with a leading
    # separator, and uses the host's separator -- normalise both so GitHub
    # annotations resolve against the repository.
    file_path = (check.get("file_path") or "").replace("\\", "/").lstrip("/")
    if prefix:
        file_path = f"{prefix.rstrip('/')}/{file_path}"
    line_range = check.get("file_line_range") or []
    line = line_range[0] if line_range else 0
    return file_path, line


def collect(runs, prefix):
    passed = failed = skipped = 0
    failures = []
    for run in runs:
        summary = run.get("summary", {})
        passed += summary.get("passed", 0) or 0
        failed += summary.get("failed", 0) or 0
        skipped += summary.get("skipped", 0) or 0
        for check in run.get("results", {}).get("failed_checks", []) or []:
            file_path, line = location(check, prefix)
            failures.append(
                {
                    "id": check.get("check_id", "?"),
                    "name": check.get("check_name", ""),
                    "resource": check.get("resource", ""),
                    "file": file_path,
                    "line": line,
                    "blocking": check.get("check_id") in BLOCKING,
                }
            )
    return passed, failed, skipped, failures


def render(passed, failed, skipped, failures):
    out = ["## Checkov — GitHub Actions workflows", ""]
    verdict = "No failed checks." if not failures else f"{len(failures)} failed check(s)."
    out.append(f"**{verdict}**  ")
    out.append(f"passed: {passed} · failed: {failed} · skipped: {skipped}")
    out.append("")

    if failures:
        out.append("| | Check | Resource | Location |")
        out.append("| --- | --- | --- | --- |")
        for f in sorted(failures, key=lambda x: (not x["blocking"], x["id"])):
            marker = "🔴 blocking" if f["blocking"] else "⚪ advisory"
            where = f"`{f['file']}:{f['line']}`" if f["file"] else ""
            out.append(
                f"| {marker} | `{f['id']}` {f['name']} | `{f['resource']}` | {where} |"
            )
        out.append("")

    out.append(NON_BLOCKING_NOTE)
    out.append("")
    return "\n".join(out)


def main(argv):
    results_path = argv[1]
    prefix = argv[2] if len(argv) > 2 else ""

    try:
        runs = load_runs(results_path)
    except FileNotFoundError:
        print(f"::error::Checkov results not found: {results_path}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"::error::Checkov results are not valid JSON: {exc}")
        return 1

    passed, failed, skipped, failures = collect(runs, prefix)
    report = render(passed, failed, skipped, failures)

    print(report)
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write(report)

    blocking = [f for f in failures if f["blocking"]]
    for f in blocking:
        print(
            f"::error file={f['file']},line={f['line']},"
            f"title=Checkov {f['id']}::{f['name']}"
        )

    if blocking:
        print(f"\n{len(blocking)} blocking Checkov finding(s); failing the build.")
        return 1

    if failures:
        print("\nOnly advisory Checkov findings; not failing the build.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv))
