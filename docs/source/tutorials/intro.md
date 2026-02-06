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
    timeout: 60
---

(tutorial:intro)=
# Introduction & Teaser

**Duration:** 1 hour

## What you will learn

By the end of this session, you will understand:

- What AiiDA is and what problems it solves for computational scientists
- How AiiDA tracks provenance automatically
- How to run a basic workflow (Equation of State with ASE)
- AiiDA's top-level architecture and key concepts (nodes, processes, provenance graph)
- AiiDAlab: How to use GUI-based interfaces for computational workflows

## What this session is for

This teaser session is designed to help you decide whether AiiDA fits your needs.

<!--
After watching this demonstration, you'll have a clear picture of AiiDA's capabilities and can decide if you want to continue with the full tutorial.

## Overview

AiiDA (Automated Interactive Infrastructure and Database for Computational Science) is a Python framework that helps you:

- **Run computational workflows** on local and remote computers
- **Automatically track provenance** of all your calculations and data
- **Query and analyze** your computational results
- **Reproduce** your work and share it with collaborators
- **Scale up** from a few calculations to thousands

:::{tip}
This session will be a live demonstration. You don't need to have AiiDA installed yet to attend!
:::

## Live Demonstration: Equation of State Workflow

In this demo, we'll run a complete workflow that:

1. Takes a crystal structure as input
2. Performs calculations at different volumes
3. Fits the results to an equation of state
4. Extracts bulk modulus and equilibrium volume

All of this will be done with full provenance tracking!

```{code-cell} ipython3
:tags: ["hide-cell"]

# Setup code for the demo (hidden from users)
from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

%load_ext aiida

profile = load_profile(
    SqliteTempBackend.create_profile(
        'tutorial-intro',
        options={
            'warnings.development_version': False,
            'runner.poll.interval': 1
        },
        debug=False
    ),
    allow_switch=True
)
```

### Setting up the structure

```{code-cell} ipython3
from ase import Atoms
from aiida.orm import StructureData

# Create a simple silicon structure
silicon_ase = Atoms('Si2', positions=[(0, 0, 0), (1.35, 1.35, 1.35)], cell=[2.7, 2.7, 2.7], pbc=True)

# Store it in AiiDA
structure = StructureData(ase=silicon_ase)
structure.store()

print(f"Stored structure with PK: {structure.pk}")
```

### Running the workflow

```{code-cell} ipython3
# Demo: Run an EOS workflow here
# This section will be filled in with the actual workflow demonstration
# For now, this is a placeholder

print("In the live demo, we will:")
print("1. Set up an ASE calculator")
print("2. Run the EOS workflow")
print("3. Visualize the results")
print("4. Explore the provenance graph")
```

## Key Concepts Introduced

### Nodes

Everything in AiiDA is a **node**:
- **Data nodes**: Store your data (structures, parameters, results)
- **Process nodes**: Record calculations and workflows
- **Code nodes**: Represent the codes you run

### Provenance

AiiDA automatically tracks:
- What data was used as input
- What code processed it
- What outputs were produced
- Who ran it and when

This creates a complete, queryable history of your research!

### Workflows

Combine multiple calculations into automated pipelines that can:
- Handle complex multi-step procedures
- Recover from errors automatically
- Run on remote HPC systems
- Scale to thousands of calculations

## AiiDAlab: Workflows with a GUI

AiiDAlab provides graphical interfaces for AiiDA workflows:

- No programming required for running complex workflows
- Interactive structure editors and result viewers
- Example: AiiDAlab-QE for Quantum ESPRESSO calculations
- Access through Jupyter notebooks in your browser

:::{note}
AiiDAlab demo will be shown live during the session.
:::

## Next Steps

After this teaser, you can:

1. **Continue to Module 1**: Learn to run external codes with AiiDA
2. **Install AiiDA**: Follow the {ref}`installation guide <installation>` and join the installation support session
3. **Explore the ecosystem**: Check out {ref}`available plugins <reference:plugins>` for your favorite codes

:::{seealso}
- {ref}`AiiDA documentation homepage <index>`
- {ref}`Installation guide <installation>`
- {ref}`How-to guides <how-to>`
- [AiiDA tutorials repository](https://github.com/aiidateam/aiida-tutorials)
:::

## What we haven't covered yet

This was just a taste! The main tutorial modules will teach you:
- How to set up and run codes yourself
- How to query and organize your data
- How to write your own workflows
- How to debug when things go wrong
- How to work with production-ready plugins
- How to scale up to high-throughput computing
-->
