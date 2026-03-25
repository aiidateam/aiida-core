.. _tutorials:

**********
Tutorials
**********

The tutorials teach you the core concepts of AiiDA through a complete
**reaction-diffusion simulation** (Gray-Scott model) that progressively grows
in complexity.  Each module builds on the previous one — start with the
Introduction and work through the modules in order.

Reaction-Diffusion Tutorial
============================

.. grid:: 1 2 2 3
   :gutter: 3

   .. grid-item-card:: :fa:`map;mr-1` Introduction
      :text-align: center
      :shadow: md

      The Gray-Scott model, simulation inputs and outputs, and the full tutorial roadmap.

      +++

      .. button-ref:: intro
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Get started

   .. grid-item-card:: :fa:`circle-play;mr-1` Module 1: Running a Simulation
      :text-align: center
      :shadow: md

      Store data, run a tracked calculation, and explore the provenance graph.

      +++

      .. button-ref:: module1
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 1

   .. grid-item-card:: :fa:`code;mr-1` Module 2: Parsing Outputs
      :text-align: center
      :shadow: md

      Extract structured results from output files and handle exit codes.

      +++

      .. button-ref:: module2
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 2

   .. grid-item-card:: :fa:`cubes;mr-1` Module 3: Data Types
      :text-align: center
      :shadow: md

      Store arrays, scalars, and parameters using AiiDA's native data types.

      +++

      .. button-ref:: module3
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 3

   .. grid-item-card:: :fa:`diagram-project;mr-1` Module 4: Workflow Basics
      :text-align: center
      :shadow: md

      Build automated workflows with WorkGraph and chain calculations together.

      +++

      .. button-ref:: module4
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 4

   .. grid-item-card:: :fa:`wrench;mr-1` Module 5: Error Handling
      :text-align: center
      :shadow: md

      Debug failed calculations and implement automatic error recovery handlers.

      +++

      .. button-ref:: module5
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 5

   .. grid-item-card:: :fa:`chart-bar;mr-1` Module 6: High-Throughput Scans
      :text-align: center
      :shadow: md

      Run parameter sweeps, query results with QueryBuilder, and organize with Groups.

      +++

      .. button-ref:: module6
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 6

   .. grid-item-card:: :fa:`chart-line;mr-1` Module 7: Post-Processing
      :text-align: center
      :shadow: md

      Analyze trends across simulations, create plots, and export archives.

      +++

      .. button-ref:: module7
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 7

   .. grid-item-card:: :fa:`flask;mr-1` Module 8: Advanced Topics
      :text-align: center
      :shadow: md

      Multi-parameter sweeps, MPI execution, FFT analysis, and more (optional).

      +++

      .. button-ref:: module8
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 8

Classic Tutorial
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

   intro
   basic
   module1
   module2
   module3
   module4
   module5
   module6
   module7
   module8
