#!/usr/bin/env python3
"""Measure one repo's contribution stats with the method recorded in reports/*/report.json.

usage: github_stats.py <bare-or-normal-git-dir> <rev> <report.json>
Prints one JSON object with the README fields.
"""
import json
import subprocess
import sys

repo, rev, report = sys.argv[1:4]
meta = json.load(open(report))
exts = tuple(meta["method"]["extensions"])
excluded = set(meta["method"]["exclusions"])
authors = [f"--author={e}" for e in meta["author_emails"]]


def git(*args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


# Absent from the 2026-10-03 report; reverse-engineered by matching its rows.
SOURCE_NAMES = set(meta["method"].get("source_filenames", ["CMakeLists.txt", "Makefile", "Dockerfile"]))
GENERATED = tuple(meta["method"].get("generated_suffixes", [".g.dart", ".freezed.dart", ".d.ts"]))


def is_source(path):
    parts = path.split("/")
    if excluded.intersection(parts[:-1]) or path.endswith(GENERATED):
        return False
    return parts[-1] in SOURCE_NAMES or path.lower().endswith(exts)


commits = int(git("rev-list", "--count", *authors, rev))
nonmerge = int(git("rev-list", "--count", "--no-merges", *authors, rev))
files, src_files = set(), set()
added = deleted = 0
for line in git("log", rev, "--no-merges", "--numstat", "--no-renames", "--format=", *authors).splitlines():
    a, d, path = (line.split("\t", 2) + ["", ""])[:3] if line else ("", "", "")
    if not path:
        continue
    files.add(path)
    if is_source(path):
        src_files.add(path)
        if a != "-":
            added += int(a)
            deleted += int(d)

print(json.dumps({
    "commits": commits, "nonmerge_commits": nonmerge, "merge_commits": commits - nonmerge,
    "files_touched": len(files), "source_files_touched": len(src_files),
    "source_lines_added": added, "source_lines_deleted": deleted,
}))
