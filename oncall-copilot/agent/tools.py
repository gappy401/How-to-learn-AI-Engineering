"""Tools the on-call agent can call.

Each tool is a plain Python function plus a JSON schema describing it to the
model. The agent loop in agent.py dispatches model tool-calls to these.
"""

import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent / "sample_repo"
LOG_FILE = Path(__file__).resolve().parent.parent / "scenarios" / "production.log"


def read_file(path: str) -> str:
    """Return the contents of a file inside the sample repo."""
    target = (REPO / path).resolve()
    if REPO not in target.parents and target != REPO:
        return "ERROR: path escapes repo"
    if not target.exists():
        return f"ERROR: {path} not found"
    return target.read_text()


def list_files() -> str:
    """List source and test files in the repo."""
    out = []
    for p in sorted(REPO.rglob("*.py")):
        if "__pycache__" not in str(p):
            out.append(str(p.relative_to(REPO)))
    return "\n".join(out)


def search_logs(query: str) -> str:
    """Naive substring search over production logs. Returns matching lines."""
    if not LOG_FILE.exists():
        return "ERROR: no logs"
    terms = [t.lower() for t in query.split() if ":" not in t]
    lines = LOG_FILE.read_text().splitlines()
    if not terms:
        return "\n".join(lines)
    hits = [ln for ln in lines if any(t in ln.lower() for t in terms)]
    return "\n".join(hits) if hits else "(no matching log lines)"


def git_log() -> str:
    """Recent commits touching the repo (mocked for the demo)."""
    return (
        "a3f9c1 2026-05-28 01:55  refactor discount math\n"
        "9b2e10 2026-05-27 18:30  add tax rounding\n"
        "77c4aa 2026-05-26 09:12  initial billing service\n"
    )


def run_tests() -> str:
    """Run the repo's pytest suite and return a summary."""
    proc = subprocess.run(
        ["python", "-m", "pytest", "-q"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=60,
    )
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-8:]
    return f"exit_code={proc.returncode}\n" + "\n".join(tail)


def apply_patch(path: str, old: str, new: str) -> str:
    """Replace `old` with `new` in a repo file. `old` must appear exactly once."""
    target = (REPO / path).resolve()
    if not target.exists():
        return f"ERROR: {path} not found"
    text = target.read_text()
    count = text.count(old)
    if count == 0:
        return "ERROR: `old` string not found"
    if count > 1:
        return "ERROR: `old` not unique; include more context"
    target.write_text(text.replace(old, new))
    return f"OK: patched {path}"


# ---- tool schemas exposed to the model -------------------------------------

TOOLS = [
    {
        "name": "list_files",
        "description": "List all Python source and test files in the repo.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_file",
        "description": "Read a file's contents. Path is relative to repo root, e.g. 'src/billing.py'.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "search_logs",
        "description": "Search production logs for context about the incident.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "git_log",
        "description": "Show recent commits to help correlate the incident with a deploy.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_tests",
        "description": "Run the repo's test suite. Use to confirm a fix works.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "apply_patch",
        "description": "Replace an exact substring in a file with a fix. `old` must be unique.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old": {"type": "string"},
                "new": {"type": "string"},
            },
            "required": ["path", "old", "new"],
        },
    },
]

DISPATCH = {
    "list_files": lambda **k: list_files(),
    "read_file": lambda **k: read_file(k["path"]),
    "search_logs": lambda **k: search_logs(k["query"]),
    "git_log": lambda **k: git_log(),
    "run_tests": lambda **k: run_tests(),
    "apply_patch": lambda **k: apply_patch(k["path"], k["old"], k["new"]),
}
