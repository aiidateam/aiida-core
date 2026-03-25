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
# Module 6: High-Throughput Scans and Querying

## What you will learn

After this module, you will be able to execute parameter sweeps over many values of F, collect all results, query the database for specific calculations, and organize your work using Groups.

**Key concepts introduced:**

- Loops in WorkGraphs for parameter sweeps
- Storing multiple calculation outputs
- Querying the AiiDA database (QueryBuilder)
- Groups for organization
- Provenance visualization for multi-calculation workflows

## What you will not learn yet

You cannot yet analyze trends across your parameter sweep or create publication-quality figures — post-processing is {ref}`Module 7 <tutorial:module7>`.

## Parameter scan over F

In `driver.py`, the parameter scan is a simple Python loop that calls `subprocess.run()` for each value of F. With AiiDA, we replace this with a WorkGraph that:

1. Iterates over F values (~20 values in the range 0.035–0.05)
2. Submits a calculation for each F
3. Collects results with full provenance

### Setting up the scan

<!-- TODO: define the range of F values -->
<!-- TODO: create a WorkGraph with a loop over F -->
<!-- TODO: submit the scan workflow -->

### Monitoring the scan

<!-- TODO: verdi process status to see all child calculations -->
<!-- TODO: verdi process list to see progress -->

## Querying results with QueryBuilder

Once the scan is complete, we need to find and extract results across all calculations.

### Finding calculations by parameter

<!-- TODO: QueryBuilder to find all finished calculations -->
<!-- TODO: filter by input parameter F -->
<!-- TODO: project variance_V and mean_V outputs -->

### Extracting results into a table

<!-- TODO: collect F, variance_V, mean_V into a table -->
<!-- TODO: show how to use QueryBuilder projections efficiently -->

## Organizing with Groups

<!-- TODO: create a Group for this parameter scan -->
<!-- TODO: add calculations to the Group -->
<!-- TODO: query within a Group -->

## Next steps

We have a complete parameter scan with organized, queryable results. In {ref}`Module 7 <tutorial:module7>`, you'll learn how to analyze these results, create plots, and export data for sharing.
