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

(tutorial:module5)=
# Module 5: Error Handling and Debugging

## What you will learn

After this module, you will be able to:

- Diagnose failed calculations using `verdi process report` and `verdi process dump`
- Inspect failed jobs (exit codes, stderr, output files)
- Implement error handlers that automatically retry or adjust parameters
- Build resilient workflows with re-submission strategies

## What you will not learn yet

You cannot yet run systematic parameter sweeps or analyze trends across many runs — high-throughput capabilities come in {ref}`Module 6 <tutorial:module6>`.

## Inspecting failed calculations

### Using `verdi process report`

<!-- TODO: run a calculation with parameters that cause exit code 30 (trivial solution) -->
<!-- TODO: verdi process report <PK> to see the error message -->

### Using `verdi process dump`

<!-- TODO: verdi process dump <PK> to inspect the full calculation directory -->
<!-- TODO: examine stderr and output files -->

### Reading logs and outputs

<!-- TODO: verdi calcjob outputcat <PK> to see stdout -->
<!-- TODO: show how exit codes appear in verdi process list -->

## Understanding failure modes

<!-- TODO: recap exit codes from Module 2 (10, 11, 20, 30) -->
<!-- TODO: run examples that trigger each failure mode -->
<!-- TODO: discuss what each failure means and how to respond -->

## Implementing error handlers

### Handler for numerical instability (exit code 20)

<!-- TODO: implement handler that catches exit code 20, reduces dt, resubmits -->

### Handler for trivial solutions (exit code 30)

<!-- TODO: implement handler that catches exit code 30, adjusts F, resubmits -->

### Adding handlers to a workflow

<!-- TODO: extend the WorkGraph from Module 4 with error handlers -->
<!-- TODO: run the workflow with parameters that trigger the handler -->
<!-- TODO: inspect the workflow to see the retry in the provenance graph -->

## Summary

In this module you learned to:

- **Diagnose** failures with `verdi process report` and `verdi process dump`
- **Inspect** failed jobs' exit codes and output files
- **Implement** error handlers for automatic recovery
- **Build** resilient workflows that retry with adjusted parameters

## Next steps

With robust error handling in place, we're ready to scale up. In {ref}`Module 6 <tutorial:module6>`, you'll learn how to run parameter sweeps, collect results, and create publication-quality plots.
