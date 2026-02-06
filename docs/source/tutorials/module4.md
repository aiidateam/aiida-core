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
# Module 4: Writing Workflows

**Duration:** Half day (Day 2, afternoon)

## What you will learn

By the end of this module, you will be able to:

- Write simple linear workflows with WorkGraph
- Implement conditional logic and branching
- Use calculation functions and work functions
- Design modular, reusable workflow components
- Debug workflow logic
- Understand the differences between WorkGraph and WorkChains

## Prerequisites

- Completed {ref}`Module 2: Running Workflows <tutorial:module2>`
- Understanding of how workflows work
- Basic Python programming skills

<!--
```{code-cell} ipython3
:tags: ["hide-cell"]

# Setup for the tutorial
from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

%load_ext aiida

profile = load_profile(
    SqliteTempBackend.create_profile(
        'tutorial-module4',
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

Now that you've seen how to run workflows, it's time to create your own! In this module, you'll learn to write workflows using WorkGraph, AiiDA's modern workflow tool.

## Introduction to WorkGraph

[Content to be added]

## Your first workflow: A simple linear example

[Content to be added]

## Calculation functions

[Content to be added]

## Work functions

[Content to be added]

## Adding conditional logic

[Content to be added]

## Building modular workflows

[Content to be added]

## Debugging workflows

[Content to be added]

## Next Steps

After learning to write workflows, proceed to {ref}`Module 5: Debugging & Error Handling <tutorial:module5>` to master debugging techniques and error recovery strategies.

:::{seealso}
- {ref}`How-to: write workflows <how-to:write-workflows>`
- {ref}`Topics: workflows <topics:workflows>`
- [WorkGraph documentation](https://aiida-workgraph.readthedocs.io/)
:::

## What we haven't covered yet

- Writing WorkChains (classical approach, covered in {ref}`how-to guides <how-to>`)
- Advanced WorkGraph features (while loops, context, etc.)
- Error handlers (covered in {ref}`Module 5 <tutorial:module5>`)
- Publishing workflows as plugins
-->
