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

(tutorial:module2)=
# Module 2: Running Workflows

**Duration:** Half day (Day 1, afternoon)

## What you will learn

By the end of this module, you will be able to:

- Execute existing workflows with AiiDA
- Customize workflow inputs to fit your needs
- Use protocol-based setup with `get_builder_from_protocol()`
- Understand workflow configurations and nested structures
- Monitor workflow execution and status
- Run workflows on remote systems

## Prerequisites

- Completed {ref}`Module 1: Running External Code(s) <tutorial:module1>`
- Understanding of how to run simple calculations

<!--
```{code-cell} ipython3
:tags: ["hide-cell"]

# Setup for the tutorial
from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

%load_ext aiida

profile = load_profile(
    SqliteTempBackend.create_profile(
        'tutorial-module2',
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

Workflows in AiiDA orchestrate multiple calculations into automated pipelines. In this module, you'll learn how to run pre-built workflows and customize them for your research.

## Understanding workflows

[Content to be added]

## Running your first workflow

[Content to be added]

## Customizing workflow inputs

[Content to be added]

## Using protocols

[Content to be added]

## Monitoring workflow execution

[Content to be added]

## Next Steps

After completing this module, you'll have run several calculations and workflows. In {ref}`Module 3: Working with Data <tutorial:module3>`, you'll learn how to query, organize, and manage all the data you've generated.

:::{seealso}
- {ref}`How-to: run workflows <how-to:run-workflows>`
- {ref}`Topics: workflows <topics:workflows>`
- {ref}`Topics: provenance <topics:provenance>`
:::

## What we haven't covered yet

- Writing your own workflows (covered in {ref}`Module 4 <tutorial:module4>`)
- Advanced workflow patterns (error handlers, conditional logic)
- WorkChains vs WorkGraph (covered in Module 4)
-->
