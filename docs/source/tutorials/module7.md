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

(tutorial:module7)=
# Module 7: Post-Processing and Visualization

## What you will learn

After this module, you will be able to analyze results across parameter sweeps, create plots showing how pattern characteristics vary with parameters, and export representative pattern images.

**Key concepts introduced:**

- Collecting results from multiple calculations
- Plotting variance vs F, mean vs F
- Selecting and exporting representative patterns
- Exporting `.aiida` archives for reproducibility

## Collecting results across the scan

<!-- TODO: use QueryBuilder to collect F, variance_V, mean_V from all calculations in the Group -->
<!-- TODO: sort and organize into arrays for plotting -->

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

## Exporting results

### Exporting an `.aiida` archive

<!-- TODO: export the Group as a portable archive -->
<!-- TODO: explain how archives enable reproducibility and sharing -->

## What you have learned

At this point, you have completed the core tutorial and understand the full AiiDA workflow cycle: from running a single calculation, to parsing and storing results, to building workflows with error handling, to running parameter sweeps and analyzing the results.

## Next steps

If you want to go further, {ref}`Module 8 <tutorial:module8>` covers advanced topics like multi-parameter sweeps and larger-scale simulations.
