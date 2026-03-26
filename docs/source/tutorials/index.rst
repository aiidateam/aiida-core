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

   .. grid-item-card:: :fa:`bolt;mr-1` AiiDA in Action
      :text-align: center
      :shadow: md

      See the full power of AiiDA in a quick demo — then learn to build it yourself.

      +++

      .. button-ref:: intro
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         See the demo

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

   .. grid-item-card:: :fa:`code;mr-1` Module 2: Running External Codes
      :text-align: center
      :shadow: md

      Run codes with aiida-shell and CalcJobs, write parsers, and handle exit codes.

      +++

      .. button-ref:: module2
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 2

   .. grid-item-card:: :fa:`cubes;mr-1` Module 3: Working with Your Data
      :text-align: center
      :shadow: md

      Store data, query with QueryBuilder, organize with Groups, and export archives.

      +++

      .. button-ref:: module3
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 3

   .. grid-item-card:: :fa:`diagram-project;mr-1` Module 4: Building Workflows
      :text-align: center
      :shadow: md

      Chain calculations into automated workflows with WorkGraph.

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

   .. grid-item-card:: :fa:`chart-bar;mr-1` Module 6: High-Throughput & Post-Processing
      :text-align: center
      :shadow: md

      Run parameter sweeps, analyze trends, and create publication-quality plots.

      +++

      .. button-ref:: module6
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 6

   .. grid-item-card:: :fa:`flask;mr-1` Module 7: Advanced Topics
      :text-align: center
      :shadow: md

      Multi-parameter sweeps, remote HPC execution, daemon, and more (optional).

      +++

      .. button-ref:: module7
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to Module 7

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
