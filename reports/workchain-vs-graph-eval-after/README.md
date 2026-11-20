# WorkChain vs graph authoring: eval after language improvements

## Unpack the complete raw artifacts

Full agent logs, HTML sessions, submissions, evaluator fixtures and source manifests are preserved in
`evaluation-logs.tar.xz`; they are not discarded. Unpack them before following the raw-artifact links or rerun instructions:

```bash
(cd reports/workchain-vs-graph-eval-after && \\
  sha256sum -c evaluation-logs.tar.xz.sha256 && tar -xJf evaluation-logs.tar.xz)
```

The small result/metadata files below remain directly readable without extraction.


## Task and setup

Implement bounded adaptive relaxation: choose a stride, repeatedly submit a scientific child WorkChain until
convergence or a budget limit, branch on the outcome, then submit a finalizer and return its existing report node.
The same fixed collaborators, contract and 13 acceptance cases are supplied to both arms. See [task.md](task.md).

Two fresh **Pi OS processes**, separate source snapshots/Git repositories and new sessions;
no inherited conversation, previous solution or cross-agent context.
Same model: `openai-codex/gpt-6.1-sol`, thinking `medium`.
Concurrent execution, 900-second limit per arm.
Snapshots include the dirty working tree, not just HEAD; see [baseline-manifest.json](baseline-manifest.json).

## Final measured results

| Arm | Seconds | Input | Output | Cached read | Total tokens | Acceptance | All tests |
|---|---:|---:|---:|---:|---:|---:|---:|
| workchain | 113.0 | 19,257 | 2,574 | 54,912 | 76,743 | 13/13 | 22/22 |
| graph | 151.5 | 51,067 | 2,107 | 154,240 | 207,414 | 13/13 | 23/23 |

Solve time includes discovery, reasoning, edits and agent tests, but excludes subsequent independent validation.
Tokens are cumulative across calls; total includes repeated cached context. Detailed categories, costs and validation
 timings are in each arm's metrics JSON. All-tests counts differ because agents wrote different additional tests;
the common acceptance suite is identical.

Both submissions comply with their assigned orchestration style and preserve output node identity.
See [review.md](review.md), [implementation.md](implementation.md) for commits/tests, and
[comparison.md](comparison.md) for before/after metrics.
[audit.json](audit.json) cross-checks usage against saved sessions and confirms distinct fresh session IDs.

One paired task is not statistically significant evidence that either style is generally better.
Tests are visible, not held out. See [evaluator-notes.md](evaluator-notes.md) for methodology and limits.

## Artifacts

Each of `workchain/` and `graph/` contains:

- `prompt.md`, `invocation.json`: complete task, style constraint and process invocation.
- `events.jsonl`: full streamed events, including tool calls/results and usage.
- `sessions/*.jsonl`, `session.html`: full persisted session and browsable export.
- `stderr.log`, `assistant-text.md`: diagnostics and all assistant text, not just the final response.
- `metrics.json`: elapsed time, token categories, exit codes, model and fixed-file integrity.
- `submission/`: implementation, agent tests and shared evaluator/collaborators.
- `solution.patch`: changes relative to the starting snapshot.
- `validation.log`, `validation.xml`: independently rerun acceptance and agent-authored tests.

Shared files include the task, collaborators, acceptance tests, runner, report scripts, run metadata and results.
The previous evaluation remains in `../workchain-vs-graph-eval/`; its metrics are embedded in `comparison.json`.
The raw evaluator templates intentionally refer to modules injected into temporary workspaces, not this report folder.

## Reproduce with fresh agents

Use a new empty folder to avoid overwriting these results:

```bash
mkdir -p reports/workchain-vs-graph-eval-rerun
source=reports/workchain-vs-graph-eval-after
cp "$source"/{run_eval.py,summarize.py,task.md,collaborators.py,test_acceptance.py} \
  reports/workchain-vs-graph-eval-rerun/
uv run --no-sync python reports/workchain-vs-graph-eval-rerun/run_eval.py
uv run --no-sync python reports/workchain-vs-graph-eval-rerun/summarize.py
```

Requires installed project dependencies, `pi` and provider credentials.
`PI_PROVIDER`, `PI_MODEL` and `PI_REASONING_LEVEL` select the shared settings.
Workspaces remain under the temporary path recorded in `run.json`.
The dependency environment is shared, but `PYTHONPATH` selects each workspace's own source.
