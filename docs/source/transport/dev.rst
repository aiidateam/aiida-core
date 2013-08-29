aiida.transport documentation
=============================

.. toctree::
   :maxdepth: 2
   
This chapter describes the generic implementation of a transport plugin.
The currently implemented are the local and the ssh plugin.
The local plugin makes use only of some standard python modules like os and shutil.
The ssh plugin is a wrapper to the library paramiko, that you installed with AiiDA.

Every new plugin should implement all these function in order to guarantee compatibility.
A generic set of tests is contained in plugin_test.py, while plugin-specific tests are written separately.

Generic transport class
-----------------------

.. automodule:: aiida.transport.__init__
   :members:
   :special-members: __enter__, __exit__





