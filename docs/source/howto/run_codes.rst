.. _how-to:run-codes:

*************************
How to run external codes
*************************

This how-to walks you through the steps of setting up a (possibly remote) compute resource, setting up a code on that computer and submitting a calculation through AiiDA (similar to the :ref:`introductory tutorial <tutorial:basic:calcjob>`, but in more detail).

To run an external code with AiiDA, you need an appropriate :ref:`calculation plugin <topics:plugins>`.
In the following, we assume that a plugin for your code is already available from the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_ and installed on your machine, e.g. using ``pip install aiida-quantumespresso``.
If a plugin for your code is not yet available, see :ref:`how-to:plugin-codes`.

Throughout the process you will be prompted for information on the computer and code.
In these prompts:

 * Type ``?`` followed by ``<enter>`` to get help on what is being asked at any prompt.
 * Press ``<CTRL>+C`` at any moment to abort the setup process.
   Your AiiDA database will remain unmodified.

.. note::

  The ``verdi`` commands use ``readline`` extensions to provide default answers, which require an advanced terminal.
  Use a standard terminal -- terminals embedded in some text editors (such as ``emacs``) have been known to cause problems.

.. _how-to:run-codes:computer:

How to set up a computer
========================

A |Computer| in AiiDA denotes a computational resource on which you will run your calculations.
It can either be:

 1. the machine where AiiDA is installed or
 2. any machine that is accessible via `SSH <https://en.wikipedia.org/wiki/Secure_Shell>`_ from the machine where AiiDA is installed.

The second option allows managing multiple remote compute resources (including HPC clusters and cloud services) from the same AiiDA installation and moving computational jobs between them.

.. tip::

    The second option requires access through a SSH keypair.
    If your compute resource demands two-factor authentication, you may need to install AiiDA directly on the compute resource instead.


Computer requirements
---------------------

Requirements for configuring a compute resource in AiiDA are:

* It runs a Unix-like operating system (Linux distros and MacOS should work fine)
* It has ``bash`` installed
* (option 2.) It is accessible *via* SSH from the machine that runs AiiDA (possibly :ref:`via a proxy server<how-to:ssh:proxy>`)
* (optional) It has batch scheduler installed (see the :ref:`list of supported schedulers <topics:schedulers>`)

If you are configuring a remote computer, start by :ref:`configuring password-less SSH access <how-to:ssh>` to it.

.. note::

    AiiDA will use ``bash`` on the remote computer, regardless of the default shell.
    Please ensure that your remote ``bash`` configuration does not load a different shell.


.. _how-to:run-codes:computer:setup:

Computer setup
--------------

The configuration of computers happens in two steps: setting up the public metadata asociated with the |Computer| in AiiDA provenance graphs, and configuring private connection details.

Start by creating a new computer instance in the database:

.. code-block:: console

   $ verdi computer setup

At the end, the command will open your default editor on a file containing a summary of the configuration up to this point.
You can add ``bash`` commands that will be executed

 * *before* the actual execution of the job (under 'Pre-execution script'), and
 * *after* the script submission (under 'Post execution script').

Use these additional lines to perform any further set up of the environment on the computer, for example loading modules or exporting environment variables:

.. code-block:: bash

   export NEWVAR=1
   source some/file

.. note::

   Don't specify settings here that are specific to a code or calculation: you can set further pre-execution commands at the ``Code`` and even ``CalcJob`` level.

When you are done editing, save and quit (e.g. ``<ESC>:wq<ENTER>`` in ``vim``).
The computer has now been created in the database but you still need to *configure* access to it using your credentials.

.. tip::
    In order to avoid having to retype the setup information the next time round, you can provide some (or all) of the information via a configuration file:

    .. code-block:: console

       $ verdi computer setup --config computer.yml

    where ``computer.yml`` is a configuration file in the `YAML format <https://en.wikipedia.org/wiki/YAML#Syntax>`__.
    This file contains the information in a series of key:value pairs:

    .. code-block:: yaml

       ---
       label: "localhost"
       hostname: "localhost"
       transport: local
       scheduler: "direct"
       work_dir: "/home/max/.aiida_run"
       mpirun_command: "mpirun -np {tot_num_mpiprocs}"
       mpiprocs_per_machine: "2"
       prepend_text: |
          module load mymodule
          export NEWVAR=1

   The list of the keys for the ``yaml`` file is given by the options of the ``computer setup`` command:

   .. code-block:: console

      $ verdi computer setup --help

   Note: Remove the ``--`` prefix and replace ``-`` within the keys by the underscore ``_``.

.. _how-to:run-codes:computer:configuration:

Computer configuration
----------------------

The second step configures private connection details using:

.. code-block:: console

   $ verdi computer configure TRANSPORTTYPE COMPUTERNAME

with the appropriate transport type (``local`` for option 1., ``ssh`` for option 2.) and computer label.

After setup and configuration have been completed, let AiiDA check if everything is working properly:

.. code-block:: console

   $ verdi computer test COMPUTERNAME

This will test logging in, copying files, and checking the jobs in the scheduler queue.


Managing your computers
-----------------------

If you are unsure whether a computer is already set up, list configured computers with:

.. code-block:: console

   $ verdi computer list

To get detailed information on the specific computer named ``COMPUTERNAME``:

.. code-block:: console

   $ verdi computer show COMPUTERNAME

To rename a computer or remove it from the database:

.. code-block:: console

   $ verdi computer rename OLDCOMPUTERNAME NEWCOMPUTERNAME
   $ verdi computer delete COMPUTERNAME

.. note::

   Before deleting a |Computer|, you will need to delete *all* nodes linked to it (e.g. any ``CalcJob`` and ``RemoteData`` nodes).
   Otherwise, AiiDA will prevent you from doing so in order to preserve provenance.

If a remote machine is under maintenance (or no longer operational), you may want to **disable** the corresponding |Computer|.
Doing so will prevent AiiDA from connecting to the given computer to check the state of calculations or to submit new calculations.

.. code-block:: console

   $ verdi computer disable COMPUTERNAME
   $ verdi computer enable COMPUTERNAME

For further hints on tuning the configuration of your computers, see :ref:`how-to:installation:supercomputers`



.. _how-to:run-codes:code:

How to setup a code
===================

Once your computer is configured, you can set up codes on it.

AiiDA stores a set of metadata for each code, which is attached automatically to each calculation using it.
Besides being important for reproducibility, this also makes it easy to query for all calculations that were run with a given code (for instance, if a specific version is found to contain a bug).

.. _how-to:run-codes:code:setup:

Setting up a code
-----------------

The ``verdi code`` CLI is the access point for managing codes in AiiDA.
To setup a new code, execute:

.. code-block:: console

   $ verdi code setup

and you will be guided through a process to setup your code.

.. admonition:: On remote and local codes
    :class: tip title-icon-lightbulb

    In most cases, it is advisable to install the executables to be used by AiiDA on the target machine *before* submitting calculations using them in order to take advantage of the compilers and libraries present on the target machine.
    This setup is referred to as *remote* codes (``Installed on target computer?: True``).

    Occasionally, you may need to run small, reasonably machine-independent scripts (e.g. Python or bash), and copying them manually to a number of different target computers can be tedious.
    For this use case, AiiDA provides *local* codes (``Installed on target computer?: False``).
    Local codes are stored in the AiiDA file repository and copied to the target computer for every execution.

    Do *not* use local codes as a way of encapsulating the environment of complex executables.
    Containers are a much better solution to this problem, and we are working on adding native support for containers in AiiDA.


At the end of these steps, you will be prompted to edit a script, where you can include ``bash`` commands that will be executed

 * *before* running the submission script (after the 'Pre execution script' lines), and
 * *after* running the submission script (after the 'Post execution script' separator).

Use this for instance to load modules or set variables that are needed by the code, such as:

.. code-block:: bash

    module load intelmpi

At the end, you receive a confirmation, with the *PK* and the *UUID* of your new code.

.. admonition:: Using configuration files
    :class: tip title-icon-lightbulb

  Analogous to a :ref:`computer setup <how-to:run-codes:computer>`, some (or all) the information described above can be provided via a configuration file:

  .. code-block:: console

     $ verdi code setup --config code.yml

  where ``code.yml`` is a configuration file in the `YAML format <https://en.wikipedia.org/wiki/YAML#Syntax>`_.

  This file contains the information in a series of key:value pairs:

  .. code-block:: yaml

      ---
      label: "qe-6.3-pw"
      description: "quantum_espresso v6.3"
      input_plugin: "quantumespresso.pw"
      on_computer: true
      remote_abs_path: "/path/to/code/pw.x"
      computer: "localhost"
      prepend_text: |
        module load module1
        module load module2
      append_text: " "

  The list of the keys for the ``yaml`` file is given by the available options of the ``code setup`` command:

  .. code-block:: console

    $ verdi code setup --help

  Note: Remove the ``--`` prefix and replace ``-`` within the keys by the underscore ``_``.

Managing codes
--------------

You can change the label of a code by using the following command:

.. code-block:: console

  $ verdi code relabel <IDENTIFIER> "new-label"

where <IDENTIFIER> can be the numeric *PK*, the *UUID* or the label of the code (either ``label`` or ``label@computername``) if the label is unique.

You can also list all available codes and their identifiers with:

.. code-block:: console

  $ verdi code list

which also accepts flags to filter only codes on a given computer, or only codes using a specific plugin, etc. (use the ``-h`` option).

You can get the information of a specific code with:

.. code-block:: console

  $ verdi code show <IDENTIFIER>

Finally, to delete a code use:

.. code-block:: console

  $ verdi code delete <IDENTIFIER>

(only if it wasn't used by any calculation, otherwise an exception is raised).

.. note::

  Codes are a subclass of :py:class:`Node <aiida.orm.nodes.Node>` and, as such, you can attach ``extras`` to a code, for example:

  .. code-block:: python

      load_code('<IDENTIFIER>').set_extra('version', '6.1')
      load_code('<IDENTIFIER>').set_extra('family', 'cp2k')

  These can be useful for querying, for instance in order to find all runs done with the CP2K code of version 6.1 or later.

.. _how-to:run-codes:submit:

How to submit a calculation
===========================

After :ref:`setting up your computer <how-to:run-codes:computer>` and :ref:`setting up your code <how-to:run-codes:code:setup>`, you are ready to launch your calculations!

 * Make sure the daemon is running:

    .. code-block:: bash

        verdi daemon status

 * Figure out which inputs your |CalcJob|  plugin needs, e.g. using:

    .. code-block:: bash

        verdi plugin list aiida.calculations arithmetic.add

 * Write a ``submit.py`` script:

    .. code-block:: python

        from aiida.engine import submit

        code = load_code(label='add@localhost')
        builder = code.get_builder()
        builder.x = Int(4)
        builder.y = Int(5)
        builder.metadata.options.withmpi = False
        builder.metadata.options.resources = {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1,

        }
        builder.metadata.description = "My first calculation."

        print(submit(builder))

    Of course, the code label and builder inputs need to be adapted to your code and calculation.

 * Submit your calculation to the AiiDA daemon:

   .. code-block:: bash

       verdi run submit.py

After this, use ``verdi process list`` to monitor the status of the calculations.

See :ref:`topics:processes:usage:launching` and :ref:`topics:processes:usage:monitoring` for more details.


.. |Code| replace:: :py:class:`~aiida.orm.nodes.data.Code`
.. |Computer| replace:: :py:class:`~aiida.orm.Computer`
.. |CalcJob| replace:: :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`
