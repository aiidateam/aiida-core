.. _troubleshooting:

Troubleshooting
===============

Installation phase
------------------

* [**numpy dependency**] On a clean Ubuntu 16.04 install the pip install command ``pip install -e aiida_core``
  may fail due to a problem with dependencies on the ``numpy`` package. In this case
  you may be presented with a message like the following::

    from numpy.distutils.misc_util import get_numpy_include_dirs
    ImportError: No module named numpy.distutils.misc_util

  To fix this, simply install ``numpy`` individually through pip in your virtual env, i.e.::

    pip install numpy

  followed by executing the original install command once more::

    pip install -e .

  This should fix the dependency error.

* [**Database installation and location**] If the installation fails while installing the packages related
  to the database, you may have not installed or set up the database
  libraries.

  In particular, on Mac OS X, if you installed the binary package of
  PostgreSQL, it is possible that the PATH environment variable is not
  set correctly, and you get a "Error: pg_config executable not found." error.
  In this case, discover where the binary is located, then add a line to
  your ``~/.bashrc`` file similar to the following::

    export PATH=/the/path/to/the/pg_config/file:${PATH}

  and then open a new bash shell.
  Some possible paths can be found at this
  `Stackoverflow link`_ and a non-exhaustive list of possible
  paths is the following (version number may change):

  * ``/Applications/Postgres93.app/Contents/MacOS/bin``
  * ``/Applications/Postgres.app/Contents/Versions/9.3/bin``
  * ``/Library/PostgreSQL/9.3/bin/pg_config``

  Similarly, if the package installs but then errors occur during the first
  of AiiDA (with ``Symbol not found`` errors or similar), you may need to
  point to the path where the dynamical libraries are. A way to do it is to
  add a line similar to the following to the ``~/.bashrc`` and then open
  a new shell::

    export DYLD_FALLBACK_LIBRARY_PATH=/Library/PostgreSQL/9.3/lib:$DYLD_FALLBACK_LIBRARY_PATH

  (you should of course adapt the path to the PostgreSQL libraries).

.. _Stackoverflow link: http://stackoverflow.com/questions/21079820/how-to-find-pg-config-pathlink

* [**ensuring a UTF-8 locale**]For some reasons, on some machines 
  (notably often on Mac OS X) there is no
  default locale defined, and when you run ``verdi setup`` for the first
  time it fails (see also `this issue`_ of django).
  Run in your terminal (or maybe even better, add to your ``.bashrc``, but
  then remember to open a new shell window!)::

     export LANG="en_US.UTF-8"
     export LC_ALL="en_US.UTF-8"

  and then run ``verdi setup`` again.

.. _this issue: https://code.djangoproject.com/ticket/16017

* [**possible Ubuntu dependencies**] Several users reported the need to install 
  also ``libpq-dev`` (header files for libpq5 - PostgreSQL library)::

    apt-get install libpq-dev

  But under Ubuntu 12.04 this is not needed.

Configuring remote SSH computers
--------------------------------

* [**ssh_kerberos installation**] When installing the ``ssh_kerberos`` *optional*
  requirement through Anaconda you may encounter the following error on Ubuntu machines::

    version 'GFORTRAN_1.4' not found (required by /usr/lib/libblas.so.3)

  This is related to an open issue in anaconda `ContinuumIO/anaconda-issues#686`_.
  A potential solution is to run the following command::

    export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libgfortran.so.3

.. _ContinuumIO/anaconda-issues#686: https://github.com/ContinuumIO/anaconda-issues/issues/686

* [**.bashrc and .bash_profile behavior on remote computers**] 
  (**NOTE** This applies also to a computer configured via a ``local`` transport!)
  
  When connecting
  to remote computers, AiiDA (like other codes as ``sftp``) might get very confused
  if you have code in your ``.bashrc`` or ``.bash_profile`` producing output
  or e.g. running commands like ``clean`` that require a terminal.

  For instance, if you add a ``echo "a"`` in your ``.bashrc`` and then try to SFTP
  a file from it, you will get an error like ``Received message too long 1091174400``.

  If you still want to have code that needs an interactive shell (``echo``, 
  ``clean``, ...), but you want to disable it for non-interactive shells, put 
  at the top of your file a guard like this::

    if [[ $- != *i* ]] ; then
      # Shell is non-interactive.  Be done now!
      return
    fi

  Everything below this will not be executed in a non-interactive shell.
  **Note**: Still, you might want to have some code on top, like e.g. setting the PATH or 
  similar, if this needs to be run also in the case of non-interactive shells.

  To test if a the computer does not produce spurious output, run (after 
  configuring)::

     verdi computer test <COMPUTERNAME>

  which checks and, in case of problems, suggests how to solve the problem.
  You can track the discussion on this issue in `aiidateam/aiida_core#1890`_.

.. _aiidateam/aiida_core#1890: https://github.com/aiidateam/aiida_core/issues/1890
.. _StackExchange thread: https://apple.stackexchange.com/questions/51036/what-is-the-difference-between-bash-profile-and-bashrc


Improvements for dependencies
-----------------------------
* [**Activating the ASE visualizer**] Within a virtual environment, 
  attempt to visualize a structure 
  with ``ase`` (either from the shell, or using the 
  command ``verdi data structure show --format=ase <PK>``), 
  might end up with the following error message::
  
     ImportError: No module named pygtk

  The issue is that ``pygtk`` is currently not pip-installable. One has to install it
  separately and create the appropriate bindings manually in the virtual environment.
  You can follow the following procedure to get around this issue:
  
  + Install the ``python-gtk2`` package. Under Ubuntu, do::
     
     sudo apt-get install python-gtk2
  
  + Create the ``lib/python2.7/dist-packages`` folder within your virtual
    environment::
    
     mkdir <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages
     chmod 755 <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages
     
    where ``<AIIDA_VENV_FOLDER>`` is the virtual environment folder you have created
    during the installation process.

  + Create several symbolic links from this folder, pointing to a number of files
    in ``/usr/lib/python2.7/dist-packages/``::
    
     cd <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages
     ln -s /usr/lib/python2.7/dist-packages/glib glib
     ln -s /usr/lib/python2.7/dist-packages/gobject gobject
     ln -s /usr/lib/python2.7/dist-packages/gtk-2.0 gtk-2.0
     ln -s /usr/lib/python2.7/dist-packages/pygtk.pth pygtk.pth
     ln -s /usr/lib/python2.7/dist-packages/pygtk.py pygtk.py
     ln -s /usr/lib/python2.7/dist-packages/cairo cairo

  After that, ``verdi data structure show --format=ase <PK>`` should work.

Use in ipython/jupyter
----------------------

* In order to use the AiiDA objects and functions in Jupyter, this latter has to be instructed to use the iPython kernel installed in the AiiDA virtual environment. This happens by default if you install AiiDA with ``pip`` including the ``notebook`` option and run Jupyter from the AiiDA virtual environment.

  If, for any reason, you do not want to install Jupyter in the virtual environment, you might consider to install it out of the virtual environment, if not already done::

      $ pip install jupyter

  Then, activate the AiiDA virtual environment::

      $ source ~/<aiida.virtualenv>/bin/activate

  and setup the AiiDA iPython kernel::

      $ pip install ipykernel
      $ python -m ipykernel install --user --name=<aiida.kernel.name>

  where you have chosen a meaningful name for the new kernel.

  Finally, start a Jupyter server::

      $ jupyter notebook

  and from the newly opened browser tab select ``New -> <aiida.kernel.name>``

.. _updating_aiida:

For developers (testing)
------------------------

* [**Making the SSH tests pass**] The developer tests of the *SSH* transport plugin are
  performed connecting to ``localhost``. The tests will fail if
  a passwordless ssh connection is not set up. Therefore, if you want to run
  the tests:

  + make sure to have a ssh server. On Ubuntu, for instance, you can install
    it using::

       sudo apt-get install openssh-server

  + Configure a ssh key for your user on your machine, and then add
    your public key to the authorized keys of localhsot.
    The easiest way to achieve this is to run::

       ssh-copy-id localhost

    (it will ask your password, because it is connecting via ssh to ``localhost``
    to install your public key inside ~/.ssh/authorized_keys).

