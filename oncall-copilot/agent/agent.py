"""On-Call Copilot — alert-to-PR agent.

Flow:
  1. Load an alert (scenarios/alert.json)
  2. Agent investigates via tools (read code, search logs, git log)
  3. Agent diagnoses and applies a patch
  4. Agent runs tests until they pass
  5. We open a real GitHub PR with the fix + the agent's explanation

Usage:
  export ANTHROPIC_API_KEY=...
  python -m agent.agent                 # dry run, no PR
  python -m agent.agent --open-pr       # also open a GitHub PR

GitHub PR requires:
  export GITHUB_TOKEN=...               # repo-scoped PAT
  export GITHUB_REPO=youruser/oncall-copilot-demo
"""

import argparse
import json
import os
import subprocess
from pathlib import Path

import anthropic

from agent.tools import TOOLS, DISPATCH, REPO

MODEL = "claude-sonnet-4-5"
ROOT = Path(__file__).resolve().parent.parent

SYSTEM = """You are an on-call AI engineer. You are paged with a production alert.
Investigate the root cause using your tools, then fix it.

Method:
- Gather context first: read suspect files, search logs, check recent commits.
- Form a hypothesis about the root cause before changing code.
- Apply the minimal correct patch with apply_patch.
- Run the tests. If they fail, read the output, revise, and retry.
- Stop only when the full suite passes.

When tests pass, output a final message with exactly these sections:
  ROOT CAUSE: one or two sentences.
  FIX: what you changed and why.
  VERIFICATION: the test result.
Keep it crisp — this becomes a pull request description."""


def load_alert() -> dict:
    return json.loads((ROOT / "scenarios" / "alert.json").read_text())


def run_agent() -> str:
    client = anthropic.Anthropic()
    alert = load_alert()
    messages = [
        {
            "role": "user",
            "content": f"You've been paged. Alert:\n\n{json.dumps(alert, indent=2)}",
        }
    ]

    final_text = ""
    for step in range(20):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        # collect any text the model emitted this turn
        for block in resp.content:
            if block.type == "text" and block.text.strip():
                print(f"\n[agent] {block.text.strip()}\n")
                final_text = block.text.strip()

        if resp.stop_reason != "tool_use":
            break

        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                print(f"[tool] {block.name}({json.dumps(block.input)[:120]})")
                try:
                    out = DISPATCH[block.name](**block.input)
                except Exception as e:  # noqa: BLE001
                    out = f"ERROR: {e}"
                print(f"[result] {out[:300]}\n")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(out),
                    }
                )
        messages.append({"role": "user", "content": tool_results})

    return final_text


def open_pr(description: str) -> None:
    """Commit the patched file on a branch and open a GitHub PR via the API."""
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPO"]  # e.g. "youruser/oncall-copilot-demo"
    branch = "oncall-copilot/fix-billing-discount"

    # The sample_repo must be a git repo pushed to `repo` as the default branch.
    sr = REPO
    subprocess.run(["git", "checkout", "-B", branch], cwd=sr, check=True)
    subprocess.run(["git", "add", "-A"], cwd=sr, check=True)
    subprocess.run(
        ["git", "commit", "-m", "fix(billing): correct percentage discount math"],
        cwd=sr,
        check=True,
    )
    subprocess.run(["git", "push", "-f", "origin", branch], cwd=sr, check=True)

    import urllib.request

    body = json.dumps(
        {
            "title": "fix(billing): correct percentage discount math",
            "head": branch,
            "base": "main",
            "body": description + "\n\n— opened automatically by On-Call Copilot 🤖",
        }
    ).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "oncall-copilot",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        pr = json.loads(r.read())
    print(f"\n✅ PR opened: {pr.get('html_url')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--open-pr", action="store_true", help="open a real GitHub PR")
    args = ap.parse_args()

    description = run_agent()

    if args.open_pr:
        open_pr(description)
    else:
        print("\n(dry run — re-run with --open-pr to open a GitHub PR)")


if __name__ == "__main__":
    main()
