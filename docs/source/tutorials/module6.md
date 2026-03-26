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

- Run parameter sweeps over F using loops in WorkGraph
- Collect and analyze results across many calculations
- Create plots showing how pattern characteristics vary with parameters
- Build a representative pattern gallery

## What you will not learn yet

This module completes the core tutorial. For advanced extensions, see {ref}`Module 7 <tutorial:module7>`.

## Parameter sweeps over F

### Setting up the scan

<!-- TODO: define the range of F values (~20 values in 0.035–0.05) -->
<!-- TODO: create a WorkGraph with a loop over F -->
<!-- TODO: submit the scan workflow -->

### Monitoring the scan

<!-- TODO: verdi process status to see all child calculations -->
<!-- TODO: verdi process list to see progress -->

## Collecting and analyzing results

<!-- TODO: use QueryBuilder to collect F, variance_V, mean_V from the scan -->
<!-- TODO: organize results into arrays for plotting -->

## Variance vs F plot

<!-- TODO: plot variance_V as a function of F -->
<!-- TODO: identify the pattern-forming regime -->
<!-- TODO: explain what the plot tells us about the system -->

## Mean vs F plot

<!-- TODO: plot mean_V as a function of F -->
<!-- TODO: discuss the relationship between mean concentration and feed rate -->

## Representative pattern gallery

<!-- TODO: select a few representative F values (low, medium, high variance) -->
<!-- TODO: load V_final arrays from ArrayData -->
<!-- TODO: display patterns side by side as a figure -->

## Summary

In this module you learned to:

- **Run** parameter sweeps using WorkGraph loops
- **Collect** results across many calculations with the QueryBuilder
- **Plot** trends (variance vs F, mean vs F)
- **Visualize** representative patterns

At this point, you have completed the core tutorial and understand the full AiiDA workflow cycle: from running a single calculation, to parsing and storing results, to building workflows with error handling, to running parameter sweeps and analyzing the results.

## Next steps

If you want to go further, {ref}`Module 7 <tutorial:module7>` covers advanced topics like multi-parameter sweeps, remote HPC execution, and more.
