.. _virtual_environment:

===================
Virtual environment
===================

Why a virtual environment?
++++++++++++++++++++++++++

AiiDA depends on third party python packages and very often on specific versions of those packages.
If AiiDA were to be installed system wide, it may up- or downgrade third party packages used by other parts of the system and leave them potentially broken.
Conversely, if a different version of a package is later installed which is incompatible with AiiDA, it too will become broken.

In short, installing AiiDA might interfere with installed python packages and installing other packages might interfere with AiiDA.
Since your scientific data is important to you and to us, we *strongly* recommend isolating AiiDA in what is called a virtual environment.

For a single purpose machine, only meant to run AiiDA and nothing else, you may at your own risk opt to omit working in a virtual environment.
In this case, you may want to install AiiDA and its dependencies in user space by using a ``--user`` flag, to avoid the need for administrative rights to install them system wide.

What is a virtual environment?
++++++++++++++++++++++++++++++
A python virtual environment is essentially a folder, that contains everything that is needed to run python programs, including

* python executable
* python standard packages
* package managers such as ``pip``
* an activation script that sets the ``PYTHONPATH`` and ``PATH`` variables

The ``python`` executable might be a link to an executable elsewhere, depending on the way the environment is created.
The activation script ensures that the python executable of the virtualenv is the first in ``PATH``, and that python programs have access only to packages installed inside the virtualenv (unless specified otherwise during creation).
This allows to have an isolated environment for programs that rely on running with a specific version of python or specific versions of third party python packages.

A virtual environment as well as the packages that will be installed within it, will often be installed in the home space of the user such that administrative rights are not required, therefore also making this technique very useful on machines where one has restricted access.

Creating a virtual environment
++++++++++++++++++++++++++++++
There are different programs that can create and work with virtual environments.
An example for python virtual environments is called ``virtualenv`` and can be installed with for example ``pip`` by running::

    $ pip install --user -U virtualenv

As explained before, a virtual environment is in essence little more than a directory containing everything it needs.
In principle a virtual environment can thus be created anywhere where you can create a directory.
You could for example opt to create a directory for all your virtual environments in your home folder::

    $ mkdir ~/.virtualenvs

Using ``virtualenv`` you can then create a new virtual environment with python 2.7 by running::

    $ virtualenv --python=<path/to/python2.7> ~/.virtualenvs/my_env

This will create the environment ``my_env`` and automatically activate it for you.
If you open a new terminal, or you have deactivated the environment, you can reactivate it as follows::

    $ ~/.virtualenvs/my_env/bin/activate

If it is activated successfully, you should see that your prompt is prefixed with the name of the environment::

    (my_env) $

To leave or deactivate the environment and set all the settings back to default, simply run::

    (my_env) $ deactivate


.. _aiida_path_in_virtualenv:

Creating a ``.aiida`` folder in your virtualenvironment
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

When you run AiiDA in multiple virtual environments, it can be convenient to use a separate ``.aiida`` folder for each virtualenv. To do this, you can use the :ref:`AIIDA_PATH mechanism <directory_location>` as follows:

1. Create your virtualenv, as described above
2. Create a ``.aiida`` directory in your virtualenv directory::

    $ mkdir ~/.virtualenvs/my_env/.aiida
3. At the end of ``~/.virtualenvs/my_env/bin/activate``, add the following line::

    export AIIDA_PATH='~/.virtualenvs/my_env'
4. Deactivate and re-activate the virtualenv
5. You can test that everything is set up correctly if you can reproduce the following::

    (my_env)$ echo $AIIDA_PATH
    >>> ~/.virtualenvs/my_env

    (my_env)$ verdi profile list
    >>> Configuration folder: /home/my_username/.virtualenvs/my_env/.aiida
    >>> Stopping: No configuration file found
    >>> Note: if no configuration file was found, it means that you have not run
    >>> 'verdi setup' yet to configure at least one AiiDA profile.
6. Continue setting up AiiDA with ``verdi setup`` or ``verdi quicksetup``.



