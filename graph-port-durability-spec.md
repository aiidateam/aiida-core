# Port durability

Builds on `661924a57852d057e270fec5ae76a76dcc4ea0ba` (file-backed process checkpoints).

## Contract

Add `durable: bool = True` to `PortField`. This is a retention policy, not a choice of storage backend. Both kinds of value may be written to disk; only a durable value becomes part of the long-term provenance record.

| Port | Storage and provenance |
| --- | --- |
| `durable=True` (default) | Use normal data-node storage and provenance links. The node outlives the workflow. |
| `durable=False` | Keep the binding in workflow execution state. Persist it with checkpoints when needed for restart. Do not create a data node or a provenance link for the binding. |

Apply the flag to leaf inputs and outputs, including fields of a `PortModel`. Existing ports keep their behavior. An already-stored node passed to a checkpoint-only port is not demoted or deleted: the checkpoint can hold its UUID, but this port does not add a data link.

`durable` controls what survives the run; it does not grant permission to mutate a node. Checkpoint-only ports support Python values and references to already-stored nodes, not inline serialization of unstored ORM nodes. A separate port mutability proposal is outside this implementation.

## Wiring and publication

- A checkpoint-only output can feed a checkpoint-only input, including across nested graph scopes. Reject checkpoint-only-to-durable wiring at build time when known, otherwise before dispatch. Do not silently store the value to satisfy the receiving port.
- A durable value may feed a checkpoint-only input. The source node and its existing links stay intact; the receiving port does not add an input link.
- To publish a checkpoint-only result, use a task that consumes it through a checkpoint-only input and emits a durable output. This is a visible storage boundary: the task creates the output node, but its checkpoint-only input has no data link.
- A root graph can take a checkpoint-only input, but cannot declare a checkpoint-only output. Once the run ends, there is no checkpoint-backed result for callers to retrieve. Nested graphs can return checkpoint-only values to the enclosing scope because that scope shares the root's lifetime.

The initial scope is `@graph` and function `@task` placements within a graph. Checkpoint-only ports on standalone tasks, wrapped `CalcJob`/`WorkChain` processes, and legacy process functions are out of scope. A `par_map` cannot collect checkpoint-only outputs into a durable container. Reject unsupported declarations rather than falling back to normal storage.

## Example

```python
from typing import Annotated

from aiida.engine import PortField, PortModel, graph, task

ScratchFloat = Annotated[float, PortField(durable=False)]


@task
def estimate(seed: float) -> ScratchFloat:
    return 2.0 * seed


@graph
def prepare(seed: float) -> ScratchFloat:
    return estimate(seed=seed)


@task
def normalize(estimate: ScratchFloat) -> float:
    return estimate / 10.0


class Report(PortModel):
    score: float


@graph
def report(seed: float) -> Report:
    scratch = prepare(seed=seed)
    score = normalize(estimate=scratch)
    return {'score': score}
```

For `seed=3.0`, the runtime passes `6.0` from `estimate` through `prepare` to `normalize`. A checkpoint can save and restore that binding. The long-term graph is:

```text
F0 [Float(3.0)] ── INPUT_WORK:seed ───────────▶ report
F0              ── INPUT_CALC:seed ───────────▶ estimate
report          ── CALL_CALC:prepare__estimate ▶ estimate
report          ── CALL_CALC:normalize ───────▶ normalize
normalize       ── CREATE:result ─────────────▶ F1 [Float(0.6)]
report          ── RETURN:score ───────────────▶ F1
```

There is no `Float(6.0)` node, no data link between `estimate` and `normalize`, and no separate process node for `prepare`. The task process nodes and call links remain. The stored graph is deliberately incomplete as a record of data dependencies: AiiDA cannot query or reconstruct the omitted input from provenance. The process record should identify checkpoint-only ports without retaining their payloads.

## Checkpoint and restart behavior

The checkpoint commit added pickle files and a digest reference on the process node. The pickler can carry Python values and resolves stored ORM entities by UUID; it rejects unstored entities. The port implementation must keep checkpoint-only values out of the ORM input/output storage path and carry them in checkpoint state. In particular, graph state currently walks and stores unstored nodes before encoding; it must not do so for checkpoint-only bindings.

The root workflow owns the lifetime of the temporary payloads. A child currently publishes outputs through ORM links and deletes its own checkpoint when it terminates. Neither works as the handoff for a checkpoint-only result. Publish the temporary result into workflow-owned checkpoint storage, keyed by the child invocation and output port, before the parent can observe success. The publication must be recoverable if the child finishes and the parent restarts before saving its next checkpoint. Do not report a child as successfully complete if its checkpoint-only outputs cannot be recovered. Do not put their payloads in broker messages, process attributes, or task output links.

Retain payloads needed to resume from the latest committed checkpoint, including results not yet incorporated by the parent. Clean up workflow-owned payloads when the root reaches a terminal state, using the checkpoint store's rollback and backup safeguards. A paused or interrupted run retains its checkpoint state. This is a lifecycle guarantee, not secure erasure: a backup taken during execution can contain a checkpoint.

Disable process cache reuse for tasks with checkpoint-only ports in the initial implementation. The normal cache key does not account for omitted inputs, and cached node outputs cannot restore omitted results. A value that cannot be checkpointed should fail with the port name and type; it must not be silently stored as a node instead.

## Acceptance checks

- A workflow using only default ports has unchanged provenance. In `report`, query the links shown above and verify that no data node was stored for `scratch`.
- Restart after `estimate` finishes but before `report` incorporates its result. `normalize` receives the saved `6.0`; recovery does not depend on the terminated child's checkpoint or node outputs.
- Reject implicit promotion and checkpoint-only root outputs. Verify that passing a pre-existing node to a checkpoint-only port adds no data link and does not delete or change the node.
- Verify that completion, failure, and kill remove the workflow's checkpoint payloads under normal cleanup, while pause and restart preserve them. A checkpoint serialization failure must not publish a successful result or create an ORM node as a fallback.
