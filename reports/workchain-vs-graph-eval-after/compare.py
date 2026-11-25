###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Compare the paired runs and audit event usage against persisted sessions."""

import json
from pathlib import Path

REPORT = Path(__file__).resolve().parent
BEFORE = REPORT.parent / 'workchain-vs-graph-eval'


def main() -> None:
    before = json.loads((BEFORE / 'results.json').read_text())
    after = json.loads((REPORT / 'results.json').read_text())
    comparison = {}
    audit = {}
    rows = []
    for arm in ('workchain', 'graph'):
        old, new = before[arm], after[arm]
        comparison[arm] = {'before': old, 'after': new}
        for field in ('wall_seconds', 'provider_reported_cost_usd', 'assistant_messages', 'tool_calls'):
            comparison[arm][field + '_change_percent'] = (new[field] / old[field] - 1) * 100
        for field in new['usage']:
            if old['usage'][field]:
                comparison[arm][field + '_change_percent'] = (new['usage'][field] / old['usage'][field] - 1) * 100
        sessions = list((REPORT / arm / 'sessions').glob('*.jsonl'))
        assert len(sessions) == 1
        records = [json.loads(line) for line in sessions[0].read_text().splitlines()]
        usage = dict.fromkeys(new['usage'], 0)
        for record in records:
            message = record.get('message', {})
            if record.get('type') == 'message' and message.get('role') == 'assistant':
                for key in usage:
                    usage[key] += message.get('usage', {}).get(key, 0)
        assert usage == new['usage']
        assert records[0].get('parentSession') is None
        assert new['validation_returncode'] == 0
        assert all(new['fixed_files_unchanged'].values())
        audit[arm] = {
            'session_usage': usage,
            'matches_event_metrics': True,
            'session_header': records[0],
            'validation_passed': True,
            'fixed_files_unchanged': True,
        }
        rows.append(
            f'| {arm} | {old["wall_seconds"]:.1f} → {new["wall_seconds"]:.1f} | '
            f'{old["usage"]["totalTokens"]:,} → {new["usage"]["totalTokens"]:,} | '
            f'{old["assistant_messages"]} → {new["assistant_messages"]} | '
            f'${old["provider_reported_cost_usd"]:.4f} → ${new["provider_reported_cost_usd"]:.4f} |'
        )
    assert audit['workchain']['session_header']['id'] != audit['graph']['session_header']['id']
    (REPORT / 'comparison.json').write_text(json.dumps(comparison, indent=2) + '\n')
    (REPORT / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    text = (
        """# Before/after comparison

Same task, style constraints, collaborators, acceptance tests, model and thinking level; new
independent Pi sessions and separate source snapshots for both arms. The before figures refer
to the final measured pair, not its excluded pilot. Each pair ran concurrently on the same host.
No previous solutions or sessions were supplied to the new agents.

| Arm | Solve seconds: before → after | Total tokens: before → after | Model calls | Reported USD |
|---|---:|---:|---:|---:|
"""
        + '\n'.join(rows)
        + """

Both new submissions pass all 13 common acceptance cases. All-tests counts include each
agent's additional tests and therefore differ. Full token categories and costs are retained in
`comparison.json`; totals include cached context, not just newly generated tokens.

## Observations, not causal claims

- The graph agent used literal counters/flags/strings and an iteration-local `step` directly.
  It no longer needed arithmetic to manufacture constants, output-unpacking to avoid a local,
  or duplicated finalizer placements to choose a literal mode. Its initial workflow solution
  passed all common acceptance cases without edits or graph-language build errors.
- It retained a named/branch-armed loop condition rather than using the newly supported `and`
  or a conditional expression. The eval therefore does not measure every new feature's effect.
- Its first agent-authored test run failed on input namespace access (not workflow behavior);
  it corrected its own tests and reran successfully. The same `graph_inputs` vs direct input
  distinction remains an API-discoverability issue outside these language features.
- Total graph tokens fell about 62%, but noncached input rose from 35,805 to 51,067. Much of
  the total reduction is cached context reprocessing across fewer turns; reported graph cost
  fell only about 9%. Do not equate total-token reduction with an equal cost reduction.
- WorkChain also became faster and used fewer tokens despite unchanged orchestration APIs.
  Agents reran tests different numbers of times, and the integrated suite ran concurrently
  during this new pair. Provider latency/cache state, host load and agent sampling vary.
  One before/after pair cannot establish a causal productivity improvement or stable speedup.
"""
    )
    (REPORT / 'comparison.md').write_text(text)


if __name__ == '__main__':
    main()
