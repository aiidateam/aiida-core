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
    timeout: 180
---

(tutorial:module6)=
# Module 6: Real Plugins & High-Throughput Computing

**Duration:** Half day (Day 3, afternoon)

## What you will learn

By the end of this module, you will be able to:

- Work with flagship AiiDA plugins (e.g., `aiida-quantumespresso`)
- Run workflows with real computational codes (QE, CP2K, etc.)
- Navigate plugin-specific documentation
- Submit multiple calculations efficiently
- Manage large datasets with groups
- Use advanced QueryBuilder techniques for large-scale data
- Design high-throughput screening workflows

## Prerequisites

- Completed all previous modules
- Access to a computational code (or use provided examples)
- Understanding of workflows and data management

<!--
```{code-cell} ipython3
:tags: ["hide-cell"]

# Setup for the tutorial
from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

%load_ext aiida

profile = load_profile(
    SqliteTempBackend.create_profile(
        'tutorial-module6',
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

You've learned the fundamentals of AiiDA. Now it's time to apply them to real-world scenarios with production-ready plugins and high-throughput computing!

## Working with aiida-quantumespresso

[Content to be added]

### Installing and setting up

[Content to be added]

### Running a simple QE calculation

[Content to be added]

### Running QE workflows

[Content to be added]

## Understanding plugin-specific documentation

[Content to be added]

## High-throughput computing strategies

[Content to be added]

### Submitting multiple calculations

[Content to be added]

### Managing large datasets

[Content to be added]

### Advanced querying for high-throughput

[Content to be added]

## Designing screening workflows

[Content to be added]

## Best practices for production use

[Content to be added]

## Exploring the plugin ecosystem

[Content to be added]

## Congratulations!

You've completed the AiiDA tutorial! You now have the skills to:

- Run calculations and workflows with AiiDA
- Manage and query your computational data
- Write your own workflows
- Debug issues when they arise
- Work with production plugins
- Scale up to high-throughput computing

## Next Steps

- Explore the {ref}`AiiDA plugin registry <reference:plugins>` for your favorite codes
- Join the [AiiDA community on Discourse](https://aiida.discourse.group/)
- Check out [AiiDAlab](https://www.materialscloud.org/work/aiidalab) for GUI-based workflows
- Read the {ref}`how-to guides <how-to>` for advanced topics
- Consider contributing to the AiiDA ecosystem!

:::{seealso}
- [aiida-quantumespresso documentation](https://aiida-quantumespresso.readthedocs.io/)
- {ref}`Plugin registry <reference:plugins>`
- [AiiDA Discourse forum](https://aiida.discourse.group/)
- [Materials Cloud](https://www.materialscloud.org/)
:::

## What we haven't covered

Some advanced topics for further exploration:

- Writing your own CalcJob plugins
- Creating a complete plugin package
- Advanced WorkChain patterns
- REST API development
- Integration with external tools and databases
- Contributing to AiiDA core

These topics are covered in the {ref}`how-to guides <how-to>` and {ref}`developer documentation <internal_architecture>`.
-->
