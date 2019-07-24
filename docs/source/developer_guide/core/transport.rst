Transport plugins
=================

.. toctree::
   :maxdepth: 2

The term `transport` in AiiDA, refers to a utility that the engine can use to perform certain operations on the machines where its processes are running.
The base class :py:class:`~aiida.transports.transport.Transport`, defines an interface for these operations, such as copying files and executing commands.
A `transport plugin`, is a class that implements this base class for a specific connection method.
The ``aiida-core`` package ships with two transport plugins: the :py:class:`~aiida.transports.plugins.local.LocalTransport` and :py:class:`~aiida.transports.plugins.ssh.SshTransport` classes.
The ``local`` transport can be used to connect with the `localhost` and makes use only of some standard python modules like ``os`` and ``shutil``.
The ``ssh`` transport, which can be used for machines that can be connected to over ssh, is simply a wrapper around the library `paramiko <https://www.paramiko.org/>`_, that is installed as a required dependency of ``aiida-core``.


Developing a plugin
-------------------

The transport class is actually almost never used directly by the user.
It is mostly utilized by the engine, that uses the transport plugin to connect to the remote computer where the calculation, that it is managing, is running.
The engine has to be able to use always the same methods regardless of which kind of transport is required to connect to the computer in question.

The generic transport class contains a set of minimal methods that an implementation must support, in order to be fully compatible with the other plugins.
If not, a ``NotImplementedError`` will be raised, interrupting the managing of the calculation or whatever is using the transport plugin.

Since it is important that all plugins have the same interface, or the same response behavior, a set of generic tests has been written (alongside with a set of tests that are implementation specific).
After **every** modification, or when implementing a new plugin, it is crucial to run the tests and verify that all of them pass.
The modification of tests possibly means breaking backwards compatibility and/or modifications to every piece of code using a transport plugin.

If unexpected behavior is observed during the usage, the way of fixing it is:

    1) Write a new test that shows the problem (one test for one problem when possible)
    2) Fix the bug
    3) Verify that the test now passes

The importance of point 1) is often neglected, but unit testing is a useful tool that helps you avoid the repetition of errors.
Despite the appearence, ultimately it is a time-saver!
In addition to making the transport plugin more robust, the test also helps one to quickly see how the plugin is used.

As for the general functioning of the plugin, the :py:meth:`~aiida.transports.transport.Transport.__init__` method is used only to initialize the class instance, without actually opening the transport channel.
The connection must be opened only by the :py:meth:`~aiida.transports.transport.Transport.__enter__` method, (and closed by :py:meth:`~aiida.transports.transport.Transport.__exit__`).
The :py:meth:`~aiida.transports.transport.Transport.__enter__` method lets you use the transport class using the ``with`` statement (see `python docs <https://docs.python.org/3/reference/compound_stmts.html#with>`_), in a way similar to the following::

    with TransportPlugin() as transport:
        transport.do_something_remotely

To ensure this, for example, the local plugin uses a hidden boolean variable ``_is_open`` that is set when the :py:meth:`~aiida.transports.transport.Transport.__enter__` and :py:meth:`~aiida.transports.transport.Transport.__exit__` methods are called.
The ``ssh`` logic is instead given by the property sftp.

The other functions that require some care are the copying functions, called using the following terminology:

    1) ``put``: from local source to remote destination
    2) ``get``: from remote source to local destination
    3) ``copy``: copying files from remote source to remote destination

Note that these functions must accept both files and folders and internally they will fallback to functions like ``putfile`` or ``puttree``.

The last function requiring care is :py:meth:`~aiida.transports.transport.Transport.exec_command_wait`, which is an analogue to the `subprocess <http://docs.python.org/3/library/subprocess.html>`_ python module.
The function gives the freedom to execute a string as a remote command, thus it could produce nasty effects if not written with care.
Be sure to escape any strings for bash!
Download :download:`this template <transport_template.py>` to easily implement a new transport plugin.
It contains the interface with all the methods that need to be implemented, including docstrings that will work with Sphinx documentation.
