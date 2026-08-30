.. _tutorials:

*********
Tutorials
*********

These tutorials teach you the core concepts of AiiDA, from running a single
calculation to orchestrating multi-step, parallel workflows, using a running
example that progressively grows in complexity.

.. note::

   These tutorials are actively being developed and may still change. If you
   run into any problems or have suggestions for improvement, please add a
   comment on the `tutorial feedback issue
   <https://github.com/aiidateam/aiida-core/issues/7590>`__ or start a thread
   on `Discourse <https://aiida.discourse.group/>`__; your feedback is very
   welcome.

Introductory modules
=====================

.. note::

   These four modules are designed to be worked through in order.
   Each builds on the previous one, so start with Module 0 if you are new to AiiDA.

.. raw:: html

   <p>Prefer to run them locally? <a href="aiida-tutorials.zip" download><strong>Download all notebooks (.zip)</strong></a>, then extract them into one folder and run in order.</p>

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

      Turn opaque outputs into structured, queryable data with calcfunctions and full provenance tracking.

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

      Chain calculations into an automated workflow with WorkGraph (3a), then run it over many inputs in parallel with ``Map`` (3b).

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

.. note::

   The running example continues beyond the basics. These modules are being
   finalized and will be added soon.

.. grid:: 2 2 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`server;mr-1` Module 4: Remote submission
      :text-align: center
      :shadow: md

      Run calculations on remote HPC clusters with schedulers, transports, and queue management.

      +++

      :bdg-secondary:`Coming soon`

   .. grid-item-card:: :fa:`magnifying-glass-chart;mr-1` Module 5: Querying and analysis
      :text-align: center
      :shadow: md

      Use the QueryBuilder to search, filter, and analyze your provenance graph at scale.

      +++

      :bdg-secondary:`Coming soon`

   .. grid-item-card:: :fa:`code-branch;mr-1` Module 6: Complex workflows
      :text-align: center
      :shadow: md

      Branch and loop on results with ``If``/``While`` (6a); then build a workflow that adapts its own later steps from earlier outputs (6b).

      +++

      :bdg-secondary:`Coming soon`

   .. grid-item-card:: :fa:`compass;mr-1` Module 7: Where to go next
      :text-align: center
      :shadow: md

      Error handlers, CalcJob plugins, WorkChains, caching, and a map of the wider plugin ecosystem.

      +++

      :bdg-secondary:`Coming soon`

More tutorials
==============

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`graduation-cap;mr-1` A provenance deep dive
      :text-align: center
      :shadow: md

      An in-depth, hands-on tour of AiiDA's provenance model and core concepts (data nodes, calcfunctions, CalcJobs, workflows), using simple arithmetic examples.

      +++

      .. button-ref:: basic
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to the deep dive

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

Where to go next
================

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`atom;mr-1` Quantum ESPRESSO with AiiDA
      :text-align: center
      :shadow: md

      AiiDA workflows for running Quantum ESPRESSO, from single SCF calculations to automated band structures.

      +++

      .. button-link:: https://aiida-quantumespresso.readthedocs.io/
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Go to aiida-quantumespresso

   .. grid-item-card:: :fa:`plug;mr-1` AiiDA plugin registry
      :text-align: center
      :shadow: md

      A directory of plugins that connect AiiDA to other simulation codes and tools.

      +++

      .. button-link:: https://aiida.net/plugin-registry/
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Browse the registry


.. toctree::
   :maxdepth: 1
   :hidden:

   module0
   module1
   module2
   module3a
   module3b
   module4
   module5
   module6a
   module6b
   module7
