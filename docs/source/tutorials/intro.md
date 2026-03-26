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

(tutorial:intro)=
# Introduction: Reaction-Diffusion Tutorial

## What this tutorial is about

This tutorial teaches you the core concepts of AiiDA through a single, running example: a **reaction-diffusion simulation** based on the Gray-Scott model.

*"This code simulates how two diffusing and reacting substances on a 2D grid spontaneously form spatial patterns, starting from a nearly uniform initial state."*

:::{admonition} Why this example?
:class: tip

- **Conceptually simple**: You do not need to understand the full mathematics to follow the tutorial; the model provides a visually intuitive result.
- **Parameterizable**: The main parameters (feed rate F, kill rate k, diffusion constants) are scalars that are easy to sweep.
- **Deterministic and reproducible**: Simulations with the same seed always produce the same results.
- **Visual output**: Produces 2D patterns, providing immediate feedback.
- **Error-prone in a controlled way**: Numerical instabilities or trivial states allow natural introduction of exit codes, handlers, and debugging.
:::

:::{dropdown} Longer explanation of the Gray-Scott model
*"Reaction-diffusion systems model two competing processes: chemicals spreading out (diffusion) and chemicals transforming into each other (reaction). In the Gray-Scott model specifically, we track two substances U and V on a grid. U is constantly fed into the system and both substances can decay, while V catalyzes its own production from U in a positive feedback loop. When diffusion, feeding, and decay are balanced just right, these simple local rules spontaneously create global patterns — the same mathematical framework explains everything from leopard spots to chemical oscillations in test tubes. The fascinating part is that identical starting conditions (nearly uniform concentrations everywhere) can produce wildly different patterns just by tweaking two parameters: the feed rate F and kill rate k."*
:::

## Input and output overview

The simulation code (`reaction-diffusion.py`) is a standalone Python script that acts as our "external code" — the equivalent of a quantum chemistry binary like `pw.x`.

### Inputs (YAML file)

| Parameter | Type | Description |
|-----------|------|-------------|
| `grid_size` | int | Size of the 2D grid (grid_size × grid_size) |
| `du`, `dv` | float | Diffusion rates of U and V |
| `F` | float | Feed rate (primary scan parameter) |
| `k` | float | Kill rate |
| `dt` | float | Time step for simulation |
| `n_steps` | int | Number of iterations |
| `seed` | int, optional | Random seed for reproducibility |

### Outputs (`.npz` file)

| Output | Type | Description |
|--------|------|-------------|
| `U_final` | 2D array | Final distribution of U (values 0–1) |
| `V_final` | 2D array | Final distribution of V (values 0–1) |
| `variance_V` | float | Scalar measure of pattern "strength" |
| `mean_V` | float | Average value of V |
| `params` | JSON string | Full simulation parameters used |

### Success and failure signaling

- **Success**: stdout prints `JOB DONE`, exit code 0
- **Failure**: non-zero exit code with `ERROR[code]: message` on stderr

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 10 | Diffusion constants not positive |
| 11 | Time step not positive |
| 20 | Numerical instability (NaN/Inf detected) |
| 30 | Trivial steady state (no pattern formed) |

## Tutorial structure

The tutorial is organized in six modules that progressively introduce AiiDA concepts:

| Module | Topic | Key concepts |
|--------|-------|-------------|
| {ref}`Module 1 <tutorial:module1>` | Running a simulation | `calcfunction`, `verdi`, provenance |
| {ref}`Module 2 <tutorial:module2>` | Running external codes | `aiida-shell`, CalcJob, parser, exit codes |
| {ref}`Module 3 <tutorial:module3>` | Working with your data | `ArrayData`, QueryBuilder, Groups, archives |
| {ref}`Module 4 <tutorial:module4>` | Building workflows | WorkGraph, chaining, context variables |
| {ref}`Module 5 <tutorial:module5>` | Error handling & debugging | Handlers, `verdi process dump`, retries |
| {ref}`Module 6 <tutorial:module6>` | High-throughput & post-processing | Parameter sweeps, plots, pattern gallery |
| {ref}`Module 7 <tutorial:module7>` | Advanced topics (optional) | Multi-param sweeps, remote HPC, FFT |

Each module builds on the previous one, gradually replacing manual steps with AiiDA automation.
