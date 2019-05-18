.. _configure_aiida:

Configure AiiDA
===============

.. _tab-completion:

Verdi tab-completion
--------------------
The ``verdi`` command line interface has many commands and options,
which can be tab-completed to simplify your life.
Enable tab-completion with the following shell command::

    eval "$(_VERDI_COMPLETE=source verdi)"

Place this command in your startup file, i.e. one of

* the startup file of your shell (``.bashrc``, ``.zsh``, ...), if aiida is installed system-wide
* the `activate script <https://virtualenv.pypa.io/en/latest/userguide/#activate-script>`_ of your virtual environment
* a `startup file <https://conda.io/docs/user-guide/tasks/manage-environments.html#saving-environment-variables>`_ for your conda environment

In order to enable tab completion in your current shell,
make sure to source the startup file once.

.. note::
    This line replaces the ``eval "$(verdi completioncommand)"`` line that was used in ``aiida-core<1.0.0``. While this continues to work, support for the old line may be dropped in the future.


.. _directory_location:

Using AiiDA in Jupyter
----------------------

`Jupyter <http://jupyter.org>`_ is an open-source web application that allows you to create in-browser notebooks containing live code, visualizations and formatted text.

Originally born out of the iPython project, it now supports code written in many languages and customized iPython kernels.

If you didn't already install AiiDA with the ``[notebook]`` option (during ``pip install``), run ``pip install jupyter`` **inside** the virtualenv, and then run **from within the virtualenv**::

    jupyter notebook

This will open a tab in your browser. Click on ``New -> Python`` and type::

    import aiida

followed by ``Shift-Enter``. If no exception is thrown, you can use AiiDA in Jupyter.

If you want to set the same environment as in a ``verdi shell``,
add the following code to a ``.py`` file (create one if there isn't any) in ``<home_folder>/.ipython/profile_default/startup/``::



  try:
      import aiida
  except ImportError:
      pass
  else:
      import IPython
      from aiida.tools.ipython.ipython_magics import load_ipython_extension

      # Get the current Ipython session
      ipython = IPython.get_ipython()

      # Register the line magic
      load_ipython_extension(ipython)

This file will be executed when the ipython kernel starts up and enable the line magic ``%aiida``.
Alternatively, if you have a ``aiida_core`` repository checked out locally,
you can just copy the file ``<aiida_core>/aiida/tools/ipython/aiida_magic_register.py`` to the same folder.
The current ipython profile folder can be located using::

  ipython locate profile

After this, if you open a Jupyter notebook as explained above and type in a cell::

    %aiida

followed by ``Shift-Enter``. You should receive the message "Loaded AiiDA DB environment."
This line magic should also be enabled in standard ipython shells.

Customizing the configuration directory location
------------------------------------------------

By default, the AiiDA configuration is stored in the directory ``~/.aiida``.
This can be changed by setting the ``AIIDA_PATH`` environment variable.
The value of ``AIIDA_PATH`` can be a colon-separated list of paths.
For each of the paths in the list, AiiDA will look for a ``.aiida`` directory in the given path.
The first configuration folder that is encountered will be used
If no ``.aiida`` directory is found in any of the paths found in the environment variable, one will be created automatically in the last path that was considered.

For example, the directory structure in your home might look like this ::

    .
    ├── .aiida
    └── project_a
        ├── .aiida
        └── subfolder


If you leave the ``AIIDA_PATH`` variable unset, the default location in your home will be used.
However, if you set ::

    export AIIDA_PATH='~/project_a:'

The configuration directory used will be ``~/project_a/.aiida``.

.. warning::
    Note that even if the sub directory ``.aiida`` would not yet have existed in ``~/project_a``, AiiDA will automatically create it for you.
    Be careful therefore to check that the path you set for ``AIIDA_PATH`` is correct.


