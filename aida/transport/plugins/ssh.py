from stat import S_ISDIR,S_ISREG
import StringIO
import paramiko
import os
import fnmatch
import glob

import aida.transport
from aida.common.utils import escape_for_bash
from aida.common import aidalogger
from aida.transport import FileAttribute

# TODO : callback functions in paramiko are currently not used much and probably broken

class SshTransport(aida.transport.Transport):
    # Valid keywords accepted by the connect method of paramiko.SSHClient
    # I disable 'password'
    _valid_connect_params = ['port', 'username', 'pkey',
                             'key_filename', 'timeout', 'allow_agent',
                             'look_for_keys', 'compress']
    
    def __init__(self, machine, **kwargs):
        """
        Initialize the SshTransport class.
        
        Args:
            machine: the machine to connect to
            load_system_host_keys (optional, default False): if False, do not
                load the system host keys
            key_policy (optional, default = paramiko.RejectPolicy()): the
                policy to use for unknown keys
            Other parameters valid for the ssh connect function (see the 
            self._valid_connect_params list) are passed to the connect
            function (as port, username, password, ...); taken from the
            accepted paramiko.SSHClient.connect() params)

            TODO : implement a property self.sftp that raises a reasonable
               exception if the channel has not been opened. Understand if
               we need explicit open() and close() functions.
        """

        ## First call the parent __init__ to setup the logger!
        super(SshTransport,self).__init__()
        self._logger = super(SshTransport,self).logger.getChild('ssh')

        self._is_open = False
        self._sftp = None
        
        self._machine = machine

        self._client = paramiko.SSHClient()
        self._load_system_host_keys = kwargs.pop(
            'load_system_host_keys', False)
        if self._load_system_host_keys:
            self._client.load_system_host_keys()

        self._missing_key_policy = kwargs.pop(
            'key_policy',paramiko.RejectPolicy()) # This is paramiko default
        self._client.set_missing_host_key_policy(self._missing_key_policy)

        self._connect_args = {}
        for k in self._valid_connect_params:
            try:
                self._connect_args[k] = kwargs.pop(k)
            except KeyError:
                pass

        if kwargs:
            raise ValueError("The following parameters were not accepted by "
                             "the transport: {}".format(
                    ",".join(str(k) for k in kwargs)))

    def __enter__(self):
        """
        Open a SSHClient to the machine possibly using the parameters given
        in the __init__. 
        
        Also opens a sftp channel, ready to be used.
        The current working directory is set explicitly, so it is not None.
        """
        
        # Open a SSHClient
        try:
            self._client.connect(self._machine,**self._connect_args)
        except Exception as e:
            self.logger.error("Error connecting through SSH: [{}] {}, "
                              "connect_args were: {}".format(
                                  e.__class__.__name__,
                                  e.message,
                                  self._connect_args))
            raise

        # Open also a SFTPClient
        self._sftp = self._client.open_sftp()
        # Set the current directory to a explicit path, and not to None
        self._sftp.chdir(self._sftp.normalize('.'))

        self._is_open = True
        
        return self
        
    def __exit__(self, type, value, traceback):
        """
        Close the SFTP channel, and the SSHClient.
        
        TODO : correctly manage exceptions
        """
        self._sftp.close()
        self._client.close()
        self._is_open = False

    @property
    def sshclient(self):
        if not self._is_open:
            raise aida.transport.TransportInternalError(
                "Error, ssh method called for SshTransport "
                "without opening the channel first")
        return self._client

    @property
    def sftp(self):
        if not self._is_open:
            raise aida.transport.TransportInternalError(
                "Error, sftp method called for SshTransport "
                "without opening the channel first")
        return self._sftp

    def __unicode__(self):
        """
        Return a useful string.
        """
        conn_info = unicode(self._machine)
        try:
            conn_info = (unicode(self._connect_args['username']) + 
                         u'@' + conn_info)
        except KeyError:
            # No username explicitly defined: ignore
            pass
        try:
            conn_info += u':{}'.format(self._connect_args['port'])
        except KeyError:
        # No port explicitly defined: ignore
            pass
            
        return u'{}({})'.format(self.__class__.__name__, conn_info)

    def chdir(self, path):
        """
        Change directory of the SFTP session. Emulated internally by
        paramiko. 

        Differently from paramiko, if you pass None to chdir, nothing
        happens and the cwd is unchanged.
        """
        old_path = self.sftp.getcwd()
        if path is not None:
            self.sftp.chdir(path)
        
        # Paramiko already checked that path is a folder, otherwise I would
        # have gotten an exception. Now, I want to check that I have read
        # permissions in this folder (nothing is said on write permissions,
        # though).
        # Otherwise, if I do _exec_command_internal, that as a first operation 
        # cd's in a folder, I get a wrong retval, that is an unwanted behavior.
        #
        # Note: I don't store the result of the function; if I have no
        # read permissions, this will raise an exception.
        try:
            self.sftp.stat('.')
        except IOError as e:
            if 'Permission denied' in e:
                self.chdir(old_path)
            raise IOError(e)


    def normalize(self, path):
        """
        Returns the normalized path (removing double slashes, etc...)
        """
        return self.sftp.normalize(path)
        
    def getcwd(self):
        """
        Return the current working directory for this SFTP session, as
        emulated by paramiko. If no directory has been set with chdir,
        this method will return None. But in __enter__ this is set explicitly,
        so this should never happen within this class.
        """
        return self.sftp.getcwd()


    def makedirs(self,path,ignore_existing=False):
        """
        Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        NOTE: since os.path.split uses the separators as the host system
        (that could be windows), I assume the remote computer is Linux-based
        and use '/' as separators!

        Args:
            path (str) - directory to create
            ignore_existing (bool) - if set to true, it doesn't give any error
            if the leaf directory does already exist

        Raises:
            If the directory already exists, OSError is raised.
        """
        if path.startswith('/'):
            to_create = path.strip().split('/')[1:]
            this_dir='/'
        else:
            to_create = path.strip().split('/')
            this_dir = ''
            
        for count,element in enumerate(to_create):
            if count>0:
                this_dir += '/'
            this_dir += element
            if count+1==len(to_create) and self.isdir(this_dir) and ignore_existing:
                return
            if count+1==len(to_create) and self.isdir(this_dir) and not ignore_existing:
                self.mkdir(this_dir)
            if not self.isdir(this_dir):
                self.mkdir(this_dir)


    
    def mkdir(self,path,ignore_existing=False):
        """
        Create a folder (directory) named path.

        Args:
            path (str) - name of the folder to create
            ignore_existing: if True, does not give any error if the directory
                already exists

        Raises:
            If the directory already exists, OSError is raised.
        """
        if ignore_existing and self.isdir(path):
            return
        
        try:
            self.sftp.mkdir(path)
        except IOError as e:
            raise OSError("Error during mkdir of '{}' in '{}', maybe the directory "
                          "already exists? ({})".format(
                              path,self.getcwd(), e.message))

    # TODO : implement rmtree
    def rmtree(self,path):
        """
        Remove a file or a directory at path, recursively
        Flags used: -r: recursive copy; -f: force, makes the command non interactive;

        Args:
            path (str) - remote path to delete

        Raises:
            IOError if the rm execution failed.
        """
        # Assuming linux rm command!
        
        # TODO : do we need to avoid the aliases when calling rm_exe='rm'? Call directly /bin/rm?
                
        rm_exe = 'rm'
        rm_flags = '-r -f'
        # if in input I give an invalid object raise ValueError
        if not path:
            raise ValueError('Input to rmtree() must be a non empty string. ' +
                             'Found instead %s as path' % path)
        
        command = '{} {} {}'.format(rm_exe,
                                       rm_flags,
                                       escape_for_bash(path))

        retval,stdout,stderr = self.exec_command_wait(command)
        
        if retval == 0:
            if stderr.strip():
                self.logger.warning("There was nonempty stderr in the rm "
                                    "command: {}".format(stderr))
            return True
        else:
            self.logger.error("Problem executing rm. Exit code: {}, stdout: '{}', "
                              "stderr: '{}'".format(retval, stdout, stderr))
            raise IOError("Error while executing rm. Exit code: {}".format(retval) )

    
    def rmdir(self, path):
        """
        Remove the folder named 'path' if empty.
        """
        self.sftp.rmdir(path)


    def isdir(self,path):
        """
        Return True if the given path is a directory, False otherwise.
        Return False also if the path does not exist.
        """
        # Return False on empty string (paramiko would map this to the local
        # folder instead)
        if not path:
            return False
        try:
            return S_ISDIR(self.sftp.stat(path).st_mode)
        except IOError as e:
            if getattr(e,"errno",None) == 2:
                # errno=2 means path does not exist: I return False
                return False
            else:
                raise # Typically if I don't have permissions (errno=13)


    def chmod(self,path,mode):
        """
        Change permissions to path

        Args: path (str) - path to file
               mode (int) - new permission bits
        """
        if not path:
            raise IOError("Input path is an empty argument.")
        return self.sftp.chmod(path,mode)


    def _os_path_split_asunder(self, path):
        """
        Used by makedirs. Takes path (a str)
        and returns a list deconcatenating the path
        """
        parts = []
        while True:
            newpath, tail = os.path.split(path)
            if newpath == path:
                assert not tail
                if path: parts.append(path)
                break
            parts.append(tail)
            path = newpath
        parts.reverse()
        return parts
            

    def put(self,localpath,remotepath,callback=None,dereference=False,overwrite=True,
            pattern=None):
        """
        Put a file or a folder from local to remote.
        redirects to putfile or puttree.
        Args:
            localpath: an (absolute) local path
            remotepath: a remote path
            dereference(bool) - follow symbolic links
                default = False
            overwrite(bool) - if True overwrites files and folders
                default = False
            pattern (str) - return list of files matching filters
                            in Unix style. Tested on unix only.
                            default = None
                            Works only on the cwd, e.g.
                            listdir('.',*/*.txt) will not work

        Raises:
            ValueError if local path is invalid
            OSError if the localpath does not exist
        """
        # TODO: flag confirm exists since v1.7.7. What is the paramiko
        # version supported?

        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")

        if pattern:
            filtered_list = self._local_listdir(localpath,pattern)
            to_send = [ os.path.join(localpath,i) for i in filtered_list ]
            to_arrive = [ os.path.join(remotepath,i) for i in filtered_list ]

            for this_lpath,this_rpath in zip(to_send,to_arrive):
                splitted_list = self._os_path_split_asunder(this_rpath)

                does_dir_exist = ''
                for this_dir in splitted_list[:-1]:
                    does_dir_exist = os.path.join(does_dir_exist,this_dir)
                    try:
                        self.mkdir(does_dir_exist)
                    except OSError as e:
                        if 'File exists' in e.message:
                            pass
                        
                if os.path.isdir(this_lpath):
                    self.puttree( this_lpath,this_rpath,callback,dereference,overwrite )
                else:
                    self.putfile( this_lpath,this_rpath,callback,overwrite )

        else:
            if os.path.isdir(localpath):
                self.puttree( localpath,remotepath,callback,dereference,overwrite )
            else:
                self.putfile( localpath,remotepath,callback,overwrite )


    def putfile(self,localpath,remotepath,callback=None,overwrite=True):
        """
        Put a file from local to remote.

        Args:
            localpath: an (absolute) local path
            remotepath: a remote path
            overwrite(bool) - if True overwrites files and folders
                default = False

        Raises:
            ValueError if local path is invalid
            OSError if the localpath does not exist,
                    or unintentionally overwriting
        """        
        # TODO : check what happens if I give in input a directory
        
        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")

        if self.isfile(remotepath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')
        
        return self.sftp.put(localpath,remotepath,callback=callback)


    def puttree(self,localpath,remotepath,callback=None,dereference=False,overwrite=True):
        """
        Put a folder recursively from local to remote.

        Args:
            localpath: an (absolute) local path
            remotepath: a remote path
            dereference(bool) - follow symbolic links
                default = False
            overwrite(bool) - if True overwrites files and folders
                default = False

        Raises:
            ValueError if local path is invalid
            OSError if the localpath does not exist, or trying to overwrite
            IOError if remotepath is invalid

        Note: setting dereference equal to true could cause infinite loops.
              see os.walk() documentation
        """
        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")
        
        if not os.path.exists(localpath):
            raise OSError("The localpath does not exists")

        if not os.path.isdir(localpath):
            raise ValueError("Input localpath is not a folder: {}".format(localpath))

        if not remotepath:
            raise IOError("remotepath must be a non empty string")

        if self.isdir(remotepath) and overwrite:
            pass
        elif self.isdir(remotepath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')
        elif not self.isdir(remotepath):
            self.mkdir(remotepath)
        
        base_name = localpath
        
        for this_source in os.walk(localpath):
            this_basename = this_source[0].lstrip(localpath)
            try:
                self.sftp.stat( os.path.join(remotepath,this_basename) )
            except IOError as e:
                self.mkdir( os.path.join(remotepath,this_basename) )
                
            for this_file in this_source[2]:
                this_local_file = os.path.join(localpath,this_basename,this_file)        
                this_remote_file = os.path.join(remotepath,this_basename,this_file)
                self.putfile(this_local_file,this_remote_file)


    def get(self,remotepath,localpath,callback=None,dereference=False,overwrite=True,
            pattern=None):
        """
        Get a file or folder from remote to local.
        Redirects to getfile or gettree.

        Args:
            remotepath: a remote path
            localpath: an (absolute) local path
            dereference(bool) - follow symbolic links
                default = False
            overwrite(bool) - if True overwrites files and folders
                default = False
            pattern (str) - return list of files matching filters
                            in Unix style. Tested on unix only.
                            default = None
                            Works only on the cwd, e.g.
                            listdir('.',*/*.txt) will not work

        Raises:
            ValueError if local path is invalid
            IOError if the remotepath is not found
        """
        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")

        if pattern:
            filtered_list = self.listdir(remotepath,pattern)
            to_retrieve = [ os.path.join(remotepath,i) for i in filtered_list ]
            to_arrive = [ os.path.join(localpath,i) for i in filtered_list ]

            for this_src,this_dst in zip(to_retrieve,to_arrive):
                splitted_list = self._os_path_split_asunder(this_dst)

                does_dir_exist = ''
                for this_dir in splitted_list[:-1]:
                    does_dir_exist = os.path.join(does_dir_exist,this_dir)
                    try:
                        self.mkdir(does_dir_exist)
                    except OSError as e:
                        if 'File exists' in e.message:
                            pass
                        
                if self.isdir(this_src):
                    self.gettree( this_src,this_dst,callback,dereference,overwrite )
                else:
                    self.getfile( this_src,this_dst,callback,overwrite )

        else:
            if self.isdir(remotepath):
                self.gettree( remotepath,localpath,callback,dereference,overwrite )
            else:
                self.getfile( remotepath,localpath,callback,overwrite )


    def getfile(self,remotepath,localpath,callback=None,overwrite=True):
        """
        Get a file from remote to local.

        Args:
            remotepath: a remote path
            localpath: an (absolute) local path
            overwrite(bool) - if True overwrites files and folders
                default = False

        Raises:
            ValueError if local path is invalid
            OSError if unintentionally overwriting
        """
        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")

        if os.path.isfile(localpath) and not overwrite:            
            raise OSError('Destination already exists: not overwriting it')

        return self.sftp.get(remotepath,localpath,callback)
        
        
    def gettree(self,remotepath,localpath,callback=None,dereference=False,overwrite=True):
        """
        Get a folder recursively from remote to local.

        Args:
            remotepath: a remote path
            localpath: an (absolute) local path
            dereference(bool) - follow symbolic links. Currently not implemented
                default = False
            overwrite(bool) - if True overwrites files and folders
                default = False

        Raises:
            ValueError if local path is invalid
            IOError if the remotepath is not found
            OSError if unintentionally overwriting
        """
        # TODO : implement dereference
        item_list = self.listdir(remotepath)
        dest = str(localpath)

        if os.path.isdir(localpath) and not overwrite:            
            raise OSError('Destination already exists: not overwriting it')

        if not remotepath:
            raise IOError("Remotepath must be a non empty string")
        if not localpath:
            raise ValueError("Localpaths must be a non empty string")

        if not os.path.isabs(localpath):
            raise ValueError("Localpaths must be an absolute path")
        
        if not os.path.isdir(dest):
            os.mkdir(dest)
        
        for item in item_list:
            item = str(item)

            if self.isdir( os.path.join(remotepath,item) ):
                self.gettree( os.path.join(remotepath,item) , os.path.join(dest,item) )
            else:
                self.getfile( os.path.join(remotepath,item) , os.path.join(dest,item) )


    def get_attribute(self,path):
        """
        Returns the object Fileattribute, specified in aida.transport
        Receives in input the path of a given file.
        """
        paramiko_attr = self.sftp.lstat(path)
        aida_attr = FileAttribute()
        # map the paramiko class into the aida one
        # note that paramiko object contains more informations than the aida
        for key in aida_attr._valid_fields:
            aida_attr[key] = getattr(paramiko_attr,key)
        return aida_attr


    def copyfile(self,remotesource,remotedestination):
        """
        Copy a file from remote source to remote destination
        Redirects to copy().
        
        Args:
        remotesource,remotedestination
        """
        cp_flags = '-f'
        return copy(remotesource,remotedestination,cp_flags=cp_flags)


    def copytree(self,remotesource,remotedestination):
        """
        copy a folder recursively from remote source to remote destination
        Redirects to copy()

        Args:
        remotesource,remotedestination
        """
        cp_flags = '-r -f'
        return copy(remotesource,remotedestination,cp_flags=cp_flags)


    def copy(self,remotesource,remotedestination,dereference=False, cp_flags='-r -f',
             pattern=None):
        """
        Copy a file or a directory from remote source to remote destination.
        Flags used: -r: recursive copy; -f: force, makes the command non interactive;
          -L follows symbolic links

        Args:
            remotesource (str) - file to copy from
            remotedestination (str) - file to copy to
            dereference (bool) - if True, copy content instead of copying the symlinks only
            cp_flags (str)     - default = '-r -f'
            pattern (str)      - return list of files matching filters
                                 in Unix style. Tested on unix only.
                                 default = None
                                 Works only on the cwd, e.g.
                                 listdir('.',*/*.txt) will not work

        Raises:
            IOError if the cp execution failed.
        """
        # In the majority of cases, we should deal with linux cp commands
        
        # TODO : do we need to avoid the aliases when calling cp_exe='cp'? Call directly /bin/cp?
        
        # TODO: verify that it does not re
        
        # For the moment, these are hardcoded. They may become parameters
        # as soon as we see the need.
        
        cp_exe='cp'
        
        ## To evaluate if we also want -p: preserves mode,ownership and timestamp
        if dereference:
            # use -L; --dereference is not supported on mac
            cp_flags+=' -L'

        # if in input I give an invalid object raise ValueError
        if not remotesource:
            raise ValueError('Input to copy() must be a non empty string. ' +
                             'Found instead %s as remotesource' % remotesource)

        if not remotedestination:
            raise ValueError('Input to copy() must be a non empty string. ' +
                             'Found instead %s as remotedestination' % remotedestination)
        
        if pattern:
            filtered_files = self.listdir(remotesource,pattern)
            to_copy = [ os.path.join(remotesource,i) for i in filtered_files ]
            to_copy_to = [ os.path.join(remotedestination,i) for i in filtered_files ]

            for this_src,this_dst in zip(to_copy,to_copy_to):
                splitted_list = self._os_path_split_asunder(this_dst)

                does_dir_exist = ''
                for this_dir in splitted_list[:-1]:
                    does_dir_exist = os.path.join(does_dir_exist,this_dir)
                    try:
                        self.mkdir(does_dir_exist)
                    except OSError as e:
                        if 'File exists' in e.message:
                            pass

                self._exec_cp(cp_exe,cp_flags,this_src,this_dst)

        else:
            self._exec_cp(cp_exe,cp_flags,remotesource,remotedestination)


    def _exec_cp(self,cp_exe,cp_flags,src,dst):
        # to simplify writing the above copy function
        command = '{} {} {} {}'.format(cp_exe,cp_flags,escape_for_bash(src),
                                       escape_for_bash(dst))

        retval,stdout,stderr = self.exec_command_wait(command)
        
        # TODO : check and fix below
            
        if retval == 0:
            if stderr.strip():
                self.logger.warning("There was nonempty stderr in the cp "
                                        "command: {}".format(stderr))
        else:
            self.logger.error("Problem executing cp. Exit code: {}, stdout: '{}', "
                              "stderr: '{}', command: '{}'"
                              .format(retval, stdout, stderr,command))
            raise IOError("Error while executing cp. Exit code: {}".format(retval) )

                
    def _local_listdir(self,path,pattern=None):
        # acts on the local folder, for the rest, same as listdir
        if not pattern:
            return os.listdir( path )
        else:
            import re
            if path.startswith('/'): # always this is the case in the local case
                base_dir = path
            else:
                base_dir = os.path.join(os.getcwd(),path)

            filtered_list = glob.glob(os.path.join(base_dir,pattern) )
            if not base_dir.endswith(os.sep):
                base_dir+=os.sep
            return [ re.sub(base_dir,'',i) for i in filtered_list ]


    def listdir(self,path='.',pattern=None):
        """
        Get the list of files at path.
        Args: path - default = '.'
              filter (str) - returns the list of files matching pattern.
                             Unix only. (Use to emulate ls * for example)
        """
        if not pattern:
            return self.sftp.listdir(path)
        else:
            import re
            if path.startswith('/'):
                base_dir = path
            else:
                base_dir = os.path.join(self.getcwd(),path)

            filtered_list = glob.glob(os.path.join(base_dir,pattern) )
            if not base_dir.endswith('/'):
                base_dir += '/'
            return [ re.sub(base_dir,'',i) for i in filtered_list ]


    def remove(self,path):
        """
        Remove a single file at 'path'
        """
        return self.sftp.remove(path)

    
    def isfile(self,path):
        """
        Return True if the given path is a file, False otherwise.
        Return False also if the path does not exist.
        """
        # This should not be needed for files, since an empty string should
        # be mapped by paramiko to the local directory - which is not a file -
        # but this is just to be sure
        if not path:
            return False
        try:
            self.logger.debug("stat for path '{}' ('{}'): {} [{}]".format(
                    path, self.sftp.normalize(path),
                    self.sftp.stat(path),self.sftp.stat(path).st_mode))
            return S_ISREG(self.sftp.stat(path).st_mode)
        except IOError as e:
            if getattr(e,"errno",None) == 2:
                # errno=2 means path does not exist: I return False
                return False
            else:
                raise # Typically if I don't have permissions (errno=13)

    def _exec_command_internal(self,command,combine_stderr=False,bufsize=-1):
        """
        Executes the specified command, first changing directory to the
        current working directory are returned by
        self.getcwd().
        Does not wait for the calculation to finish.

        For a higher-level _exec_command_internal that automatically waits for the
        job to finish, use exec_command_wait.

        Args:
            command: the command to execute
            combine_stderr (default False): if True, combine stdout and
                stderr on the same buffer (i.e., stdout).
                Note: If combine_stderr is True, stderr will always be empty.
            bufsize: same meaning of the one used by paramiko.
        
        Returns:
            a tuple with (stdin, stdout, stderr, channel),
            where stdin, stdout and stderr behave as file-like objects,
            plus the methods provided by paramiko, and channel is a 
            paramiko.Channel object.
        """
        channel = self.sshclient.get_transport().open_session()
        channel.set_combine_stderr(combine_stderr)

        if self.getcwd() is not None:
            escaped_folder = escape_for_bash(self.getcwd())
            command_to_execute = ("cd {escaped_folder} && "
                                  "{real_command}".format(
                    escaped_folder = escaped_folder,
                    real_command = command))
        else:
            command_to_execute = command

        self.logger.debug("Command to be executed: {}".format(
                command_to_execute))

        channel.exec_command(command_to_execute)
        
        stdin = channel.makefile('wb',bufsize) 
        stdout = channel.makefile('rb',bufsize) 
        stderr = channel.makefile_stderr('rb',bufsize) 

        return stdin, stdout, stderr, channel

    def exec_command_wait(self,command,stdin=None,combine_stderr=False,
                          bufsize=-1):
        """
        Executes the specified command and waits for it to finish.
        
        TODO: To see if like this it works or hangs because of buffer problems.

        Args:
            command: the command to execute
            stdin: can either be None (the default), a string or a
                   file-like object.
            combine_stderr: (optional, default=False) see docstring of
                   self._exec_command_internal()
            bufsize: same meaning of paramiko.

        Returns:
            a tuple with (return_value, stdout, stderr) where stdout and stderr
            are strings.
        """
        ssh_stdin, stdout, stderr, channel = self._exec_command_internal(
            command, combine_stderr,bufsize=bufsize)
        
        if stdin is not None:
            if isinstance(stdin, basestring):
                filelike_stdin = StringIO.StringIO(stdin)
            else:
                filelike_stdin = stdin

            try:
                for l in filelike_stdin.readlines():
                    ssh_stdin.write(l)
            except AttributeError:
                raise ValueError("stdin can only be either a string of a "
                                 "file-like object!")

        # I flush and close them anyway; important to call shutdown_write
        # to avoid hangouts
        ssh_stdin.flush()
        ssh_stdin.channel.shutdown_write()

        output_text = stdout.read()
        
        # I get the return code (blocking, but in principle I waited above)
        retval = channel.recv_exit_status()

        stderr_text = stderr.read()

        return retval, output_text, stderr_text


if __name__ == '__main__':
    # Test ssh plugin on localhost
    import unittest
    import logging
    from test import *
#    aidalogger.setLevel(logging.DEBUG)


    class TestBasicConnection(unittest.TestCase):
        """
        Test basic connections.
        """

        def test_closed_connection_ssh(self):
            with self.assertRaises(aida.transport.TransportInternalError):
                t = SshTransport(machine='localhost')
                t._exec_command_internal('ls')

        def test_closed_connection_sftp(self):
            with self.assertRaises(aida.transport.TransportInternalError):
                t = SshTransport(machine='localhost')
                t.listdir()
                
        def test_invalid_param(self):
            with self.assertRaises(ValueError):
                SshTransport(machine='localhost', invalid_param=True)
                             

        def test_auto_add_policy(self):
            with SshTransport(machine='localhost', timeout=30, 
                              load_system_host_keys=True,
                              key_policy=paramiko.AutoAddPolicy()) as t:
                pass

        def test_no_host_key(self):
            with self.assertRaises(paramiko.SSHException):
                with SshTransport(machine='localhost', timeout=30, 
                                  load_system_host_keys = False) as t:
                    pass

    # Load the plugin tests
    run_tests('ssh')
    
    unittest.main()
