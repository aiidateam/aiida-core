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
# Module 6: Querying and analysis (coming soon)

:::{note}
This module is under development. Planned topics:

- Searching the provenance graph with the QueryBuilder (filter, project, join)
- Analyzing trends across many runs at scale
- Organizing calculations and data with Groups
- Exporting and sharing data as `.aiida` archives

See {ref}`Module 3 <tutorial:module3>` for the latest completed module.
:::

<!-- Original content commented out for future development

## What you will learn

After this module, you will be able to:

- Use the QueryBuilder to find, filter, and project data
- Organize data with Groups
- Export and share data as `.aiida` archives

## Finding data with the QueryBuilder

### Basic queries: find, filter, project

TODO: introduce QueryBuilder
TODO: find all CalcJobs, filter by state or input parameters
TODO: project specific output values (variance_V, mean_V)

### Combining filters

TODO: filter by multiple criteria (e.g., F value AND successful exit code)
TODO: show how to extract results into a table

## Organizing data with Groups

TODO: create a Group
TODO: add calculations/data to the Group
TODO: query within a Group

## Inspecting and exporting data

### `verdi process dump`

TODO: dump a calculation's full directory to disk
TODO: inspect the dumped files

### Exporting `.aiida` archives

Archives include full provenance — not just the data, but how it was produced,
with which inputs, by which code version.
A colleague importing your archive can trace every result back to its origin.

TODO: export a Group as a portable archive
TODO: explain how archives enable reproducibility and sharing

## Summary

In this module you learned to:

- **Query** the database with the QueryBuilder
- **Organize** data with Groups
- **Dump** calculation data to disk
- **Export** data as `.aiida` archives

-->
