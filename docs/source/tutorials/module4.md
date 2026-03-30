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
# Module 4: Building Workflows

## What you will learn

After this module, you will be able to:

- Build a workflow as a graph of tasks using WorkGraph
- Chain calculations together (simulate → parse → post-process)
- Pass data between tasks using context variables
- Add simple branching logic to a workflow

## What you will not learn yet

You cannot yet handle failures gracefully or debug complex workflow issues — error handling is covered in {ref}`Module 5 <tutorial:module5>`.

## Why workflows?

<!-- TODO: motivate: manual step-by-step is tedious and error-prone -->
<!-- TODO: a workflow automates the sequence, passes data, records provenance -->

## WorkGraph basics

:::{tip}
Any function decorated with `@calcfunction` (from {ref}`Module 1 <tutorial:module1>`) can be used directly as a WorkGraph task — just pass it to `wg.add_task()`.
No additional decorator is needed.

You may see `@task.calcfunction` in aiida-workgraph documentation.
This is only needed when you want extra features like custom socket specs or attaching error handlers directly in the decorator.
For most use cases, a plain `@calcfunction` works.
:::

<!-- TODO: introduce WorkGraph: tasks (CalcJob, calcfunction) + links -->
<!-- TODO: create a minimal WorkGraph with one task -->
<!-- TODO: run it and inspect the result -->

## Chaining calculations

<!-- TODO: build a workflow: simulate → parse → post-process (visualize) -->
<!-- TODO: link outputs of one task to inputs of the next -->
<!-- TODO: run the multi-step workflow -->
<!-- TODO: inspect the hierarchical provenance graph -->

## Context variables for data flow

<!-- TODO: show how context variables pass data between tasks -->
<!-- TODO: explain when to use context vs direct links -->

## Simple branching

<!-- TODO: add conditional logic: skip visualization if variance is below threshold -->
<!-- TODO: run and inspect the branching workflow -->

## Comparing: with and without a workflow

<!-- TODO: side-by-side provenance graph comparison -->
<!-- TODO: show how the workflow groups related steps together -->

## Summary

In this module you learned to:

- **Build** workflows with WorkGraph
- **Chain** calculations together
- **Pass data** between tasks using context variables
- **Branch** workflow logic based on conditions

## Next steps

We have a working workflow, but what happens when a calculation fails? In {ref}`Module 5 <tutorial:module5>`, you'll learn how to diagnose failures and build resilient workflows with error handlers.
