# Review of the new submissions

Both satisfy their assigned orchestration styles and pass all 13 unchanged common acceptance cases. The independent validations also pass each agent's own tests: WorkChain 22/22 total (9 additional), graph 23/23 (10 additional).

- **WorkChain:** conventional subclass/outline, self.ctx state, while_/if_, self.submit and ToContext. The root returns the finalizer's existing report node.
- **Graph:** public @graph with task(TrialWorkChain)/task(FinalizeWorkChain), direct scalar bindings (stride=2, attempts=0, pending=False, mode='square'), and an iteration-local step namespace. The root loop controls attempts and convergence, then one finalizer placement receives the branch-selected mode. No extra WorkChain or hidden orchestration task was introduced.

Compared with the old graph submission, no constant-arithmetic hacks, one-element output-unpacking workaround, or duplicated finalizer placement are needed. There were no graph-language build errors and no edits to the initial solution. The graph agent initially wrote incorrect root input access in its own tests, then fixed those tests without modifying the solution or acceptance suite. This is distinct from the unsupported-expression issues addressed by the new features.

Both agents left the fixed collaborators/tests unchanged and changed only their new solution and own test files. The acceptance suite verifies exact scientific updates and budgets, zero-iteration cases, both directions/negative values, branches, child counts, output creator links and returned-node identity. No application source was changed by an eval agent.
