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

(tutorial:module3)=
# Module 3: Working with Your Data

## What you will learn

After this module, you will be able to:

- Use AiiDA's data types (`ArrayData`, `Float`, `Dict`) to store scientific data
- Visualize stored data (pattern images from arrays)
- Find and filter data with the QueryBuilder
- Organize calculations and data using Groups
- Dump calculation data to disk with `verdi process dump`
- Export and share data as `.aiida` archives

## What you will not learn yet

You cannot yet chain multiple steps into automated workflows — that comes in {ref}`Module 4 <tutorial:module4>`.

## AiiDA data types for scientific data

### Storing arrays with `ArrayData`

<!-- TODO: store U_final and V_final as ArrayData -->
<!-- TODO: show how to retrieve and inspect ArrayData -->

### Storing scalars and parameters

<!-- TODO: recap Float and Dict from Module 1, show additional usage -->

### Visualizing stored data

<!-- TODO: write a calcfunction that generates a pattern image from V_final -->
<!-- TODO: show the resulting pattern -->

## Finding data with the QueryBuilder

### Basic queries: find, filter, project

<!-- TODO: introduce QueryBuilder -->
<!-- TODO: find all CalcJobs, filter by state or input parameters -->
<!-- TODO: project specific output values (variance_V, mean_V) -->

### Combining filters

<!-- TODO: filter by multiple criteria (e.g., F value AND successful exit code) -->
<!-- TODO: show how to extract results into a table -->

## Organizing data with Groups

<!-- TODO: create a Group -->
<!-- TODO: add calculations/data to the Group -->
<!-- TODO: query within a Group -->

## Inspecting and exporting data

### `verdi process dump`

<!-- TODO: dump a calculation's full directory to disk -->
<!-- TODO: inspect the dumped files -->

### Exporting `.aiida` archives

<!-- TODO: export a Group as a portable archive -->
<!-- TODO: explain how archives enable reproducibility and sharing -->

## Summary

In this module you learned to:

- **Store** scientific data using `ArrayData`, `Float`, and `Dict`
- **Query** the database with the QueryBuilder
- **Organize** data with Groups
- **Dump** calculation data to disk
- **Export** data as `.aiida` archives

## Next steps

You can now store, find, and organize your data. In {ref}`Module 4 <tutorial:module4>`, you'll learn how to chain calculations into automated workflows using WorkGraph.
