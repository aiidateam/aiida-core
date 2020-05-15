.. _configure_aiida:

Configure AiiDA
===============

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
