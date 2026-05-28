# On-Call Copilot 🚨🤖

A minimal **alert-to-pull-request agent** — the core loop behind autonomous
on-call tooling, built in a weekend. Give it a production alert; it
investigates the codebase and logs, diagnoses the root cause, writes a fix,
runs the tests until they pass, and opens a real GitHub pull request.

This is a deliberately scoped prototype of the TasksMind value prop: take an
alert all the way to a clean PR while the engineer sleeps.

## The loop

```
alert.json ─▶ investigate ─▶ diagnose ─▶ patch ─▶ run tests ─▶ open PR
              (read code,                          (retry until
               search logs,                         green)
               git log)
```

The agent is a tool-calling loop over the Anthropic API. It decides which
tools to call; the harness executes them and feeds results back until the
suite is green.

## Tools the agent has

| Tool          | What it does                                       |
|---------------|----------------------------------------------------|
| `list_files`  | Enumerate source + test files                      |
| `read_file`   | Read any repo file                                 |
| `search_logs` | Grep mock production logs for incident context     |
| `git_log`     | Correlate the incident with a recent deploy        |
| `apply_patch` | Make a precise, unique-match edit                  |
| `run_tests`   | Run pytest and read the result                     |

## The scenario

`sample_repo/` is a tiny billing service with a planted regression: a
"refactor discount math" commit made `apply_discount` treat `10` (percent) as
the fraction `10` instead of `0.10`, producing wildly negative invoice totals.
Two tests fail. The alert, logs, and git history all point at the deploy — the
agent has to connect them and ship the one-line fix.

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=

...

# watch the agent investigate and fix (no PR)
python -m agent.agent

# also open a real GitHub PR
export GITHUB_TOKEN=...                       # repo-scoped PAT
export GITHUB_REPO=youruser/oncall-copilot-demo
python -m agent.agent --open-pr
```

For the PR step, push `sample_repo/` to GitHub as its own repo first (its
default branch should be `main`), and point `GITHUB_REPO` at it.

## What this demonstrates

- **Context-gathering, not just prompting** — the agent has to pull the right
  code, logs, and commit before it can diagnose. That's the hard, valuable part.
- **Closed-loop verification** — it doesn't "propose" a fix and hope; it runs
  the tests and iterates until green.
- **Real artifact out** — a genuine GitHub PR with a structured root-cause
  writeup, the way an on-call engineer would hand off.

## Next steps (if extended past the weekend)

- Real integrations: PagerDuty webhook in, Datadog logs query, GitHub Actions
  to run the suite in CI rather than locally.
- Multiple scenarios + an eval harness scoring fix correctness and steps taken.
- Guardrails: diff-size limits, human approval gate, blast-radius checks.
- Confidence scoring — when to auto-PR vs. when to just post findings.
