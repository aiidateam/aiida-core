.. _how-to:setup_code:

*******************
How to setup a code
*******************

Once you have at least one computer configured (see :ref:`how-to:setup_computer`), you can configure the codes.
In AiiDA, for full reproducibility of each calculation, we store each code in the database, and attach to each calculation a given code. This has the further advantage to make very easy to query for all calculations that were run with a given code (for instance because I am looking for phonon calculations, or because I discovered that a specific version had a bug and I want to rerun the calculations).

In AiiDA, we distinguish two types of codes: **remote** codes and **local** codes, where the distinction between the two is described here below.

Local codes
-----------

With local codes we denote codes for which the code is not already present on the remote machine, and must be copied for every submission.
This is the case if you have for instance a small, machine-independent Python script that you did not copy previously in all your clusters.

In AiiDA, a local code can be set up by specifying:

* A folder, containing all files to be copied over at every submission
* The name of executable file among the files inside the folder specified above

Remote codes
------------

With remote codes we denote codes that are installed/compiled on the remote computer.
Indeed, this is very often the case for codes installed in supercomputers for high-performance computing applications, because the code is typically installed and optimized on the supercomputer.

In AiiDA, a remote code is identified by two mandatory pieces of information:

* A computer on which the code is (that must be a previously configured computer);
* The absolute path of the code executable on the remote computer.

Setting up a code
-----------------

The following CLI command is the access point for managing codes in AiiDA:

.. code-block:: console

   $ verdi code

To setup a new code, you execute:

.. code-block:: console

   $ verdi code setup

and you will be guided through a process to setup your code.

.. admonition:: Setup Help
    :class: tip title-icon-lightbulb

  The setup will ask you a few pieces of information.
  At every prompt, you can type the ``?`` character and press ``<enter>`` to get a more detailed explanation of what is being asked.

You will be asked for:

Label
  A label to refer to this code.

  .. note::

    This label is not enforced to be unique.
    However, if you try to keep it unique, at least within the same computer, you can use it later to reference your code.
    Otherwise, you need to remember its ``PK`` or ``UUID``.

Description
  A human-readable description of this code (for instance "Quantum Espresso v.5.0.2 with 5.0.3 patches, pw.x code, compiled with openmpi").

Default calculation input plugin
  A string that identifies the default input plugin to be used to generate new calculations to use with this code.
  This string has to be a valid string recognized by the ``CalculationFactory`` function.
  To get the list of all available Calculation plugin strings, use the ``verdi plugin list aiida.calculations`` command.

Installed on target computer
  Either True (for local codes) or False (for remote codes).
  For the meaning of the distinction, see above.
  Depending on your choice, you will be asked for:

  * LOCAL CODES:

    Local directory containing the code
      The absolute path where the executable and all other files needed to run the code are stored; these will be copied over to the remote computers for every submitted calculation.

    Relative path of executable inside code folder
      The relative path of the executable file inside the folder entered in the previous step.

  * REMOTE CODES:

    Remote computer name
      The computer name on which the code resides, as configured and stored in the AiiDA database. See :ref:`this section <how-to:setup_computer>` for information on how to set up a remote computer.

    Remote absolute path
      The (full) absolute path of the code executable on the remote machine, *including the name of the executable*.

At the end of these steps, you will be prompted to edit a script, and you will have the opportunity to include ``bash`` commands that will be executed *before* running the submission script (after the 'pre execution script' lines) and *after* running the submission script (after the 'Post execution script' separator).
This is intended for code-dependent settings, for instance to load modules or set variables that are needed by the code. For example:

.. code-block:: bash

    module load intelmpi


At the end, you will get a confirmation command, and also the ID of the code in the
database (the ``pk``, i.e. the principal key, and the ``uuid``).

In a manner analogous to a :ref:`computer setup <how-to:setup_computer>`, it is also possible to provide some (or all) the information described above via a configuration file using:

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

.. admonition:: Available Keys
    :class: tip title-icon-lightbulb

  The keys mirror the available options of the command, which you can print using:

  .. code-block:: console

    $ verdi code setup --help

  Note the syntax differences: remove the ``--`` prefix and replace ``-`` within the keys by the underscore ``_``.


.. note::

  Codes are a subclass of the :py:class:`Node <aiida.orm.nodes.Node>` class and, as such, you can attach any set of attributes to the code.
  These can be extremely useful for querying: for instance, you can attach the version of the code as an attribute, or the code family (for instance: "pw.x code of Quantum Espresso") to later query for all runs done with a ``pw.x`` code and version more recent than 5.0.0, for instance.
  However, in the present AiiDA version you cannot add attributes from the command line using ``verdi``, but you have to do it using Python code.

.. note:: You can change the label of a code by using the following command:

  .. code-block:: console

    $ verdi code relabel <PK> "new-label"

  <PK> can either be the numeric Primary Key (PK) of the code (preferentially), or possibly its label (or ``label@computername``), if this string uniquely identifies a code.

  You can also list all available codes (and their relative IDs) with:

  .. code-block:: console

    $ verdi code list

  which also accepts flags to filter only codes on a given computer, or only codes using a specific plugin, etc. Use the ``-h`` command line option to see the documentation of all possible options.

  You can then get the information of a specific code with:

  .. code-block:: console

    $ verdi code show <PK>

  Finally, to delete a code use:

  .. code-block:: console

    $ verdi code delete <PK>

  (only if it wasn't used by any calculation, otherwise an exception is raised).

And now, you are ready to launch your calculations!

.. admonition:: Where Next?
    :class: seealso title-icon-read-more

    Try running a basic Calcjob in the :ref:`introductory tutorial <tutorial:basic:calcjob>`, or find more information about running external codes in :ref:`this howto <how-to:plugin-codes>`.
