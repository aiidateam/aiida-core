# WorkChain vs graph authoring: paired agent evaluation

## Unpack the complete raw artifacts

Full agent logs, HTML sessions, submissions, evaluator fixtures and source manifests are preserved in
`evaluation-logs.tar.xz`; they are not discarded. Unpack them before following the raw-artifact links or rerun instructions:

```bash
(cd reports/workchain-vs-graph-eval && \\
  sha256sum -c evaluation-logs.tar.xz.sha256 && tar -xJf evaluation-logs.tar.xz)
```

The small result/metadata files below remain directly readable without extraction.


## Task and setup

Implement bounded adaptive relaxation: choose a stride, repeatedly submit a scientific child WorkChain until convergence or a budget limit, branch on the outcome, then submit a finalizer and return its existing report node. The same fixed scientific collaborators, input/output contract and 13 acceptance cases are supplied to both arms. See [task.md](task.md).

Two fresh **Pi OS processes**, separate source snapshots/Git repositories and new sessions; no inherited conversation, pilot solution or cross-agent context. Same model: `openai-codex/gpt-6.1-sol`, thinking `medium`. Concurrent execution, 900-second limit per arm. Snapshots include the current dirty working tree, not just HEAD; file hashes are in [baseline-manifest.json](baseline-manifest.json).

## Final measured results

| Arm | Solve time (s) | Input tokens | Output tokens | Cached-read tokens | Total tokens | Common acceptance | All tests |
|---|---:|---:|---:|---:|---:|---:|---:|
| workchain | 183.1 | 17,550 | 3,481 | 103,168 | 124,199 | 13/13 | 23/23 |
| graph | 206.2 | 35,805 | 3,047 | 501,120 | 539,972 | 13/13 | 24/24 |

Solve time includes the agent's exploration, reasoning, edits and its own tests, but excludes the evaluator's subsequent validation. Tokens are cumulative usage across model calls; total includes cached context. Input/output alone are not the total. Detailed costs, calls and validation timings are in each arm's metrics JSON.

Both submissions comply with their assigned orchestration style and preserve the returned node's identity. See [review.md](review.md). The all-tests counts differ because each agent wrote its own additional tests; the common acceptance suite is identical. [audit.json](audit.json) independently cross-checks event usage totals against persisted sessions and confirms distinct fresh session IDs.

This is one task and one final run per style, not statistically significant evidence that either style is generally better. Tests are visible rather than held out. See [evaluator-notes.md](evaluator-notes.md) for isolation limits and the excluded pilot/evaluator correction history.

## Artifacts

Each of `workchain/` and `graph/` contains:

- `prompt.md`, `invocation.json`: complete initial task, style constraint and process invocation.
- `events.jsonl`: complete streamed agent events including tool calls/results and usage.
- `sessions/*.jsonl`, `session.html`: persisted full session and browsable export.
- `stderr.log`, `assistant-text.md`: process diagnostics and all assistant text (not just the final response).
- `metrics.json`: measured time, token categories, exit codes, model and fixed-file integrity.
- `submission/`: complete submitted implementation, agent tests and shared evaluator/collaborators.
- `solution.patch`: changes relative to its starting snapshot.
- `validation.log`, `validation.xml`: independently rerun acceptance and agent-authored tests.

Shared files: `collaborators.py`, `test_acceptance.py`, `run_eval.py`, `summarize.py`, `run.json`, `results.json`. The excluded first pair's complete artifacts remain under `pilot/`.

## Reproduce with fresh agents

Use a new empty report folder to avoid overwriting these results:

```bash
mkdir -p reports/workchain-vs-graph-eval-rerun
cp reports/workchain-vs-graph-eval/{run_eval.py,summarize.py,task.md,collaborators.py,test_acceptance.py} reports/workchain-vs-graph-eval-rerun/
uv run --no-sync python reports/workchain-vs-graph-eval-rerun/run_eval.py
uv run --no-sync python reports/workchain-vs-graph-eval-rerun/summarize.py
```

Requires the already-installed project environment, `pi` and configured provider credentials. `PI_PROVIDER`, `PI_MODEL` and `PI_REASONING_LEVEL` select the shared model settings (defaults are recorded in the runner). Workspaces are retained under the temporary path recorded in `run.json`. The installed dependency environment is shared, but `PYTHONPATH` selects each workspace's own source.
