.. _tutorials:

*********
Tutorials
*********

These tutorials teach you the core concepts of AiiDA, from running a single
calculation to orchestrating multi-step, parallel workflows, using a running
example that progressively grows in complexity.

Introductory modules
=====================

.. note::

   These four modules are designed to be worked through in order.
   Each builds on the previous one, so start with Module 0 if you are new to AiiDA.

.. grid:: 2 2 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`flask;mr-1` Module 0: Calculations without AiiDA
      :text-align: center
      :shadow: md

      Run a simulation the traditional way and discover the pain points AiiDA is built to solve.

      +++

      .. button-ref:: module0
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 0

   .. grid-item-card:: :fa:`circle-play;mr-1` Module 1: Calculations with AiiDA
      :text-align: center
      :shadow: md

      Run tracked calculations with aiida-shell, inspect provenance, and handle failures.

      +++

      .. button-ref:: module1
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 1

   .. grid-item-card:: :fa:`cubes;mr-1` Module 2: Structured data and calcfunctions
      :text-align: center
      :shadow: md

      Data types, calcfunctions, and parameter sweeps with full provenance tracking.

      +++

      .. button-ref:: module2
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 2

   .. grid-item-card:: :fa:`diagram-project;mr-1` Module 3: Writing workflows
      :text-align: center
      :shadow: md

      Chain calculations into an automated workflow with WorkGraph (3a), then run it over many inputs in parallel with ``Map``, no hand-written ``for``-loop (3b).

      +++

      .. button-ref:: module3a
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 3

Advanced modules
================

.. admonition:: Under development
   :class: seealso

   The running example continues beyond the basics, onto remote HPC resources,
   querying at scale, adaptive workflows, and robust error handling. These
   modules are being finalized and will land here soon.

Classic tutorial
================

.. grid:: 1 2 2 3
   :gutter: 3

   .. grid-item-card:: :fa:`graduation-cap;mr-1` Basic Tutorial
      :text-align: center
      :shadow: md

      A self-contained introduction to core AiiDA concepts using simple arithmetic examples.

      +++

      .. button-ref:: basic
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Basic Tutorial

.. toctree::
   :maxdepth: 1
   :hidden:

   module0
   module1
   module2
   module3a
   module3b
   basic
