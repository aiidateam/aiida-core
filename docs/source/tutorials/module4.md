---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

(tutorial:module4)=
# Module 4: Complex workflows (coming soon)

:::{note}
This module is under development. Planned topics:

- Conditional logic with `If` / `While` control-flow zones
- Nested sub-workflows built from `@task.graph` factories
- Dynamic workflow construction based on intermediate results
- Branching patterns for parameter-dependent pipelines

See {ref}`Module 3 <tutorial:module3>` for the latest completed module.
:::

<!-- Original content commented out for future development

## What you will learn

After this module, you will be able to:

- Diagnose failed calculations using `verdi process report` and `verdi process dump`
- Inspect failed jobs (exit codes, stderr, output files)
- Implement error handlers that automatically retry or adjust parameters
- Build resilient workflows with re-submission strategies

## What you will not learn yet

You cannot yet run systematic parameter sweeps or analyze trends across many runs.

## Inspecting failed calculations

### Using `verdi process report`

TODO: run a calculation with parameters that cause exit code 30 (trivial solution)
TODO: verdi process report <PK> to see the error message

### Using `verdi process dump`

TODO: verdi process dump <PK> to inspect the full calculation directory
TODO: examine stderr and output files

### Reading logs and outputs

TODO: verdi calcjob outputcat <PK> to see stdout
TODO: show how exit codes appear in verdi process list

## Understanding failure modes

TODO: recap exit codes from Module 1 (10, 11, 20, 30)
TODO: run examples that trigger each failure mode
TODO: discuss what each failure means and how to respond

## Implementing error handlers

Note: This module shows error handlers using the **WorkGraph** API, where handlers
are standalone functions attached to tasks.
The traditional **WorkChain** approach uses a different pattern: handler methods on the
class, discovered automatically via a `@process_handler` decorator.
Module 7 covers the WorkChain approach.
The concepts (matching exit codes, adjusting inputs, retrying) are the same — only
the registration syntax differs.

### Handler for numerical instability (exit code 20)

TODO: implement handler that catches exit code 20, reduces dt, resubmits

### Handler for trivial solutions (exit code 30)

TODO: implement handler that catches exit code 30, adjusts F, resubmits

### Adding handlers to a workflow

TODO: extend the WorkGraph from Module 3 with error handlers
TODO: run the workflow with parameters that trigger the handler
TODO: inspect the workflow to see the retry in the provenance graph

## Summary

In this module you learned to:

- **Diagnose** failures with `verdi process report` and `verdi process dump`
- **Inspect** failed jobs' exit codes and output files
- **Implement** error handlers for automatic recovery
- **Build** resilient workflows that retry with adjusted parameters

## Next steps

With robust error handling in place, we're ready to scale up.

-->
