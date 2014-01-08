=================
 Troubleshooting
=================

Connection problems
===================

* **When AiiDA tries to connect to the remote computer, it says** ``paramiko.SSHException: Server u'FULLHOSTNAME' not found in known_hosts``

  AiiDA uses the ``paramiko`` library to establish SSH connections. ``paramiko``
  is able to read the remote host keys from the ``~/.ssh/known_hosts`` of the
  user under which the AiiDA daemon is running. You therefore have to make
  sure that the key of the remote host is stored in the file.

  * As a first check, login as the user under which the AiiDA daemon is running
    and run a::

      ssh FULLHOSTNAME

    command, where ``FULLHOSTNAME`` is the complete
    host name of the remote computer configured in AiiDA. If the key of the 
    remote host is not in the ``known_hosts`` file, SSH will ask confirmation
    and then add it to the file.

  * If the above point is not sufficient, check the format of the remote host
    key. On some machines (we know that this issue happens at least on recent
    Ubuntu distributions) the default format is not RSA but ECDSA. However,
    ``paramiko`` is still not able to read keys written in this format.
    
    To discover the format, run the following command::

      ssh-keygen -F FULLHOSTNAME

    that will print the remote host key. If the output contains the string 
    ``ecdsa-sha2-nistp256``, then ``paramiko`` will not be able to use this
    key (see below for a solution).
    If instead ``ssh-rsa``, the key should be OK and
    paramiko will be able to use it.

    In case your key is in *ecdsa* format, you have to first delete the key
    by using the command::

      ssh-keygen -R FULLHOSTNAME

    Then, in your ``~/.ssh/config`` file (create it if it does not exist)
    add the following lines::

      Host *
        HostKeyAlgorithms ssh-rsa

    (use the same indentation, and leave an empty line before and one after).
    This will set the RSA algorithm as the default one for all remote hosts.
    In case, you can set the ``HostKeyAlgorithms`` attribute only to the 
    relevant computers (use ``man ssh_config`` for more information).

    Then, run a::

      ssh FULLHOSTNAME

    command. SSH will ask confirmation and then add it to the file, but 
    this time it should use the ``ssh-rsa`` format (it will say so in the
    prompt messsage). You can also double-check that the host key was 
    correctly inserted using the ``ssh-keygen -F FULLHOSTNAME`` command
    as described above. Now, the error messsage should not appear anymore.
    
