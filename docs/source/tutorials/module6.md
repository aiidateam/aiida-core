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

(tutorial:module6)=
# Module 6: High-Throughput and Post-Processing

## What you will learn

After this module, you will be able to:

- Run sweeps over input parameters using loops in WorkGraph
- Collect and analyze results across many calculations
- Visualize trends across parameter scans

## What you will not learn yet

This module completes the core tutorial. For advanced extensions, see {ref}`Module 7 <tutorial:module7>`.

## Running a parameter sweep

:::{note}
You could run a parameter sweep with a Python `for` loop and `engine.submit()`, but WorkGraph's `Map` handles this declaratively: it parallelizes the tasks, tracks which parameter produced which result, and groups everything under a single workflow node.
If some runs fail, only those are affected — the rest complete normally.
:::

### Setting up the scan

<!-- TODO: define the parameter range to sweep over -->
<!-- TODO: create a WorkGraph with a loop over the parameter -->
<!-- TODO: submit the scan workflow -->

### Monitoring the scan

<!-- TODO: verdi process status to see all child calculations -->
<!-- TODO: verdi process list to see progress -->

## Collecting results with the QueryBuilder

:::{tip}
This is where the QueryBuilder from {ref}`Module 3 <tutorial:module3>` becomes essential.
Instead of manually tracking which output file corresponds to which parameter value, you query the database: "give me all variance values from calculations inside this workflow, along with their input parameters."
:::

<!-- TODO: use QueryBuilder to collect inputs and outputs from the scan -->
<!-- TODO: organize results into arrays for analysis -->

## Visualizing trends

<!-- TODO: plot output quantities as a function of the scanned parameter -->
<!-- TODO: interpret the results -->

## Visualizing representative outputs

<!-- TODO: select a few representative parameter values -->
<!-- TODO: load output data from the database -->
<!-- TODO: display results side by side -->

## Summary

In this module you learned to:

- **Run** parameter sweeps using WorkGraph loops
- **Collect** results across many calculations with the QueryBuilder
- **Visualize** trends and analyze how outputs vary with inputs

At this point, you have completed the core tutorial and understand the full AiiDA workflow cycle: from running a single calculation, to parsing and storing results, to building workflows with error handling, to running parameter sweeps and analyzing the results.

## Next steps

If you want to go further, {ref}`Module 7 <tutorial:module7>` covers advanced topics like multi-parameter sweeps, remote HPC execution, and more.
