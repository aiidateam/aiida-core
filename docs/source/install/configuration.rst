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

Isolating AiiDA environments
----------------------------

By default, the AiiDA configuration is stored in the directory ``~/.aiida``.
When running AiiDA in multiple virtual environments (using ``virtualenv`` or ``conda``),
you can ask AiiDA to use a separate ``.aiida`` configuration directory per environment.

1. Create your virtual environment ``aiida2``
2. Edit the activation script ``~/.virtualenvs/aiida2/bin/activate``
   and append a line to set the ``AIIDA_PATH`` environment variable::

    export AIIDA_PATH='~/.virtualenvs/aiida2'  # use .aiida configuration in this folder
    eval "$(_VERDI_COMPLETE=source verdi)"  # e.g. set up tab completion

.. note::
   For ``conda``,     create a directory structure ``etc/conda/activate.d`` in
   the root folder of your conda environment (e.g.
   ``/home/user/miniconda/envs/aiida``), and place a file ``aiida-init.sh`` in
   that folder which exports the ``AIIDA_PATH``.

3. Deactivate and re-activate the virtual environment

You can test that everything is set up correctly if you can reproduce the following::

    (aiida2)$ echo $AIIDA_PATH
    >>> ~/.virtualenvs/aiida2

    (aiida2)$ verdi profile list
    >>> Info: configuration folder: /home/my_username/.virtualenvs/aiida/.aiida2
    >>> Critical: configuration file /home/my_username/.virtualenvs/aiida/.aiida2/config.json does not exist

Now simply :ref:`create a new AiiDA profile <setup_aiida>` in the ``aiida2`` environment.

``AIIDA_PATH`` Details
......................

The value of ``AIIDA_PATH`` can be a colon-separated list of paths.
AiiDA will go through each of the paths and check whether they contain a ``.aiida`` directory.
The first configuration directory that is encountered will be used.
If no ``.aiida`` directory is found, one will be created in the last path that was considered.

For example, the directory structure in your home folder ``~/`` might look like this ::

    .
    ├── .aiida
    └── project_a
        ├── .aiida
        └── subfolder


If you leave the ``AIIDA_PATH`` variable unset, the default location ``~/.aiida`` will be used.
However, if you set ::

    export AIIDA_PATH='~/project_a:'

the configuration directory ``~/project_a/.aiida`` will be used.

.. warning::
    If there was no ``.aiida`` directory in ``~/project_a``, AiiDA would have created it for you.
    Thus make sure to set the ``AIIDA_PATH`` correctly.


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
Alternatively, if you have a ``aiida-core`` repository checked out locally,
you can just copy the file ``<aiida-core>/aiida/tools/ipython/aiida_magic_register.py`` to the same folder.
The current ipython profile folder can be located using::

  ipython locate profile

After this, if you open a Jupyter notebook as explained above and type in a cell::

    %aiida

followed by ``Shift-Enter``. You should receive the message "Loaded AiiDA DB environment."
This line magic should also be enabled in standard ipython shells.
