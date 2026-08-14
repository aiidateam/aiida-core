.. _tutorials:

*********
Tutorials
*********

These tutorials teach you the core concepts of AiiDA, from running a single
calculation to orchestrating multi-step, parallel workflows, using a running
example that progressively grows in complexity.

.. note::

   These tutorials are actively being iterated on and may still change. If you
   run into any problems or have suggestions for improvement, please open an
   issue on `GitHub <https://github.com/aiidateam/aiida-core/issues>`__; your
   feedback is very welcome.

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

      Run tracked calculations with aiida-shell and inspect the provenance AiiDA records for them.

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

More tutorials
==============

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`graduation-cap;mr-1` Basic tutorial
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

         Go to the basic tutorial

   .. grid-item-card:: :fa:`chalkboard-user;mr-1` Past AiiDA tutorials
      :text-align: center
      :shadow: md

      Material from AiiDA's in-person and virtual hands-on tutorials, held regularly since 2016, including recorded presentations and demonstrations.

      +++

      .. button-link:: https://aiida-tutorials.readthedocs.io/en/latest/
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Browse the material

.. toctree::
   :maxdepth: 1
   :hidden:

   module0
   module1
   module2
   module3a
   module3b
   basic
   Past AiiDA tutorials <https://aiida-tutorials.readthedocs.io/en/latest/>
