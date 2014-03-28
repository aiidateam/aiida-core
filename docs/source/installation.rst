====================================
Installation and Deployment of AiiDA
====================================

Supported architecture
++++++++++++++++++++++
AiiDA has a few strict requirements, in its current version:
first, it will run only on Unix-like systems - it
is tested (and developed) in Mac OS X and Linux (Ubuntu), but other Unix
flavours *should* work as well.

Moreover, on the clusters (computational resources) side, it expects to find
a Unix system, and the default shell is **required** to be ``bash``. 

Installing python
+++++++++++++++++

AiiDA requires python 2.7.x (only CPython has been tested).
It is probable that you already have a version of
python installed on your computer. To check, open a terminal and type::

    python -V

that will print something like this::
    
    Python 2.7.3
    
If you don't have python installed, or your version is outdated, please install
a suitable version of python (either refer to the manual of your Linux 
distribution, or for instance you can download the ActiveState Python from
ActiveState_. Choose the appropriate distribution corresponding to your 
architecture, and with version 2.7.x.x).

.. _ActiveState: http://www.activestate.com/activepython/downloads

Installation of the core dependencies
+++++++++++++++++++++++++++++++++++++

Database
--------

As a first thing, :doc:`choose and setup the database that you want to
use<database/index>`.

Other core dependencies
-----------------------

Before continuing, you still need to install a few more programs. Some of them 
are mandatory, while others are optional (but often strongly suggested), also
depending for instance on the :doc:`type of database <database/index>`
that you plan to use.

Here is a list of packages/programs that you need to install (for each of them,
there may be a specific/easier way to install them in your distribution, as
for instance ``apt-get`` in Debian/Ubuntu -see below for the specific names
of packages to install- or ``yum`` in RedHat/Fedora).

* `git`_ (required to download the code)
* `python-pip`_ (required to automatically download and install further
  python packages required by AiiDA)
* `ipython`_ (optional, but strongly recommended for interactive usage)
* python 2.7 development files (these may be needed; refer to your distribution
  to know how to locate and install them)
* To support  SQLite:

  * `SQLite3 development files`_ (required later to compile the library,
    when configuring the python sqlite module)

.. _git: http://git-scm.com/
.. _python-pip: https://pypi.python.org/pypi/pip
.. _ipython: http://ipython.org/
.. _SQLite3 development files: http://www.sqlite.org/

For Ubuntu, you can install the above packages using (tested on Ubuntu 12.04,
names may change in different releases)::

      sudo apt-get install git
      sudo apt-get install python-pip
      sudo apt-get install ipython
      sudo apt-get install python2.7-dev
      sudo apt-get install libsqlite3-dev

Downloading the code
++++++++++++++++++++

Download the code using git in a directory of your choice (``~/git/aiida`` in
this tutorial), using the
following command::

    git clone https://pizzi@bitbucket.org/aiida_team/aiida.git ~/git/aiida

(or use ``git@bitbucket.org:aiida_team/aiida.git`` if you are downloading
through SSH; note that this requires your ssh key to be added on the
Bitbucket account.)

Python dependencies
+++++++++++++++++++
Python dependencies are managed using ``pip``, that you have installed in the
previous steps.

As a first step, check that ``pip`` is at its most recent version.

One possible way of doing this is to update ``pip`` with itself, with
a command similar to the following::

  sudo pip install -U pip

Then, install the python dependencies is as simple as this::

      cd ~/git/aiida # or the folder where you downloaded AiiDA
      pip install --user -U -r requirements.txt

(this will download and install requirements that are listed in the
``requirements.txt`` file; the ``--user`` option allows to install
the packages as a normal user, without the need of using ``sudo`` or
becoming root). Check that every package is installed correctly.

If everything went smoothly, congratulations! Now the code is installed!
However, we need still a few steps to properly configure AiiDA for your user.

Note : if the ``pip install`` command gives you an error that ressembles the one
shown below, you will need to downgrade to an older version of pip::

	Cannot fetch index base URL https://pypi.python.org/simple/

To downgrade pip, use the following command::

	sudo easy_install pip==1.2.1


AiiDA configuration
+++++++++++++++++++

Path configuration
------------------

The main interface to AiiDA is through its command-line tool, called ``verdi``.
For it to work, it must be on the system path, and moreover the AiiDA python
code must be found on the python path. 

To do this, add the following to your ``~/.bashrc`` file (create it if not already present)::

      export PYTHONPATH=~/git/aiida:${PYTHONPATH}
      export PATH=~/git/aiida/bin:${PATH}

and then source the .bashrc file with the command ``source ~/.bashrc``, or login
in a new window.

.. note:: replace ``~/git/aiida`` with the path where you installed AiiDA. Note
  also that in the ``PYTHONPATH`` you simply have to specify the AiiDA path, while
  in ``PATH`` you also have to append the ``/bin`` subfolder!

.. note:: if you installed the modules with the ``--user`` parameter during the
  ``pip install`` step, you will need to add one more directory to your ``PATH``
  variable in the ``~/.bashrc`` file.
  For Linux systems, the path to add is usually ``~/.local/bin``::
  
  	export PATH=~/git/aiida/bin:~/.local/bin:${PATH}
  
  For Mac OS X systems, the path to add is usually ``~/Library/Python/2.7/bin``::
  
  	export PATH=~/git/aiida/bin:~/Library/Python/2.7/bin:${PATH}
  
  To verify if this is the correct path to add, navigate to this location and
  you should find the executable ``supervisord`` in the directory.

To verify if the path setup is OK:

* type ``verdi`` on your terminal, and check if the program starts (it should 
  provide a list of valid commands). If it doesn't, check if you correctly set
  up the ``PATH`` environmente variable above.
* go in your home folder or in another folder different from the AiiDA folder,
  run ``python`` or ``ipython`` and try to import a module, e.g. typing::

    import aiida
    
  If the setup is ok, you shouldn't get any error. If you do get an
  ``ImportError`` instead, check if you correctly set up the ``PYTHONPATH``
  environment variable in the steps above.


Bash completion
^^^^^^^^^^^^^^^

``verdi`` fully supports bash completion (i.e., the possibility to press the
``TAB`` of your keyboard to get a list of sensible commands to type.
We strongly suggest to enable bash completion by adding also the following
line to your ``.bashrc``, **after** the previous lines::
   
   eval "$(verdi completioncommand)"

If you feel that the bash loading time is becoming too slow, you can instead
run the::

    verdi completioncommand
    
on a shell, and copy-paste the output directly inside your ``.bashrc`` file,
**instead** of the ``eval "$(verdi completioncommand)"`` line.
    
Remember, after any modification to the ``.bashrc`` file, to source it,
or to open a new shell window. 

.. note:: remember to check that your ``.bashrc`` is sourced also from your
  ``.profile`` or ``.bash_profile`` script. E.g., if not already present,
  you can add to your ``~/.bash_profile`` the following lines::

    if [ -f ~/.bashrc ] 
    then
        . ~/.bashrc
    fi



AiiDA first setup
-----------------

Run the following command::

    verdi install
    
to configure AiiDA. The command will guide you through a process to configure
the database, the repository location, and it will finally (automatically) run 
a ``verdi syncdb`` command, that creates the required tables in the database
and installs the database triggers.

.. note:: If this is your first installation, the code (Django, actually)
  will ask to setup an admin user ("Would you like to create one now?" prompt).
  In this case chose ``yes`` and type the required information. Some notes:

  * **Make sure that the username matches your local machine username!** This is
    required for the current version of AiiDA to work.
  * The password, in the current version of AiiDA, is not used (even if a non-null
    password should be specified).

If something fails, you may have misconfigured the database.

Start the daemon
-----------------
To try AiiDA, run::

    verdi daemon start

to start the daemon. If everything was done correctly, the daemon should start.
You can inquire the daemon status using::

    verdi daemon status

and, if the daemon is running, you should see something like::

  * aiida-daemon[0]        RUNNING    pid 12076, uptime 0:39:05
  * aiida-daemon-beat[0]   RUNNING    pid 12075, uptime 0:39:05


To stop the daemon, use::

    verdi daemon stop

Detailed logs of what is going can be found in ``in ~/.aiida/daemon/log/``. The daemon is 
a fundamental component of AiiDA, and it is in charge of submitting new
calculations, checking their status on the cluster, retrieving and parsing
the results of finished calculations, and managing the workflow steps.

**Congratulations, your setup is complete!**

Before going on, however, you will need to setup *at least one computer* (i.e.,
on computational resource as a cluster or a supercomputer, on which you want 
to run your calculations) *and one code*. The documentation for these steps can
be found :doc:`here<setup/computerandcodes>`.


Further comments and troubleshooting
++++++++++++++++++++++++++++++++++++

* For some reasons, on some machines (notably often on Mac OS X) there is no
  default locale defined, and when you run ``verdi syncdb`` for the first
  time it fails (see also `this issue`_ of django).  To solve the problem, first
  remove the sqlite database that was created. 
  
  Then, run in your terminal (or maybe even better, add to your ``.bashrc``, but
  then remember to open a new shell window!)::
  
     export LANG="en_US.UTF-8"
     export LC_ALL="en_US.UTF-8"

  and then run ``verdi syncdb`` again.

.. _this issue: https://code.djangoproject.com/ticket/16017

* [*Only for developers*] The developer tests of the *SSH* transport plugin are 
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
