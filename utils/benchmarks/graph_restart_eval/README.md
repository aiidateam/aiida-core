# Graph restart evaluation — `BaseRestartWorkChain` vs direct `GraphIR`

Fairness probe (n=1, see disclaimer): two agents start from scratch and solve
the **same** transient-failure retry task, one with `BaseRestartWorkChain`
(arm A), one by constructing `GraphIR` directly (arm B, no `@graph` sugar).
Judged on correctness (shared hidden acceptance tests) plus time/tokens.

Status: **completed paired run recorded — harness reusable.** The original
n=1 paired run (model `gpt-6.1-sol`, thinking `medium`) finished and is
preserved at `reports/graph-restart-study/` (repository root, with the
consolidated `report.json` assembled mechanically by `assemble_report.py`).
`config.json` keeps the same GO values (same budgets for both arms) for
future reruns; a rerun writes fresh untracked per-run `reports/` in this
directory and never touches the committed study folder.

## Layout

- `TASK_COMMON.md` — shared problem statement (same for both arms; includes
  the isolation rules each agent must obey).
- `ARM_A_BRWC.md` / `ARM_B_GRAPHIR.md` — the ONLY allowed method per arm
  (high-level method constraints only; no solution supplied to either arm).
- `fixtures/flaky_child.py` — shared flaky collaborator (agents may read,
  never modify; hidden tests import the identical file).
- `run_eval.py` — orchestrator: builds isolated worktrees, pre-warms
  `.venv` via `uv sync` for BOTH arms before either solve starts, launches
  one fresh `pi --mode json` process group per arm, records transcripts +
  metrics + run cards.
- `parse_events.py` — parses `pi --mode json` JSONL: authoritative
  `message_end` usage (`input/output/cacheRead/cacheWrite/totalTokens`),
  provider/model, stop reason; wall time comes from the harness monotonic
  clock; `--check-cap N` does a post-hoc budget check.
- `grading/` — tracked v2 hidden acceptance tests plus `conftest.py`
  (loads `aiida.tools.pytest_fixtures` outside `tests/`, SQLite + ZeroMQ
  defaults) and `verify_arm.py` (the ONLY supported verification entry
  point for future runs). Committed AFTER the original solves; `prepare_arm`
  physically removes this directory from every fresh solver worktree before
  the solve starts, so solvers never see it. Never show it to agents.
- `tests_hidden/` — frozen v1 snapshot of the original hidden tests:
  git-ignored, never copied into agent worktrees, never modified. Kept only
  so the original (defective) scoring stays reproducible; future runs hash
  (`manifest.json`: `grader_version: v2`) and execute `grading/` instead.
  The original v1 results are preserved in the completed study report, not
  re-run.
- `reports/` — untracked run cards, prompts, transcripts, metrics, session
  logs for the CURRENT/NEXT run (outside both arm worktrees and outside this
  conversation). The completed study lives at `reports/graph-restart-study/`
  (repository root) and is never overwritten by a rerun.
- `config.json` — GO values: `model=gpt-6.1-sol`, `provider=openai-codex`,
  `thinking=medium`, `timeout_s_each_arm=1800`,
  `max_total_tokens_each_arm=1000000` (same for both arms).

## Rerun command (harness is reusable)

```sh
# config.json holds the same GO values used by the completed study run.
# Confirm the model resolves: pi --list-models gpt-6.1-sol
# Launch (from this worktree root):
uv run python utils/benchmarks/graph_restart_eval/run_eval.py \
  --config utils/benchmarks/graph_restart_eval/config.json
```

Offline smoke test — prepare-arm safety with a tempfile fake worktree only
(no model, no `pi` binary, no git worktree, no network):

```sh
uv run python utils/benchmarks/graph_restart_eval/run_eval.py --self-check
```

Optional overrides: `--model ... --thinking ... --timeout-s 1800
--revision <sha> --arms a,b`. One arm only for smoke-testing the harness:
`--arms a` (still counts as a real run for that arm — re-run both for the eval).

## After both agents finish (and only then)

```sh
uv run python utils/benchmarks/graph_restart_eval/grading/verify_arm.py \
  --solution-dir <arm-a worktree>/eval-scratch-a/restart_solution --arm a
uv run python utils/benchmarks/graph_restart_eval/grading/verify_arm.py \
  --solution-dir <arm-b worktree>/eval-scratch-b/restart_solution --arm b
```

This runs the hidden tests with
`pytest -p aiida.tools.pytest_fixtures --broker-backend zmq -m presto`
(SQLite storage, ZeroMQ broker — no external services).

Never show agents the hidden tests, the other arm's worktree, transcripts, or
metrics.

## Isolation measures (how no context is shared)

- **Separate OS processes**: each arm is a NEW `pi` subprocess
  (`pi --mode json ...` with the full prompt as its first positional message),
  never a worker tool-context/subagent of this session.
- **Separate process groups, no orphans**: each child starts with
  `start_new_session=True`; timeout and token-cap kills signal the ENTIRE
  subprocess group (`killpg`), so tool children cannot outlive `pi`.
- **No inherited agent context**: both commands use
  `--no-extensions -e builtin:codemode --no-mcp` with explicit
  `--tools read,bash,edit,write,codemode --exclude-tools 'mcp__*'`, so no
  extensions, MCP servers, skills-gated tools, or session-continuation state
  leak from the parent into either child.
- **Scrubbed child environment**: every `PI_*` variable (including
  `PI_SESSION_ID`, `PI_SESSION_FILE`, `PI_CODING_AGENT_SESSION_DIR`,
  `PI_PROVIDER`, `PI_MODEL`, `PI_REASONING_LEVEL`) is removed from the child
  environment (`--model`, `--thinking`, `--session-dir`, `--session-id` are
  passed explicitly). Provider credentials are inherited so the child can
  authenticate, and are never written to any log (only the redacted argv is
  recorded; `--api-key` is never used).
- **Separate repository checkouts**: `git worktree add --detach <revision>`
  per arm at the SAME recorded revision; arm cwd is a fresh
  `eval-scratch-<arm>/` dir inside its own worktree. Immediately after the
  worktree is created — before the scratch dir is staged and long before the
  solver starts — `prepare_arm` physically deletes the tracked `grading/`
  grader directory and any root `reports/` checkout from the NEW disposable
  worktree only (never this checkout), then asserts both are absent; the
  per-arm pre-flight additionally asserts no `grading/`/`reports/` paths
  reached the scratch dir.
- **Pre-warmed environments, same caches**: `uv sync` runs once per worktree
  for BOTH arms BEFORE either agent launches (outside the timed solve),
  identically for both arms, so neither arm pays install time and both share
  the same warm `.venv`/package caches.
- **Fresh sessions, no history**: explicit `--session-dir reports/sessions-arm-<arm>`
  (fresh per arm) + `--session-id graph-restart-eval-<arm>-v1`; never
  `--continue/--resume/--fork`, no conversation history carried over.
  Persisted session logs stay under `reports/` (outside both arm cwds and
  outside this worktree's session) alongside the full-stdout JSONL transcript.
- **Prompt-level prohibitions**: each prompt forbids reading the other arm's
  files, `reports/`, `grading/`, `*.jsonl`, `tests_hidden/`/`*verify*` paths, and any git
  history or other worktrees; agents work only inside their scratch.
- **No report JSONL or grader source in arm reach**: pre-flight asserts zero
  `*.jsonl` plus zero `*hidden*`/`*verify*`/`grading`/`reports` paths under
  each arm scratch before launch; the tracked `grading/` grader is deleted
  from each fresh arm worktree outright, and the frozen v1 `tests_hidden/`
  snapshot is git-ignored so it never enters a fresh checkout. Reference
  transcripts and run cards also live only in untracked per-run `reports/`
  (invisible inside the fresh arm worktrees). Fresh sessions carry no history:
  there is no transcript carry-over between runs.
- **Frozen identical inputs**: `manifest.json` records SHA-256 of
  `TASK_COMMON.md`, both arm files, `fixtures/flaky_child.py`, and the
  tracked `grading/*.py` hidden tests (`grader_version: v2`) before either arm
  launches. Task, arm, and fixture files are frozen (already
  vetted); do not modify them. The original `manifest.json` and run cards
  are preserved in the completed study folder.
- **Identical task except method**: both prompts contain `TASK_COMMON.md` +
  `fixtures/flaky_child.py` verbatim; prompts differ ONLY in the arm file and
  the scratch path.
- **Same budgets**: same `--model gpt-6.1-sol`, `--provider openai-codex`,
  `--thinking medium`, harness `--timeout-s 1800`, and
  `max_total_tokens_each_arm=1000000` for both arms (monotonic wall clock;
  tokens from authoritative `message_end` usage). The token cap is sampled at
  `message_end` boundaries and can overshoot by up to one response before the
  child group is terminated; the cap and the overshoot policy are recorded on
  the run card.

## Reading the results

The completed study is `reports/graph-restart-study/` (repository root):
`report.json` is the authoritative consolidated record (assembled
mechanically by `assemble_report.py`; no hand-transcribed measurements),
with the benchmark timings under `benchmarks/` and the paired eval
(transcripts, run cards, prompts, metrics, session logs, preserved v1 and
v2 verification logs) under `evaluation/`.

Per arm, a fresh run's untracked `reports/` holds `run-card-arm-<arm>.json`
(method, model, thinking, revision, `pi --version`,
transcript/metrics/prompt/session-file SHA-256, scrubbed worktree paths,
prewarm timing, harness timing incl. timeout/cap flags), `metrics-arm-<arm>.json`
(token totals, provider/model, stop reason, tool-call counts, wall seconds),
`events-arm-<arm>.jsonl` (full raw stdout JSONL), `stderr-arm-<arm>.log`,
`prompt-arm-<arm>.md`, `sessions-arm-<arm>/` (raw pi
session logs), and `manifest.json` (model/thinking/tools/timeout/token-cap,
revision, `grader_version`, frozen input hashes, repo status). Compare correctness
(hidden tests) against time/tokens.

## Grading correction (v1 import-alias defect, corrected after the solves)

The frozen v1 grader imported the eval-root `flaky_child` module while both
agent solutions legally import `fixtures.flaky_child` from their scratch, so
the v1 contract identity check (`is`) and the `QueryBuilder` process-type
filter found zero children even though the wrappers behaved correctly. The
corrected v2 grader (`grading/`, committed after the solves) validates the
scratch `fixtures/flaky_child.py` SHA-256 against the frozen eval fixture,
then pre-imports the canonical scratch `fixtures.flaky_child` module (aliased
under both legal import names) before loading the solution. Acceptance
semantics — output pk identity, retry cap of 5, fatal single-run stop,
non-zero exit statuses — are unchanged, and no agent was rerun or fixed up:
time/token metrics are identical to the original paired run. Original v1
scoring is preserved unchanged (`initial_v1_hidden_tests`,
`verification-{a,b}.json`, `verify-{a,b}.log`, and the `grader-v1/` snapshot
in the study folder) and superseded as authoritative by the v2 verification
(`verification-v2-{a,b}.json`, 4/4 each). Verify future arms with
`grading/verify_arm.py`, run only AFTER both agents finish.

## Disclaimer

n=1 per method: a single paired run cannot establish a general productivity
difference between the APIs. Treat the outcome as one anecdotal data point
(model, thinking level, timeout, and revision are recorded on each run card
for context), not a benchmark claim.
