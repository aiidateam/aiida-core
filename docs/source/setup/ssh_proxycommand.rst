.. _ssh_proxycommand:

#######################################
Using the proxy_command option with ssh
#######################################

This page explains how to use the ``proxy_command`` feature of ``ssh``. This feature
is needed when you want to connect to a computer ``B``, but you are not allowed to
connect directly to it; instead, you have to connect to computer ``A`` first, and then
perform a further connection from ``A`` to ``B``.


Requirements
++++++++++++
The idea is that you ask ``ssh`` to connect to computer ``B`` by using
a proxy to create a sort of tunnel. One way to perform such an
operation is to use ``netcat``, a tool that simply takes the standard input and
redirects it to a given TCP port.

Therefore, a requirement is to install ``netcat`` on computer A. 
You can already check if the ``netcat`` or ``nc`` command is available
on you computer, since some distributions include it (if it is already
installed, the output of the command::

  which netcat

or::

  which nc

will return the absolute path to the executable).
If this is not
the case, download the ``netcat`` source code from `here
<http://netcat.sourceforge.net/>`_. Then, unpack the tar.gz (or tar.bz2)
file in a folder on computer A, ``cd`` into the folder and execute::

  ./configure --prefix=.
  make
  make install

This will create a subdirectory ``bin``, containing the ``netcat`` and
``nc`` executables.

In any case, write down the full path to ``nc``, that we will
need later.


ssh/config
++++++++++
You can now test the proxy command with ``ssh``. Edit the
``~/.ssh/config`` file on the computer on which you installed AiiDA
(or create it if missing) and add the following lines::
  
  Host FULLHOSTNAME_B
  Hostname FULLHOSTNAME_B
  User USER_B
  ProxyCommand ssh USER_A@FULLHOSTNAME_A ABSPATH_NETCAT %h %p

where you have to replace:

* ``FULLHOSTNAMEA`` and ``FULLHOSTNAMEB`` with
  the fully-qualified hostnames of computer ``A`` and ``B`` (remembering that ``B``
  is the computer you want to actually connect to, and ``A`` is the
  intermediate computer to which you have direct access)
* ``USER_A`` and ``USER_B`` are the usernames on the two machines (that 
  can possibly be the same).
* ``ABSPATH_NETCAT`` is the absolute path to the ``nc`` executable
  that you obtained in the previous step.

Remember also to configure passwordless ssh connections using ssh keys
both from your computer to ``A``, and from ``A`` to ``B``.

Once you add this lines and save the file, try to execute::
  
  ssh FULLHOSTNAME_B

which should allow you to directly connect to ``B``.


AiiDA config
++++++++++++
If the above steps work, setup and configure now the computer as
explained :ref:`here <computer_setup>`.

If you properly set up the ``~/.ssh/config`` file in the previous
step, AiiDA should properly parse the information in the file and
provide the correct default value for the ``proxy_command`` during the
``verdi computer configure`` step.

.. _ssh_proxycommand_notes:

Some notes on the ``proxy_command`` option
------------------------------------------

* In the ``~/.ssh/config`` file, you can leave the ``%h`` and ``%p``
  placeholders, that are then automatically replaced by ssh with the hostname
  and the port of the machine ``B`` when creating the proxy.
  However, in the AiiDA ``proxy_command`` option, you need to put the
  actual hostname and port. If you start from a properly configured 
  ``~/.ssh/config`` file, AiiDA will already replace these
  placeholders with the correct values. However, if you input the ``proxy_command``
  value manually, remember to write the
  hostname and the port and not ``%h`` and ``%p``.
* In the ``~/.ssh/config`` file, you can also insert stdout and stderr
  redirection, e.g. ``2> /dev/null`` to hide any error that may occur
  during the proxying/tunneling. However, you should only give AiiDA
  the actual command to be executed, without any redirection. Again,
  AiiDA will remove the redirection when it automatically reads the
  ``~/.ssh/config`` file, but be careful if entering manually the
  content in this field.

