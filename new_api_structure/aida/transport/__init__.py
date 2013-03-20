#
# TODO: move copyfile in the ExecutionManager
# def copyfile(src, dst):
#     """
#     a function that does the correct thing depending on whether src and
#     dst are on the same remote machine or not.
    
#     src and dst will be urls to be parsed using the functions in
#     aida.common.aidaurl.

#     Will do something like:
#     if src.protocol == dst.protocol and src.computer == dst.computer:
#        transport = src.transport
#        transport.copyfile(src.path,dst.path)
#     else:
#        raise NotImplementedError
#        ## in the future, first copy from src to local sandbox, then back to dst
#        ## (or possibly directly btw src and dst? understand how rsync works
#        ## in this case)
#     """
#     pass


class Transport(object):
    """
    Abstract class for a generic transport (ssh, local, ...)
    Has following methods to operate remotely on machine, 
    and to copy a file from remote to local or viceversa:
    - chdir(self,path)
    - chmod(self,path,mode)
    - chown(self,path,uid,gid)
    - copy(self,src,dst)
    - exec_and_get_output(self)
    - exec_command(self,command)
    - get(self, src, dst)
    - getcwd(self)
    - get_attribute(self,path)
    - is_dir(self,path)
    - is_file(self,path)
    - listdir(self, path)
    - mkdir(self,path,mode)
    - normalize(self,path)
    - put(self, src, dst)
    - remove(self,path)
    - rename(self,oldpath,newpath)
    - rmdir(self,path)
    
    * __enter__ and __exit__ so that we can use with statements
      to open/close the channel (if any) and leave it open only
      while we are inside the with statement; see if we also need some
      explicit open/close methods. I'm thinking to something like:
      with Transport(...) as t:
         t.put(...)
         t.get(...)
         ...
      ...
      # And here the channel is automatically open
    """
    def __init__(self, further_params):
        """
        Will actually load the proper subclass from the plugins subfolder
        (ssh, local, ...)

        Most of the methods must be implemented there
        TODO: instead of pass, think at a proper method
        """
        pass

    
    def chdir(self,path):
        """
        Change directory to 'directory'
        
        Args: 
            path (str) - path to change working directory into.

        Raises:
            IOError - if the requested path doesn't exist on the server
        """
        raise NotImplementedError


    def chmod(self,path,mode):
        """
        Change permissions of a path.

        Args:
            path (str) - path to file
            mode (int) - new permissions
        """
        raise NotImplementedError

    
    def chown(self,path,uid,gid):
        """
        Change the owner (uid) and group (gid) of a file. 
        As with python's os.chown function, you must pass both arguments, 
        so if you only want to change one, use stat first to retrieve the 
        current owner and group.

        Args:
            path (str) - path of the file to change the owner and group of
            uid (int) - new owner's uid
            gid (int) - new group id
        """
        raise NotImplementedError


    def copy(self,src,dst):
        """
        Copy a file or a directory from remote source to remote destination
        
        Args:
            src (str) - path of the remote source directory / file
            dst (str) - path of the remote destination directory / file

        Raises: IOError if one of src or dst does not exist
        """
        raise NotImplementedError
    
    
    def exec_and_get_output(self):
        """
        TODO: must do all the bunch of task for sending and submitting a 
        calculation remotely and retrieve the results.
        """
        raise NotImplementedError


    def exec_command(self,command):
        """
        Execute the command on the shell, similarly to os.system.
        Return the value of the exit status of the command execution
        
        Args:
            command (str) - execute the command given as a string
        """
        raise NotImplementedError


    def get(self, src, dst):
        """
        Retrieve a file from remote source to local destination

        TODO: To be implemented in the plugins
        
        Args:
            src (str) - remote_folder_path
            dst (str) - local_folder_path
        """
        raise NotImplementedError


    def getcwd(self):
        """
        Return a string identifying the current working directory

        Args:
            None
        """
        raise NotImplementedError


    def get_attribute(self,path):
        """
        Return an attribute objects for file in a given path. 
        Each attribute object consists in a dictionary with the following keys:
            - st_size: size of files, in bytes 
            - st_uid: user id of owner
            - st_gid: group id of owner
            - st_mode: protection bits
            - st_atime: time of most recent access
            - st_mtime: time of most recent modification

        TODO: define in this Module the object

        Args:
            path (str) - path to file
        """
        raise NotImplementedError


    def is_dir(self,path):
        """
        Return True if path is an existing directory.

        Args:
            path (str) - path to directory
        """
        raise NotImplementedError


    def is_file(self,path):
        """
        Return True if path is an existing file.

        Args:
            path (str) - path to file
        """
        raise NotImplementedError


    def listdir(self, path='.'):
        """
        Return a list of the names of the entries in the given path. 
        The list is in arbitrary order. It does not include the special 
        entries '.' and '..' even if they are present in the directory.

        Args: 
            path (str) - path to list (default to '.')
        """
        raise NotImplementedError


    def mkdir(self,path,mode=511):
        """
        Create a folder (directory) named path with numeric mode mode. 

        Args:
            path (str) - name of the folder to create
            mode (int) - permissions (posiz-style) for the newly created folder

        TODO: decide a default permission for creation.

        Raises:
            If the directory already exists, OSError is raised.
        """
        raise NotImplementedError


    def normalize(self,path='.'):
        """
        Return the normalized path (on the server) of a given path. 
        This can be used to quickly resolve symbolic links or determine 
        what the server is considering to be the "current folder".

        Args:
            path (str) - path to be normalized

        Raises:
            IOError - if the path can't be resolved on the server
        """
        raise NotImplementedError


    def put(self, src, dst):
        """
        Put a file from local src to remote dst

        TODO: To be implemented in the plugins
        
        Args:
           src (str) - remote_folder_path
           dst (str) - local_folder_path
        """
        raise NotImplementedError


    def remove(self,path):
        """
        Remove the file at the given path. This only works on files; 
        for removing folders (directories), use rmdir.

        Args: 
            path: path to file to remove

        Raises:
            IOError: if the path is a directory
        """
        raise NotImplementedError


    def rename(self,oldpath,newpath):
        """
        Rename a file or folder from oldpath to newpath.

        Parameters:
            oldpath (str) - existing name of the file or folder
            newpath (str) - new name for the file or folder

        Raises:
            IOError - if something goes wrong
        """
        raise NotImplementedError


    def rmdir(self,path):
        """
        Remove the folder named path

        Args:
            path (str) - name of the folder to remove
        """
        raise NotImplementedError
