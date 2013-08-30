aiida.transport documentation
=============================

.. toctree::
   :maxdepth: 2
   
This chapter describes the generic implementation of a transport plugin.
The currently implemented are the local and the ssh plugin.
The local plugin makes use only of some standard python modules like os and shutil.
The ssh plugin is a wrapper to the library paramiko, that you installed with AiiDA.

A generic set of tests is contained in plugin_test.py, while plugin-specific tests are written separately.

Generic transport class
-----------------------

.. automodule:: aiida.transport.__init__
   :members:
   :special-members: __enter__, __exit__,__unicode__

Developing a plugin
-------------------

The transport class is actually almost never used in first person by the user.
It is mostly utilized by the ExecutionManager, that use the transport plugin to connect to the remote computer to manage the calculation.
The ExecutionManager has to be able to use always the same function, or the same interface, regardless of which kind of connection is actually really using. 

The generic transport class contains a set of minimal methods that an implementation must support, in order to be fully compatible with the other plugins.
If not, a NotImplementedError will be raised, interrupting the managing of the calculation or whatever is using the transport plugin.

Since it is important that all plugins have the same interface, or the same response behavior, a set of generic tests has been written (alongside with set of tests that are implementation specific).
After **every** modification, or when implementing a new plugin, it is crucial to run the tests and verify that everything is passed.
The modification of tests possibly means breaking back-compatibility and/or modifications to every piece of code using a transport plugin.

If an unexpected behavior is observed during the usage, the way of fixing it is:

1) Write a new test that shows the problem (one test for one problem when possible)

2) Fix the bug

3) Verify that the test is passed correctly

The importance of point 1) is often neglected, but unittesting is a useful tool that helps you avoiding the repetition of errors. Despite the appearence, it's a time-saver!
Not only, the tests help you seeing how the plugin is used.

As for the general functioning of the plugin, the ``__init__`` method is used only to initialize the class instance, without actually opening the transport channel. The connection must be opened only by the ``__enter__`` method, (and closed by ``__exit__``.
The ``__enter__`` method let you use the transport class using the ``with`` statement (see `Python docs <http://docs.python.org/release/2.5/whatsnew/pep-343.html>`_), in a way similar to the following::

  t = TransportPlugin()
  with open(t):
      t.do_something_remotely

To ensure this, for example, the local plugin uses a hidden boolean variable ``_is_open`` that is set when the ``__enter__`` and ``__exit__`` methods are called. The Ssh logic is instead already managed by the underlying Paramiko library.

The other functions that require some care are the copying functions, called using the following terminology:

1) ``put``: from local source to remote destination

2) ``get``: from remote source to local destination

3) ``copy``: copying files from remote source to remote destination

Note that these functions must copy files or folders regardless, internally, they will fallback to functions like ``putfile`` or ``puttree``.

The last function requiring care is ``exec_command_wait``, which is an analogue to the `subprocess <http://docs.python.org/2/library/subprocess.html>`_ Python module.
The function gives the freedom to execute a string as a remote command, thus it could produce nasty effects if not written with care. 
Be sure to escape any string for bash!

Currently, the implemented plugins are the Local and the Ssh transports.
The Local one is simply a wrapper to some standard Python modules, like ``shutil`` or ``os``, those functions are simply interfaced in a different way with AiiDA.
The SSh instead is an interface to the `Paramiko <http://www.lag.net/paramiko/>`_ library.




