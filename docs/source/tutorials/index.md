(tutorials)=
# Tutorials

These tutorials teach you the core concepts of AiiDA -- from running a single
calculation to building automated, error-resilient workflows -- using a running
example that progressively grows in complexity.

<!-- AiiDA in Action teaser — commented out until content is finalized

::::{grid} 1
:gutter: 3

:::{grid-item-card} {fa}`bolt;mr-1` AiiDA in Action
:text-align: center
:shadow: md

See the full power of AiiDA in a quick demo -- then learn to build it yourself.

+++

```{button-ref} teaser
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

See the demo
```
:::
::::

-->

## Introductory modules

:::{note}
These four modules are designed to be worked through in order.
Each builds on the previous one, so start with Module 0 if you are new to AiiDA.
:::

::::{grid} 2 2 2 2
:gutter: 3

:::{grid-item-card} {fa}`flask;mr-1` Module 0: The running example
:text-align: center
:shadow: md

Meet the Gray-Scott simulation, run it directly, and see what's missing without AiiDA.

+++

```{button-ref} module0
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

Go to Module 0
```
:::

:::{grid-item-card} {fa}`circle-play;mr-1` Module 1: Running with AiiDA
:text-align: center
:shadow: md

Run tracked calculations with aiida-shell, inspect provenance, and handle failures.

+++

```{button-ref} module1
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

Go to Module 1
```
:::

:::{grid-item-card} {fa}`cubes;mr-1` Module 2: Structured data and calcfunctions
:text-align: center
:shadow: md

Data types, calcfunctions, and parameter sweeps with full provenance tracking.

+++

```{button-ref} module2
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

Go to Module 2
```
:::

:::{grid-item-card} {fa}`diagram-project;mr-1` Module 3: Writing simple workflows
:text-align: center
:shadow: md

Chain calculations into automated workflows with WorkGraph, including parameter sweeps with Map.

+++

```{button-ref} module3
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

Go to Module 3
```
:::
::::

## Advanced modules

:::{note}
These modules can be worked through in any order, depending on your needs.
They assume familiarity with the introductory modules above.
:::

::::{grid} 2 2 2 2
:gutter: 3

:::{grid-item-card} {fa}`code-branch;mr-1` Module 4: Complex workflows
:text-align: center
:shadow: md

Conditional logic (If/While), nested sub-workflows, and dynamic workflow construction.

+++

*Coming soon*
:::

:::{grid-item-card} {fa}`server;mr-1` Module 5: Remote submission
:text-align: center
:shadow: md

Run calculations on remote HPC clusters with schedulers, transports, and queue management.

+++

*Coming soon*
:::

:::{grid-item-card} {fa}`magnifying-glass-chart;mr-1` Module 6: Querying and analysis
:text-align: center
:shadow: md

Use the QueryBuilder to search, filter, and analyze your provenance graph at scale.

+++

*Coming soon*
:::

:::{grid-item-card} {fa}`shield-halved;mr-1` Module 7: Error handling
:text-align: center
:shadow: md

Exit code checking, error handlers, and automatic retries in your workflows.

+++

*Coming soon*
:::
::::

## Classic tutorial

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} {fa}`graduation-cap;mr-1` Basic Tutorial
:text-align: center
:shadow: md

A self-contained introduction to core AiiDA concepts using simple arithmetic examples.

+++

```{button-ref} basic
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

Go to Basic Tutorial
```
:::
::::

```{toctree}
:maxdepth: 1
:hidden:

teaser
module0
module1
module2
module3
module4
module5
module6
module7
basic
```
