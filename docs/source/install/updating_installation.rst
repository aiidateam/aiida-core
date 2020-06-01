.. _updating_aiida:

**************
Updating AiiDA
**************
.. _updating_instructions:

Generic update instructions
===========================

1. Enter the python environment where AiiDA is installed
2. Finish all running calculations. After migrating your database, you will not be able to resume unfinished calculations. Data of finished calculations will of course be automatically migrated.
3. Stop the daemon using ``verdi daemon stop``
4. :ref:`Create a backup of your database and repository<backup>`

.. warning::

    Once you have migrated your database, you can no longer go back to an older version of ``aiida-core`` (unless you restore your database and repository from a backup).

5. Update your ``aiida-core`` installation

    - If you have installed AiiDA through ``pip`` simply run: ``pip install --upgrade aiida-core``
    - If you have installed from the git repository using ``pip install -e .``, first delete all the ``.pyc`` files (``find . -name "*.pyc" -delete``) before updating your branch.

6. Migrate your database with ``verdi -p <profile_name> database migrate``.
   Depending on the size of your database and the number of migrations to perform, data migration can take time, so please be patient.

After the database migration finishes, you will be able to continue working with your existing data.

.. note::
    If your update involved a change in the major version number of ``aiida-core``, expect :ref:`backwards incompatible changes<updating_backward_incompatible_changes>` and check whether you also need to update your installed plugin packages.


Updating from 0.12.* to 1.*
===========================

Besides the generic update instructions, the following applies:

 * Finish all running legacy workflows.
   The legacy workflows are completely deprecated and all data will be removed from your database, so make sure to create a backup (see point 5).
 * The upgrade involves several long-running migrations. Migrating databases containing millions of nodes can take a few hours.

.. _updating_backward_incompatible_changes:

Breaking changes from 0.12.* to 1.*
===================================

The following list covers the most important backward incompatible changes between ``aiida-core==0.12.*`` and ``aiida-core==1.0.0``.

General
-------

-  Reorganization of some second-level modules. Various classes and functions have been moved, renamed or replaced. See :ref:`this page <python_api_public_list>` for the rules on the publicness of parts of the python API `[#2357] <https://github.com/aiidateam/aiida-core/pull/2357>`__
-  The module ``aiida.work`` has been renamed to ``aiida.engine`` and reorganized significantly `[#2524] <https://github.com/aiidateam/aiida-core/pull/2524>`__
-  The module ``aiida.scheduler`` has been renamed to ``aiida.schedulers`` `[#2498] <https://github.com/aiidateam/aiida-core/pull/2498>`__
-  The module ``aiida.transport`` has been renamed to ``aiida.transports`` `[#2498] <https://github.com/aiidateam/aiida-core/pull/2498>`__
-  The module ``aiida.utils`` has been removed and its contents have been placed in other places where appropriate `[#2357] <https://github.com/aiidateam/aiida-core/pull/2357>`__
-  Requirements were moved from ``setup_requirements.py`` to ``setup.json`` `[#2307] <https://github.com/aiidateam/aiida-core/pull/2307>`__


ORM
---

In order to define a clearer interface for users to the AiiDA entities, and allow (in the future) to swap between different profiles, the underlying hierarchy of nodes and links has been reworked (and a new paradigm has been implemented, with a "frontend" class that all users will interact with, and a "backend" class that users should never use directly, that implements the interaction to the database with a common interface, independent of the underlying ORM).
The reorganisation of nodes and linktypes is mostly invisible to the user, but existing import statements will need to be updated.

-  Refactoring the ORM `[#2190] <https://github.com/aiidateam/aiida-core/pull/2190>`__\ `[#2210] <https://github.com/aiidateam/aiida-core/pull/2210>`__\ `[#2227] <https://github.com/aiidateam/aiida-core/pull/2227>`__\ `[#2225] <https://github.com/aiidateam/aiida-core/pull/2225>`__\ `[#2481] <https://github.com/aiidateam/aiida-core/pull/#2481>`__\ `[#2544] <https://github.com/aiidateam/aiida-core/pull/2544>`__
-  Renamed the node classes for the various process types
-  ``WorkCalculation`` to ``WorkChainNode`` `[#2192] <https://github.com/aiidateam/aiida-core/pull/2192>`__
-  ``FunctionCalculation`` to ``WorkFunctionNode`` `[#2189] <https://github.com/aiidateam/aiida-core/pull/2189>`__
-  ``JobCalculation`` to ``CalcJobNode`` `[#2184] <https://github.com/aiidateam/aiida-core/pull/2184>`__ `[#2201] <https://github.com/aiidateam/aiida-core/pull/2201>`__
-  ``InlineCalculation`` to ``CalcFunctionNode`` `[#2195] <https://github.com/aiidateam/aiida-core/pull/2195>`__
-  Reorganization of the ``aiida.orm`` module, all node sub classes are now located under ``aiida.orm.nodes`` `[#2402] <https://github.com/aiidateam/aiida-core/pull/2402>`__\ `[#2497] <https://github.com/aiidateam/aiida-core/pull/2497>`__
-  Make ``Code`` a real sub class of ``Data`` `[#2193] <https://github.com/aiidateam/aiida-core/pull/2193>`__
-  Implement new link types `[#2220] <https://github.com/aiidateam/aiida-core/pull/2220>`__

    -  ``CREATE``: ``CalculationNode -> Data``
    -  ``RETURN``: ``WorkflowNode -> Data``
    -  ``INPUT_CALC``: ``Data -> CalculationNode``
    -  ``INPUT_WORK``: ``Data -> WorkflowNode``
    -  ``CALL_CALC``: ``WorkflowNode -> CalculationNode``
    -  ``CALL_WORK``: ``WorkflowNode -> WorkflowNode``

-  Moved the plugin factories to ``aiida.plugins.factories`` `[#2498] <https://github.com/aiidateam/aiida-core/pull/2498>`__
-  Methods that operated on the repository of a ``Node`` instance have been moved to a ``Repository`` utility that is exposed through the ``Node.repository`` property `[#2506] <https://github.com/aiidateam/aiida-core/pull/2506>`__
-  Removed the ``Error`` data sub class and its entry point `[#2529] <https://github.com/aiidateam/aiida-core/pull/2529>`__
-  Removed the ``FrozenDict`` data sub class and its entry point `[#2532] <https://github.com/aiidateam/aiida-core/pull/2532>`__
-  Renamed the ``ParameterData`` data sub class to ``Dict`` `[#2517] <https://github.com/aiidateam/aiida-core/pull/2517>`__


``QueryBuilder``
----------------

-  Changed relationship indicator keywords, e.g. ``input_of`` is now ``with_outgoing``. `[#2224] <https://github.com/aiidateam/aiida-core/pull/2224>`__\ `[#2278] <https://github.com/aiidateam/aiida-core/pull/2278>`__
-  Changed type of UUIDs returned by the ``QueryBuilder`` to always be of type unicode `[#2259] <https://github.com/aiidateam/aiida-core/pull/2259>`__


``Group``
---------

-  Change group type strings `[#2329] <https://github.com/aiidateam/aiida-core/pull/2329>`__

    -  ``data.upf.family`` to ``data.upf``
    -  ``aiida.import`` to ``auto.import``
    -  ``autogroup.run`` to ``auto.run``
    -  custom ones to ``user``

-  Remove ``Group.query`` and ``Group.group_query`` methods have been removed `[#2329] <https://github.com/aiidateam/aiida-core/pull/2329>`__
-  Renamed ``type`` column of ``Group`` database model to ``type_string`` `[#2329] <https://github.com/aiidateam/aiida-core/pull/2329>`__
-  Renamed ``name`` column of ``Group`` database model to ``label`` `[#2329] <https://github.com/aiidateam/aiida-core/pull/2329>`__
- Class method ``Group.get_or_create`` has been removed, use the collection method ``Group.objects.get_or_create`` instead
- Class method ``Group.get_from_string`` has been removed, use the class method ``Group.get`` instead


``Node``
--------

-  The column ``type`` has been renamed to ``node_type`` `[#2522] <https://github.com/aiidateam/aiida-core/pull/2522>`__
-  The methods ``get_inputs``, ``get_outputs``, ``get_inputs_dict`` and ``get_outputs_dict`` have been removed and replace by ``get_incoming`` and ``get_outgoing`` `[#2236] <https://github.com/aiidateam/aiida-core/pull/2236>`__
-  Removed the link manager methods ``Node.inp`` and ``Node.out`` and the functionality has partially been replaced by: `[#2569] <https://github.com/aiidateam/aiida-core/pull/2569>`__

   -  The link manager properties ``inputs`` and ``outputs`` for the ``CalculationNode`` and ``WorkflowNode`` classes.
   -  Added the ``Data.creator`` property
   -  Added the ``ProcessNode.caller`` property
   -  Functionality to traverse the graph with tab completion when there is no uniqueness on the label is no longer supported and ``get_incoming`` and ``get_outgoing`` should be used instead.

-  The classes ``Node``, ``ProcessNode`` can no longer be stored but only their sub classes `[#2301] <https://github.com/aiidateam/aiida-core/pull/2301>`__


``Data``
--------

-  ``Kind.is_alloy()`` has been changed to a property ``Kind.is_alloy`` `[#2374] <https://github.com/aiidateam/aiida-core/pull/2374>`__
-  ``Kind.has_vacancies()`` has been changed to a property ``Kind.has_vacancies`` `[#2374] <https://github.com/aiidateam/aiida-core/pull/2374>`__
-  ``StructureData.is_alloy()`` has been changed to a property ``StructureData.is_alloy`` `[#2374] <https://github.com/aiidateam/aiida-core/pull/2374>`__
-  ``StructureData.has_vacancies()`` has been changed to a property ``StructureData.has_vacancies`` `[#2374] <https://github.com/aiidateam/aiida-core/pull/2374>`__
-  ``CifData._get_aiida_structure()`` has been renamed to ``CifData.get_structure()``. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  ``CifData`` default library used in ``get_structure`` to convert to ``StructureData`` has been changed from ``ase`` to ``pymatgen`` `[#1257] <https://github.com/aiidateam/aiida-core/pull/1257>`__
-  ``SinglefileData`` the methods ``get_file_content``, ``add_path`` and ``remove_path`` have been removed in favor of ``put_object_from_file`` and ``get_content`` `[#2506] <https://github.com/aiidateam/aiida-core/pull/2506>`__
-  ``ArrayData.iterarrays()`` has been renamed to ``ArrayData.get_iterarrays()``. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  ``TrajectoryData._get_cif()`` has been renamed to ``TrajectoryData.get_cif()``. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  ``TrajectoryData._get_aiida_structure()`` has been renamed to ``TrajectoryData.get_structure()``. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  ``StructureData._get_cif()`` has been renamed to ``StructureData.get_cif()``. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  ``Code.full_text_info()`` has been renamed to ``Code.get_full_text_info()``. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  ``Code.is_hidden()`` has been renamed and changed to ``Code.hidden`` property. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  ``RemoteData.is_empty()`` has been changed to a property ``RemoteData.is_empty``. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  The arguments ``stepids`` and ``cells`` of the ``TrajectoryData.set_trajectory()`` method are made optional which has implications on the ordering of the arguments passed to this method. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  The list of atomic symbols for ``TrajectoryData`` is no longer stored as array data but is now accessible through the ``TrajectoryData.symbols`` attribute. `[#2422] <https://github.com/aiidateam/aiida-core/pull/2422>`__
-  Removed deprecated methods ``BandsData._prepare_dat_1`` and ``BandsData._prepare_dat_2`` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed deprecated method `KpoinstData.bravais_lattice` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed deprecated method `KpoinstData._set_bravais_lattice` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed deprecated method `KpoinstData._get_or_create_bravais_lattice` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed deprecated method `KpoinstData.set_kpoints_path` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed deprecated method `KpoinstData._find_bravais_info` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed deprecated method `KpoinstData.find_bravais_lattice` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed deprecated method `KpoinstData.get_special_kpoints` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__

``Process``
-----------

-  Metadata inputs that used to start with an underscore (``_label``, ``_description`` and ``_options``) no longer use an underscore and have moved within the ``metadata`` namespace `[#1105] <https://github.com/aiidateam/aiida-core/pull/1105>`__
-  Non-storable input ports are now markable as such through the ``non_db`` keyword `[#1105] <https://github.com/aiidateam/aiida-core/pull/1105>`__


Inline calculations
-------------------

-  The ``make_inline`` and ``optional_inline`` decorators have been replaced by ``calcfunction``. `[#2203] <https://github.com/aiidateam/aiida-core/pull/2203>`__


``JobCalculation``
------------------

In the new engine, it is not possible to launch calculation jobs by first creating an instance of the Calculation and then calling the ``calculation.use_xxx`` methods, as it was common in early versions of AiiDA.
Instead, you need to pass the correct Calculation class to the ``run`` or ``submit`` function, passing the nodes to link as input as ``kwargs``.
For the past few versions, we have kept back-compatibility by supporting both ways of submitting. In version 1.0 we have decided to keep only one single way of submitting calculations for simplicity.

-  ``JobCalculation`` has been replaced by ``CalcJob`` process class `[#2389] <https://github.com/aiidateam/aiida-core/pull/2389>`__
-  Custom methods on the node class should now be implemented through a ``CalculationTools`` plugin `[#2331] <https://github.com/aiidateam/aiida-core/pull/2331>`__
-  Explicit ``set_`` methods of the ``JobCalculation`` have been replaced with generic ``set_option`` method `[#2361] <https://github.com/aiidateam/aiida-core/pull/2361>`__
-  Explicit ``get_`` methods of the ``JobCalculation`` have been replaced with generic ``get_option`` method `[#1961] <https://github.com/aiidateam/aiida-core/pull/1961>`__
-  New calculation job states have been introduced set as an attribute, only to be used for querying `[#2389] <https://github.com/aiidateam/aiida-core/pull/2389>`__
-  The ``DbCalcState`` table that recorded the old job state of ``JobCalculations`` has been removed `[#2389] <https://github.com/aiidateam/aiida-core/pull/2389>`__


``Parser``
----------

-  ``parse_from_retrieved`` has been renamed to ``parse``. In addition the arguments and return signatures have changed, for details see the PR `[#2397] <https://github.com/aiidateam/aiida-core/pull/2397>`__


``WorkChain``
-------------

-  The free function ``submit`` in any ``WorkChain`` should be replaced with ``self.submit``.
-  The future returned by ``submit`` no longer has the ``pid`` attribute but rather ``pk``.
-  The ``workfunction`` decorator can only be used for functions that return one of the inputs they receive, for all other use the ``calcfunction``
-  The ``get_inputs_template class`` method has been replaced by ``get_builder``. See the `section on the process builder in the documentation <https://aiida-core.readthedocs.io/en/latest/concepts/processes.html#the-process-builder>`__ on how to use it.
-  The ``input_group`` has been deprecated and been replaced by namespaces. See the `section on ports in the documentation <https://aiida-core.readthedocs.io/en/latest/concepts/workflows.html#ports-and-portnamespaces>`__ on how to use them.
-  The use of a ``.`` (period) in output keys is not supported in ``Process.out`` because that is now reserved to indicate namespaces.


Legacy workflows
----------------

-  Remove implementation of legacy workflows `[#2379] <https://github.com/aiidateam/aiida-core/pull/2379>`__


``verdi``
---------

The ``verdi`` command line interface has been migrated over to a new system (called ``click``), making the interface of all ``verdi`` commands consistent: now the way to specify a node (via a PK, a UUID or a LABEL) is the same for all commands, and command-line options that have the same meaning use the same flags in all commands.
To make this possible, the interface of various verdi commands has been changed to ensure consistency.
Also the output of most commands has been homogenised (e.g. to print errors or warnings always in the same style).
Moreover, some of the commands have been renamed to be consistent with the new names of the classes in AiiDA.

-  Removed ``verdi data plugins`` in favor of ``verdi plugin list`` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed ``verdi code rename`` in favor of ``verdi code relabel`` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed ``verdi code update`` in favor of ``verdi code duplicate`` `[#3114] <https://github.com/aiidateam/aiida-core/pull/3114>`__
-  Removed ``verdi work`` in favor of ``verdi process`` `[#2574] <https://github.com/aiidateam/aiida-core/pull/2574>`__
-  Removed ``verdi calculation`` in favor of ``verdi process`` and ``verdi calcjob`` `[#2574] <https://github.com/aiidateam/aiida-core/pull/2574>`__
-  Removed ``verdi workflows`` `[#2379] <https://github.com/aiidateam/aiida-core/pull/2379>`__
-  Deprecated the commands to set and get config options ``verdi devel *property*`` in favor of ``verdi config`` `[#2354] <https://github.com/aiidateam/aiida-core/pull/2354>`__
-  ``verdi code show`` no longer shows number of calculations by default to improve performance, with ``--verbose`` flag to restore old behavior `[#1428] <https://github.com/aiidateam/aiida-core/pull/1428>`__
- The tab-completion activation for ``verdi`` has changed, simply replace the ``eval "$(verdi completioncommand)"`` line in your activation script with ``eval "$(_VERDI_COMPLETE-source verdi)"``


Daemon
------

-  Each profile now has its own daemon that can be run completely independently in parallel, so ``verdi daemon configureuser`` has been removed `[#1217] <https://github.com/aiidateam/aiida-core/pull/1217>`__
-  Replaced ``Celery`` with ``Circus`` as the daemonizer of the daemon `[#1213] <https://github.com/aiidateam/aiida-core/pull/1213>`__


Schedulers
----------

-  Renamed ``aiida.daemon.execmanager.job_states`` to ``JOB_STATES``, conforming to python conventions `[#1799] <https://github.com/aiidateam/aiida-core/pull/1799>`__
-  Abstract method ``aiida.scheduler.Scheduler._get_detailed_jobinfo_command()`` raises ``aiida.common.exceptions.FeatureNotAvailable`` (was ``NotImplemented``).
-  Moved the ``SchedulerFactory`` to ``aiida.plugins.factories`` `[#2498] <https://github.com/aiidateam/aiida-core/pull/2498>`__


Transports
----------

-  Moved the ``TransportFactory`` to ``aiida.plugins.factories`` `[#2498] <https://github.com/aiidateam/aiida-core/pull/2498>`__


Export import
-------------

-  New export archive format introduced ``v0.6``. Older archives will automatically be converted when using ``verdi import``, or alternatively can be manually exported using ``verdi export migrate``


.. _update_older_versions:

Older versions
==============

To determine the current version of your installation use ``verdi --version``.
If the command does not exist, you have an older version of AiiDA, in which case you need to get it from the ``aiida.__init__.py`` file.
Update instructions for older versions can be found in the documentation of the corresponding version:

* `0.11.*`_
* `0.10.*`_
* `0.9.*`_
* `0.8.* Django`_
* `0.7.* Django`_
* `0.6.* Django`_
* `0.6.* SqlAlchemy`_
* `0.5.* Django`_
* `0.4.* Django`_


.. _0.11.*: https://aiida-core.readthedocs.io/en/v0.12.2/installation/updating.html#updating-from-0-11-to-0-12-0
.. _0.10.*: http://aiida-core.readthedocs.io/en/v0.10.0/installation/updating.html#updating-from-0-9-to-0-10-0
.. _0.9.*: http://aiida-core.readthedocs.io/en/v0.10.0/installation/updating.html#updating-from-0-9-to-0-10-0
.. _0.8.* Django: http://aiida-core.readthedocs.io/en/v0.9.1/installation/index.html#updating-from-0-8-django-to-0-9-0-django
.. _0.7.* Django: http://aiida-core.readthedocs.io/en/v0.8.1/installation/index.html#updating-from-0-7-0-django-to-0-8-0-django
.. _0.6.* Django: http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-6-0-django-to-0-7-0-django
.. _0.6.* SqlAlchemy:   http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-6-0-django-to-0-7-0-sqlalchemy
.. _0.5.* Django: http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-5-0-to-0-6-0
.. _0.4.* Django: http://aiida-core.readthedocs.io/en/v0.5.0/installation.html#updating-from-0-4-1-to-0-5-0
