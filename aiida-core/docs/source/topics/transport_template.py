from aiida.transports import Transport


class NewTransport(Transport):
    def __init__(self, machine, **kwargs):
        """Initialize the Transport class.

        :param machine: the machine to connect to
        """

    def __enter__(self):
        """Open the connection."""

    def __exit__(self, type, value, traceback):
        """Close the connection."""

    def chdir(self, path):
        """Change directory to 'path'.

        :param str path: path to change working directory into.
        :raises: OSError, if the requested path does not exist
        :rtype: string
        """

    def chmod(self, path, mode):
        """Change permissions of a path.

        :param str path: path to file
        :param int mode: new permissions
        """

    def copy(self, remotesource, remotedestination, *args, **kwargs):
        """Copy a file or a directory from remote source to remote destination (on the same remote machine).

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raises: OSError, if source or destination does not exist
        """

    def copyfile(self, remotesource, remotedestination, *args, **kwargs):
        """Copy a file from remote source to remote destination (on the same remote machine).

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raises OSError: if one of src or dst does not exist
        """

    def copytree(self, remotesource, remotedestination, *args, **kwargs):
        """Copy a folder from remote source to remote destination (on the same remote machine).

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raise OSError: if one of src or dst does not exist
        """

    def exec_command_wait_bytes(self, command, stdin=None, **kwargs):
        """Execute the command on the shell, wait for it to finish and return the retcode, the stdout and the stderr.

        Enforce the execution to be run from the pwd (as given by ``self.getcwd``), if this is not None.

        :param str command: execute the command given as a string
        :param stdin: (optional,default=None) can be a string or a file-like object.
        :return: a tuple: the retcode (int), stdout (bytes) and stderr (bytes).
        """

    def get_attribute(self, path):
        """Return a :py:class:`~aiida.common.extenddeddicts.FixedFieldsAttributeDict` for file in a given path.

        Each attribute dictionary will contain the following keys:

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
        """Get working directory.

        :return: a string identifying the current working directory
        """

    def get(self, remotepath, localpath, *args, **kwargs):
        """Retrieve a file or folder from remote source to local destination.

        .. note:: the destination must be an absolute path, the source not necessarily

        :param remotepath: (str) remote_folder_path
        :param localpath: (str) local_folder_path
        """

    def getfile(self, remotepath, localpath, *args, **kwargs):
        """Retrieve a file from remote source to local destination.

        .. note:: the destination must be an absolute path, the source not necessarily

        :param str remotepath: remote_folder_path
        :param str localpath: local_folder_path
        """

    def gettree(self, remotepath, localpath, *args, **kwargs):
        """Retrieve a folder recursively from remote source to local destination

        .. note:: the destination must be an absolute path, the source not necessarily

        :param str remotepath: remote_folder_path
        :param str localpath: local_folder_path
        """

    def gotocomputer_command(self, remotedir=None):
        """Return a string to be run using os.system in order to connect via the transport to the remote directory.

        Expected behaviors:

        * A new bash session is opened
        * A reasonable error message is produced if the folder does not exist

        :param str remotedir: the full path of the remote directory
        """

    def isdir(self, path):
        """True if path is an existing directory.

        :param str path: path to directory
        :return: boolean
        """

    def isfile(self, path):
        """Return True if path is an existing file.

        :param str path: path to file
        :return: boolean
        """

    def listdir(self, path='.', pattern=None):
        """Return a list of the names of the entries in the given path.

        The list is in arbitrary order. It does not include the special entries '.' and '..' even if they are present
        in the directory.

        :param str path: path to list (default to '.')
        :param str pattern: if used, listdir returns a list of files matching filters in Unix style. Unix only.
        :return: a list of strings
        """

    def makedirs(self, path, ignore_existing=False):
        """Super-mkdir; create a leaf directory and all intermediate ones.

        Works like mkdir, except that any intermediate path segment (not just the rightmost) will be created if it does
        not already exist.

        :param str path: directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error, if the leaf directory does already exist
        :raises: OSError, if directory at path already exists
        """

    def mkdir(self, path, ignore_existing=False):
        """Create a folder (directory) named path.

        :param str path: name of the folder to create
        :param bool ignore_existing: if True, does not give any error if the directory already exists
        :raises: OSError, if directory at path already exists
        """

    def normalize(self, path='.'):
        """Return the normalized path (on the server) of a given path.

        This can be used to quickly resolve symbolic links or determine what the server is considering to be the
        "current folder".

        :param str path: path to be normalized
        :raise OSError: if the path can't be resolved on the server
        """

    def put(self, localpath, remotepath, *args, **kwargs):
        """Put a file or a directory from local src to remote dst.

        Redirects to putfile and puttree.

        .. note:: the destination must be an absolute path, the source not necessarily

        :param str localpath: path to remote destination
        :param str remotepath: absolute path to local source
        """

    def putfile(self, localpath, remotepath, *args, **kwargs):
        """Put a file from local src to remote dst.

        .. note:: the destination must be an absolute path, the source not necessarily

        :param str localpath: path to remote file
        :param str remotepath: absolute path to local file
        """

    def puttree(self, localpath, remotepath, *args, **kwargs):
        """Put a folder recursively from local src to remote dst.

        .. note:: the destination must be an absolute path, the source not necessarily

        :param str localpath: path to remote folder
        :param str remotepath: absolute path to local folder
        """

    def rename(self, src, dst):
        """Rename a file or folder from src to dst.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder
        :raises OSError: if src/dst is not found
        :raises ValueError: if src/dst is not a valid string
        """

    def remove(self, path):
        """Remove the file at the given path.

        This only works on files; for removing folders (directories), use rmdir.

        :param str path: path to file to remove
        :raise OSError: if the path is a directory
        """

    def rmdir(self, path):
        """Remove the folder named path.

        This works only for empty folders. For recursive remove, use rmtree.

        :param str path: absolute path to the folder to remove
        """

    def rmtree(self, path):
        """Remove recursively the content at path.

        :param str path: absolute path to remove
        """
