# Before/after comparison

Same task, style constraints, collaborators, acceptance tests, model and thinking level; new
independent Pi sessions and separate source snapshots for both arms. The before figures refer
to the final measured pair, not its excluded pilot. Each pair ran concurrently on the same host.
No previous solutions or sessions were supplied to the new agents.

| Arm | Solve seconds: before → after | Total tokens: before → after | Model calls | Reported USD |
|---|---:|---:|---:|---:|
| workchain | 183.1 → 113.0 | 124,199 → 76,743 | 13 → 9 | $0.0802 → $0.0697 |
| graph | 206.2 → 151.5 | 539,972 → 207,414 | 23 → 14 | $0.1522 → $0.1386 |

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
