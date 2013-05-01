###
### GP: a note on the local transport:
### I believe that we must not use os.chdir to keep track of the folder
### in which we are, since this may have very nasty side effects in other
### parts of code, and make things not thread-safe.
### we should instead keep track internally of the 'current working directory'
### in the exact same way as paramiko does already.

import os,shutil,subprocess
import aida.transport
from aida.common.utils import escape_for_bash
from aida.common import aidalogger
from aida.common.extendeddicts import FixedFieldsAttributeDict
import StringIO

class FileAttribute(FixedFieldsAttributeDict):
    """
    A class with attributes of a file, that is returned by get_attribute()
    """
    _valid_fields = (
        'st_size',
        'st_uid',
        'st_gid',
        'st_mode',
        'st_atime',
        'st_mtime',
        )


class LocalTransport(aida.transport.Transport):

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
        if self._machine and self._machine is not 'localhost':
            # TODO: check if we want a different logic
            self.logger.warning('machine was passed, but it is not localhost')
        if kwargs:
            raise ValueError("Input parameters to LocalTransport"
                             " are not recognized")
        
    
    def __enter__(self):
        """
        Opens a local transport channel
        """
        self._internal_dir = os.path.expanduser("~")
        self._is_open = True
        return self
    
    
    def __exit__(self, type, value, traceback):
        """
        Closes the local transport channel
        """
        self._is_open = False

    @property
    def curdir(self):
        if self._is_open:
            return os.path.realpath(self._internal_dir)
        # TODO : rather use os.path.realpath
        # but on mac, there will be a disambiguity to correct, since the folde /tmp
        # is in fact a symbolic link to /private/tmp
        else:
            raise aida.transport.TransportInternalError(
                "Error, local method called for LocalTransport "
                "without opening the channel first")


    def chdir(self, path):
        """
        Changes directory to path, emulated internally.
        Raises OSError if the directory does not have read attributes.
        """
        new_path = os.path.join( self.curdir,path )
        if os.access(new_path, os.R_OK):
            self._internal_dir = os.path.normpath( new_path )
        else:
            raise IOError('Not having read permissions')

    
    def normalize(self, path):
        """
        Normalizes path, eliminating double slashes, etc..
        """
        return os.path.realpath( os.path.join(self.curdir,path) )

    
    def getcwd(self):
        """
        Returns the current working directory, emulated by the transport
        """
        return self.curdir


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
        """
        if not path:
            raise IOError("Directory not given in input")
        real_path = os.path.join( self.curdir,path )
        if not os.path.exists(real_path):
            raise IOError("Directory not given in input")
        else:
            os.chmod( real_path , mode )
            
    
    def put(self,source,destination,dereference=False,overwrite=True):
        """
        Copies a file from source to destination
        """
        if not destination:
            raise IOError("Input destination to put function "
                             "must be a non empty string")
        if not source:
            raise ValueError("Input source to put function "
                             "must be a non empty string")

        if not os.path.isabs( source ):
            raise ValueError("Source must be an absolute path")

        if self.isdir(source):
            self.puttree( source,destination,dereference,overwrite )
        else:
            self.putfile( source,destination,overwrite )
                    

    def putfile(self,source,destination,overwrite=True):
        """
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

        shutil.copytree( source, the_destination )


    def rmtree(self,path):
        the_path = os.path.join(self.curdir,path)
        shutil.rmtree(the_path)
        

    def get(self,source,destination,dereference=False,overwrite=True):
        """
        Copies a file from source to destination
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
        
        if self.isdir(source):
            self.gettree( source,destination,dereference,overwrite )
        else:
            self.getfile( source,destination,overwrite )


    def getfile(self,source,destination,overwrite=True):
        """
        Copies a file from source to destination
        (equivalent to copy)
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
        Copies a file from source to destination
        (equivalent to copy)
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
        

    def copy(self,source,destination,dereference=False):
        """
        """
        if not source:
            raise ValueError("Input source to copy "
                             "must be a non empty object")
        if not destination:
            raise ValueError("Input destination to copy "
                             "must be a non empty object")
        if not os.path.exists(os.path.join( self.curdir,source )):
            raise OSError("Source not found")
        if self.isdir(source):
            return self.copytree(source,destination,dereference)

        if self.isfile(source):
            return self.copyfile( source,destination )        


    def copyfile(self,source,destination):
        """
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
        try:
            shutil.copyfile( the_source, the_destination )
            return True
        except Exception as e:
            raise IOError("Error while executing shutil.copyfile")


    def copytree(self,source,destination,dereference=False):
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
        try:
            shutil.copytree( the_source, the_destination, symlinks = dereference )
            return True
        except Exception as e:
            raise IOError("Error while executing shutil.copytree")
            
    
    def get_attribute(self,path):
        """
        Returns the list of attributes of a file.
        Receives in input the path of a given file.
        """
        os_attr = os.lstat( os.path.join(self.curdir,path) )
        aida_attr = FileAttribute()
        # map the paramiko class into the aida one
        # note that paramiko object contains more informations than the aida
        for key in aida_attr._valid_fields:
            aida_attr[key] = getattr(os_attr,key)
        return aida_attr


    def listdir(self,path='.'):
        """
        Returns a list containing the names of the entries in the directory .
        """
        return os.listdir( os.path.join( self.curdir,path ) )

    
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
            except AttributeError as e:
                raise ValueError("stdin can only be either a string of a "
                                 "file-like object!")
        else:
            filelike_stdin = None

        local_stdin.flush()
        # TODO : instead of strinIO use cstringIO
        # TODO : use input option of communicate()
        output_text, stderr_text = local_proc.communicate()

        retval = local_proc.returncode

        return retval, output_text, stderr_text
            
    
if __name__ == '__main__':
    import unittest
    import logging

    class TestBasicConnection(unittest.TestCase):
        """
        Test basic connections.
        """
        def test_closed_connection(self):
            with self.assertRaises(aida.transport.TransportInternalError):
                t = LocalTransport()
                t.listdir()
                
        def test_invalid_param(self):
            with self.assertRaises(ValueError):
                LocalTransport(unrequired_var='something')
                             
        def test_basic(self):
            with LocalTransport() as t:
                pass

    from test import *
    run_tests('local')

    unittest.main()
