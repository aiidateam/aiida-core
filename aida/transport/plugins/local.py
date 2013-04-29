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

    def __init__(self):
        # # First call the parent __init__ to setup the logger!
        # super(LocalTransport,self).__init__()
        # self._logger = super(LocalTransport,self).logger.getChild('local')

        # _internal_dir will emulate the concept of working directory
        # The real current working directory is not to be changed
        #        self._internal_dir = None
        self._is_open = False
        self._internal_dir = None
        #        if kwargs:
            #            raise ValueError("Input parameters to LocalTransport"
                             #                             " are not recognized")
    
    
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
        
        
    # def __unicode__(self):
    #     """
    #     Return a useful string.
    #     """
    #     conn_info = unicode(self._machine)
    #     try:
    #         conn_info = (unicode(self._connect_args['username']) + 
    #                      u'@' + conn_info)
    #     except KeyError:
    #         # No username explicitly defined: ignore
    #         pass
    #     try:
    #         conn_info += u':{}'.format(self._connect_args['port'])
    #     except KeyError:
    #     # No port explicitly defined: ignore
    #         pass
            
    #     return u'{}({})'.format(self.__class__.__name__, conn_info)


    # TODO : fix this decorator
    @property
    def lc(self):
        if not self._is_open:
            raise aida.transport.TransportInternalError(
                "Error, local method called for LocalTransport "
                "with channel closed")
        return self


    def chdir(self, path):
        """
        Changes directory to path, emulated internally.
        Raises OSError if the directory does not have read attributes.
        """
        if os.access("myfile", os.R_OK):
            _internal_dir = os.path.normpath( os.path.join( _internal_dir,path ) )
        else:
            raise OSError
    
    
    def normalize(self, path):
        """
        Normalizes path, eliminating double slashes, etc..
        """
        return os.path.normpath( os.path.join(_internal_dir,path) )
    
    
    def getcwd(self):
        """
        Returns the current working directory, emulated by the transport
        """
        return _internal_dir


    def mkdir(self, path):
        """
        Creates the folder path.
        """
        os.mkdir( os.path.join( _internal_dir,path ) )


    def rmdir(self, path):
        """
        Removes a folder at location path.
        """
        os.rmdir( os.path.join( _internal_dir,path ) )


    def isdir(self,path):
        """
        Checks if 'path' is a directory.
        Returns a bool
        """
        return os.path.isdir( os.path.join( _internal_dir,path ) )


    def chmod(self,path,mode):
        """
        Changes permission bits of object at path
        """
        os.chmod( os.path.join( _internal_dir,path ) , mode )
    

    def put(self,source,destination):
        """
        Copies a file from source to destination
        (equivalent to copy)
        """
        return self.copy( source,destination )


    def get(self,source,destination):
        """
        Copies a file from source to destination
        (equivalent to copy)
        """
        return self.copy( source,destination )


    def copy(self,source,destination):
        """
        Copies a file from source to destination
        """
        the_source = os.path.join( _internal_dir,source )
        the_destination = os.path.join( _internal_dir,destination )
        shutil.copyfile( the_source, the_destination )


    def get_attribute(self,path):
        """
        Returns the list of attributes of a file.
        Receives in input the path of a given file.
        """
        os_attr = os.lstat( os.path.join(_internal_dir,path) )
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
        return os.listdir( os.path.join( _internal_dir,path ) )


    def remove(self,path):
        """
        Removes a file at position path.
        """
        os.remove( os.path.join( _internal_dir,path ) )

    
    def isfile(self,path):
        """
        Checks if object at path is a file.
        Returns a boolean.
        """
        return os.path.isdir( os.path.join( _internal_dir,path ) )


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
        proc = subprocess.Popen( command, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 cwd=self.getcwd() )
        return proc.stdin, proc.stdout, proc.stderr, proc


    def exec_command_wait(self,command):
        """
        Executes the specified command and waits for it to finish.
        
        Args:
            command: the command to execute

        Returns:
            a tuple with (return_value, stdout, stderr) where stdout and stderr
            are strings.
        """

        proc = subprocess.Popen( command, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 cwd=self.getcwd() )
        retval = proc.wait()
        output_text, stderr_text = proc.communicate()
        
        return retval, output_text, stderr_text







if __name__ == '__main__':
    import unittest
    import logging
    #    from test import *

# TODO : implement tests of basic connections

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
                LocalTransport(machine='localhost')
                             
        def test_basic(self):
            with LocalTransport() as t:
                pass

    # run_tests('local')

    unittest.main()
