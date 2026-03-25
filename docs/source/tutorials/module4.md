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

(tutorial:module4)=
# Module 4: Workflow Basics

## What you will learn

After this module, you will be able to wrap a single calculation in a WorkGraph, understand workflow logic, and use context variables to pass data between steps.

**Key concepts introduced:**

- WorkGraph basics
- Adding tasks (CalcJob, calcfunction) to a graph
- Context (`ctx`) variables for data flow between tasks
- Simple workflow logic: run, then post-process

## What you will not learn yet

You cannot yet handle failures gracefully or debug complex workflow issues — error handling is covered in {ref}`Module 5 <tutorial:module5>`.

## Why workflows?

In the previous modules, we ran each step manually:
1. Submit a calculation
2. Wait for it to finish
3. Run post-processing

A **workflow** automates this: it defines the sequence of steps, passes data between them, and records the entire process in the provenance graph.

## WorkGraph: building a workflow as a graph

AiiDA's `WorkGraph` lets you define workflows as directed graphs where:
- **Tasks** are the computational steps (CalcJobs, calcfunctions)
- **Links** connect outputs of one task to inputs of another

### A minimal workflow

<!-- TODO: create a WorkGraph that runs the reaction-diffusion CalcJob -->
<!-- TODO: add a post-processing task that visualizes the result -->
<!-- TODO: link the CalcJob output to the visualization input -->

### Running the workflow

<!-- TODO: submit the WorkGraph -->
<!-- TODO: verdi process status to see the hierarchical execution -->
<!-- TODO: inspect the workflow's provenance graph -->

### Context variables

<!-- TODO: show how context variables pass data between steps -->
<!-- TODO: explain how this differs from direct node links -->

## Comparing: with and without a workflow

<!-- TODO: side-by-side comparison of the provenance graph -->
<!-- TODO: show how the workflow groups related steps together -->

## Next steps

We have a working workflow, but what happens when a calculation fails? In {ref}`Module 5 <tutorial:module5>`, you'll learn how to diagnose failures and build resilient workflows with error handlers.
