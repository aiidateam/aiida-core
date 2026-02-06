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
execution:
    timeout: 120
---

(tutorial:module3)=
# Module 3: Working with Data

**Duration:** Half day (Day 2, morning)

## What you will learn

By the end of this module, you will be able to:

- Navigate the AiiDA database with QueryBuilder
- Query and filter data efficiently
- Organize data with Groups
- Export and import data for sharing and backup
- Understand and visualize provenance graphs
- Access and inspect remote calculation data
- Work with different AiiDA data types

## Prerequisites

- Completed {ref}`Module 1 <tutorial:module1>` and {ref}`Module 2 <tutorial:module2>`
- Have data from calculations and workflows in your database

<!--
```{code-cell} ipython3
:tags: ["hide-cell"]

# Setup for the tutorial
from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

%load_ext aiida

profile = load_profile(
    SqliteTempBackend.create_profile(
        'tutorial-module3',
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

By now, you've run calculations and workflows that have generated data in your AiiDA database. In this module, you'll learn how to find, organize, and manage that data effectively.

## Understanding AiiDA's data model

[Content to be added]

## Querying data with QueryBuilder

[Content to be added]

## Organizing data with Groups

[Content to be added]

## Exploring provenance graphs

[Content to be added]

## Exporting and importing data

[Content to be added]

## Accessing remote data

[Content to be added]

## Working with different data types

[Content to be added]

## Next Steps

Now that you can manage your data, proceed to {ref}`Module 4: Writing Workflows <tutorial:module4>` to learn how to create your own automated workflows.

:::{seealso}
- {ref}`How-to: query the database <how-to:query>`
- {ref}`How-to: share data <how-to:share-data>`
- {ref}`Topics: provenance <topics:provenance>`
- {ref}`Topics: data types <topics:data_types>`
:::

## What we haven't covered yet

- Writing custom data types (covered in {ref}`how-to guides <how-to>`)
- Advanced QueryBuilder features (aggregation, etc.)
- REST API for accessing data
- Provenance browser on Materials Cloud
-->
