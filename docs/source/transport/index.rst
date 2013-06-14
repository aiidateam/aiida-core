aiida.transport documentation
=========================

.. toctree::
   :maxdepth: 2
   
This chapter describes the generic implementation of a transport plugin.
Currently implemented are the local and the ssh plugin.
The local plugin makes use mostly of python os and shutil modules.
The ssh plugin is a wrapper to the library paramiko.
Every new plugin should possibly implement all these function for optimal compatibility.
A generic set of tests is contained in plugin_test.py, while plugin-specific tests have to be written in separate files.

Generic transport class
--------

.. automodule:: aiida.transport.__init__
   :members:
   :special-members: __enter__





