# Methodology

## Same task and fresh contexts

- Comparison baseline: the immediately previous final pair in `../workchain-vs-graph-eval-after/`, not its predecessor or pilot.
- `task.md`, `collaborators.py`, `test_acceptance.py`, per-arm task prompts and substantive runner settings are unchanged. Both arms still need to implement their assigned style and write their own tests. The visible shared acceptance suite has 13 cases.
- Each arm is a new OS-level Pi process with its own randomly generated UUID session and separate source/Git workspace. No parent conversation, prior session or previous solution is supplied; all `PI_SESSION*` environment variables are removed. Report folders are excluded from copied source.
- New sessions retain ordinary project instructions and skill discovery. The new graph authoring skill/guide is deliberately available as part of this revision. The graph agent actually reads it first; it is not manually appended as a special hint.
- Source snapshots include tracked working-tree contents and relevant untracked source/tests/docs. This preserves the current user's local examples rather than silently switching to a different HEAD-only baseline. Both arms receive identical source hashes; the dirty status is recorded in run.json. The evaluator changes no application source.
- Installed dependencies are shared, but each workspace's own src and repository paths lead PYTHONPATH. AiiDA configuration paths are separate. This is context/workspace isolation, not a filesystem security sandbox.
- Same explicit provider/model/thinking: openai-codex/gpt-6.1-sol, medium. Same read/bash/edit/write tools and 900-second limit. Neither agent delegates to another model. The complete invocations and logs are retained.

## Measurements

- Solve time is monotonic process launch-to-exit time, including exploration, reasoning, code generation, tool use and agent-run tests. Independent post-agent validation is excluded and timed separately.
- Both agents run concurrently on the same host, as in the previous pair. Independent validation can overlap the other arm as it finishes. No full application suite is run concurrently during this measured pair; the previous pair did overlap a large integrated suite. Provider latency, host load and cache availability are uncontrolled.
- Usage is summed once per assistant message_end event and independently checked against persisted session messages. Model turns are completed assistant responses, not scientific process submissions or necessarily all hidden provider retries.
- Total tokens include noncached input, output, cached reads and any cached writes. Dollar values preserve the runner's historical `provider_reported_cost_usd` field name but represent Pi's `usage.cost.total` estimate. No authoritative provider bill is populated (`totalFromProvider` is zero).
- Discovery output is the number of text characters returned by tools before the first write/edit. It includes legitimate collaborator and test-guidance reads, not just wasted searches. Tool-output character counts are not exact token counts.
- Tool durations come from harness tool-result durationMs. Overlapping tool intervals are merged for aggregate tool time; no claim is made that wall time minus tools precisely measures model reasoning.
- Shared collaborators and acceptance tests remain unchanged in both submissions. Their restored copies are used for independent validation. Only each new solution.py and test_solution.py appear in the agent workspace diff. Tests are visible, not held out.

## Additional test timing experiment

After both agents and their independent validations finish, timing_probe.py reruns the frozen graph submission's full 30-test suite in serial / xdist-two-workers / xdist-two-workers / serial order. Every run uses the same source, test cases, backend and profile-fixture machinery. All 30 cases pass on all four runs. Commands, wall times, logs and JUnit XML are retained separately in test-timing-probe/.

No additional model calls or solution changes occur in this probe. It is excluded from all agent solve metrics. The ABBA order reduces simple warmup/order bias but two repeats per mode do not support a statistically powered inference. Estimated end-to-end saving is an extrapolation, not a rerun of an agent using parallel tests.

## Scope of conclusions

One new matched pair is sufficient to inspect concrete behavior (guide adoption, successful public input inspection, zero correction cycles), not to establish statistical significance. The canonical guide intentionally covers this bounded-workflow family. Broader productivity claims require multiple fresh matched pairs and different workflow families. Further reductions must retain the scientific task boundaries, acceptance/provenance checks and correctness bar rather than optimizing the metric by omitting work.

## Workflow resource measurement addendum

A later, separate experiment executes each frozen solution on all 13 shared input cases, three times each: 39 executions per arm, 78 total. Each execution gets a fresh Python process, a temporary SQLite profile without a broker, and the same single logical CPU affinity (CPU 0). Pair order alternates by case and repetition. The 708 source-file hashes per snapshot and the archived solution/collaborator bytes are verified before execution. No new coding-agent sessions or application edits are involved.

After importing the frozen implementation, initializing the temporary profile and constructing input nodes, the worker records baseline RSS and resets only its own Linux RSS high-water mark with `/proc/self/clear_refs` value 5. Immediately around `run_get_node`, it records wall/user/system time and reads VmHWM on return, before result/provenance assertions. All 78 workers support this reset. The absolute window peak includes the resident interpreter/library baseline, graph compilation at first launch, and the child WorkChains/calcfunctions running in that same interpreter. Earlier bootstrap peaks and later validation/teardown peaks are excluded from the window. Preparation/final RSS, kernel ru_maxrss and process peak through workflow completion are retained separately; RSS includes shared pages and is not an allocation or proportional-memory metric.

Peak values are reported as maxima and medians over the measured small-workflow cases, not as guaranteed memory bounds or significant differences. Every execution verifies exact report values, attempt counts, child counts, successful completion, returned-node identity and no root CREATE links.

Hardware cache access is independently probed with user-mode perf counters. This host rejects even cycles:u because kernel.perf_event_paranoid is 4. L1 data/L2/L3-LLC access/miss counters therefore remain null with an explicit diagnostic; no zero counts, miss rates or occupancy values are inferred. L1 instruction usage is also unmeasured. Static cache sizes from sysfs/lscpu are hardware metadata only. No host security settings or privileges are changed. If counters are available on a permitted rerun, their scope is the full profiling process, not the narrower RSS execution window; event names and counter running percentages are recorded. Intel-specific L2 aliases need adaptation on other CPUs.

See runtime-resources/README.md, summary.json, runs.jsonl, per-run JSON/logs and audit.json. Seven profiler tests verify case reuse, perf-format parsing, real zero versus unavailable counters, zero-denominator handling and invalid-input rejection. Original agent time/token/cost results are unchanged.
