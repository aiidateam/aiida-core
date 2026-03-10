.. _tutorials:

**********
Tutorials
**********

Welcome to the AiiDA tutorials! These tutorials are designed to help you learn AiiDA step by step, from basic concepts to advanced workflows.

.. note::

   These tutorials are intended for users who want to *use* AiiDA to run and manage computational workflows. If you are interested in developing AiiDA plugins, see the :ref:`how-to guides <how-to>`.

.. admonition:: Prerequisites
   :class: important

   Before starting the tutorials, you should have:

   - A working AiiDA installation (see :ref:`installation guide <installation>`)
   - Basic Python scripting knowledge
   - Familiarity with the command line/terminal
   - An AiiDA profile set up in your current Python environment

Getting Started
===============

We recommend starting with the **Introduction & Teaser** to see what AiiDA can do, then proceeding through the modules in order.

Pre-Sessions
============

.. grid:: 1
   :gutter: 3

   .. grid-item-card:: :fa:`rocket;mr-1` Introduction & Teaser
      :link: tutorial:intro
      :link-type: ref

      **Duration:** 1 hour

      A live demonstration showcasing AiiDA's capabilities to help you decide if it fits your needs.

      **What you will learn:**

      - What AiiDA is and what problems it solves
      - How to run a basic workflow (Equation of State)
      - Overview of AiiDA's architecture and key concepts
      - Introduction to provenance tracking
      - AiiDAlab: GUI-based workflow execution

   .. grid-item-card:: :fa:`wrench;mr-1` Installation & Setup Support
      :link: installation
      :link-type: ref

      **Duration:** Self-paced with support session

      Instructions for installing AiiDA on your machine, with dedicated support sessions to help troubleshoot.

      **What you will learn:**

      - How to install AiiDA (see :ref:`installation guide <installation>`)
      - Setting up the AiiDA daemon
      - Environment configuration

Main Tutorial Modules
======================

.. grid:: 1 1 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`play;mr-1` Module 1: Running External Code(s)
      :link: tutorial:module1
      :link-type: ref

      **Duration:** Half day (Day 1, morning)

      Learn how to run external codes and executables with AiiDA.

      **What you will learn:**

      - Set up computers and codes
      - Understand the role of plugins
      - Use ``aiida-shell`` for simple executables
      - Use ``aiida-pythonjob`` for Python calculations
      - Run calculations on remote HPC systems

   .. grid-item-card:: :fa:`list;mr-1` Module 2: Running Workflows
      :link: tutorial:module2
      :link-type: ref

      **Duration:** Half day (Day 1, afternoon)

      Run pre-built workflows and learn to customize them for your needs.

      **What you will learn:**

      - Execute existing workflows
      - Customize workflow inputs
      - Use protocol-based setup
      - Monitor workflow execution
      - Run workflows on remote systems

   .. grid-item-card:: :fa:`database;mr-1` Module 3: Working with Data
      :link: tutorial:module3
      :link-type: ref

      **Duration:** Half day (Day 2, morning)

      Learn to query, organize, and manage your computational data.

      **What you will learn:**

      - Navigate the AiiDA database with QueryBuilder
      - Organize data with Groups
      - Export and import data
      - Understand provenance graphs
      - Access and inspect remote data

   .. grid-item-card:: :fa:`code;mr-1` Module 4: Writing Workflows
      :link: tutorial:module4
      :link-type: ref

      **Duration:** Half day (Day 2, afternoon)

      Create your own workflows using WorkGraph.

      **What you will learn:**

      - Write simple linear workflows
      - Implement conditional logic and branching
      - Use calculation and work functions
      - Design modular, reusable workflows
      - Debug workflow logic

   .. grid-item-card:: :fa:`bug;mr-1` Module 5: Debugging & Error Handling
      :link: tutorial:module5
      :link-type: ref

      **Duration:** Half day (Day 3, morning)

      Master debugging techniques and error handling strategies.

      **What you will learn:**

      - Diagnose failed calculations
      - Inspect calculation inputs and outputs
      - Use process reports and logs
      - Implement error handlers
      - Common errors and how to fix them

   .. grid-item-card:: :fa:`fire;mr-1` Module 6: Real Plugins & High-Throughput
      :link: tutorial:module6
      :link-type: ref

      **Duration:** Half day (Day 3, afternoon)

      Work with production plugins and scale up your computations.

      **What you will learn:**

      - Use flagship plugins (``aiida-quantumespresso``)
      - Run workflows with real computational codes
      - Submit multiple calculations efficiently
      - Manage large datasets
      - Advanced querying techniques

.. toctree::
   :maxdepth: 1
   :hidden:

   intro
   module1
   module2
   module3
   module4
   module5
   module6
