# Weekend Build Plan — On-Call Copilot

A tight, demo-first plan. The goal is a flawless end-to-end run you can record,
not maximum surface area. **A demo that works beats broad scope that's flaky.**

## Saturday

### Morning — get the loop green (you mostly have this already)
1. Clone the scaffold. `pip install -r requirements.txt`.
2. Read `agent/tools.py` and `agent/agent.py` until you can explain every tool
   and the loop out loud. (Founders will ask "what happens on step 4?")
3. Run `python -m agent.agent` with your API key. Watch it investigate and fix.
   If it wanders, tighten the `SYSTEM` prompt — that's the main tuning knob.

### Afternoon — make it real
4. Create a GitHub repo `oncall-copilot-demo`, push `sample_repo/` to it (`main`).
5. Make a PAT (repo scope). Run `python -m agent.agent --open-pr`. Confirm a
   real PR appears with the agent's root-cause writeup.
6. If the agent's final PR body is sloppy, tighten the ROOT CAUSE / FIX /
   VERIFICATION instructions in `SYSTEM`.

## Sunday

### Morning — make it robust + a second scenario
7. Add one more bug + scenario (e.g. an off-by-one in tax rounding, with its
   own alert.json + log lines). Two scenarios proves it's an agent, not a
   hardcoded script. Keep scenario files swappable.
8. Add a tiny guardrail: refuse patches over N changed lines, or require the
   suite to exist before patching. Founders love to see you thinking about
   blast radius.

### Afternoon — package it
9. Record a 2–3 min Loom: read the alert, run the agent, narrate each tool
   call, show the green tests, click into the live PR. That video is the
   single most persuasive artifact.
10. Polish the README. Add the Loom link at the top.
11. Write the outreach message (below) and send it with the repo + Loom.

## Stretch (only if ahead)
- PagerDuty webhook receiver (Flask) so a real alert triggers the run.
- Simple eval: run each scenario 5×, log steps-taken and pass/fail.
- Stream the agent's reasoning to a minimal web UI.

## What to emphasize when you show Vatsal
- You rebuilt his **core loop**, and you understand *why* context-gathering and
  closed-loop testing are the hard parts — not the LLM call.
- You made deliberate scope cuts (mock logs, one repo) to ship a working demo.
- You have concrete ideas for what's next (integrations, evals, guardrails).

## Outreach message to send with it

> Hi Vatsal — TasksMind stuck with me, so I spent the weekend building a tiny
> version of your core loop: an agent that takes a production alert,
> investigates the code + logs, writes a fix, runs the tests until they pass,
> and opens a real PR. Repo + 3-min demo here: [links]. I'd love to compare
> notes on the hard parts — especially context-gathering and when to auto-PR
> vs. just post findings. Open to a quick call?

## Talking points for the call
- **Why it's hard:** gathering the *right* context cheaply; knowing when the
  fix is trustworthy enough to auto-PR.
- **Where it breaks:** multi-file root causes, flaky tests, incidents with no
  test coverage at all.
- **What you'd build next at TasksMind:** ask what their hardest current
  failure mode is and connect it to what you saw building this.
