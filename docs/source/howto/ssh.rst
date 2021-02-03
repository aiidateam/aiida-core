.. _how-to:ssh:

****************************
How to setup SSH connections
****************************

AiiDA communicates with remote computers via the SSH protocol.
There are two ways of setting up an SSH connection for AiiDA:

 1. Using a passwordless SSH key (easier, less safe)
 2. Using a password-protected SSH key through ``ssh-agent`` (one more step, safer)

.. _how-to:ssh:passwordless:

Using a passwordless SSH key
============================


There are numerous tutorials on the web, see e.g. `here <https://www.redhat.com/sysadmin/passwordless-ssh>`_.
Very briefly, first create a new private/public keypair (``aiida``/``aiida.pub``), leaving passphrase emtpy:

.. code-block:: console

   $ ssh-keygen -t rsa -b 4096 -f ~/.ssh/aiida

Copy the public key to the remote machine, normally this will add the public key to the rmote machine's ``~/.ssh/authorized_keys``:

.. code-block:: console

   $ ssh-copy-id -i ~/.ssh/aiida YOURUSERNAME@YOURCLUSTERADDRESS

Add the following lines to your ``~/.ssh/config`` file (or create it, if it does not exist):

.. code-block:: bash

   Host YOURCLUSTERADDRESS
         User YOURUSERNAME
         IdentityFile ~/.ssh/aiida

.. note::

  If your cluster needs you to connect to another computer *PROXY* first, you can use the ``proxy_command`` feature of ssh, see :ref:`how-to:ssh:proxy`.

You should now be able to access the remote computer (without the need to type a password) *via*:

.. code-block:: console

   $ ssh YOURCLUSTERADDRESS
   # this connection is used to copy files
   $ sftp YOURCLUSTERADDRESS

.. admonition:: Connection closed failures
   :class: attention title-icon-troubleshoot


   If the ``ssh`` command works, but the ``sftp`` command prints ``Connection closed``, there may be a line in the ``~/.bashrc`` file **on the cluster** that either produces text output or an error.
   Remove/comment lines from this file until no output or error is produced: this should make ``sftp`` work again.

Finally, if you are planning to use a batch scheduler on the remote computer, try also:

.. code-block:: console

   $ ssh YOURCLUSTERADDRESS QUEUE_VISUALIZATION_COMMAND

replacing ``QUEUE_VISUALIZATION_COMMAND`` by ``squeue`` (SLURM), ``qstat`` (PBSpro) or the equivalent command of your scheduler and check that it prints a list of the job queue without errors.

.. admonition:: Scheduler errors?
    :class: attention title-icon-troubleshoot

    If the previous command errors with ``command not found``, while the same ``QUEUE_VISUALIZATION_COMMAND`` works fine after you've logged in via SSH, it may be that a guard in the ``.bashrc`` file on the cluster prevents necessary modules from being loaded.

    Look for lines like:

    .. code-block:: bash

        [ -z "$PS1" ] && return

    or:

    .. code-block:: bash

        case $- in
            *i*) ;;
            *) return;;
        esac

    which will prevent any instructions that follow from being executed.

    You can either move relevant instructions before these lines or delete the guards entirely.
    If you are wondering whether the ``PATH`` environment variable is set correctly, you can check its value using:

    .. code-block:: bash

        $ ssh YOURCLUSTERADDRESS 'echo $PATH'

.. _how-to:ssh:passphrase:

Using passphrase-protected keys *via* an ssh-agent
==================================================


Tools like ``ssh-agent`` (available on most Linux distros and MacOS) allow you to enter the passphrase of a protected key *once* and provide access to the decrypted key for as long as the agent is running.
This allows you to use a passphrase-protected key (required by some HPC centres), while making the decrypted key available to AiiDA for automatic SSH operations.

Creating the key
^^^^^^^^^^^^^^^^

Start by following the instructions above for :ref:`how-to:ssh:passwordless`, the only difference being that you enter a passphrase when creating the key (and when logging in to the remote computer).

Adding the key to the agent
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now provide the passphrase for your private key to the agent:

.. code:: bash

    ssh-add ~/.ssh/aiida

The private key and the relative passphrase are now recorded in an instance of the agent.

.. note::

   The passphase is stored in the agent only until the next reboot.
   If you shut down or restart the AiiDA machine, before starting the AiiDA deamon remember to run the ``ssh-add`` command again.

Starting the ssh-agent
^^^^^^^^^^^^^^^^^^^^^^

On most modern Linux installations, the ``ssh-agent`` starts automatically at login (e.g. Ubuntu 16.04 and later or MacOS 10.5 and later).
If you received an error ``Could not open a connection to your authentication agent``, you will need to start the agent manually instead.

Check whether you can start an ``ssh-agent`` **in your current shell**:

.. code:: bash

   eval `ssh-agent`

In order to reuse the same agent instance everywhere (including the AiiDA daemon), the environment variables of ``ssh-agent`` need to be reused by *all* shells.
Download the script :download:`load-singlesshagent.sh <include/load-singlesshagent.sh>` and place it e.g. in ``~/bin``.
Then add the following lines to your ``~/.bashrc`` file:

.. code:: bash

   if [ -f ~/bin/load-singlesshagent.sh ]; then
      . ~/bin/load-singlesshagent.sh
   fi

To check that it works:

* Open a new shell (``~/.bashrc`` file is sourced).
* Run ``ssh-add``.
* Close the shell.
* Open a new shell and try logging in to the remote computer.

Try logging in to the remote computer; it should no longer require a passphrase.

The key and its corresponding passphrase are now stored by the agent until it is stopped.
After a reboot, remember to run ``ssh-add ~/.ssh/aiida`` again before starting the AiiDA daemon.

Integrating the ssh-agent with keychain on OSX
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On OSX Sierra and later, the native ``ssh-add`` client allows passphrases to be stored persistently in the `OSX keychain <https://support.apple.com/en-gb/guide/keychain-access/kyca1083/mac>`__.
Store the passphrase in the keychain using the OSX-specific ``-k`` argument:

.. code:: bash

    ssh-add -k ~/.ssh/aiida

To instruct ssh to look in the OSX keychain for key passphrases, add the following lines to ``~/.ssh/config``:

.. code:: bash

   Host *
      UseKeychain yes

AiiDA configuration
^^^^^^^^^^^^^^^^^^^

When :ref:`configuring the computer in AiiDA <how-to:run-codes:computer:configuration>`, simply make sure that ``Allow ssh agent`` is set to ``true`` (default).

.. _how-to:ssh:proxy:

Connecting to a remote computer *via* a proxy server
====================================================

Some compute clusters require you to connect to an intermediate server *PROXY*, from which you can then connect to the cluster *TARGET* on which you run your calculations.
This section explains how to use the ``proxy_command`` feature of ``ssh`` in order to make this jump automatically.

.. tip::

  This method can also be used to automatically tunnel into virtual private networks, if you have an account on a proxy/jumphost server with access to the network.



SSH configuration
^^^^^^^^^^^^^^^^^

Edit the ``~/.ssh/config`` file on the computer on which you installed AiiDA (or create it if missing) and add the following lines::

  Host SHORTNAME_TARGET
      Hostname FULLHOSTNAME_TARGET
      User USER_TARGET
      IdentityFile ~/.ssh/aiida
      ProxyCommand ssh -W %h:%p USER_PROXY@FULLHOSTNAME_PROXY

replacing the ``..._TARGET`` and ``..._PROXY`` variables with the host/user names of the respective servers.

This should allow you to directly connect to the *TARGET* server using

.. code-block:: console

   $ ssh SHORTNAME_TARGET

For a *passwordless* connection, you need to follow the instructions :ref:`how-to:ssh:passwordless` *twice*: once for the connection from your computer to the *PROXY* server, and once for the connection from the *PROXY* server to the *TARGET* server.


AiiDA configuration
^^^^^^^^^^^^^^^^^^^

When :ref:`configuring the computer in AiiDA <how-to:run-codes:computer:configuration>`, AiiDA will automatically parse the required information from your ``~/.ssh/config`` file.

.. dropdown:: Specifying the proxy_command manually

    If, for any reason, you need to specify the ``proxy_command`` option of ``verdi computer configure ssh`` manually, please note the following:

      1. Don't use placeholders ``%h`` and ``%p`` (AiiDA replaces them only when parsing from the ``~/.ssh/config`` file) but provide the actual hostname and port.
      2. Don't include stdout/stderr redirection (AiiDA strips it automatically, but only when parsing from the ``~/.ssh/config`` file).


Using kerberos tokens
=====================

If the remote machine requires authentication through a Kerberos token (that you need to obtain before using ssh), you typically need to

 * install ``libffi`` (``sudo apt-get install libffi-dev`` under Ubuntu)
 * install the ``ssh_kerberos`` extra during the installation of aiida-core (see :ref:`intro:install:setup`).

If you provide all necessary ``GSSAPI`` options in your ``~/.ssh/config`` file, ``verdi computer configure`` should already pick up the appropriate values for all the gss-related options.
