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

.. automodule:: aiida.transport
   :members:
   :special-members: __enter__, __exit__,__unicode__

Existing plugins
----------------
.. automodule:: aiida.transport.plugins.ssh
   :members:
   :special-members: __enter__, __exit__,__unicode__


.. automodule:: aiida.transport.plugins.local
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

To ensure this, for example, the local plugin uses a hidden boolean variable ``_is_open`` that is set when the ``__enter__`` and ``__exit__`` methods are called. The Ssh logic is instead given by the property sftp.

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


Below, you can find a template to fill for a new transport plugin, with a minimal docstring that also work for the sphinx documentation.

::

  class NewTransport(aiida.transport.Transport):
        
    def __init__(self, machine, **kwargs):
        """
        Initialize the Transport class.
        
        :param machine: the machine to connect to
        """

    def __enter__(self):
        """
        Open the connection
        """
        
    def __exit__(self, type, value, traceback):
        """
        Close the connection
        """

    def chdir(self,path):
        """
        Change directory to 'path'
        
        :param str path: path to change working directory into.
        :raises: IOError, if the requested path does not exist
        :rtype: string
        """

    def chmod(self,path,mode):
        """
        Change permissions of a path.

        :param str path: path to file
        :param int mode: new permissions
        """

    def copy(self,remotesource,remotedestination,*args,**kwargs):
        """
        Copy a file or a directory from remote source to remote destination 
        (On the same remote machine)
        
        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raises: IOError, if source or destination does not exist
        """
        raise NotImplementedError
        
    def copyfile(self,remotesource,remotedestination,*args,**kwargs):
        """
        Copy a file from remote source to remote destination 
        (On the same remote machine)
        
        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raises IOError: if one of src or dst does not exist
        """
   
    def copytree(self,remotesource,remotedestination,*args,**kwargs):
        """
        Copy a folder from remote source to remote destination 
        (On the same remote machine)
        
        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raise IOError: if one of src or dst does not exist
        """

    def exec_command_wait(self,command, **kwargs):
        """
        Execute the command on the shell, waits for it to finish,
        and return the retcode, the stdout and the stderr.

        Enforce the execution to be run from the pwd (as given by
        self.getcwd), if this is not None.

        :param str command: execute the command given as a string
        :return: a tuple: the retcode (int), stdout (str) and stderr (str).
        """

    def get_attribute(self,path):
        """
        Return an object FixedFieldsAttributeDict for file in a given path,
        as defined in aiida.common.extendeddicts 
        Each attribute object consists in a dictionary with the following keys:
        
        * st_size: size of files, in bytes 

        * st_uid: user id of owner

        * st_gid: group id of owner

        * st_mode: protection bits

        * st_atime: time of most recent access

        * st_mtime: time of most recent modification

        :param str path: path to file
        :return: object FixedFieldsAttributeDict
        """

    def getcwd(self):
        """
        Get working directory

        :return: a string identifying the current working directory
        """

    def get(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a file or folder from remote source to local destination
        dst must be an absolute path (src not necessarily)
        
        :param remotepath: (str) remote_folder_path
        :param localpath: (str) local_folder_path
        """

    def getfile(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a file from remote source to local destination
        dst must be an absolute path (src not necessarily)
        
        :param str remotepath: remote_folder_path
        :param str localpath: local_folder_path
        """

    def gettree(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a folder recursively from remote source to local destination
        dst must be an absolute path (src not necessarily)
        
        :param str remotepath: remote_folder_path
        :param str localpath: local_folder_path
        """
    
    def gotocomputer_command(self, remotedir):
        """
        Return a string to be run using os.system in order to connect
        via the transport to the remote directory.

        Expected behaviors:

        * A new bash session is opened

        * A reasonable error message is produced if the folder does not exist

        :param str remotedir: the full path of the remote directory
        """

    def isdir(self,path):
        """
        True if path is an existing directory.

        :param str path: path to directory
        :return: boolean
        """

    def isfile(self,path):
        """
        Return True if path is an existing file.

        :param str path: path to file
        :return: boolean
        """

    def listdir(self, path='.',pattern=None):
        """
        Return a list of the names of the entries in the given path. 
        The list is in arbitrary order. It does not include the special 
        entries '.' and '..' even if they are present in the directory.
        
        :param str path: path to list (default to '.')
        :param str pattern: if used, listdir returns a list of files matching
                            filters in Unix style. Unix only.
        :return: a list of strings
        """

    def makedirs(self,path,ignore_existing=False):
        """
        Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        :param str path: directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error
                                     if the leaf directory does already exist

        :raises: OSError, if directory at path already exists
        """
    
    def mkdir(self,path,ignore_existing=False):
        """
        Create a folder (directory) named path.

        :param str path: name of the folder to create
        :param bool ignore_existing: if True, does not give any error if the
                                     directory already exists

        :raises: OSError, if directory at path already exists
        """

    def normalize(self,path='.'):
        """
        Return the normalized path (on the server) of a given path. 
        This can be used to quickly resolve symbolic links or determine 
        what the server is considering to be the "current folder".

        :param str path: path to be normalized

        :raise IOError: if the path can't be resolved on the server
        """

    def put(self, localpath, remotepath, *args, ** kwargs):
        """
        Put a file or a directory from local src to remote dst.
        src must be an absolute path (dst not necessarily))
        Redirects to putfile and puttree.
       
        :param str localpath: path to remote destination
        :param str remotepath: absolute path to local source
        """

    def putfile(self, localpath, remotepath, *args, ** kwargs):
        """
        Put a file from local src to remote dst.
        src must be an absolute path (dst not necessarily))
        
        :param str localpath: path to remote file
        :param str remotepath: absolute path to local file
        """

    def puttree(self, localpath, remotepath, *args, ** kwargs):
        """
        Put a folder recursively from local src to remote dst.
        src must be an absolute path (dst not necessarily))
        
        :param str localpath: path to remote folder
        :param str remotepath: absolute path to local folder
        """

   def rename(src,dst):
        """
        Rename a file or folder from src to dst.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises IOError: if src/dst is not found
        :raises ValueError: if src/dst is not a valid string
        """

    def remove(self,path):
        """
        Remove the file at the given path. This only works on files; 
        for removing folders (directories), use rmdir.

        :param str path: path to file to remove

        :raise IOError: if the path is a directory
        """
    
    def rmdir(self,path):
        """
        Remove the folder named path.
        This works only for empty folders. For recursive remove, use rmtree.

        :param str path: absolute path to the folder to remove
        """
        raise NotImplementedError

    def rmtree(self,path):
        """
        Remove recursively the content at path

        :param str path: absolute path to remove
        """

