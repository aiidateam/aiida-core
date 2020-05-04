.. _cli_concepts:

Concepts
========

This section explains basic concepts of the command line interface that apply to all ``verdi`` commands.

.. _cli_parameters:

Parameters
----------
Parameters to ``verdi`` commands come in two flavors:

  * Arguments: positional parameters, e.g. ``123`` in ``verdi process kill 123``
  * Options: announced by a flag (e.g. ``-f`` or ``--flag``), potentially followed by a value. E.g. ``verdi process list --limit 10`` or ``verdi process -h``.

.. _cli_multi_value_options:

Multi-value options
...................

Some ``verdi`` commands provide *options* that can take multiple values.
This allows to avoid repetition and e.g. write::

  verdi export create -N 10 11 12 -- archive.aiida

instead of the more lengthy::

  verdi export create -N 10 -N 11 -N 12 archive.aiida

Note the use of the so-called 'endopts' marker ``--`` that is necessary to mark the end of the ``-N`` option and distinguish it from the ``archive.aiida`` argument.

.. _cli_help_strings:

Help strings
------------
Append the ``--help`` option to any verdi (sub-)command to get help on how to use it.
For example, ``verdi process kill --help`` shows::

  Usage: verdi process kill [OPTIONS] [PROCESSES]...

    Kill running processes.

  Options:
    -t, --timeout FLOAT  Time in seconds to wait for a response before timing
                         out.  [default: 5.0]
    --wait / --no-wait   Wait for the action to be completed otherwise return as
                         soon as it's scheduled.
    -h, --help           Show this message and exit.

All help strings consist of three parts:

  * A ``Usage:`` line describing how to invoke the command
  * A description of the command's functionality
  * A list of the available options

The ``Usage:`` line encodes information on the command's parameters, e.g.:

 * ``[OPTIONS]``: this command takes one (or more) options
 * ``PROCESSES``: this command *requires* a process as a positional argument
 * ``[PROCESSES]``: this command takes a process as an *optional* positional argument
 * ``[PROCESSES]...``: this command takes one or more processes as *optional* positional arguments

Multi-value options are followed by ``...`` in the help string and the ``Usage:`` line of the corresponding command will contain the 'endopts' marker.
For example::

  Usage: verdi export create [OPTIONS] [--] OUTPUT_FILE

    Export various entities, such as Codes, Computers, Groups and Nodes, to an
    archive file for backup or sharing purposes.

  Options:
    -X, --codes CODE...             one or multiple codes identified by their
                                    ID, UUID or label
    -Y, --computers COMPUTER...     one or multiple computers identified by
                                    their ID, UUID or label
    -G, --groups GROUP...           one or multiple groups identified by their
                                    ID, UUID or name
    -N, --nodes NODE...             one or multiple nodes identified by their ID
                                    or UUID
    ...

.. _cli_profile:

Profile
-------
AiiDA supports multiple profiles per installation, one of which is marked as the default and used unless another profile is requested.
Show the current default profile using::

  verdi profile list

In order to use a different profile, pass the ``-p/--profile`` option to any ``verdi`` command, for example::

  verdi -p <profile> process list

Note that the specified profile will be used for this and *only* this command.
Use ``verdi profile setdefault`` in order to permanently change the default profile.

.. _cli_identifiers:

Identifiers
-----------

When working with AiiDA entities, you need a way to *refer* to them on the command line.
Any entity in AiiDA can be addressed via three identifiers:

 * "Primary Key" (PK): An integer, e.g. ``723``, identifying your entity within your database (automatically assigned)
 * `Universally Unique Identifier <https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)>`_ (UUID): A string, e.g. ``ce81c420-7751-48f6-af8e-eb7c6a30cec3`` identifying your entity globally (automatically assigned)
 * Label: A human-readable string, e.g. ``test_calculation`` (manually assigned)

.. note::

   PKs are easy to type and work as long as you stay within your database.
   **When sharing data with others, however, always use UUIDs.**

Any ``verdi`` command that expects an identifier as a paramter will accept PKs, UUIDs and labels.

In almost all cases, this will work out of the box.
Since command line parameters are passed as strings, AiiDA needs to deduce the type of identifier from its content, which can fail in edge cases (see :ref:`cli_identifier_resolution` for details).
You can take the following precautions in order to avoid such edge cases:

  * PK: no precautions needed
  * UUID: no precautions needed for full UUIDs. Partial UUIDs should include at least one non-numeric character or dash
  * Label: add an exclamation mark ``!`` at the end of the identifier in order to force interpretation as a label


.. _cli_identifier_resolution:

Implementation of identifier resolution
.......................................

The logic for deducing the identifier type is as follows:

 1. Try interpreting the identifier as a PK (integer)
 2. If this fails, try interpreting the identifier as a UUID (full or partial)
 3. If this fails, interpret the identifier as a label

The following example illustrates edge cases that can arise in this logic:

===  =====================================  ========
PK   UUID                                   LABEL
===  =====================================  ========
10   12dfb104-7b2b-4bca-adc0-1e4fd4ffcc88   group
11   deadbeef-62ba-444f-976d-31d925dac557   10
12   3df34a1e-5215-4e1a-b626-7f75b9586ef5   deadbeef
===  =====================================  ========

 * trying to identify the first entity by its partial UUID ``12`` would match the third entity by its PK instead
 * trying to identify the second entity by its label ``10`` would match the first entity by its PK instead
 * trying to identify the third entity by its label ``deadbeef`` would match the second entity on its partial UUID ``deadbeef`` instead

The ambiguity between a partial UUID and a PK can always be resolved by including a longer substring of the UUID, eventually rendering the identifier no longer a valid PK.

The case of a label being also a valid PK or (partial) UUID requires a different solution.
For this case, ``verdi`` reserves a special character, the exclamation mark ``!``, that can be appended to the identifier.
Before any type guessing is done, AiiDA checks for the presence of this marker and, if found, will interpret the identifier as a label.
I.e. to solve ambiguity examples mentioned above, one would pass ``10!`` and ``deadbeef!``.


