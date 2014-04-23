###
### GP: a note on the local transport:
### I believe that we must not use os.chdir to keep track of the folder
### in which we are, since this may have very nasty side effects in other
### parts of code, and make things not thread-safe.
### we should instead keep track internally of the 'current working directory'
### in the exact same way as paramiko does already.

import os,shutil,subprocess
import aiida.transport
from aiida.transport import FileAttribute
import StringIO
import glob
from aiida.common import aiidalogger
execlogger = aiidalogger.getChild('transport')


class LocalTransport(aiida.transport.Transport):
    """
    Support copy and command execution on the same host on which AiiDA is running via direct file copy and execution commands.
    """
    # There are no valid parameters for the local transport
    _valid_auth_params = []

    def __init__(self,**kwargs):
        super(LocalTransport,self).__init__()
        self._logger = super(LocalTransport,self).logger.getChild('local')

        # _internal_dir will emulate the concept of working directory
        # The real current working directory is not to be changed
        #        self._internal_dir = None
        self._is_open = False
        self._internal_dir = None
        # Just to avoid errors
        self._machine = kwargs.pop('machine', None)
        if self._machine and self._machine != 'localhost':
            # TODO: check if we want a different logic
            self.logger.warning('machine was passed, but it is not localhost')
        if kwargs:
            raise ValueError("Input parameters to LocalTransport"
                             " are not recognized")
        
    
    def open(self):
        """
        Opens a local transport channel
        """
        self._internal_dir = os.path.expanduser("~")
        self._is_open = True
        return self
    
    
    def close(self):
        """
        Closes the local transport channel
        """
        self._is_open = False

    @property
    def curdir(self):
        """
        Returns the _internal_dir, if the channel is open.
        If possible, use getcwd() instead!
        """
        if self._is_open:
            return os.path.realpath(self._internal_dir)
        else:
            raise aiida.transport.TransportInternalError(
                "Error, local method called for LocalTransport "
                "without opening the channel first")


    def chdir(self, path):
        """
        Changes directory to path, emulated internally.
        Args:
            path (str) - path to cd into
        Raises
            OSError if the directory does not have read attributes.
        """
        new_path = os.path.join( self.curdir,path )
        if os.access(new_path, os.R_OK):
            self._internal_dir = os.path.normpath( new_path )
        else:
            raise IOError('Not having read permissions')


    def normalize(self, path):
        """
        Normalizes path, eliminating double slashes, etc..
        Args:
            path (str) : path to normalize
        """
        return os.path.realpath( os.path.join(self.curdir,path) )

    
    def getcwd(self):
        """
        Returns the current working directory, emulated by the transport
        """
        return self.curdir


    def _os_path_split_asunder(self, path):
        """
        Used by makedirs. Takes path (a str)
        and returns a list deconcatenating the path
        """
        # TODO : test it on windows (sigh!)
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


    def makedirs(self,path,ignore_existing=False):
        """
        Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        Args:
            path (str) - directory to create
            ignore_existing (bool) - if set to true, it doesn't give any error
            if the leaf directory does already exist

        Raises:
            If the directory already exists, OSError is raised.
        """
        the_path = os.path.join(self.curdir,path)
        to_create = self._os_path_split_asunder(the_path)
        this_dir = ''
        for count,element in enumerate(to_create):
            this_dir=os.path.join(this_dir,element)
            if count+1==len(to_create) and self.isdir(this_dir) and ignore_existing:
                return
            if count+1==len(to_create) and self.isdir(this_dir) and not ignore_existing:
                os.mkdir(this_dir)
            if not os.path.exists(this_dir):
                os.mkdir(this_dir)
    
    
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

        os.mkdir( os.path.join( self.curdir,path ) )


    def rmdir(self, path):
        """
        Removes a folder at location path.
        Args:
            path (str) - path to remove
        """
        os.rmdir( os.path.join( self.curdir,path ) )


    def isdir(self,path):
        """
        Checks if 'path' is a directory.
        Returns a bool
        """
        if not path:
            return False
        else:
            return os.path.isdir( os.path.join( self.curdir,path ) )


    def chmod(self,path,mode):
        """
        Changes permission bits of object at path
        Args
            path (str) - path to modify
            mode (int) - permission bits

        Raises IOError if path does not exist.
        """
        if not path:
            raise IOError("Directory not given in input")
        real_path = os.path.join( self.curdir,path )
        if not os.path.exists(real_path):
            raise IOError("Directory not given in input")
        else:
            os.chmod( real_path , mode )
            
    
    def put(self,source,destination,dereference=False,overwrite=True,pattern=None,
            ignore_nonexisting=False):
        """
        Copies a file or a folder from source to destination.
        Automatically redirects to putfile or puttree.

        Args:
            source (str)       - absolute path to local file
            destination (str)  - path to remote file
            dereference (bool) - if True follows symbolic links
                                 default = False
            overwrite (bool)   - if True overwrites destination
                                 default = False
            pattern (str) - copy list of files matching filters
                            in Unix style. Tested on unix only.
                            default = None
                            Works only on the cwd, e.g.
                            listdir('.',*/*.txt) will not work

        Raises:
            IOError if destination is not valid
            ValueError if source is not valid
        """
        if not destination:
            raise IOError("Input destination to put function "
                             "must be a non empty string")
        if not source:
            raise ValueError("Input source to put function "
                             "must be a non empty string")

        if not os.path.isabs( source ):
            raise ValueError("Source must be an absolute path")

        if pattern:
            filtered_list = self._local_listdir(source,pattern)
            to_send = [ os.path.join(source,i) for i in filtered_list ]
            to_arrive = [ os.path.join(destination,i) for i in filtered_list ]

            for this_src,this_dst in zip(to_send,to_arrive):
                splitted_list = self._os_path_split_asunder(this_dst)

                does_dir_exist = ''
                for this_dir in splitted_list[:-1]:
                    does_dir_exist = os.path.join(does_dir_exist,this_dir)
                    try:
                        self.mkdir(does_dir_exist)
                    except OSError as e:
                        if 'File exists' in str(e):
                            pass
                        else:
                            raise
                        
                if self.isdir(this_src):
                    self.puttree( this_src,this_dst,dereference,overwrite )
                elif self.isfile(this_src):
                    self.putfile( this_src,this_dst,overwrite )
                else:
                    if ignore_nonexisting:
                        pass
                    else:
                        raise OSError("The local path {} does not exist"
                                      .format(source))                    

        else:
            if self.isdir(source):
                self.puttree( source,destination,dereference,overwrite )
            elif self.isfile(source):
                self.putfile( source,destination,overwrite )
            else:
                if ignore_nonexisting:
                    pass
                else:
                    raise OSError("The local path {} does not exist"
                                  .format(source))

                    

    def putfile(self,source,destination,overwrite=True):
        """
        Copies a file from source to destination.
        Automatically redirects to putfile or puttree.

        Args:
            source (str) - absolute path to local file
            destination (Str) - path to remote file
            overwrite (bool) - if True overwrites destination
                               default = False

        Raises:
            IOError if destination is not valid
            ValueError if source is not valid
            OSError if source does not exist
        """
        if not destination:
            raise IOError("Input destination to putfile "
                             "must be a non empty string")
        if not source:
            raise ValueError("Input source to putfile "
                             "must be a non empty string")

        if not os.path.isabs( source ):
            raise ValueError("Source must be an absolute path")

        if not os.path.exists( source ):
            raise OSError( "Source does not exists" )

        the_destination = os.path.join(self.curdir,destination)
        if os.path.exists(the_destination) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')
            
        shutil.copyfile( source, the_destination )
        
        
    def puttree(self,source,destination,dereference=False,overwrite=True):
        """
        Copies a folder recursively from source to destination.
        Automatically redirects to putfile or puttree.

        Args:
            source (str) - absolute path to local file
            destination (Str) - path to remote file
            dereference (bool) - follow symbolic links
                                 default = False
            overwrite (bool) - if True overwrites destination
                               default = False

        Raises:
            IOError if destination is not valid
            ValueError if source is not valid
            OSError if source does not exist
        """
        if not destination:
            raise IOError("Input destination to putfile "
                             "must be a non empty string")
        if not source:
            raise ValueError("Input source to putfile "
                             "must be a non empty string")

        if not os.path.isabs( source ):
            raise ValueError("Source must be an absolute path")

        if not os.path.exists( source ):
            raise OSError( "Source does not exists" )

        the_destination = os.path.join(self.curdir,destination)
        if os.path.exists(the_destination) and overwrite:
            self.rmtree(the_destination)
        elif os.path.exists(the_destination) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        shutil.copytree( source, the_destination,symlinks=dereference )


    def rmtree(self,path):
        """
        Remove tree as rm -r would do
        
        Args: path (str)
        """
        the_path = os.path.join(self.curdir,path)
        shutil.rmtree(the_path)
        

    def get(self,source,destination,dereference=False,overwrite=True,pattern=None,
            ignore_nonexisting=False):
        """
        Copies a folder or a file recursively from 'remote' source to
        'local' destination.
        Automatically redirects to getfile or gettree.

        Args:
            source (str) - path to local file
            destination (Str) - absolute path to remote file
            dereference (bool) - follow symbolic links
                                 default = False
            overwrite (bool) - if True overwrites destination
                               default = False
            pattern (str) - copy list of files matching filters
                            in Unix style. Tested on unix only.
                            default = None
                            Works only on the cwd, e.g.
                            listdir('.',*/*.txt) will not work

        Raises:
            IOError if 'remote' source is not valid
            ValueError if 'local' destination is not valid
        """
        if not destination:
            raise ValueError("Input destination to get function "
                             "must be a non empty string")
        if not source:
            raise IOError("Input source to get function "
                             "must be a non empty string")

        if not os.path.exists( os.path.join(self.curdir,source) ):
            raise IOError("Source not found")

        if not os.path.isabs( destination ):
            raise ValueError("Destination must be an absolute path")

        if pattern:
            filtered_list = self.listdir(source,pattern)
            to_retrieve = [ os.path.join(source,i) for i in filtered_list ]
            to_arrive = [ os.path.join(destination,i) for i in filtered_list ]

            for this_src,this_dst in zip(to_retrieve,to_arrive):
                splitted_list = self._os_path_split_asunder(this_dst)

                does_dir_exist = ''
                for this_dir in splitted_list[:-1]:
                    does_dir_exist = os.path.join(does_dir_exist,this_dir)
                    try:
                        os.mkdir(does_dir_exist)
                    except OSError as e:
                        if 'File exists' in str(e) or 'Is a directory' in str(e):
                            pass
                        else:
                            raise
                        
                if self.isdir(this_src):
                    self.gettree( this_src,this_dst,dereference,overwrite )
                elif self.isfile(this_src):
                    self.getfile( this_src,this_dst,overwrite )
                else:
                    if ignore_nonexisting:
                        execlogger.debug(
                                "File {} not found on the remote machine".format(this_src))
                        pass
                    else:
                        raise IOError("The remote path {} does not exist".format(
                            this_src))

        else:
            if self.isdir(source):
                self.gettree( source,destination,dereference,overwrite )
            elif self.isfile(source):
                self.getfile( source,destination,overwrite )
            else:
                if ignore_nonexisting:
                    execlogger.debug(
                        "File {} not found on the remote machine".format(source))
                    pass
                else:
                    raise IOError("The remote path {} does not exist".format(
                        source))


    def getfile(self,source,destination,overwrite=True):
        """
        Copies a file recursively from 'remote' source to
        'local' destination.

        Args:
            source (str) - path to local file
            destination (Str) - absolute path to remote file
            overwrite (bool) - if True overwrites destination
                               default = False

        Raises:
            IOError if 'remote' source is not valid or not found
            ValueError if 'local' destination is not valid
            OSError if unintentionally overwriting
        """
        if not destination:
            raise ValueError("Input destination to get function "
                             "must be a non empty string")
        if not source:
            raise IOError("Input source to get function "
                             "must be a non empty string")
        the_source = os.path.join(self.curdir,source)
        if not os.path.exists( the_source ):
            raise IOError("Source not found")
        if not os.path.isabs( destination ):
            raise ValueError("Destination must be an absolute path")
        if os.path.exists(destination) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        shutil.copyfile( the_source, destination )
        

    def gettree(self,source,destination,dereference=False,overwrite=True):
        """
        Copies a folder recursively from 'remote' source to
        'local' destination.

        Args:
            source (str) - path to local file
            destination (Str) - absolute path to remote file
            dereference (bool) - follow symbolic links
                                 default = False
            overwrite (bool) - if True overwrites destination
                               default = False

        Raises:
            IOError if 'remote' source is not valid
            ValueError if 'local' destination is not valid
            OSError if unintentionally overwriting
        """
        if not destination:
            raise ValueError("Input destination to get function "
                             "must be a non empty string")
        if not source:
            raise IOError("Input source to get function "
                             "must be a non empty string")
        the_source = os.path.join(self.curdir,source)
        if not os.path.exists( the_source ):
            raise IOError("Source not found")
        if not os.path.isabs( destination ):
            raise ValueError("Destination must be an absolute path")

        if os.path.exists(destination) and overwrite:
            self.rmtree(destination)
        elif os.path.exists(destination) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        shutil.copytree( the_source, destination, symlinks=dereference )
        

    def copy(self,source,destination,dereference=False,pattern=None):
        """
        Copies a file or a folder from 'remote' source to
        'remote' destination.
        Automatically redirects to copyfile or copytree.

        Args:
            source (str)       - path to local file
            destination (Str)  - path to remote file
            dereference (bool) - follow symbolic links
                                 default = False
            pattern (str) - copies list of files matching filters
                            in Unix style. Tested on unix only.
                            default = None

        Raises:
            ValueError if 'remote' source or destination is not valid
            OSError if source does not exist
        """
        if not source:
            raise ValueError("Input source to copy "
                             "must be a non empty object")
        if not destination:
            raise ValueError("Input destination to copy "
                             "must be a non empty object")
        if not os.path.exists(os.path.join( self.curdir,source )):
            raise OSError("Source not found")

        # exotic case where destination = source
        if self.normalize(source) == self.normalize(destination):
            raise ValueError("Cannot copy from itself to itself")

        # by default, overwrite old files
        if self.isfile(destination) or self.isdir(destination):
            self.rmtree(destination)

# TODO : fix the pattern option and make it work like put and get do

        if pattern:
            file_list = self.listdir(source,pattern)
            to_copy = [os.path.join(source,i) for i in file_list ]
            to_copy_to = [os.path.join(destination,i) for i in file_list ]

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

                if self.isdir(this_src):
                    return self.copytree(this_src,this_dst,dereference)
                else:
                    return self.copyfile( this_src,this_dst )

        else:
            if self.isdir(source):
                return self.copytree(source,destination,dereference)
            else:
                return self.copyfile( source,destination )


    def copyfile(self,source,destination):
        """
        Copies a file from 'remote' source to
        'remote' destination.

        Args:
            source (str) - path to local file
            destination (Str) - path to remote file

        Raises:
            ValueError if 'remote' source or destination is not valid
            OSError if source does not exist

        """
        if not source:
            raise ValueError("Input source to copyfile "
                             "must be a non empty object")
        if not destination:
            raise ValueError("Input destination to copyfile "
                             "must be a non empty object")
        the_source = os.path.join( self.curdir,source )
        the_destination = os.path.join( self.curdir,destination )
        if not os.path.exists(the_source):
            raise OSError("Source not found")

        shutil.copyfile( the_source, the_destination )


    def copytree(self,source,destination,dereference=False):
        """
        Copies a folder from 'remote' source to
        'remote' destination.

        Args:
            source (str) - path to local file
            destination (Str) - path to remote file
            dereference (bool) - follow symbolic links
                                 default = False

        Raises:
            ValueError if 'remote' source or destination is not valid
            OSError if source does not exist
        """
        if not source:
            raise ValueError("Input source to copytree "
                             "must be a non empty object")
        if not destination:
            raise ValueError("Input destination to copytree "
                             "must be a non empty object")
        the_source = os.path.join( self.curdir,source )
        the_destination = os.path.join( self.curdir,destination )
        if not os.path.exists(the_source):
            raise OSError("Source not found")

        shutil.copytree( the_source, the_destination, symlinks = dereference )
            
    
    def get_attribute(self,path):
        """
        Returns an object FileAttribute,
        as specified in aiida.transport.
        Receives in input the path of a given file.
        """
        os_attr = os.lstat( os.path.join(self.curdir,path) )
        aiida_attr = FileAttribute()
        # map the paramiko class into the aiida one
        # note that paramiko object contains more informations than the aiida
        for key in aiida_attr._valid_fields:
            aiida_attr[key] = getattr(os_attr,key)
        return aiida_attr


    def _local_listdir(self,path,pattern=None):
        # acts on the local folder, for the rest, same as listdir
        if not pattern:
            return os.listdir( path )
        else:
            import re
            if path.startswith('/'): # always this is the case in the local plugin
                base_dir = path
            else:
                base_dir = os.path.join(os.getcwd(),path)

            filtered_list = glob.glob(os.path.join(base_dir,pattern) )
            if not base_dir.endswith(os.sep):
                base_dir+=os.sep
            return [ re.sub(base_dir,'',i) for i in filtered_list ]
        

    def listdir(self,path='.',pattern=None):
        """
        Returns a list containing the names of the entries in the directory.
        Args = path (str) - default ='.'
               filter (str) - returns the list of files matching pattern.
                              Unix only. (Use to emulate ls * for example)
        """
        the_path = os.path.join(self.curdir,path).strip()
        if not pattern:
            return os.listdir( the_path )
        else:
            import re
            filtered_list = glob.glob(os.path.join(the_path,pattern) )
            if not the_path.endswith('/'):
                the_path+='/'
            return [ re.sub(the_path,'',i) for i in filtered_list ]


    def remove(self,path):
        """
        Removes a file at position path.
        """
        os.remove( os.path.join( self.curdir,path ) )

    
    def isfile(self,path):
        """
        Checks if object at path is a file.
        Returns a boolean.
        """
        if not path:
            return False
        else:
            return os.path.isfile( os.path.join( self.curdir,path ) )

    
    def _exec_command_internal(self,command):
        """
        Executes the specified command, first changing directory to the
        current working directory as returned by self.getcwd().
        Does not wait for the calculation to finish.

        For a higher-level exec_command that automatically waits for the
        job to finish, use exec_command_wait.
        Otherwise, to end the process, use the proc.wait() method.

        Args:
            command: the command to execute

        Returns:
            a tuple with (stdin, stdout, stderr, proc),
            where stdin, stdout and stderr behave as file-like objects,
            proc is the process object as returned by the
            subprocess.Popen() class.
        """
        proc = subprocess.Popen( command, shell=True, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 cwd=self.getcwd() )
        return proc.stdin, proc.stdout, proc.stderr, proc

    
    def exec_command_wait(self,command,stdin=None):
        """
        Executes the specified command and waits for it to finish.
        
        Args:
            command: the command to execute

        Returns:
            a tuple with (return_value, stdout, stderr) where stdout and stderr
            are strings.
        """
        local_stdin, local_stdout, local_stderr, local_proc = self._exec_command_internal(
                                                                   command)
        
        if stdin is not None:
            if isinstance(stdin, basestring):
                filelike_stdin = StringIO.StringIO(stdin)
            else:
                filelike_stdin = stdin
            
            try:
                for l in filelike_stdin.readlines():
                    local_proc.stdin.write(l)
            except AttributeError:
                raise ValueError("stdin can only be either a string of a "
                                 "file-like object!")
        else:
            filelike_stdin = None

        local_stdin.flush()
        # TODO : instead of stringIO use cstringIO
        # TODO : use input option of communicate()
        output_text, stderr_text = local_proc.communicate()

        retval = local_proc.returncode

        return retval, output_text, stderr_text


    def gotocomputer_command(self, remotedir):
        """
        Return a string to be run using os.system in order to connect
        via the transport to the remote directory.

        Expected behaviors:

        * A new bash session is opened

        * A reasonable error message is produced if the folder does not exist

        :param str remotedir: the full path of the remote directory
        """
        return """bash -c "if [ -d {escaped_remotedir} ] ; then cd {escaped_remotedir} ; bash --rcfile <(echo 'if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi ; export PS1="'"\[\033[01;31m\][AiiDA]\033[00m\]$PS1"'"') ; else echo  '  ** The directory' ; echo '  ** {remotedir}' ; echo '  ** seems to have been deleted, I logout...' ; fi" """.format(
        escaped_remotedir="'{}'".format(remotedir), remotedir=remotedir)


    def rename(self, src,dst):
        """
        Rename a file or folder from oldpath to newpath.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises IOError: if src/dst is not found
        :raises ValueError: if src/dst is not a valid string
        """
        if not src:
            raise ValueError("Source {} is not a valid string".format(src))
        if not dst:
            raise ValueError("Destination {} is not a valid string".format(dst))
        if not os.path.exists( src ):
            raise IOError("Source {} does not exist".format(src))
        if not os.path.exists( dst ):
            raise IOError("Destination {} does not exist".format(dst))
        
        shutil.move(src,dst)

