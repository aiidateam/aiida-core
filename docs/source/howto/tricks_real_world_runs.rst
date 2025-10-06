.. _how-to:real-world-tricks:

========================================
Real-world calculations: tips and tricks
========================================

This how-to page collects useful tips and tricks that may be useful in real-world AiiDA simulations.

How to provide specific configuration to a calculation job
==========================================================

When submitting a job, you can provide specific instruction which should be put in the job submission script (e.g. for a slurm scheduler).
All these additional instructions can be provided via the ``metadata.options`` dictionary of the specific calculation job.

In particular, you can provide:

- custom scheduler directives, like additional ``#SBATCH`` lines in case of slurm schedulers
- prepend text to the job script (e.g. if you need to load specific modules or set specific environment variables which are not already specified in the computer/code setup)
- additional mpirun parameters (e.g. if you need to bind processes to cores, etc.)


Basic pattern
-------------

These options are set on the process builder under ``builder.metadata.options`` and are available for all ``CalcJob`` plugins (e.g. ``aiida-quantumespresso.PwCalculation``):

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


Prepend/append shell text to the job script
-------------------------------------------

Use ``prepend_text`` to add shell commands immediately before launching the code, and ``append_text`` for commands executed right after the code finishes:

.. code-block:: python

	builder.metadata.options.prepend_text = """
	echo "Run started on $(hostname) at $(date)"
	""".strip()

	builder.metadata.options.append_text = """
	echo "Run finished on $(hostname) at $(date)"
	""".strip()

Tip: for simple environment variables you can also use ``environment_variables`` (AiiDA will export them for you):

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


Understand the workflow inputs
==============================

When you are running a complex workflow, it is often useful to understand what inputs can be passed to it (or better, to its builder).
This is particularly useful when you are using a new workflow for the first time, or if you are using a complex workflow with many nested subworkflows.
You can use the following in a ``verdi shell`` to print the structure of inputs accepted by a workflow (or any process class):

.. code-block:: python

  from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain
  PwBaseWorkChain.spec().get_description()['inputs'].keys()
  # -> dict_keys(['_attrs', 'metadata', 'max_iterations', 'clean_workdir', 'handler_overrides', 'pw', 'kpoints', 'kpoints_distance', 'kpoints_force_parity'])

Or via tab completion:

.. code-block:: python

  builder = PwBaseWorkChain.get_builder()
  builder.<TAB>

.. code-block:: text

  _attrs          handler_overrides  kpoints_distance  max_iterations
  clean_workdir   kpoints            metadata          pw


How to go to quickly  inspect a failed calculation
==================================================

If a calcjob fails, there are few ways to inspect the raw outputs and understand what happened.

Go to the remote folder of a calculation
----------------------------------------

If you want to go to a calculation folder to see what happened, e.g. if it failed. To go on the remote folder of a given calculation with pk ``<pk>``,
you can use the following command:

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

If you want to re-submit a calculation/workflow (i.e. a process) for whatever reason, i.e. it failed for some wrong input or not enough resources, you can use 
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
