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
        """
        pass

    
    def get(self, src, dst):
        """
        Retrieve a file

        To be implemented in the plugins
        
        Args:
           src: remote_folder_path
           dst: local_folder_path
        """
        raise NotImplementedError

    def put(self, src, dst):
        """
        Put a file remotely

        To be implemented in the plugins
        
        Args:
           src: remote_folder_path
           dst: local_folder_path
        """
        raise NotImplementedError

