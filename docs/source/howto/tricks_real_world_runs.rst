.. _how-to:real-world-tricks:

========================================
Real-world calculations: tips and tricks
========================================

This how-to page collects useful tips and tricks for running real-world AiiDA simulations.  

Setting runtime configuration of a calculation job  
==================================================

When submitting a job, you can provide specific instructions which should be put in the job submission script (e.g. for the Slurm scheduler).  
They can be provided via the ``metadata.options`` dictionary of the calculation job.  

In particular, you can provide:

- custom scheduler directives, like additional ``#SBATCH`` commands for the Slurm scheduler  
- prepend text to the job script (e.g. if you need to load specific modules or set specific environment variables which are not already specified in the computer/code setup)
- additional mpirun parameters (e.g. if you need to bind processes to cores, etc.)

The full list of available options can be found in the `AiiDA CalcJob options documentation <https://aiida--7048.org.readthedocs.build/projects/aiida-core/en/7048/topics/calculations/usage.html#options>`__.


Basic pattern
-------------

These options are set on the process builder under ``builder.metadata.options`` and are available for all ``CalcJob`` implementations (e.g. ``aiida-quantumespresso.PwCalculation``):

.. code-block:: python

	builder = PwCalculation.get_builder()

	# Required scheduler resources (example: 2 nodes x 16 MPI per node)
	builder.metadata.options.resources = {
		 'num_machines': 2,
		 'num_mpiprocs_per_machine': 16,
	}

	# Optional scheduler settings
	builder.metadata.options.max_wallclock_seconds = 2 * 60 * 60  # 2 hours
	builder.metadata.options.queue_name = 'debug'                  # scheduler queue/partition
	builder.metadata.options.account = 'proj123'                   # accounting/project (if required)

In case you are submitting a ``PwBaseWorkChain``, these options should be set under the ``pw`` input namespace:

.. code-block:: python

    builder = PwBaseWorkChain.get_builder()

    # Required scheduler resources (example: 2 nodes x 16 MPI per node)
    builder.pw.metadata.options.resources = {
         'num_machines': 2,
         'num_mpiprocs_per_machine': 16,
    }

    # Optional scheduler settings
    builder.pw.metadata.options.max_wallclock_seconds = 2 * 60 * 60  # 2 hours
    builder.pw.metadata.options.queue_name = 'debug'                  # scheduler queue/partition
    builder.pw.metadata.options.account = 'proj123'                   # accounting/project (if required)

Custom scheduler directives (e.g. extra ``#SBATCH``)
----------------------------------------------------

Use ``custom_scheduler_commands`` to inject raw scheduler lines near the top of the submit script (before any non-scheduler command):

.. code-block:: python

	builder.metadata.options.custom_scheduler_commands = """
	#SBATCH --constraint=mc
	#SBATCH --exclusive
	#SBATCH --hint=nomultithread
	""".strip()

Notes:

- Keep the lines valid for your scheduler (Slurm here; adapt to PBS/LSF/etc.).
- Use this when a directive is not covered by a dedicated option.


Prepend/append shell code to the job script  
-------------------------------------------

Use ``prepend_text`` to add shell commands immediately before launching the code, and ``append_text`` for commands executed right after the code finishes:

.. code-block:: python

	builder.metadata.options.prepend_text = """
	echo "Run started on $(hostname) at $(date)"
	""".strip()

	builder.metadata.options.append_text = """
	echo "Run finished on $(hostname) at $(date)"
	""".strip()

.. tip:: for simple environment variables you can also use ``environment_variables`` (AiiDA will export them for you):  

.. code-block:: python

	builder.metadata.options.environment_variables = {
		 'OMP_NUM_THREADS': '1',
	}



Extra parameters to mpirun (or equivalent)
------------------------------------------

Set ``mpirun_extra_params`` to pass flags to the MPI launcher in addition to the computer's configured ``mpirun_command``:

.. code-block:: python

	# Example for OpenMPI process binding
	builder.metadata.options.mpirun_extra_params = [
		 '--bind-to', 'core', '--map-by', 'socket:PE=2',
	]

.. note::
	``mpirun_extra_params`` is a list/tuple of strings; AiiDA will join them with spaces. Keep launcher-specific flags consistent with your cluster (OpenMPI, MPICH, srun, etc.).


Full list of metadata available
-------------------------------

Here is the full list of options that can be set in ``builder.metadata``.

.. dropdown:: Click to see all available metadata options

    The following fields can be set on ``builder.metadata``:

    - call_link_label (str): The label to use for the CALL link if the process is called by another process.
    - computer (Computer | None): When using a "local" code, set the computer on which the calculation should be run.
    - description (str | None): Description to set on the process node.
    - disable_cache (bool | None): Do not consider the cache for this process, ignoring all other caching configuration rules.
    - dry_run (bool): When set to True will prepare the calculation job for submission but not actually launch it.
    - label (str | None): Label to set on the process node.
    - options (Namespace):

      - account (str | None): Set the account to use for the queue on the remote computer.
      - additional_retrieve_list (list | tuple | None): Relative file paths to retrieve in addition to what the plugin specifies.
      - append_text (str): Text appended to the scheduler-job script just after the code execution.
      - custom_scheduler_commands (str): Raw scheduler directives inserted before any non-scheduler command (e.g. extra ``#SBATCH`` lines).
      - environment_variables (dict): Environment variables to export for this calculation.
      - environment_variables_double_quotes (bool): If True, use double quotes instead of single quotes to escape ``environment_variables``.
      - import_sys_environment (bool): If True, the submission script will load the system environment variables.
      - input_filename (str): Name of the main input file written to the remote working directory.
      - max_memory_kb (int | None): Maximum memory in kilobytes to request from the scheduler.
      - max_wallclock_seconds (int | None): Wallclock time in seconds requested from the scheduler.
      - mpirun_extra_params (list | tuple): Extra parameters passed to the MPI launcher in addition to the computer's configured command.
      - output_filename (str): Name of the primary output file produced by the code.
      - parser_name (str): Entry point name of the parser to use for this calculation.
      - prepend_text (str): Text prepended in the scheduler-job script just before the code execution.
      - priority (str | None): Job priority (if supported by the scheduler).
      - qos (str | None): Quality of service to use for the queue on the remote computer.
      - queue_name (str | None): Name of the queue/partition on the remote computer.
      - rerunnable (bool | None): Whether the job can be requeued/rerun by the scheduler.
      - resources (dict) [required]: Scheduler resources (e.g. number of nodes, CPUs, MPI per machine). The exact keys are scheduler-plugin dependent.
      - scheduler_stderr (str): Filename to which the scheduler stderr stream is written.
      - scheduler_stdout (str): Filename to which the scheduler stdout stream is written.
      - stash (Namespace): Directives to stash files after the calculation completes.

        - dereference (bool | None): Whether to follow symlinks while stashing (applies to certain stash modes).
        - source_list (tuple | list | None): Relative filepaths in the remote directory to be stashed.
        - stash_mode (str | None): Mode with which to perform stashing; value of ``aiida.common.datastructures.StashMode``.
        - target_base (str | None): Base location to stash files to (e.g. absolute path on remote computer for copy mode).
      - submit_script_filename (str): Filename to which the job submission script is written.
      - withmpi (bool): Whether to run the code with the MPI launcher.
      - without_xml (bool | None): If True, the parser will not fail if a normally expected XML file is missing in the retrieved folder (plugin-dependent).
    - store_provenance (bool): If False, provenance will not be stored in the database (use with care).


Understand the builder structure
================================

When you are running a complex workflow, it is often useful to understand what inputs can be passed to it (or better, to its builder).
This is particularly useful when you are using a new workflow for the first time, or if you are using a complex workflow with many nested subworkflows.
You can use the following in a ``verdi shell`` to print the structure of inputs accepted by a workflow (or any process class):

.. code-block:: python

  from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain
  PwBaseWorkChain.spec().get_description()['inputs'].keys()
  # -> dict_keys(['_attrs', 'metadata', 'max_iterations', 'clean_workdir', 'handler_overrides', 'pw', 'kpoints', 'kpoints_distance', 'kpoints_force_parity'])

To have a full description of the inputs needed for the `pw` calculation, you can also run `PwBaseWorkChain.spec().get_description()['inputs']['pw']` in the same verdi shell.
Alternatively, you can run `verdi plugin list aiida.calculations quantumespresso.pw` in a standard terminal to see the entry point name of the `PwCalculation` class.

The same can also be inspected via tab completion:

.. code-block:: python

  builder = PwBaseWorkChain.get_builder()
  builder.<TAB>

.. code-block:: text

  clean_workdir() handler_overrides      kpoints_distance  max_iterations()
  kpoints         kpoints_force_parity   metadata          pw

We can inspect the inputs of the ``pw`` sub-workflow in the same way:

.. code-block:: python

  builder.pw.<TAB>

.. code-block:: text

  code monitors   parent_folder     settings   remote_folder 
  hubbard_file    parallelization   pseudos    structure 
  kpoints         parameters        metadata   vdw_table

please note that the tab completion could change, depending on the installed packages and plugins.

How to interactively explore the provenance of a node
=====================================================

If a calculation or workflow node is in the database, it is possible to explore its provenance interactively via the verdi shell or a jupyter notebook.  
For example, if you want to explore the provenance of a calculation with pk ``<pk>``, you can do the following:

.. code-block:: python

    from aiida import orm
    pw_calc = orm.load_node(<pk>)

    pw_calc.inputs.<TAB>
    # -> dict_keys(['code', 'kpoints', 'settings', 'parameters', 'parent_folder', 'pseudos', 'structure'])

    pw_calc.outputs.<TAB>
    # -> dict_keys(['output_parameters', 'output_structure', 'output_trajectory', 'retrieved', 'remote_folder'])

It is possible to inspect, for example, the creator of a given remote_folder (in this case, the pw_calc itself):  

.. tip::  
The combination of ``verdi shell`` + tabbing through autocompletion at the various levels and for various entities is an intuitive and powerful way to explore AiiDA's API. It's frequently also used by the devs, when they don't remember details of AiiDA's large API surface. When you don't know how to achieve something, just fire up a ``verdi shell``!  

.. code-block:: python

    remote_folder = pw_calc.outputs.remote_folder

    remote_folder.creator
    # -> <CalcJobNode: uuid: 'a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6' (pk: 123) (aiida.calculations:quantumespresso.pw)>

    remote_folder.creator.pk
    # -> 123

    remote_folder.creator.process_type
    # -> 'aiida.calculations:quantumespresso.pw'

from the creator, it is possible to go back to its inputs and outputs, and so on.
It is also possible to find the higher-level workflow that called a given calculation via the ``.caller`` attribute:

.. code-block:: python

    pw_calc.caller
    # -> <WorkChainNode: uuid: 'z1y2x3w4-v5u6-t7s8-r9q0-p1o2n3m4l5k6' (pk: 456) (aiida.workflows:quantumespresso.pw.base)>

    pw_calc.caller.pk
    # -> 456

    pw_calc.outputs.remote_folder.creator.caller.pk
    # -> 456


How to quickly inspect a calculation  
====================================

There are a few ways to inspect the raw inputs/outputs of a calculation as read/written by the executable.

Go to the remote folder of a calculation
----------------------------------------

If you want to go to the (remote) execution folder of a given calculation to see what happened (e.g., why it failed) with pk ``<pk>``, you can use the following command:  

.. code-block:: console

    verdi calcjob gotocomputer <pk>

And that will open an SSH session on the remote folder of the calculation.

Dump the retrieved files of a calculation
-----------------------------------------

If you want to inspect the retrieved files of a calculation, you can use the following command:

.. code-block:: console

    verdi process dump <pk>

That will create a folder in your current directory, and it will contain all the retrieved files of the calculation (including the inputs).
This is particularly useful if you want to inspect the retrieved files of a failed calculation, or if you want to re-run the calculation locally or somewhere else for debugging.

Once you checked that a calculation failed, and you understood what happened, you may want to re-submit it. Please check :ref:`how-to:quick-restart` below.

.. _how-to:quick-restart:

How to quickly re-submit something: get_builder_restart()
=========================================================

If you want to re-submit a calculation/workflow (i.e. a process) for whatever reason, i.e. it failed due to wrong inputs or insufficient resources, you can use  
the ``get_builder_restart()`` method of the process node. This is particularly useful if you want to re-submit a complex workflow with many inputs, and you do not want to
build the process builder from scratch again.
The ``get_builder_restart()`` method  will return a process builder with all the inputs of the previous calculation, so that you can modify only what you want to change,
and then submit it again.
For example, if you want to re-submit a calculation with pk ``<pk>``, you can use the following:

.. code-block:: python

    from aiida import orm
    from aiida.engine import submit

    failed_pw_base_workchain = orm.load_node(<pk>)
    builder = failed_pw_base_workchain.get_builder_restart()

    # modify the builder if needed
    builder.pw.metadata.options.max_wallclock_seconds = 4 * 60 * 60  # 4 hours

    new_calc = submit(builder)

Skipping already done calculations in a workflow: caching
--------------------------------------------------------

If you are running a complex workflow with many steps, and you want to skip the already done calculations, you can use the caching feature of AiiDA.
This is particularly useful if you want to re-run a workflow that failed at some point, or if you want to run a workflow with different parameters for only few steps, 
but you do not want to re-run the already done previous calculations.
However, caching should be used with care, as it can lead to unexpected results if not used properly in some cases:
- if you are re-compiling the code on the remote cluster, caching will not detect that the code has changed, and it will use the previous results (which could be different from the ones you would obtain with the new executable)
- if your remote folder used as parent 

Caching is not enabled by default, and you need to explicitly enable it in the workflow definition.
Please have a look at the `caching documentation <https://aiida.readthedocs.io/projects/aiida-core/en/stable/howto/run_codes.html#how-to-save-compute-time-with-caching>`__ for more details.


