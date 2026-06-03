.. _how-to:interact:

**************************
How to interact with AiiDA
**************************

There are a variety of manners to interact with AiiDA:

* :ref:`Through the command line interface <how-to:interact-cli>`
* :ref:`Through scripts <how-to:interact-scripts>`
* :ref:`Through interactive shells <how-to:interact-shell>`
* :ref:`Through interactive notebooks <how-to:interact-notebook>`
* :ref:`Through the REST API <how-to:interact-restapi>`


.. _how-to:interact-cli:

Command line interface
======================

AiiDA comes with a command line interface called ``verdi``.
The :ref:`reference:command-line` section gives an overview of all available commands.
For more detailed information, refer to the topic section :ref:`topics:cli`.

.. tip::

    The ``verdi`` command line interface can also be explored as a `text-based user interface <https://en.wikipedia.org/wiki/Text-based_user_interface>`_ (TUI).
    It requires ``aiida-core`` to be installed with the ``tui`` extra (e.g. ``pip install aiida-core[tui]``).
    The TUI can then be launched with ``verdi tui``.


.. _how-to:interact-scripts:

Scripts
=======

AiiDA's Python API can be used in Python scripts mixed with any other Python code.
The only requirement is that before the API is used an AiiDA profile is loaded.
The recommended way of accomplishing this is to run the script through the command line interface:

.. code-block:: console

    verdi run script.py

The ``verdi`` CLI will automatically load the default profile, before calling the actual script, passing any command line arguments that may have been specified.

.. note::

    A :ref:`different profile can be selected <topics:cli:profile>` using the ``--profile`` option, just as for all other ``verdi`` commands.

Alternatively, one can also add AiiDA's specific `shebang <https://en.wikipedia.org/wiki/Shebang_(Unix)>`_ to the top of the file.

.. code-block:: bash

    #!/usr/bin/env runaiida

When a script starts with this shebang, when it is executed, it is automatically passed to ``verdi run`` just as if it would have been called through ``verdi run`` directly.
This has the advantage that one no longer has to explicitly type ``verdi run`` when running the script, but can simply make it executable and execute it directly.
The downside is that it does not allow to specify a particular profile, but it always loads the default profile.

If, for whatever reason, ``verdi run`` nor the special shebang can be used, a profile can also be loaded directly through the API within the Python script itself:

.. code-block:: python

    from aiida import load_profile
    load_profile()

One can pass a particular profile name to :meth:`~aiida.manage.configuration.load_profile`, otherwise the default profile is loaded.

Within a script or Python instance, you can also switch to a different profile, or use one within a context manager:

.. code-block:: python

    from aiida import load_profile, profile_context, orm

    with profile_context('my_profile_1'):
        # The profile will be loaded within the context
        node_from_profile_1 = orm.load_node(1)
        # then the profile will be unloaded automatically

    # load a global profile
    load_profile('my_profile_2')
    node_from_profile_2 = orm.load_node(1)

    # switch to a different global profile
    load_profile('my_profile_3', allow_switch=True)
    node_from_profile_3 = orm.load_node(1)

.. _how-to:interact-shell:

Interactive shells
==================

AiiDA provides a Python API that can be used from an interactive shell, such as `IPython <https://ipython.org/>`_.
The recommended way of starting an interactive shell session to work with AiiDA, is through the command line interface:

.. code-block:: console

    $ verdi shell

This command will open a normal IPython shell but automatically loads the default AiiDA profile, which is required to use the Python API.

.. note::

    A :ref:`different profile can be selected <topics:cli:profile>` using the ``--profile`` option, just as for all other ``verdi`` commands.

In addition to automatically loading an AiiDA profile, certain modules from AiiDA's API that are used very often are automatically imported.
The modules that are pre-loaded can be configured using the :ref:`reference:command-line:verdi-config` command.

If, for whatever reason, you cannot use ``verdi shell``, a profile can also be loaded directly through the API within the shell itself:

.. code-block:: ipython

    In [1]: from aiida import load_profile

    In [2]: load_profile()
    Out[2]: <aiida.manage.configuration.profile.Profile at 0x7fccfd6c50a0>

One can pass a particular profile name to :meth:`~aiida.manage.configuration.load_profile`, otherwise the default profile is loaded.


.. _how-to:interact-notebook:

Interactive notebooks
=====================

Similar to :ref:`interactive shells <how-to:interact-shell>`, AiiDA is also directly compatbile with interactive Python notebooks, such as `Jupyter <https://jupyter.org/>`_.
To install the required Python packages, install ``aiida-core`` with the ``notebook`` extra, e.g. run:

.. code-block:: console

    pip install aiida-core[notebook]

You should now be able to start a Jupyter notebook server:

.. code-block:: console

    jupyter notebook

To use AiiDA's Python API in a notebook, first a profile has to be loaded:

.. code-block:: ipython

    In [1]: from aiida import load_profile

    In [2]: load_profile()
    Out[2]: <aiida.manage.configuration.profile.Profile at 0x7fccfd6c50a0>

One can pass a particular profile name to :meth:`~aiida.manage.configuration.load_profile`, otherwise the default profile is loaded.
The same can be accomplished using the following magic statement:

.. code-block:: ipython

    %load_ext aiida
    %aiida

This magic line replicates the same environment as :ref:`the interactive shell <how-to:interact-shell>` provided by ``verdi shell``.

It is also possible to run ``verdi`` commands inside the notebook, for example:

.. code-block:: ipython

   %verdi status


Running AiiDA engine processes in notebooks
-------------------------------------------

AiiDA supports running engine processes (such as calculation functions and work chains) directly in Jupyter notebooks.
When :meth:`~aiida.manage.configuration.load_profile` is called inside a Jupyter notebook, AiiDA automatically sets up the necessary infrastructure to allow synchronous process execution within the notebook's event loop.

.. important::

    ``load_profile()`` must be called in a **separate cell** before any AiiDA engine processes can be executed.
    The setup takes effect from the **next cell** after loading the profile.

For example, load the profile in the first cell:

.. code-block:: ipython

    In [1]: from aiida import load_profile
       ...: load_profile()

Then, in a subsequent cell, you can run engine processes as usual:

.. code-block:: ipython

    In [2]: from aiida.engine import calcfunction
       ...: from aiida import orm
       ...:
       ...: @calcfunction
       ...: def add(x, y):
       ...:     return orm.Int(x.value + y.value)
       ...:
       ...: result = add(orm.Int(3), orm.Int(4))
       ...: print(result)

.. warning::

    Attempting to run engine processes in the **same cell** where ``load_profile()`` is called will raise an error.
    Always ensure the profile is loaded in a separate cell.


.. _how-to:interact-restapi:

REST API
========

AiiDA ships with a built in REST API, that allows you to query the data of a particular profile.
Refer to section :ref:`how-to:share:serve:launch` to learn how to start the REST API.
The section :ref:`how-to:share:serve:query` provides information on how to interact with a running REST API.
