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
# Module 3: Using Data Types

## What you will learn

After this module, you will be able to store arrays, scalars, and parameters in AiiDA's native data types and optionally generate PNG visualizations of your patterns.

**Key concepts introduced:**

- `ArrayData` for storing 2D arrays (`U_final`, `V_final`)
- `Float` for scalars (`variance_V`, `mean_V`)
- `Dict` for parameters
- Simple post-processing function to generate PNG images

## What you will not learn yet

You cannot yet combine multiple calculations into automated workflows — that's {ref}`Module 4 <tutorial:module4>`.

## AiiDA data types for scientific data

So far our parser extracted `Float` values. But the simulation also produces 2D arrays (`U_final`, `V_final`) that represent the spatial patterns. Let's store those properly.

### Storing arrays with `ArrayData`

<!-- TODO: extend parser to store U_final and V_final as ArrayData -->
<!-- TODO: show how to retrieve and inspect ArrayData -->

### Storing parameters with `Dict`

<!-- TODO: store simulation parameters as a Dict node -->
<!-- TODO: show how Dict nodes appear in the provenance graph -->

## Visualizing patterns

The 2D arrays can be visualized as images. Let's write a simple `calcfunction` that takes an `ArrayData` and produces a visualization.

<!-- TODO: write a calcfunction that generates a PNG from V_final -->
<!-- TODO: show the resulting pattern image -->

## Exploring the provenance graph

With data nodes, process nodes, and their connections, we now have a meaningful provenance graph.

<!-- TODO: verdi node graph generate <PK> -->
<!-- TODO: explain the different node types and link types -->

## Next steps

We can now store and visualize scientific data in AiiDA. In {ref}`Module 4 <tutorial:module4>`, you'll learn how to chain multiple steps into automated workflows using WorkGraph.
