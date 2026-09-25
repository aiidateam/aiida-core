# Proposed process-state formatting

The examples below show the **display text**, not a change to the stored process state. In `verdi process status`, the text appears after the process label and PK (for example, `MyWorkChain<123> Running`).

| Underlying state | `verdi process list` | `verdi process show` | `verdi process status` (call graph) |
|---|---|---|---|
| Created | `⏹ Created` | `Created` | `Created` |
| Created, paused | `⏸ Created` | `Created (Paused)` | `Created (Paused)` |
| Running | `⏵ Running` | `Running` | `Running` |
| Running, paused | `⏸ Running` | `Running (Paused)` | `Running (Paused)` |
| Waiting | `⏵ Waiting` | `Waiting` | `Waiting` |
| Waiting, paused | `⏸ Waiting` | `Waiting (Paused)` | `Waiting (Paused)` |
| Finished | `⏹ Finished [0]` | `Finished [0]` | `Finished [0]` |
| Excepted | `⨯ Excepted` | `Excepted <exception>` | `Excepted` |
| Killed | `☠ Killed` | `Killed` | `Killed` |

`[0]` is an example exit status; it appears when an exit status is available. `verdi process show` may also include an exit message or exception details. `verdi process status` may include stepper information. Pause formatting applies only to Created, Running, and Waiting; the stored state and state-based filtering remain unchanged.
