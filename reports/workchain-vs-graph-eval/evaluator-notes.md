# Evaluator notes

## Final measured pair

- Both arms start concurrently as new OS-level Pi processes, with distinct new UUID sessions, separate repositories and AiiDA configuration directories. Neither receives the orchestrator conversation, pilot sessions, pilot solutions, or the other submission. Only the supplied task, identical repository snapshot, project instructions/skills and installed dependencies are provided by design. This is context isolation, not a security sandbox: no filesystem access controls are imposed.
- No application source is changed by the evaluator. Existing tracked and untracked graph-layer work is copied into both snapshots without modifying the original working tree. Neither workspace includes any report folders.
- The acceptance suite is visible, not held out. Results measure implementation against a known contract, not unseen-task generalization. Agent-authored tests are also run independently after each agent exits.
- Wall time is monotonic process launch-to-exit time, including discovery, reasoning, edits and the agent's own tests. Independent validation is measured separately. The two processes run concurrently on the same host; timing is not CPU time or a statistically controlled performance comparison.
- Token usage is summed once per assistant `message_end` usage record. Cache read/write are reported separately from input and output; `totalTokens` is the provider/harness-reported total. Totals include repeated cached context across turns, not just unique prompt tokens. Cost is provider/harness-reported, not an invoice.
- The local environment has pytest but no ruff executable (`uv run --no-sync ruff` failed). The evaluator did not change installed dependencies to add a formatter.

## Pilot retained for transparency (excluded from final comparison)

The first pair is retained under `pilot/` with all logs, metrics and submissions. It revealed an evaluator bug, not a solution failure: graph input nodes live in `root.inputs.graph_inputs`, whereas WorkChain inputs live directly in `root.inputs`. The first attempted correction also incorrectly assumed that NodeLinksManager implements `get`. The final acceptance test uses the documented `getattr` fallback. These test changes are visible in pilot patches/logs.

Both pilot submissions passed the corrected test suite, as recorded in `pilot/{workchain,graph}/corrected-validation.log`. The final measured pair was then restarted entirely from scratch with the corrected evaluator already present. No mid-run evaluator corrections or hints were sent to the final pair. Pilot metrics are not mixed into final metrics; pilot agent usage remains available in its own `metrics.json` files.
