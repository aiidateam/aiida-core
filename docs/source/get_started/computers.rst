.. _setup_computer:

****************
Setup a computer
****************

A computer in AiiDA denotes any computational resource (with a batch job scheduler) on which you will run your calculations.
Computers typically are clusters or supercomputers.

Remote computer requirements
============================

Requirements for a computer are:

* It must run a Unix-like operating system
* The default shell must be ``bash``
* It should have a batch scheduler installed (see :doc:`here <../scheduler/index>`
  for a list of supported batch schedulers)
* It must be accessible from the machine that runs AiiDA using one of the 
  available transports (see below).
  
The first step is to choose the transport to connect to the computer. Typically,
you will want to use the SSH transport, apart from a few special cases where
SSH connection is not possible (e.g., because you cannot setup a password-less
connection to the computer). In this case, you can install AiiDA directly on
the remote cluster, and use the ``local`` transport (in this way, commands to 
submit the jobs are simply executed on the AiiDA machine, and files are simply
copied on the disk instead of opening an SFTP connection).

If you plan to use the ``local`` transport, you can skip to the next section.

If you plan to use the ``SSH`` transport, you have to configure a password-less
login from your user to the cluster. To do so type first (only if you do not 
already have some keys in your local ``~/.ssh directory`` - i.e. files like 
``id_rsa.pub``)::

    ssh-keygen -t rsa
    
Then copy your keys to the remote computer (in ~/.ssh/authorized_keys) with::

    ssh-copy-id YOURUSERNAME@YOURCLUSTERADDRESS

replacing ``YOURUSERNAME`` and ``YOURCLUSTERADDRESS`` by respectively your username 
and cluster address. Finally add the following lines to ~/.ssh/config (leaving an empty
line before and after)::

  Host YOURCLUSTERADDRESS
    User YOURUSERNAME
    IdentityFile YOURRSAKEY

replacing ``YOURRSAKEY`` by the path to the rsa private key you want to use 
(it should look like ``~/.ssh/id_rsa``).

.. note:: In principle you don't have to put the ``IdentityFile`` line if you have
  only one rsa key in your ``~/.ssh`` folder.

Before proceeding to setup the computer, be sure that you are able to
connect to your cluster using::

   ssh YOURCLUSTERADDRESS
   
without the need to type a password. Moreover, make also sure you can connect
via ``sftp`` (needed to copy files). The following command::

   sftp YOURCLUSTERADDRESS

should show you a prompt without errors (possibly with a message saying
``Connected to YOURCLUSTERADDRESS``).

.. note:: If the ``ssh`` command works, but the ``sftp`` command does not
  (e.g. it just prints ``Connection closed``), a possible reason can be
  that there is a line in your ``~/.bashrc`` that either produces an output, 
  or an error. Remove/comment it until no output or error is produced: this
  should make ``sftp`` working again.

Finally, try also::

   ssh YOURCLUSTERADDRESS QUEUE_VISUALIZATION_COMMAND
   
replacing ``QUEUE_VISUALIZATION_COMMAND`` by the scheduler command that prints on screen the
status of the queue on the cluster (i.e. ``qstat`` for PBSpro scheduler, ``squeue`` for SLURM, etc.).
It should print a snapshot of the queue status, without any errors. 

.. note:: If there are errors with the previous command, then
  edit your ~/.bashrc file in the remote computer and add a line at the beginning
  that adds the path to the scheduler commands, typically (here for
  PBSpro)::
  
     export PATH=$PATH:/opt/pbs/default/bin

  Or, alternatively, find the path to the executables (like using ``which qsub``)

.. note:: If you need your remote .bashrc to be sourced before you execute the code
  (for instance to change the PATH), make sure the .bashrc file **does not** contain
  lines like::

     [ -z "$PS1" ] && return
    
  or::

     case $- in
         *i*) ;;
         *) return;;
     esac
    
  in the beginning (these would prevent the bashrc to be executed when you ssh
  to the remote computer). You can check that e.g. the PATH variable is correctly
  set upon ssh, by typing (in your local computer)::

     ssh YOURCLUSTERADDRESS 'echo $PATH'


.. note:: If you need to ssh to a computer A first, from which you can then
     connect to computer B you wanted to connect to, you can use the
     ``proxy_command`` feature of ssh, that we also support in
     AiiDA. For more information, see :ref:`ssh_proxycommand`.


.. _computer_setup:

Computer setup and configuration
================================
The configuration of computers happens in two steps.

.. note:: The commands use some ``readline`` extensions to provide default
  answers, that require an advanced terminal. Therefore, run the commands from
  a standard terminal, and not from embedded terminals as the ones included in
  text editors, unless you know what you are doing. For instance, the 
  terminal embedded in ``emacs`` is known to give problems.

1. **Setup of the computer**, using the::

    verdi computer setup
    
   command. This command allows to create a new computer instance in the DB.
   
   .. tip:: The code will ask you a few pieces of information. At every prompt, you can
     type the ``?`` character and press ``<enter>`` to get a more detailed
     explanation of what is being asked. 
  
   .. tip:: You can press ``<CTRL>+C`` at any moment to abort the setup process.
     Nothing will be stored in the DB.
   
   .. note:: For multiline inputs (like the prepend text and the append text, see below)
     you have to press ``<CTRL>+D`` to complete the input, even if you do not want
     any text.
   
   Here is a list of what is asked, together with an explanation.
   
   * **Computer name**: the (user-friendly) name of the new computer instance 
     which is about to be created in the DB (the name is used for instance when 
     you have to pick up a computer to launch a calculation on it). Names must 
     be unique. This command should be thought as a AiiDA-wise configuration of 
     computer, independent of the AiiDA user that will actually use it.

   * **Fully-qualified hostname**: the fully-qualified hostname of the computer
     to which you want to connect (i.e., with all the dots: ``bellatrix.epfl.ch``, 
     and not just ``bellatrix``). Type ``localhost`` for the local transport.

   * **Description**:  A human-readable description of this computer; this is 
     useful if you have a lot of computers and you want to add some text to
     distinguish them (e.g.: "cluster of computers at EPFL, installed in 2012, 2 GB of RAM per CPU")

   * **Enabled**: either True or False; if False, the computer is disabled
     and calculations associated with it will not be submitted. This allows to
     disable temporarily a computer if it is giving problems or it is down for
     maintenance, without the need to delete it from the DB.

   * **Transport type**: The name of the transport to be used. A list of valid 
     transport types can be obtained typing ``?``

   * **Scheduler type**: The name of the plugin to be used to manage the
     job scheduler on the computer. A list of valid 
     scheduler plugins can be obtained typing ``?``. See
     :doc:`here <../scheduler/index>` for a documentation of scheduler plugins
     in AiiDA.

   * **shebang line** This is the first line in the beginning of the submission script.
     The default is ``#!/bin/bash``. You can change this in order, for example, to add options,
     as for example the -l option. Note that AiiDA only supports bash at this point!

   * **AiiDA work directory**: The absolute path of the directory on the
     remote computer where AiiDA will run the calculations
     (often, it is the scratch of the computer). You can (should) use the
     ``{username}`` replacement, that will be replaced by your username on the
     remote computer automatically: this allows the same computer to be used
     by different users, without the need to setup a different computer for
     each one. Example::

       /scratch/{username}/aiida_work/

   * **mpirun command**: The ``mpirun`` command needed on the cluster to run parallel MPI
     programs. You can (should) use the ``{tot_num_mpiprocs}`` replacement,
     that will be replaced by the total number of cpus, or the other
     scheduler-dependent fields (see the :doc:`scheduler docs <../scheduler/index>`
     for more information). Some examples::

        mpirun -np {tot_num_mpiprocs}
        aprun -n {tot_num_mpiprocs}
        poe

   * **Text to prepend to each command execution**: This is a multiline string,
     whose content will be prepended inside the submission script before the
     real execution of the job. It is your responsibility to write proper ``bash`` code!
     This is intended for computer-dependent code, like for instance loading a
     module that should always be loaded on that specific computer. *Remember*
     *to end the input by pressing* ``<CTRL>+D``.
     A practical example::

        export NEWVAR=1
        source some/file

     A not-to-do example::

       #PBS -l nodes=4:ppn=12

     (it's the plugin that will do this!)

   * **Text to append to each command execution**: This is a multiline string,
     whose content will be appended inside the submission script after the
     real execution of the job. It is your responsibility to write proper ``bash`` code!
     This is intended for computer-dependent code. *Remember*
     *to end the input by pressing* ``<CTRL>+D``.
   
  At the end, you will get a confirmation command, and also the ID in the
  database (``pk``, i.e. the principal key, and ``uuid``).

2. **Configuration of the computer**, using the::

    verdi computer configure COMPUTERNAME
    
   command. This will allow to access more detailed configurations, that are
   often user-dependent and also depend on the specific transport (for instance,
   if the transport is ``SSH``, it will ask for username, port, ...).

  
   The command will try to provide automatically default answers, mainly reading
   the existing ssh configuration in ``~/.ssh/config``, and in most cases one 
   simply need to press enter a few times.

   .. note:: At the moment, the in-line help (i.e., just typing ``?`` to get
     some help) is not yet supported in ``verdi configure``, but only in
     ``verdi setup``.

   For ``local`` transport, you *need to run the command*,
   even if nothing will be asked to you.
   For ``ssh`` transport, the following will be asked:
   
   * **username**: your username on the remote machine
   * **port**: the port to connect to (the default SSH port is 22)
   * **look_for_keys**: automatically look for the private key in ``~/.ssh``.
     Default: True.
   * **key_filename**: the absolute path to your private SSH key. You can leave
     it empty to use the default SSH key, if you set ``look_for_keys`` to True.
   * **timeout**: A timeout in seconds if there is no response (e.g., the
     machine is down. You can leave it empty to use the default value.
   * **allow_agent**: If True, it will try to use an SSH agent.
   * **proxy_command**: Leave empty if you do not need a proxy command (i.e., 
     if you can directly connect to the machine). If you instead need to connect
     to an intermediate computer first, you need to provide here the
     command for the proxy: see documentation :ref:`here <ssh_proxycommand>` 
     for how to use this option, and in particular the notes
     :ref:`here <ssh_proxycommand_notes>` for the format of this field.
   * **compress**: True to compress the traffic (recommended)
   * **gss_auth**: yes when using Kerberos token to connect
   * **gss_kex**: yes when using Kerberos token to connect, in some cases
     (depending on your ``.ssh/config`` file)
   * **gss_deleg_creds**: yes when using Kerberos token to connect, in 
     some cases (depending on your ``.ssh/config`` file)
   * **gss_host**: hostname when using Kerberos token to connect (default
     to the remote computer hostname)
   * **load_system_host_keys**: True to load the known hosts keys from the
     default SSH location (recommended)
   * **key_policy**: What is the policy in case the host is not known.
     It is a string among the following:
     
     * ``RejectPolicy`` (default, recommended): reject the connection if the
       host is not known.
     * ``WarningPolicy`` (*not* recommended): issue a warning if the
       host is not known.
     * ``AutoAddPolicy`` (*not* recommended): automatically add the host key
       at the first connection to the host.
           
 After these two steps have been completed, your computer is ready to go!

.. note:: If the cluster you are using requires authentication through a Kerberos
    token (that you need to obtain before using ssh), you typically need to install
    ``libffi`` (``sudo apt-get install libffi-dev`` under Ubuntu), and make sure you install
    the ``ssh_kerberos`` :ref:`optional dependencies<install_optional_dependencies>` during the installation process of AiiDA.
    Then, if your ``.ssh/config`` file is configured properly (in particular includes
    all the necessary ``GSSAPI`` options), ``verdi computer configure`` will
    contain already the correct suggestions for all the gss options needed to support Kerberos.

.. note:: To check if you set up the computer correctly,
  execute::

    verdi computer test COMPUTERNAME
     
  that will run a few tests (file copy, file retrieval, check of the jobs in
  the scheduler queue) to verify that everything works as expected.

.. note:: If you are not sure if your computer is already set up, use the command::

     verdi computer list
   
   to get a list of existing computers, and::
   
     verdi computer show COMPUTERNAME
   
   to get detailed information on the specific computer named ``COMPUTERNAME``.
   You have also the::

     verdi computer rename OLDCOMPUTERNAME NEWCOMPUTERNAME
   
   and::
   
     verdi computer delete COMPUTERNAME
     
   commands, whose meaning should be self-explanatory.
   
.. note:: You can delete computers **only if** no entry in the database is using
  them (as for instance Calculations, or RemoteData objects). Otherwise, you
  will get an error message. 

.. note:: It is possible to **disable** a computer.

  Doing so will prevent AiiDA
  from connecting to the given computer to check the state of calculations or
  to submit new calculations. This is particularly useful if, for instance,
  the computer is under maintenance but you still want to use AiiDA with 
  other computers, or submit the calculations in the AiiDA database anyway.
  
  When the computer comes back online, you can re-enable it; 
  at this point pending calculations in the ``TOSUBMIT`` state will be
  submitted, and calculations ``WITHSCHEDULER`` will be checked and possibly
  retrieved.
  
  The relevant commands are::
     
     verdi computer enable COMPUTERNAME
     verdi computer disable COMPUTERNAME
     
  Note that the above commands will disable the computer for all AiiDA users.
  If instead, for some reason, you want to disable the computer only for a
  given user, you can use the following command::
  
     verdi computer disable COMPUTERNAME --only-for-user USER_EMAIL
  
  (and the corresponding ``verdi computer enable`` command to re-enable it).


On not bombarding the remote computer with requests
---------------------------------------------------

Some machine (particularly at supercomputing centres) may not tolerate opening
connections and executing scheduler commands with a high frequency.  To limit this
AiiDA currently has two settings:

 * The transport safe open interval, and,
 * the minimum job poll interval

Neither of these can ever be violated.  AiiDA will not try to update the jobs list
on a remove machine until the job poll interval has elapsed since the last update
(the first update will be immediate) at which point it will request a transport.
Because of this the maximum possible time before a job update could be the sum of
the two intervals, however this is unlikely to happen in practice.

The transport open interval is currently hardcoded by the transport plugin,
typically SSH is longer than local transport.

The job poll interval can be set programmatically on the corresponding `Computer`
object in verdi shell::

    Computer.get('localhost').set_minimum_job_poll_interval(30.0)


would set the transport interval on a computer called 'localhost' to 30 seconds.

.. note:: All of these intervals apply per *worker* meaning that a daemon with
   multiple workers will not necessarily, overall, respect these limits.
   For the time being there is no way around this and if these limits must be
   respected then do not run with more than one worker.
