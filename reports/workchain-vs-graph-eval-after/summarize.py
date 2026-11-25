###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build the report and browsable full sessions from independent validation artifacts."""

import json
import subprocess
from pathlib import Path
from xml.etree import ElementTree

REPORT = Path(__file__).resolve().parent


def main() -> None:
    results = json.loads((REPORT / 'results.json').read_text())
    rows = []
    for arm, result in results.items():
        root = ElementTree.parse(REPORT / arm / 'validation.xml').getroot()
        cases = list(root.iter('testcase'))
        passed = sum(
            case.find('failure') is None and case.find('error') is None and case.find('skipped') is None
            for case in cases
        )
        acceptance = [case for case in cases if 'test_acceptance' in case.get('classname', '')]
        acceptance_passed = sum(
            case.find('failure') is None and case.find('error') is None and case.find('skipped') is None
            for case in acceptance
        )
        usage = result['usage']
        rows.append(
            f'| {arm} | {result["wall_seconds"]:.1f} | {usage["input"]:,} | {usage["output"]:,} | '
            f'{usage["cacheRead"]:,} | {usage["totalTokens"]:,} | '
            f'{acceptance_passed}/{len(acceptance)} | {passed}/{len(cases)} |'
        )
        sessions = list((REPORT / arm / 'sessions').glob('*.jsonl'))
        if len(sessions) == 1:
            exported = subprocess.run(
                ['pi', '--no-extensions', '--no-mcp', '--export', str(sessions[0]), str(REPORT / arm / 'session.html')],
                capture_output=True,
                text=True,
                check=False,
            )
            (REPORT / arm / 'export.log').write_text(exported.stdout + exported.stderr)
    run = json.loads((REPORT / 'run.json').read_text())
    text = (
        f"""# WorkChain vs graph authoring: eval after language improvements

## Task and setup

Implement bounded adaptive relaxation: choose a stride, repeatedly submit a scientific child WorkChain until
convergence or a budget limit, branch on the outcome, then submit a finalizer and return its existing report node.
The same fixed collaborators, contract and 13 acceptance cases are supplied to both arms. See [task.md](task.md).

Two fresh **Pi OS processes**, separate source snapshots/Git repositories and new sessions;
no inherited conversation, previous solution or cross-agent context.
Same model: `{run['provider']}/{run['model']}`, thinking `{run['thinking']}`.
Concurrent execution, 900-second limit per arm.
Snapshots include the dirty working tree, not just HEAD; see [baseline-manifest.json](baseline-manifest.json).

## Final measured results

| Arm | Seconds | Input | Output | Cached read | Total tokens | Acceptance | All tests |
|---|---:|---:|---:|---:|---:|---:|---:|
"""
        + '\n'.join(rows)
        + """

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
cp "$source"/{run_eval.py,summarize.py,task.md,collaborators.py,test_acceptance.py} \\
  reports/workchain-vs-graph-eval-rerun/
uv run --no-sync python reports/workchain-vs-graph-eval-rerun/run_eval.py
uv run --no-sync python reports/workchain-vs-graph-eval-rerun/summarize.py
```

Requires installed project dependencies, `pi` and provider credentials.
`PI_PROVIDER`, `PI_MODEL` and `PI_REASONING_LEVEL` select the shared settings.
Workspaces remain under the temporary path recorded in `run.json`.
The dependency environment is shared, but `PYTHONPATH` selects each workspace's own source.
"""
    )
    (REPORT / 'README.md').write_text(text)


if __name__ == '__main__':
    main()
