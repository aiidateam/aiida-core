.. _optional_configuration:

======================
Optional configuration
======================

.. _tab-completion:

Verdi tab-completion
++++++++++++++++++++
The ``verdi`` command line tool has many commands and options.
To simplify its usage, there is a way to enable tab-completion for it in your bash shell.
To do so, simply run the following command::

    $ verdi completioncommand

and append the result to the activation script of your virtual environment (or to your bash config, e.g. ``.bashrc``).
Alternatively, you can accomplish the same by simply adding the following line to the activation script::

    eval "$(verdi completioncommand)"

For the changes to apply to your current shell, make sure to source the activation script or ``.bashrc`` (depending the approach you chose).

Adding AiiDA to the PATH
++++++++++++++++++++++++
If you used a virtual environment for the installation of AiiDA, the required commands such as ``verdi`` should have been added automatically to your ``PATH``.
Otherwise, you may have to add the install directory of AiiDA manually to your ``PATH`` so that the binaries are found.

For Linux systems, the path to add is usually ``~/.local/bin``::

    export PATH=~/.local/bin:${PATH}

For Mac OS X systems, the path to add is usually ``~/Library/Python/2.7/bin``::

    export PATH=~/Library/Python/2.7/bin:${PATH}

To verify if this is the correct path to add, navigate to this location and you should find the executable ``supervisord``, or ``celeryd``, in the directory.

After updating your ``PATH`` you can check if it worked in the following way:

* type ``verdi`` on your terminal, and check if the program starts (it should
  provide a list of valid commands). If it doesn't, check if you correctly set
  up the ``PATH`` environment variable above.
* go into your home folder or in another folder different from the AiiDA folder,
  run ``python`` or ``ipython`` and try to import a module, e.g. typing::

    import aiida

  If the setup is ok, you shouldn't get any error. If you do get an ``ImportError`` instead, check
  that you are in the correct virtual environment. If you did not install AiiDA
  within a virtual environment, you will have to set up the ``PYTHONPATH``
  environment variable in your ``.bashrc``::

    export PYTHONPATH="${PYTHONPATH}:<AiiDA_folder>"

.. _directory_location:

Customizing the configuration directory location
++++++++++++++++++++++++++++++++++++++++++++++++

By default, the AiiDA configuration is stored in the directory ``~/.aiida``. This can be changed by setting the ``AIIDA_PATH`` environment variable. The value of ``AIIDA_PATH`` can be a colon-separated list of paths. For each of the paths in the list, AiiDA will look for a ``.aiida`` directory in the given path and all of its parent folders. If no ``.aiida`` directory is found, ``~/.aiida`` will be used.

For example, the directory structure in your home might look like this ::

    .
    ├── .aiida
    ├── project_a
    │   ├── .aiida
    │   └── subfolder
    └── project_b
        └── .aiida

If you set ::

    export AIIDA_PATH='~/project_a:~/project_b'

the configuration directory used will be ``~/project_a/.aiida``. The same is true if you set ``AIIDA_PATH='~/project_a/subdir'``, because ``subdir`` itself does not contain a ``.aiida`` folder, so AiiDA will first check its parent directories.

If you set ``AIIDA_PATH='.'``, the configuration directory used depends on the current working directory. Inside the ``project_a`` and ``project_b`` directories, their respective ``.aiida`` directory will be used. Outside of these directories, ``~/.aiida`` is used.

An example for when this option might be used is when two different AiiDA versions are used simultaneously. Using two different ``.aiida`` directories also allows running two daemon concurrently.
Note however that this option does **not** change the database cluster that is being used. This means that by default you still need to take care that the database names do not clash.

Using AiiDA in Jupyter
++++++++++++++++++++++

`Jupyter <http://jupyter.org>`_ is an open-source web application that allows you to create in-browser notebooks containing live code, visualizations and formatted text.

Originally born out of the iPython project, it now supports code written in many languages and customized iPython kernels.

If you didn't already install AiiDA with the ``[notebook]`` option (during ``pip install``), run ``pip install jupyter`` **inside** the virtualenv, and then run **from within the virtualenv**::

    $ jupyter notebook

This will open a tab in your browser. Click on ``New -> Python 2`` and type::

    import aiida

followed by ``Shit-Enter``. If no exception is thrown, you can use AiiDA in Jupyter.

If you want to set the same environment as in a ``verdi shell``, add the following code in ``<your.home.folder>/.ipython/profile_default/ipython_config.py``::

  try:
      import aiida
  except ImportError:
      pass
  else:
      c = get_config()
      c.InteractiveShellApp.extensions = [
            'aiida.common.ipython.ipython_magics'
      ]

then open a Jupyter notebook as explained above and type in a cell:

    %aiida

followed by ``Shift-Enter``. You should receive the message "Loaded AiiDA DB environment."


.. _virtual-environment:


