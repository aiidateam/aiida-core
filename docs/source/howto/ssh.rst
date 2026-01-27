.. _how-to:ssh:

****************************
How to setup SSH connections
****************************

AiiDA communicates with remote computers via the SSH protocol.
There are two ways of setting up an SSH connection for AiiDA:

#. Using a passwordless SSH key (easier, less safe)
#. Using a password-protected SSH key through ``ssh-agent`` (one more step, safer)

.. _how-to:ssh:passwordless:

Using a passwordless SSH key
============================


There are numerous tutorials on the web, see e.g. `here <https://www.redhat.com/sysadmin/passwordless-ssh>`_.
Very briefly, first create a new private/public keypair (``aiida``/``aiida.pub``), leaving passphrase emtpy:

.. code-block:: console

   $ ssh-keygen -t rsa -b 4096 -f ~/.ssh/aiida

Copy the public key to the remote machine, normally this will add the public key to the remote machine's ``~/.ssh/authorized_keys``:

.. code-block:: console

   $ ssh-copy-id -i ~/.ssh/aiida YOURUSERNAME@YOURCLUSTERADDRESS

Add the following lines to your ``~/.ssh/config`` file (or create it, if it does not exist):

.. code-block:: bash

   Host YOURCLUSTERADDRESS
         User YOURUSERNAME
         IdentityFile ~/.ssh/aiida

.. note::

  If your cluster needs you to connect to another computer *PROXY* first, you can use the ``ProxyJump`` or ``ProxyCommand`` feature of SSH, see :ref:`how-to:ssh:proxy`.

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
This section explains how to use the ``ProxyJump`` or ``ProxyCommand`` feature of ``ssh`` in order to make this jump automatically.

.. tip::

  This method can also be used to avoid having to start a virtual private network (VPN) client if you have an SSH account on a proxy/jumphost server which is accessible from your current network **and** from which you can access the *TARGET* machine directly.


SSH configuration
^^^^^^^^^^^^^^^^^

To decide whether to use the ``ProxyJump`` (recommended) or the ``ProxyCommand`` directive, please check the version of your SSH client first with ``ssh -V``.
The ``ProxyJump`` directive has been added in version 7.3 of OpenSSH, hence if you are using an older version of SSH (on your machine or the *PROXY*) you have to use the older ``ProxyCommand``.

To setup the proxy configuration with ``ProxyJump``, edit the ``~/.ssh/config`` file on the computer on which you installed AiiDA (or create it if missing)
and add the following lines::

  Host SHORTNAME_TARGET
      Hostname FULLHOSTNAME_TARGET
      User USER_TARGET
      IdentityFile ~/.ssh/aiida
      ProxyJump USER_PROXY@FULLHOSTNAME_PROXY

  Host FULLHOSTNAME_PROXY
      IdentityFile ~/.ssh/aiida

Replace the ``..._TARGET`` and ``..._PROXY`` variables with the host/user names of the respective servers.

.. dropdown:: :fa:`plus-circle` Alternative setup with ``ProxyCommand``

   To setup the proxy configuration with ``ProxyCommand`` **instead**, edit the ``~/.ssh/config`` file on the computer on which you installed AiiDA (or create it if missing)
   and add the following lines::

    Host SHORTNAME_TARGET
        Hostname FULLHOSTNAME_TARGET
        User USER_TARGET
        IdentityFile ~/.ssh/aiida
        ProxyCommand ssh -W %h:%p USER_PROXY@FULLHOSTNAME_PROXY

    Host FULLHOSTNAME_PROXY
        IdentityFile ~/.ssh/aiida

  Replace the ``..._TARGET`` and ``..._PROXY`` variables with the host/user names of the respective servers.

In both cases, this should allow you to directly connect to the *TARGET* server using

.. code-block:: console

   $ ssh SHORTNAME_TARGET



.. note ::

   If the user directory is not shared between the *PROXY* and the *TARGET* (in most supercomputing facilities your user directory is shared between the machines), you need to follow the :ref:`instructions for a passwordless connection <how-to:ssh:passwordless>` *twice*: once for the connection from your computer to the *PROXY* server, and once for the connection from the *PROXY* server to the *TARGET* server (e.g. the public key must be listed in the ``~/.ssh/authorized_keys`` file of both the *PROXY* and the *TARGET* server).


AiiDA configuration
^^^^^^^^^^^^^^^^^^^

When :ref:`configuring the computer in AiiDA <how-to:run-codes:computer:configuration>`, AiiDA will automatically parse most of required information from your ``~/.ssh/config`` file. A notable exception to this is the ``proxy_jump`` directive, which **must** be specified manually.

Simply copy & paste the same instructions as you have used for ``ProxyJump`` in your ``~/.ssh/config`` to the input for ``proxy_jump``:

.. code-block:: console

   $ verdi computer configure core.ssh SHORTNAME_TARGET
   ...
   Allow ssh agent [True]:
   SSH proxy jump []: USER_PROXY@FULLHOSTNAME_PROXY

.. note:: A chain of proxies can be specified as a comma-separated list. If you need to specify a different username, you can so with ``USER_PROXY@...``. If no username is specified for the proxy the same username as for the *TARGET* is used.

.. important:: Specifying the ``proxy_command`` manually

    When specifying or updating the ``proxy_command`` option via ``verdi computer configure ssh``, please **do not use placeholders** ``%h`` and ``%p`` but provide the *actual* hostname and port.
    AiiDA replaces them only when parsing from the ``~/.ssh/config`` file.


.. _how-to:ssh:2fa:

Using two-factor authentication (2FA) with ``core.ssh_async``
=============================================================

Some HPC centers require two-factor authentication where you must first authenticate via an API using your credentials and a TOTP code, which then provides you with short-lived signed SSH keys for the actual connection.

The ``core.ssh_async`` transport plugin provides an ``authentication_script`` option that runs a local script before each SSH connection is opened.
This script must be provided by the user and is responsible for obtaining fresh SSH credentials so that the subsequent connection can succeed.

.. warning::

   You are responsible for securely storing your TOTP secret and any other credentials.
   Never commit secrets to version control or store them in plaintext in shared locations.

.. warning::

   Make sure that your HPC center's policies allow automated 2FA connections.
   It is your responsibility to comply with their security policies.

.. important::

   Your script will be called on each SSH connection and may run concurrently
   from multiple daemon workers. Use ``flock`` to prevent race conditions, and
   check certificate validity **after** acquiring the lock (another process may
   have refreshed it while you were waiting).


How it works
^^^^^^^^^^^^

The typical flow is:

1. AiiDA needs to open an SSH connection
2. Before connecting, AiiDA optionally runs an authentication script (``authentication_script``)
3. Your script authenticates to the HPC center. This largely depends on the authentication mechanism of your HPC center. For example:

   a. It may require generating a TOTP code from a shared secret, sending your username, password, and TOTP code to the HPC center, and then receiving signed SSH keys in response.
   b. Your HPC center's authentication policy may strictly require you to enter credentials manually, in which case your script may prompt you to enter the required information (username, password, TOTP code, etc.) interactively.
   c. It may require you to authenticate via a web browser, in which case your script may open a browser for you to log in.

In all of the above cases, your script should ultimately enable ``ssh <my-HPC>`` to succeed without a password.

.. note::
   If your HPC center does not allow multiple connections but relies on multiplexing, you will need to reconfigure your AiiDA computer to use the ``openssh`` transport backend instead of ``asyncssh``.

.. note::

   Your script may be called many times throughout the day. It is your responsibility to ensure the script is efficient and does not overload the HPC center's authentication service.
   For example, if the signed keys are valid for 24 hours, your script should check whether existing keys are still valid before requesting new ones.

4. AiiDA proceeds to open the SSH connection normally.

Example: Automated key retrieval with TOTP (case a)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below is an example script that authenticates to an HPC center's SSH key service using TOTP.
This is based on real-world usage patterns.
In this case, typically the HPC center has provided a script that, after filling in credentials, retrieves signed SSH keys from an API endpoint.
Here we show how to automate the process and integrate the script with AiiDA, assuming the HPC center's security policies allow it.

Suppose the script from the HPC center is called ``get_hpc_keys.sh``, which prompts the user to enter username, password, and TOTP code interactively.
In that case, your wrapper script should look something like the example below, where the TOTP code is generated automatically from a shared secret.

First, install the required tools:

.. code-block:: console

   # On Debian/Ubuntu
   $ sudo apt-get install oathtool expect

   # On macOS
   $ brew install oath-toolkit expect

Second, create an executable script at ``~/bin/get_hpc_keys.sh``:

.. code-block:: bash

   #!/bin/bash
   # Wrapper script to automate 2FA authentication for HPC SSH access.
   # Checks if existing keys are still valid before requesting new ones.
   set -e

   # === FILE LOCKING ===
   # Prevents race conditions when multiple daemon workers run simultaneously.
   # flock -x waits (blocks) if another process holds the lock.
   # Lock is automatically released when the script exits (any exit code).
   LOCK_FILE="/tmp/hpc_auth.lock"
   exec 200>"$LOCK_FILE"
   flock -x 200

   # === CONFIGURATION ===
   HPC_SCRIPT="/path/to/hpc_provided_script.sh"
   SSH_CERT_PATH="$HOME/.ssh/id_ed25519-cert.pub"
   MIN_VALIDITY=3600  # Refresh if less than 1 hour remaining
   USERNAME="${HPC_USERNAME:-your_username}"
   : "${HPC_PASSWORD:?Error: HPC_PASSWORD environment variable not set}"
   : "${HPC_TOTP_SECRET:?Error: HPC_TOTP_SECRET environment variable not set}"
   # === END CONFIGURATION ===

   # Check if existing SSH certificate is still valid
   check_cert_validity() {
       [ -f "$SSH_CERT_PATH" ] || return 1
       EXPIRY=$(ssh-keygen -L -f "$SSH_CERT_PATH" 2>/dev/null | grep "Valid:" | sed 's/.*to //')
       [ -n "$EXPIRY" ] || return 1
       EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null) || \
           EXPIRY_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$EXPIRY" +%s 2>/dev/null) || return 1
       [ $((EXPIRY_EPOCH - $(date +%s))) -gt $MIN_VALIDITY ]
   }

   # Check validity AFTER acquiring lock (another process may have refreshed while we waited)
   if check_cert_validity; then
       echo "SSH certificate still valid, skipping authentication"
       exit 0
   fi

   echo "Obtaining new SSH keys..."
   OTP_CODE=$(oathtool --totp --base32 "$HPC_TOTP_SECRET")

   # Adjust the expect patterns to match your HPC script's prompts
   expect <<EOF || exit 1
   set timeout 60
   spawn $HPC_SCRIPT
   expect -re {[Uu]sername.*:}
   send "$USERNAME\r"
   expect -re {[Pp]assword.*:}
   send "$HPC_PASSWORD\r"
   expect -re {[Oo]ne-[Tt]ime|OTP|TOTP|[Cc]ode.*:}
   send "$OTP_CODE\r"
   expect eof
   catch wait result
   exit [lindex \$result 3]
   EOF

   exit 0

.. tip::

   The script checks whether existing SSH certificates are still valid before requesting new ones.
   Adjust ``MIN_VALIDITY`` to control how early before expiry the script should refresh (default: 1 hour).

Make the script executable:

.. code-block:: console

   $ chmod +x ~/bin/get_hpc_keys.sh


Using a keyring instead of environment variables
""""""""""""""""""""""""""""""""""""""""""""""""

If you prefer to store credentials in a system keyring rather than environment variables, you can modify the script to retrieve them securely.

**On Linux (GNOME Keyring / libsecret):**

First, store your credentials:

.. code-block:: console

   $ secret-tool store --label="HPC Password" service hpc username your_username
   $ secret-tool store --label="HPC TOTP Secret" service hpc_totp username your_username

Then modify the script to read from the keyring:

.. code-block:: bash

   # Replace the environment variable reads with:
   PASSWORD=$(secret-tool lookup service hpc username your_username)
   TOTP_SECRET=$(secret-tool lookup service hpc_totp username your_username)

**On macOS (Keychain):**

First, store your credentials:

.. code-block:: console

   $ security add-generic-password -a your_username -s hpc_password -w
   $ security add-generic-password -a your_username -s hpc_totp_secret -w

Then modify the script to read from the keyring:

.. code-block:: bash

   # Replace the environment variable reads with:
   PASSWORD=$(security find-generic-password -a your_username -s hpc_password -w)
   TOTP_SECRET=$(security find-generic-password -a your_username -s hpc_totp_secret -w)


Configuring AiiDA
^^^^^^^^^^^^^^^^^

When configuring your computer with the ``core.ssh_async`` transport, specify the script path:

.. code-block:: console

   $ verdi computer configure core.ssh_async YOURCOMPUTER
   ...
   Local script to run before opening connection (path) [None]: /home/YOURUSERNAME/bin/get_hpc_keys.sh
   ...

.. note::

   - The ``authentication_script`` path must be **absolute** and the script must be **executable**.
   - The script runs locally before each SSH connection is opened.
   - If the script fails (non-zero exit code), the SSH connection will not be attempted and an error will be raised. AiiDA may retry later using its exponential backoff mechanism.

Security considerations
^^^^^^^^^^^^^^^^^^^^^^^

* Consider using encrypted files or a keyring for credential storage.
* The signed keys are typically short-lived (e.g., 24 hours), which limits exposure if compromised.
* On shared systems, ensure your credential files and downloaded keys are not readable by others.



Using kerberos tokens
=====================

If the remote machine requires authentication through a Kerberos token (that you need to obtain before using ssh), you typically need to

* install ``libffi`` (``sudo apt-get install libffi-dev`` under Ubuntu)
* install the ``ssh_kerberos`` extra during the installation of aiida-core (see :ref:`installation:guide-complete:python-package:optional-requirements`).

If you provide all necessary ``GSSAPI`` options in your ``~/.ssh/config`` file, ``verdi computer configure`` should already pick up the appropriate values for all the gss-related options.
