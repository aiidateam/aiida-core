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

(tutorial:module5)=
# Module 5: Debugging & Error Handling

**Duration:** Half day (Day 3, morning)

## What you will learn

By the end of this module, you will be able to:

- Diagnose failed calculations systematically
- Inspect calculation inputs and outputs
- Use `verdi calcjob` commands for debugging
- Read and interpret process reports and logs
- Implement error handlers for automatic recovery
- Recognize and fix common errors
- Use provenance to troubleshoot issues

## Prerequisites

- Completed previous modules
- Experience running calculations and workflows
- Some failed calculations to debug (we'll create them!)

<!--
```{code-cell} ipython3
:tags: ["hide-cell"]

# Setup for the tutorial
from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

%load_ext aiida

profile = load_profile(
    SqliteTempBackend.create_profile(
        'tutorial-module5',
        options={
            'warnings.development_version': False,
            'runner.poll.interval': 1
        },
        debug=False
    ),
    allow_switch=True
)
```

## Introduction

Things don't always go as planned! In this module, you'll learn how to debug calculations and workflows when they fail, and how to implement automatic error recovery.

## Understanding process states

[Content to be added]

## Inspecting failed calculations

[Content to be added]

## Using verdi calcjob commands

[Content to be added]

### verdi calcjob inputcat

[Content to be added]

### verdi calcjob outputcat

[Content to be added]

### verdi calcjob gotocomputer

[Content to be added]

## Reading process reports

[Content to be added]

## Using provenance for debugging

[Content to be added]

## Common errors and solutions

[Content to be added]

## Implementing error handlers

[Content to be added]

## Next Steps

With debugging skills mastered, proceed to {ref}`Module 6: Real Plugins & High-Throughput <tutorial:module6>` to work with production-ready plugins and scale up your computations.

:::{seealso}
- {ref}`How-to: debug workflows <how-to:debug-workflows>`
- {ref}`Topics: error handling <topics:error_handling>`
- {ref}`Reference: process states <reference:process_states>`
:::

## What we haven't covered yet

- Writing custom error handlers for plugins
- Advanced debugging with Python debugger (pdb)
- Remote debugging techniques
- Performance profiling
-->
