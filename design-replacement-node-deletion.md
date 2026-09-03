# Design: Replacement deletion for provenance graphs

**Status:** Draft for discussion
**Scope:** Node deletion through the Python API and `verdi node delete`

## 1. Summary

AiiDA currently deletes a target node by traversing the provenance graph and adding other nodes whose deletion is required to satisfy the consistency rules.
This behavior is safe, but deleting one intermediate node can remove a much larger downstream graph.

This design proposes an opt-in **replacement deletion** mode.
Replacement deletion removes the selected part of the graph, reconnects its surviving boundary, and inserts a single explicit replacement process for each connected removed process region.
The replacement records that provenance was intentionally omitted without pretending that the surviving data were directly related.

The existing traversal deletion remains the default and keeps its current behavior.

The existing interfaces are extended rather than adding another deletion entry point:

```console
$ verdi node delete 42 --replace --dry-run
$ verdi node delete 42 --replace
```

```python
from aiida.tools import delete_nodes

pks, was_deleted = delete_nodes([42], replace=True, dry_run=True)
```

`delete_nodes` remains the only public Python entry point for deleting nodes.
Any plan object needed internally for previewing and applying the rewrite remains an implementation detail.

## 2. Goals

The feature should:

- let a user remove one or more intermediate nodes without automatically deleting the complete dependent graph;
- preserve reachability between surviving ancestors and descendants;
- visibly represent omitted computation with a replacement process node;
- collapse multiple adjacent process nodes in a removed region into one replacement process node;
- preview every deleted node, replacement node, and new link before changing the database;
- perform the complete rewrite atomically;
- preserve the current traversal deletion as the default;
- make reduced provenance unmistakable to queries, exports, and graph visualizations.

## 3. Non-goals

Replacement deletion does not preserve full reproducibility.
It deliberately records less provenance and must never be presented as equivalent to the original graph.

The feature does not reconstruct deleted node repositories, attributes, logs, or process execution details.
It does not support running processes in the first version.
It does not infer scientific equivalence between inputs and outputs.
It does not make deletion reversible.

## 4. Terminology

The **selection** is the set of nodes requested by the user.
The **rewrite region** is the complete set of nodes that must be removed or replaced to produce a valid graph.
The **boundary** contains surviving nodes with a link to or from the rewrite region.
A **replacement process** is a new immutable process node representing one connected process-containing part of the rewrite region.

The examples use this notation:

```text
[D1]   data node
(P1)   original process node
<R1>   replacement process node
--x--> selected node or link region
-----> provenance or call link
```

## 5. User experience

### 5.1 Command-line interface

`verdi node delete` gains an opt-in flag:

```text
--replace / --no-replace
```

`--no-replace` is the default and invokes the current deletion rules unchanged.
`--replace` selects the replacement deletion rules and reconnects the surviving graph.

The existing command remains backward compatible:

```console
$ verdi node delete 42
```

This is equivalent to:

```console
$ verdi node delete 42 --no-replace
```

A replacement preview reports more than a list of primary keys:

```text
Selected nodes:                 42 43
Nodes to delete:                42 43
Surviving boundary nodes:       7 51
Replacement processes:          R1 (2 selected nodes)
New contracted links:           7 -> R1, R1 -> 51
Remote work directories:        unchanged
No changes were made.
```

Without `--force`, confirmation shows the same plan before applying it.
`--dry-run` never allocates permanent replacement primary keys, so replacements are named `R1`, `R2`, and so on in the preview.

`--replace` is mutually exclusive with the existing traversal-rule options, such as `--create-forward` and `--call-work-forward`.
Replacement deletion inspects links to find the surviving boundary but does not follow them to add nodes to the deletion set.

`--clean-workdir` cleans remote directories belonging to selected `CalcJobNode` instances.
It never associates a remote directory with a replacement process.

### 5.2 Python interface

The existing `delete_nodes` function gains a keyword-only flag:

```python
delete_nodes(
    pks,
    dry_run=True,
    backend=None,
    replace=False,
    **traversal_rules,
)
```

The default and return value remain unchanged, preserving existing callers.
When `replace=True`, the returned primary-key set contains the explicitly selected existing nodes and no traversal-expanded descendants or ancestors.
Replacement details are reported through the existing deletion logger during a dry run or execution.
An internal immutable plan can carry the selected region, boundary links, and proposed replacements between validation and application, but it is not a new public API.
Applying an internal plan must fail if an affected node or link changed since planning.

### 5.3 Relationship to `GraphTraversalRules`

`GraphTraversalRules.DELETE` controls how ordinary deletion expands an initial selection into a larger deletion set.
Replacement deletion intentionally does not perform this expansion because forward traversal would normally delete the outputs that it is meant to preserve and reconnect.
Backward traversal would similarly delete surviving creators or callers that should form the incoming boundary.

The implementation should therefore not add `GraphTraversalRules.DELETE_REPLACE`.
It should reuse graph-query utilities for inspecting incoming and outgoing links, but it should treat linked unselected nodes as boundary nodes rather than traversal candidates.

The Python API rejects `replace=True` together with any explicit `**traversal_rules` override.
The CLI rejects `--replace` together with traversal flags such as `--create-forward`, `--call-calc-forward`, or their negative forms.
This avoids combinations where the traversal first removes the graph that replacement deletion is expected to reconnect.

`replace: bool = False` remains preferable to a public `ruleset` argument because replacement is a separate deletion behavior rather than another set of link-following defaults.
The matching names `replace=True` and `--replace` are concise and explicit in the context of node deletion.

### 5.4 Other existing deletion entry points

`delete_group_nodes` gains the same `replace` argument and treats all nodes in the selected groups as one selection.
Commands such as `verdi group delete --delete-nodes` may expose the same `--replace` flag when they delegate to `delete_nodes`.
They retain traversal deletion by default.

Computer and code deletion should not initially expose replacement mode.
Their integrity constraints and ownership semantics differ from a direct request to rewrite provenance.

## 6. Graph rewrite semantics

### 6.1 High-level rule

Replacement deletion contracts the rewrite region while preserving directed reachability across its boundary.

For every directed path that:

1. starts at a surviving boundary node;
2. crosses one or more nodes in the rewrite region; and
3. ends at a surviving boundary node;

AiiDA creates a replacement route between the two surviving nodes.
If a connected selected region contains one or more process nodes, the route passes through exactly one replacement process for that region.
If a connected selected region contains only data nodes, its surviving boundary nodes are joined by a contracted link without creating a replacement process.

Replacement deletion removes only explicitly selected nodes.
It never absorbs an unselected creator, input, output, caller, or callee into the deletion set.
This requires a dedicated contracted link that can connect any supported pair of surviving provenance node types, including two process nodes separated by deleted intermediate data.

### 6.2 Replacement process type

The design introduces `ContractedProcessNode`, a sealed, immutable subtype of `ProcessNode`.
It is a provenance marker, not an executable calculation or workflow.

A replacement process:

- is never runnable, restartable, cacheable, or a cache source;
- has no repository content copied from removed nodes;
- is displayed as `ContractedProcessNode` by the CLI, REST API, exports, and graph visualizers;
- accepts typed boundary links required to represent both data and logical provenance;
- stores the deletion time, initiating user, number and broad classes of removed nodes, and the replacement policy used;
- does not copy sensitive attributes, extras, logs, comments, or repository objects from removed nodes.

Supporting mixed calculation and workflow boundaries requires explicit link-validation rules for `ContractedProcessNode`.
It must not masquerade as a `CalculationNode` that created data or a `WorkflowNode` that returned data.
The preferred design is to add a dedicated `CONTRACTED` link type that records reachability through deleted provenance and can connect supported boundary nodes either directly or through a `ContractedProcessNode`.
Reusing `INPUT_CALC`, `CREATE`, `RETURN`, or `CALL` would make scientifically false claims and is rejected.

A contracted link means only that its target was reachable from its source through deleted provenance.
It does not mean that a replacement node executed or created data.

### 6.3 Forming replacement regions

The planner divides the explicitly selected nodes into connected regions without adding linked unselected nodes.
Incoming and outgoing links crossing a selected region define its surviving boundary.

A selected connected region containing one or more process nodes produces exactly one replacement process.
Multiple selected process nodes are collapsed only when they are connected through other selected nodes.
A selected connected region containing no process produces contracted links directly between its surviving incoming and outgoing boundary nodes.
Disconnected selected regions are processed separately.

The planner reports the selected nodes, boundary nodes, replacement processes, and contracted links before deletion.

### 6.4 Link labels

Original link labels are not necessarily unique after several processes are collapsed.
New boundary labels therefore use deterministic names based on direction, original boundary node UUID, and original label.
The full old-to-new boundary-label mapping is stored on the replacement node.

No metadata about internal links is retained by default.
An installation may retain a cryptographic digest of the removed subgraph for audit purposes, but the digest cannot be used to restore it.

### 6.5 Groups, comments, and extras

Deleted nodes are removed from all groups as they are today.
Replacement nodes are not automatically added to groups that contained an internal deleted node.
If every selected node came from the same explicitly targeted group, the group deletion interface may offer to add replacements to that group.

Comments and extras are not transferred because their meaning and ownership cannot be merged safely.
The replacement receives only system-owned immutable contraction metadata.

## 7. Examples

### 7.1 Delete one intermediate data node

Consider two calculations connected by intermediate data:

```text
Before

[D0] ---> (C1) ---> [D1] ---> (C2) ---> [D2]
                       selected: D1
```

Keeping `C1` and `C2` while deleting `D1` would leave both calculations disconnected with ordinary provenance links.
The planner therefore removes only `D1` and records the omitted connection with a contracted link:

```text
After `verdi node delete D1 --replace`

[D0] ---> (C1) - - contracted - -> (C2) ---> [D2]

Deleted:  D1
Created:  one contracted link
Kept:     D0, C1, C2, D2
```

The old traversal mode remains available and follows the configured consistency rules:

```text
After `verdi node delete D1`

[D0]

Typically deleted: C1, D1, C2, D2
```

The exact traversal result continues to depend on the existing traversal options.

### 7.2 Delete multiple process nodes

The user can select the process chain directly:

```text
Before

[D0] ---> (C1) ---> [D1] ---> (C2) ---> [D2]
           x                         x
```

```console
$ verdi node delete C1 C2 --replace
```

Only the selected calculations are deleted.
Because the unselected `D1` separates them, each selected calculation is its own connected selected region:

```text
After

[D0] ---> <R1> ---> [D1] ---> <R2> ---> [D2]

Deleted:  C1, C2
Created:  R1, R2
Kept:     D0, D1, D2
```

To collapse the complete chain into one replacement, the user explicitly selects the connecting data as well:

```console
$ verdi node delete C1 D1 C2 --replace
```

```text
[D0] ---> <R1: contracted process> ---> [D2]

Deleted:  C1, D1, C2
Created:  R1
```

This is the central collapsing rule: any number of process nodes connected inside one explicitly selected region is represented by one replacement process.

### 7.3 Delete a branching intermediate region

A result can feed multiple calculations:

```text
Before

                         +---> (C2) ---> [D2]
[D0] ---> (C1) ---> [D1]-+
                         +---> (C3) ---> [D3]
                    selected: D1
```

Only `D1` is removed, and contracted links reconnect its surviving process boundary:

```text
After

                         + - contracted - -> (C2) ---> [D2]
[D0] ---> (C1) - - - - -+
                         + - contracted - -> (C3) ---> [D3]

Deleted:  D1
Created:  two contracted links
Kept:     C1, C2, C3, D0, D2, D3
```

No replacement process is created because the selected region contains no process node.

### 7.4 Preserve a surviving parent workflow

A parent workflow calls a sub-workflow, which calls a calculation:

```text
Before

(W0) --calls--> (W1) --calls--> (C1) ---> [D1]
                  x                 x
[D0] ------------------------------>
```

Deleting `W1` and `C1` in replacement mode keeps the parent and final data connected through one replacement:

```text
After

(W0) --contracted-call--> <R1> --contracted-output--> [D1]
[D0] -------------------->
```

`R1` records that it replaces both a workflow and a calculation.
It does not claim that it executed or created `D1`.

### 7.5 Delete disconnected selections

Selections in disconnected graph regions are not merged:

```text
Before

[A0] ---> (C1) ---> [A1]       [B0] ---> (C2) ---> [B1]
           x                               x
```

```text
After

[A0] ---> <R1> ---> [A1]       [B0] ---> <R2> ---> [B1]
```

Two replacement nodes preserve the fact that the original regions were unrelated.

### 7.6 Delete an isolated data node

An isolated selected data node has no surviving boundary to reconnect:

```text
Before                 After

[D0]  [D1 selected]    [D0]
```

No replacement process is created.

## 8. Safety and validation

Replacement deletion is allowed only when every node in the rewrite region is stored and every process is terminated and sealed.
Running, waiting, paused, or unsealed processes cause planning to fail with a list of offending nodes.

The planner rejects a rewrite if it would:

- create a directed cycle;
- cross profiles or storage backends;
- violate a uniqueness constraint on a surviving ordinary link;
- produce an unsupported mixed boundary;
- modify a graph that changed after the plan was created;
- include protected nodes under a future retention-policy mechanism.

The operation runs in one storage transaction.
Crossing links are removed, replacement nodes and contracted links are inserted, and original nodes and repositories are deleted as one logical operation.
If any step fails, the database graph remains unchanged.
Repository cleanup must use the storage backend's existing transactional or compensating-cleanup guarantees.

The confirmation prompt shows the explicitly selected nodes, surviving boundary nodes, replacement processes, and contracted links.
A large-selection threshold should require `--force` plus an explicit maximum, for example `--max-nodes`, in non-interactive use.

## 9. Queries, export, and visualization

QueryBuilder must expose the `CONTRACTED` link type but must not include it in ordinary `CREATE`, `RETURN`, or `CALL` queries.
Higher-level provenance traversal gets an `include_contracted` option that defaults to `True` for reachability and displays a warning when a path crosses reduced provenance.
Reproducibility-oriented operations can set `include_contracted=False` or reject contracted paths entirely.

AiiDA archives must export and import replacement nodes and contracted links.
Importing them must preserve their marker semantics and must never convert them into ordinary calculation or workflow links.

Graph visualization should render replacements with a distinct shape or dashed border and contracted links as dashed arrows.
Text output should use an explicit label such as `omitted provenance`, not a calculation plugin name.

## 10. Implementation outline

The implementation can be split into the following stages:

1. Add an internal immutable rewrite plan without introducing a new public deletion function.
2. Add `ContractedProcessNode` and the `CONTRACTED` link type with storage migrations and validation.
3. Implement selected-region discovery, boundary construction, cycle checks, and deterministic labels without deletion traversal.
4. Extend the existing deletion transaction to apply replacement nodes and links atomically.
5. Add `replace=False` to `delete_nodes` and `--replace` to `verdi node delete`, rejecting traversal-rule overrides when enabled.
6. Add archive, QueryBuilder, REST API, and visualization support.
7. Add group-deletion integration after direct node deletion is stable.

The first release should mark `replace=True` experimental because it changes the meaning of provenance traversal and archive compatibility.

## 11. Testing strategy

Tests should cover linear, branching, merging, cyclic logical-provenance, mixed workflow/calculation, disconnected, and isolated graphs.
For every generated acyclic provenance graph and valid selection, property-based tests should verify that:

- no unselected node is deleted;
- reachability between each surviving boundary pair is preserved through a contracted route;
- each connected selected region containing a process creates exactly one replacement process;
- each connected selected region containing only data creates no replacement process;
- the resulting graph is acyclic and satisfies link constraints;
- dry-run and apply compute the same rewrite region;
- applying a stale plan fails without partial changes;
- failure injection at every transaction stage leaves the original graph intact.

Backward-compatibility tests should prove that omitting `replace`, or passing `replace=False`, produces the exact current deletion set and return value.

## 12. Alternatives considered

### 12.1 Reuse ordinary calculation or workflow nodes

A synthetic calculation could connect data inputs and outputs with `INPUT_CALC` and `CREATE` links.
This would falsely state that the synthetic node executed and created the outputs.
A workflow replacement has the analogous problem for `RETURN` links and cannot represent calculation creation.
Dedicated replacement semantics are therefore preferred.

### 12.2 Reuse ordinary links as shortcuts

Reusing ordinary provenance links would make reconnection simple, but it would assign false `CREATE`, `RETURN`, or `CALL` semantics to the surviving nodes.
A dedicated `CONTRACTED` link is intentionally generic but remains visibly distinct from ordinary provenance and records only reachability through deleted nodes.

### 12.3 Change current deletion behavior

Making replacement deletion the default would surprise users, alter established scripts, and weaken provenance without explicit consent.
The current traversal mode must remain the default.

### 12.4 Keep one replacement per original process

This preserves process cardinality but does not achieve the requested graph reduction.
One replacement per connected selected process region is simpler and makes the contraction explicit.

## 13. Open questions

The following questions require agreement before implementation:

1. Should the `CONTRACTED` link type participate in default ancestor and descendant queries, or only when explicitly requested?
2. What minimal audit metadata may be retained without defeating deletion for privacy or licensing reasons?
3. Should replacement nodes be automatically added to any groups, and if so, under which unambiguous rule?
4. Should the first version support logical provenance and mixed workflow/calculation regions, or initially support data-provenance chains only?
5. Which archive format version should first support contracted nodes and links?
6. Should an administrator be able to disable replacement deletion per profile?
7. Should a hard maximum selection size be mandatory even with `--force`?

## 14. Recommended decision

Extend the existing `delete_nodes` function with `replace: bool = False` and add the matching `verdi node delete --replace` flag.
Keep replacement deletion separate from `GraphTraversalRules.DELETE` and reject combinations of `replace=True` with traversal-rule overrides.
Use a dedicated, visibly non-executable replacement process and a `CONTRACTED` link rather than overloading `CREATE`, `RETURN`, or `CALL`.
Keep rewrite planning internal to `delete_nodes`, but make its dry-run and confirmation output show the selected region, surviving boundary, and reduced graph before irreversible deletion.

## 15. Revision 1: Public API and transaction review

The first implementation review found no direct source-level break for existing `delete_nodes` callers.
The new `replace` argument is keyword-only, defaults to `False`, and leaves the existing return type unchanged.
The existing command-line behavior also remains the default.
The review nevertheless identified semantic compatibility and integrity concerns that must be resolved before release.

### 15.1 Restrict contracted-link creation

Adding `LinkType.CONTRACTED` to the public link API currently allows callers to create arbitrary links between stored nodes.
Special-casing this link in `ProcessNodeLinks` also allows links to be added to sealed process nodes.
This weakens the existing guarantee that sealed process provenance cannot be modified.

Contracted links must be created only by the internal replacement-deletion operation.
The implementation must not expose a general way for users or plugins to mutate sealed provenance with `LinkType.CONTRACTED`.
Cycle checks must apply at the layer that creates contracted links so an internal or external caller cannot create a cyclic provenance graph.

A preferred implementation places contracted-link insertion in a dedicated storage-backend rewrite operation instead of routing it through the public `Node.base.links.add_incoming` API.

### 15.2 Preserve the meaning of `ProcessNode`

`ContractedProcessNode` is specified as a `ProcessNode` even though it does not represent an execution.
This changes the results of public queries for `ProcessNode` and may affect process control, restart, dump, REST, and command-line code that assumes every process node records an executable process.

Every generic `ProcessNode` consumer must either support contracted markers explicitly or exclude them intentionally.
If this audit is too invasive, the replacement marker should derive directly from `Node` rather than `ProcessNode`, while retaining its distinct provenance role through its node type and visualization.

Re-exporting `ContractedProcessNode` from `aiida.orm` makes it stable public API under AiiDA's compatibility policy.
The class should not be re-exported while its semantics are experimental unless the project is willing to support that API through the normal deprecation cycle.

### 15.3 Version archive compatibility

An archive containing a contracted node or link cannot be represented faithfully by an older AiiDA version.
An older importer may ignore an unknown contracted link and silently import an incomplete graph.

Archive support must include a format or minimum-reader version that causes unsupported AiiDA versions to reject the archive explicitly.
Import and export tests must verify that contracted nodes and links round-trip without being converted to ordinary provenance links.

This is an archive compatibility change, not a database migration.
The database stores node and link types as strings, so adding these values does not itself require a schema migration.

### 15.4 Treat `LinkType` as public API

`LinkType` is public API, so adding `CONTRACTED` is additive but observable.
External code may iterate over every enum member or maintain an exhaustive mapping of link types.
The new member therefore requires release notes and an audit of all internal exhaustive mappings.

### 15.5 Keep replacement atomic without changing all link commits

Replacement deletion must create marker nodes and contracted links and delete the selected nodes atomically.
The initial implementation called `Node.base.links.add_incoming` while inside `backend.transaction()`.
The PostgreSQL implementation of `add_incoming` normally calls `session.commit()` after inserting a stored link.
That commit can make part of the rewrite permanent before the remaining links and node deletions succeed, defeating the all-or-nothing transaction required by this design.

The initial implementation changed `add_incoming` to call `flush()` instead of `commit()` whenever a nested transaction is active.
A flush sends pending SQL to the database but leaves final commit or rollback to the surrounding transaction.
This explains why the implementation changed transaction behavior.

The change does not require a database migration because it changes transaction timing rather than schema or stored representation.
It is nevertheless observable for every caller that adds a link inside `backend.transaction()`, not only replacement deletion.
Code that previously observed an immediate commit would now observe the link only according to the lifetime and isolation of the surrounding transaction.

The preferred solution is to avoid changing the commit behavior of the general link API solely for this feature.
The storage backend should instead provide an internal atomic operation, such as `replace_nodes_and_connections`, that inserts replacement nodes and contracted links and deletes selected nodes in one transaction.
If the global `commit()` to `flush()` change is considered an independent transaction bug fix, it should be proposed separately and covered by tests for commit, rollback, nesting, and concurrent visibility.

### 15.6 Preserve unrelated default deletion behavior

The ordinary `replace=False` path should remain unchanged apart from delegation needed to share implementation.
The initial implementation changed the debug representation of node types and shortened the existing `delete_nodes` and `delete_group_nodes` documentation.
These unrelated observable and documentation changes should be reverted.

Backward-compatibility tests must compare the deletion set, callback input, return value, logging where relevant, and exception behavior of the default path against the existing implementation.

### 15.7 Separate contraction from deletion traversal

Further review showed that replacement and traversal are not two compatible modes of the same operation.
Traversal follows a link to add the adjacent node to the deletion set, whereas contraction stops at that link, keeps the adjacent node as a boundary, and reconnects it.

For example, `create_forward=True` instructs ordinary deletion to remove a created output, while contraction requires that output to survive as an outgoing boundary.
There is no unambiguous result when both instructions are supplied.
Making `replace=True` mutually exclusive with every traversal override avoids the immediate ambiguity but leaves `delete_nodes` with two unrelated contracts.

Revision 1 therefore supersedes the original recommendation to add `replace` to `delete_nodes`.
The public Python API should instead provide two functions with separate contracts:

```python
delete_nodes(pks, dry_run=True, backend=None, **traversal_rules)
contract_nodes(pks, dry_run=True, backend=None)
```

`delete_nodes` keeps its current graph-expanding behavior, traversal rules, return type, logging, and documentation unchanged.
`contract_nodes` deletes only the explicitly selected region, preserves its surrounding boundary, creates contracted links, and creates one replacement marker for each selected connected region containing a process.
`contract_nodes` does not accept graph traversal rules.

The command-line interface should make the same distinction:

```console
verdi node delete NODES [TRAVERSAL OPTIONS]
verdi node contract NODES
```

A dedicated command avoids presenting combinations that are invalid by definition and lets dry-run and confirmation output use contraction-specific terminology.
It also allows contraction to return replacement-node and contracted-link details without changing the established `delete_nodes` return type.

The name `contract_nodes` is preferred over `replace_nodes` because a data-only selected region creates direct contracted links without necessarily creating a replacement process node.
The term `contract` should be defined prominently in user documentation because it is precise graph terminology but may be unfamiliar to users.

`delete_group_nodes` should retain its existing deletion semantics initially.
Group contraction can be considered later as an explicit operation rather than adding a mode to group deletion.

Internally, both operations may reuse missing-node handling, confirmation helpers, logging infrastructure, and backend transaction primitives.
They must not share a public signature or force contraction through `GraphTraversalRules`.
