.. _how-to:ssh:

****************************
How to setup SSH connections
****************************

If you plan to use the ``SSH`` transport for an :ref:`AiiDA computer <how-to:setup_computer>`, you have to configure a password-less login from your user to the cluster.
To do so type first (only if you do not already have some keys in your local ``~/.ssh`` directory - i.e. files like ``id_rsa.pub``):

.. code-block:: console

   $ ssh-keygen -t rsa

.. note::

  Using a passphrase to encrypt the private key is not mandatory, however it is highly recommended.
  See :ref:`this how-to <how-to:ssh:passphrase>`, for using passphrase-protected SSH keys via a ssh-agent.

Then copy your keys to the remote computer (in ``~/.ssh/authorized_keys``) with:

.. code-block:: console

   $ ssh-copy-id YOURUSERNAME@YOURCLUSTERADDRESS

replacing ``YOURUSERNAME`` and ``YOURCLUSTERADDRESS`` by respectively your username and cluster address.
Finally add the following lines to ~/.ssh/config (leaving an empty line before and after):

.. code-block:: bash

  Host YOURCLUSTERADDRESS
    User YOURUSERNAME
    IdentityFile YOURRSAKEY

replacing ``YOURRSAKEY`` by the path to the rsa private key you want to use (it should look like ``~/.ssh/id_rsa``).

.. note::

  In principle you don't have to put the ``IdentityFile`` line if you have only one rsa key in your ``~/.ssh`` folder.

Before proceeding to setup the computer, be sure that you are able to connect to your cluster using:

.. code-block:: console

   $ ssh YOURCLUSTERADDRESS

without the need to type a password.
Moreover, make also sure you can connect *via* ``sftp`` (needed to copy files).
The following command:

.. code-block:: console

   $ sftp YOURCLUSTERADDRESS

should show you a prompt without errors (possibly with a message saying ``Connected to YOURCLUSTERADDRESS``).

.. admonition:: Connection closed failures
   :class: attention title-icon-troubleshoot

  If the ``ssh`` command works, but the ``sftp`` command does not (e.g. it just prints ``Connection closed``), a possible reason can be that there is a line in your ``~/.bashrc`` (on the cluster) that either produces text output or an error.
  Remove/comment it until no output or error is produced: this should make ``sftp`` work again.

Finally, try also:

.. code-block:: console

   $ ssh YOURCLUSTERADDRESS QUEUE_VISUALIZATION_COMMAND

replacing ``QUEUE_VISUALIZATION_COMMAND`` by the scheduler command that prints on screen the status of the queue on the cluster (e.g. ``qstat`` for PBSpro scheduler or ``squeue`` for SLURM).
It should print a snapshot of the queue status, without any errors.

.. admonition:: Scheduler errors?
    :class: attention title-icon-troubleshoot

    If there are errors with the previous command, then edit your ``~/.bashrc`` file in the remote computer and add a line at the beginning that adds the path to the scheduler commands, typically (here for PBSpro):

    .. code-block:: bash

      export PATH=$PATH:/opt/pbs/default/bin

    Or, alternatively, find the path to the executables (like using ``which qsub``).

.. note::

    If you need your remote ``.bashrc`` to be sourced before you execute the code (for instance to change the PATH) make sure the ``.bashrc`` file **does not** contain lines like:

    .. code-block:: bash

        [ -z "$PS1" ] && return

    or:

    .. code-block:: bash

        case $- in
            *i*) ;;
            *) return;;
        esac

    in the beginning (these would prevent the bashrc to be executed when you ssh to the remote computer).
    You can check that e.g. the PATH variable is correctly set upon ssh, by typing (in your local computer):

    .. code-block:: bash

        $ ssh YOURCLUSTERADDRESS 'echo $PATH'


.. note::

  If you need to ssh to a computer *A* first, from which you can then connect to computer *B* you wanted to connect to, you can use the ``proxy_command`` feature of ssh, that we also support in AiiDA.
  For more information, see :ref:`how-to:ssh:proxy`.


.. _how-to:ssh:passphrase:

Using passphrase-protected SSH keys via a ssh-agent
===================================================

In order to connect to a remote computer using the ``SSH`` transport, AiiDA needs a password-less login (see :ref:`how-to:setup_computer`): for this reason, it is necessary to configure an authentication key pair.

Using a passphrase to encrypt the private key is not mandatory, however it is highly recommended.
In some cases it is indispensable because it is requested by the computer center managing the remote cluster.
To this purpose, the use of a tool like ``ssh-agent`` becomes essential, so that the private-key passphrase only needs to be supplied once (note that the key needs to be provided again after a reboot of your AiiDA machine).

Starting the ssh-agent
^^^^^^^^^^^^^^^^^^^^^^

In the majority of modern Linux systems for desktops/laptops, the ``ssh-agent`` automatically starts during login.
In some cases (e.g. virtual machines, or old distributions) it is needed to start it manually instead.
If you are unsure, just run the command ``ssh-add``: if it displays the error ``Could not open a connection to your authentication agent``, then you need to start the agent manually as described below.

.. dropdown:: Start the ``ssh-agent`` manually (and reuse it across shells)

    If you have no ``ssh-agent`` running, you can start a new one with the command:

    .. code:: bash

        eval `ssh-agent`

    However, this command will start a new agent that will be visible **only in your current shell**.

    In order to use the same agent instance in every future opened shell, and most importantly to make this accessible to the AiiDA daemon, you need to make sure that the environment variables of ``ssh-agent`` are reused by *all* shells.

    To make the ssh-agent persistent, downlod the script :download:`load-singlesshagent.sh <include/load-singlesshagent.sh>` and put it in a directory dedicated to the storage of your scripts (in our example will be ``~/bin``).

    .. note::

       You need to use this script only if a "global" ssh-agent is not available by default on your computer.
       A global agent is available, for instance, on recent versions of Mac OS X and of Ubuntu Linux.

    Then edit the file ``~/.bashrc`` and add the following lines:

    .. code:: bash

        if [ -f ~/bin/load-singlesshagent.sh ]; then
            . ~/bin/load-singlesshagent.sh
        fi

    To check that it works, perform the following steps:

    * Open a new shell, so that the ``~/.bashrc`` file is sourced.
    * Run the command ``ssh-add`` as described in the following section.
    * Logout from the current shell.
    * Open a new shell.
    * Check that you are able to connect to the remote computer without typing the passphrase.

Adding the passphrase of your key(s) to the agent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To provide the passphrase of your private key to the the agent use the command:

.. code:: bash

    ssh-add

If you changed the default position or the default name of the private key, or you want to provide the passphrase only for a specific key, you need specify the path to the SSH key file as a parameter to ``ssh-add``.

The private key and the relative passphrase are now recorded in an instance of the agent.

.. note::

   The passphase is stored in the agent only until the next reboot.
   If you shut down or restart the AiiDA machine, before starting the AiiDA deamon remember to run the ``ssh-add`` command again.

Configure AiiDA
^^^^^^^^^^^^^^^

In order to use the agent in AiiDA, you need to first make sure that you can connect to the computer via SSH without explicitly specifying a passphrase.
Make sure that this is the case also in newly opened bash shells.

Then, when configuring the corresponding AiiDA computer (via ``verdi computer configure``), make sure to specify ``true`` to the question ``Allow ssh agent``.
If you already configured the computer and just want to adapt the computer configuration, just rerun

.. code:: bash

    verdi computer configure ssh COMPUTERNAME

After the configuration, you should verify that AiiDA can connect to the computer with:

.. code:: bash

    verdi computer test COMPUTERNAME

.. _how-to:ssh:proxy:

Connecting to a remote computer *via* a proxy server
====================================================

This section explains how to use the ``proxy_command`` feature of ``ssh``.
This feature is needed when you want to connect to a computer ``B``, but you are not allowed to connect directly to it; instead, you have to connect to computer ``A`` first, and then perform a further connection from ``A`` to ``B``.

Requirements
^^^^^^^^^^^^

The idea is that you ask ``ssh`` to connect to computer ``B`` by using a proxy to create a sort of tunnel.
One way to perform such an operation is to use ``netcat``, a tool that simply takes the standard input and
redirects it to a given TCP port.

Therefore, a requirement is to install ``netcat`` on computer A.
You can already check if the ``netcat`` or ``nc`` command is available on you computer, since some distributions include it (if it is already installed, the output of the command:

.. code-block:: console

   $ which netcat

or:

.. code-block:: console

   $ which nc

will return the absolute path to the executable).

If this is not the case, you will need to install it on your own.
Typically, it will be sufficient to look for a netcat distribution on the web, unzip the downloaded package, ``cd`` into the folder and execute something like:

.. code-block:: console

   $ ./configure --prefix=.
   $ make
   $ make install

This usually creates a subfolder ``bin``, containing the ``netcat`` and ``nc`` executables.
Write down the full path to ``nc`` that we will need later.


SSH configuration
^^^^^^^^^^^^^^^^^

You can now test the proxy command with ``ssh``.
Edit the ``~/.ssh/config`` file on the computer on which you installed AiiDA (or create it if missing) and add the following lines::

  Host FULLHOSTNAME_B
  Hostname FULLHOSTNAME_B
  User USER_B
  ProxyCommand ssh USER_A@FULLHOSTNAME_A ABSPATH_NETCAT %h %p

where you have to replace:

* ``FULLHOSTNAMEA`` and ``FULLHOSTNAMEB`` with the fully-qualified hostnames of computer ``A`` and ``B`` (remembering that ``B`` is the computer you want to actually connect to, and ``A`` is the intermediate computer to which you have direct access)
* ``USER_A`` and ``USER_B`` are the usernames on the two machines (that can possibly be the same).
* ``ABSPATH_NETCAT`` is the absolute path to the ``nc`` executable that you obtained in the previous step.

Remember also to configure passwordless ssh connections using ssh keys both from your computer to ``A``, and from ``A`` to ``B`` (see above).

Once you add this lines and save the file, try to execute:

.. code-block:: console

   $ ssh FULLHOSTNAME_B

which should allow you to directly connect to ``B``.

.. warning::

   There are several versions of netcat available on the web.
   We found at least one case in which the executable wasn't working properly.
   At the end of the connection, the ``netcat`` executable might still be running: as a result, you may rapidly leave the cluster with hundreds of opened ``ssh`` connections, one for every time you connect to the cluster ``B``.
   Therefore, check on both computers ``A`` and ``B`` that the number of processes ``netcat`` and ``ssh`` are disappearing if you close the connection.
   To check if such processes are running, you can execute:

   .. code-block:: console

      $ ps -aux | grep <username>

   Remember that a cluster might have more than one login node, and the ``ssh`` connection will randomly connect to any of them.

AiiDA configuration
^^^^^^^^^^^^^^^^^^^

If the above steps work, setup and configure now the computer as explained in the :ref:`computer setup how-to <how-to:setup_computer>`.

If you properly set up the ``~/.ssh/config`` file in the previous step, AiiDA should properly parse the information in the file and provide the correct default value for the ``proxy_command`` during the ``verdi computer configure`` step.

.. _how-to:ssh:proxy:notes:

Some notes on the ``proxy_command`` option
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the ``~/.ssh/config`` file, you can leave the ``%h`` and ``%p`` placeholders, that are then automatically replaced by ssh with the hostname and the port of the machine ``B`` when creating the proxy.
However, in the AiiDA ``proxy_command`` option, you need to put the actual hostname and port.
If you start from a properly configured ``~/.ssh/config`` file, AiiDA will already replace these placeholders with the correct values.
However, if you input the ``proxy_command`` value manually, remember to write the hostname and the port and not ``%h`` and ``%p``.

In the ``~/.ssh/config`` file, you can also insert stdout and stderr redirection, e.g. ``2> /dev/null`` to hide any error that may occur during the proxying/tunneling.
However, you should only give AiiDA the actual command to be executed, without any redirection.
Again, AiiDA will remove the redirection when it automatically reads the ``~/.ssh/config`` file, but be careful if entering manually the content in this field.
