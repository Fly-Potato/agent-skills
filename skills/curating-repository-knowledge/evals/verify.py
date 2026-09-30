#!/usr/bin/env python3
"""Prepare isolated skill eval fixtures and check observable results.

Run on Windows with Python 3.12+ (for example, uv run --python 3.12):
  python verify.py prepare 9 <empty-temp-directory>
  # Give the printed prompt and prepared directory to an agent using the Skill.
  python verify.py check 9 <temp-directory> --response <answer-outside-temp.txt>

The checker verifies file state and simple answer indicators. Review the
case's expectations manually for semantic claims that cannot be proved by
substring checks. Never use a live repository as the fixture directory.
"""

import argparse
import json
import re
import sys
from pathlib import Path

EVALS = Path(__file__).with_name("evals.json")


def load_case(case_id):
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    for case in data["evals"]:
        if case["id"] == case_id:
            if "fixture" not in case or "checks" not in case:
                raise ValueError(f"case {case_id} has no executable fixture")
            return case
    raise ValueError(f"unknown case {case_id}")


def target(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes fixture: {relative}")
    return path


def files_under(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def prepare(case, root):
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"fixture destination is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for relative, content in case["fixture"].items():
        path = target(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Prepared case {case['id']} at {root}")
    print(case["prompt"])


def check(case, root, response):
    checks = case["checks"]
    before = {name: content.encode("utf-8") for name, content in case["fixture"].items()}
    after = files_under(root)
    changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
    failures = []

    if "changed_only" in checks:
        unexpected = changed - set(checks["changed_only"])
        if unexpected:
            failures.append(f"unexpected file changes: {sorted(unexpected)}")
    unchanged = set(checks.get("must_change", [])) - changed
    if unchanged:
        failures.append(f"required files unchanged: {sorted(unchanged)}")
    for relative in checks.get("exists", []):
        if relative not in after:
            failures.append(f"missing file: {relative}")
    for relative in checks.get("absent", []):
        if target(root, relative).exists():
            failures.append(f"unexpected file: {relative}")
    for field, should_exist in (("contains", True), ("not_contains", False)):
        for relative, fragments in checks.get(field, {}).items():
            content = after.get(relative, b"").decode("utf-8", errors="replace")
            for fragment in fragments:
                if (fragment in content) != should_exist:
                    failures.append(f"{relative}: {field} failed for {fragment!r}")
    for relative in changed:
        content = after.get(relative, b"").decode("utf-8", errors="replace")
        for fragment in checks.get("forbid_in_changed_files", []):
            if fragment in content:
                failures.append(f"sensitive or foreign content in {relative}: {fragment!r}")

    if any(checks.get(name) for name in ("index_links_valid", "no_orphan_cards", "no_duplicate_current")):
        index = target(root, ".agents/knowledge/INDEX.md")
        if not index.is_file():
            failures.append("knowledge index missing")
        else:
            index_text = index.read_text(encoding="utf-8")
            links = re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", index_text)
            linked = set()
            for link in links:
                try:
                    linked_path = target(root, ".agents/knowledge/" + link)
                except ValueError as exc:
                    failures.append(str(exc))
                    continue
                linked.add(linked_path)
                if checks.get("index_links_valid") and not linked_path.is_file():
                    failures.append(f"broken index link: {link}")
            if checks.get("no_orphan_cards"):
                for card in index.parent.glob("*.md"):
                    if card != index and card.resolve() not in linked:
                        failures.append(f"orphan knowledge card: {card.name}")
            if checks.get("no_duplicate_current"):
                seen = set()
                for line in index_text.splitlines():
                    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                    if len(cells) != 5 or cells[3] != "`current`":
                        continue
                    key = (cells[0], cells[2] or cells[1])
                    if key in seen:
                        failures.append(f"duplicate current knowledge entry: {key}")
                    seen.add(key)

    for field, should_exist in (("response_contains", True), ("response_not_contains", False)):
        for fragment in checks.get(field, []):
            if (fragment in response) != should_exist:
                failures.append(f"{field} failed for {fragment!r}")

    if failures:
        print("FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"PASS case {case['id']}; changed files: {sorted(changed)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "check"))
    parser.add_argument("case_id", type=int)
    parser.add_argument("workspace", type=Path, help="isolated case directory")
    parser.add_argument("--response", type=Path, help="agent final answer, required by response checks")
    args = parser.parse_args()
    case = load_case(args.case_id)
    root = args.workspace.resolve()
    if args.action == "prepare":
        prepare(case, root)
        return 0
    if not root.is_dir():
        parser.error(f"fixture directory does not exist: {root}")
    response = args.response.read_text(encoding="utf-8") if args.response else ""
    return check(case, root, response)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
