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

(tutorial:module1)=
# Module 1: Running External Code(s)

**Duration:** Half day (Day 1, morning)

## What you will learn

By the end of this module, you will be able to:

- Set up and configure computers in AiiDA (localhost and remote)
- Register codes and executables
- Understand the role of plugins in AiiDA
- Use `aiida-shell` to run simple command-line executables
- Use `aiida-pythonjob` to run Python functions as AiiDA calculations
- Run calculations on remote HPC systems
- Monitor calculation status

## Prerequisites

- AiiDA installed and profile configured
- Basic familiarity with the command line
- Basic Python knowledge

<!--
:::{important}
Make sure you have completed the {ref}`installation <installation>` before starting this module.
:::

```{code-cell} ipython3
:tags: ["hide-cell"]

# Setup for the tutorial
from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

%load_ext aiida

profile = load_profile(
    SqliteTempBackend.create_profile(
        'tutorial-module1',
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

AiiDA allows you to run external codes and executables while automatically tracking all inputs, outputs, and provenance. In this module, you'll learn how to set up and run calculations with external codes.

## Setting up a computer

[Content to be added]

## Registering a code

[Content to be added]

## Using aiida-shell

[Content to be added]

## Using aiida-pythonjob

[Content to be added]

## Running calculations remotely

[Content to be added]

## Next Steps

After completing this module, proceed to {ref}`Module 2: Running Workflows <tutorial:module2>` to learn how to run pre-built workflows that orchestrate multiple calculations.

:::{seealso}
- {ref}`How-to: run external codes <how-to:run-codes>`
- {ref}`Topics: calculations <topics:calculations>`
- [aiida-shell documentation](https://aiida-shell.readthedocs.io/)
:::

## What we haven't covered yet

- Writing your own CalcJob plugins (covered in {ref}`how-to guides <how-to>`)
- Advanced remote computer configuration
- Scheduler configuration for different HPC systems
-->
