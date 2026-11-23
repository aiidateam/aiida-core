---
name: authoring-graphs
description: Use when authoring or testing `@graph` workflows and their docs.
---

# Authoring graphs

Canonical recipe: `docs/source/topics/workflows/graphs.rst` (`Authoring recipe`).
Copy its task and graph definitions into your own module; validation and execution checks are included in the guide.
The `tests/engine/processes/graphs/programs/` fixtures include historical edge cases, not just recommended authoring style.

## Recipe

* Science lives in plain `@task` function bodies; the `@graph` only orchestrates.
* Use `task(CalcJobSubclass)` or `task(WorkChainSubclass)` when integrating an existing process, not as a prerequisite for writing a graph.
* `@graph` bodies wire names, literals, and inline expressions only; no science in the root.
* Keep the step placement local to the `while` body; branch on a comparison, bind a status literal, then report.
* One meaningful `@task` summary records value, target, attempts, and status; the root returns that existing node.
* Root returns task outputs and graph inputs by reference, and materializes returned inline values itself.
* Stored graph node keeps flat inputs (`root.inputs.initial`); `outputs['result']` reads the report.

## Testing

* First `assert workflow.build() is None`: catches syntax, wiring, and contract errors without tasks.
* Then run one representative case and check its outputs, as shown in the recipe.
* Only then exercise boundary cases such as an exhausted or zero budget and an initially satisfied condition.
* A passing `build()` does not catch runtime failures; inspect runs via outputs and the stored node.
* Keep documentation examples and their checks in the guide, not in dedicated engine test modules.
