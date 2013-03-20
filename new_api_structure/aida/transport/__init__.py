def copyfile(src, dst):
    """
    a function that does the correct thing depending on whether src and
    dst are on the same remote machine or not.
    
    src and dst will be urls to be parsed using the functions in
    aida.common.aidaurl.

    Will do something like:
    if src.protocol == dst.protocol and src.computer == dst.computer:
       transport = src.transport
       transport.copyfile(src.path,dst.path)
    else:
       raise NotImplementedError
       ## in the future, first copy from src to local sandbox, then back to dst
       ## (or possibly directly btw src and dst? understand how rsync works
       ## in this case)
    """
    pass


class Transport(object):
    """
    Abstract class for a generic transport (ssh, local, ...)

    Here we show only the implementation of get and put, but
    other functions to be implemented are (take inspiration from
    python functions e.g. in os and shutils)
    * copy (also with wildcards if dst is a dir; in the future, correct
            management of symlinks, permissions, ...)
    * exec()  to exec a specific command remotely; pass arguments
            in a list so that they can be escaped properly
    * is_dir, is_file, list_dir, mkdir, remove, chmod (to get and set)
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

    
    def chdir(self,directory):
        """
        Change directory to 'directory'
        
        Args: 
            directory: path to change working directory into.

        Raises:
            IOError: if the requested path doesn't exist on the server
        """
        raise NotImplementedError
    def exec_and_get_output():
        raise NotImplementedError
    def exec_command():
        raise NotImplementedError
    def get(self, src, dst):
        """
        Retrieve a file from remote source to local destination

        TODO: To be implemented in the plugins
        
        Args:
            src: remote_folder_path
            dst: local_folder_path
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
        Return an attribute objects for file in a given path. Each attribute object consists in a dictionary with the following keys:
            - st_size: size of files, in bytes 
            - st_uid: user id of owner
            - st_gid: group id of owner
            - st_mode: protection bits
            - st_atime: time of most recent access
            - st_mtime: time of most recent modification

        TODO: define in this Module the object

        Args:
            path: path to file
        """
        raise NotImplementedError


    def mkdir(self,path,mode=511):
        """
        Create a folder (directory) named path with numeric mode mode. 

        Args:
            path: name of the folder to create
            mode: permissions (posiz-style) for the newly created folder

        TODO: decide a default permission for creation.

        Raises:
            If the directory already exists, OSError is raised.
        """
        raise NotImplementedError


    def listdir(self, path='.'):
        """
        Return a list of the names of the entries in the given path. The list is in arbitrary order. It does not include the special entries '.' and '..' even if they are present in the directory.

        Args: 
            path: path to list (default to '.')
        """
        raise NotImplementedError


    def put(self, src, dst):
        """
        Put a file from local src to remote dst

        TODO: To be implemented in the plugins
        
        Args:
           src: remote_folder_path
           dst: local_folder_path
        """
        raise NotImplementedError


    def normalize(self,path='.'):
        """
        Return the normalized path (on the server) of a given path. This can be used to quickly resolve symbolic links or determine what the server is considering to be the "current folder".

        Args:
            path: path to be normalized

        Raises:
            IOError: if the path can't be resolved on the server
        """
        raise NotImplementedError


    def remove(self,path):
        """Remove the file at the given path. This only works on files; for removing folders (directories), use rmdir.

        Args: 

        """
        raise NotImplementedError


    def rename():
        raise NotImplementedError
    def rmdir():
        raise NotImplementedError
