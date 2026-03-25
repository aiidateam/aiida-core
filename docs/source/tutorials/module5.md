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

After this module, you will be able to diagnose failed calculations, understand different failure modes, and implement handlers that automatically retry or adjust problematic jobs.

**Key concepts introduced:**

- Inspecting failed jobs with `verdi process dump`
- Understanding exit codes and stderr messages
- Implementing error handlers for numerical instability
- Handling trivial solutions (no pattern formation)
- Re-submission strategies (e.g., reducing the time step)

## What you will not learn yet

You cannot yet run systematic parameter sweeps or organize large numbers of calculations — high-throughput capabilities come in {ref}`Module 6 <tutorial:module6>`.

## Common failure scenarios

Our reaction-diffusion simulation can fail in several controlled ways:

- **Wrong parameter ranges**: F or k outside the pattern-forming regime → exit code 30 (trivial steady state)
- **Time step too large**: Causes numerical blow-up → exit code 20 (NaN/Inf detected)
- **Invalid inputs**: Negative diffusion constants or time step → exit codes 10, 11

## Inspecting failed calculations

### Using `verdi process dump`

<!-- TODO: run a calculation with parameters that cause exit code 30 -->
<!-- TODO: verdi process dump <PK> to inspect the full calculation directory -->
<!-- TODO: examine stderr for the error message -->

### Reading process reports and logs

<!-- TODO: verdi process report <PK> -->
<!-- TODO: verdi calcjob outputcat <PK> to see stdout -->
<!-- TODO: show how exit codes appear in verdi process list -->

## Implementing error handlers

Error handlers automatically respond to specific failures. For example:

- **Numerical instability** (exit code 20): Reduce `dt` by half and resubmit
- **Trivial solution** (exit code 30): Adjust F or k and resubmit

### Writing a handler for numerical instability

<!-- TODO: implement handler that catches exit code 20, reduces dt, resubmits -->

### Writing a handler for trivial solutions

<!-- TODO: implement handler that catches exit code 30, adjusts F, resubmits -->

### Adding handlers to the workflow

<!-- TODO: extend the WorkGraph from Module 4 with error handlers -->
<!-- TODO: run the workflow with parameters that trigger the handler -->
<!-- TODO: inspect the workflow to see the retry in the provenance graph -->

## Next steps

With robust error handling in place, we're ready to scale up. In {ref}`Module 6 <tutorial:module6>`, you'll learn how to run systematic parameter sweeps, query results across many calculations, and organize your data with Groups.
