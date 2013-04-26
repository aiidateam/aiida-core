###
### GP: a note on the local transport:
### I believe that we must not use os.chdir to keep track of the folder
### in which we are, since this may have very nasty side effects in other
### parts of code, and make things not thread-safe.
### we should instead keep track internally of the 'current working directory'
### in the exact same way as paramiko does already.

import os,shutil
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

    def __init(self)__:
        # internal_dir will emulate the concept of working directory
        # The real current working directory is not to be changed
        
        internal_dir = os.getenv("HOME")
        _is_open = False

    def __init(self)__:
        self._is_open = True

        return self

    def __close__(self):
        self._is_open = False

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

    @property
    def localclient(self):
        if not self._is_open:
            raise aida.transport.TransportInternalError(
                "Error, local method called for LocalTransport "
                "without opening the channel first")
        return self

    def chdir(self, path):
        internal_dir = os.path.normpath( os.path.join( internal_dir,path ) )
        
    def normalize(self, path):
        return os.path.normpath(path)

    def getcwd(self):
        return internal_dir

    def mkdir(self, path):
        os.mkdir( os.path.join( internal_dir,path ) )

    def rmdir(self, path):
        os.rmdir( os.path.join( internal_dir,path ) )

    def isdir(self,path):
        return os.path.isdir( os.path.join( internal_dir,path ) )

    def chmod(self,path,mode):
        os.chmod( os.path.join( internal_dir,path ) , mode )
    
    def put(self,source,destination):
        return self.copy( source,destination )

    def get(self,source,destination):
        return self.copy( source,destination )

    def copy(self,source,destination):
        the_source = os.path.join( internal_dir,source )
        the_destination = os.path.join( internal_dir,destination )
        shutil.copyfile( the_source, the_destination )

    def get_attribute(self,path):
        """
        Returns the list of attributes of a file
        Receives in input the path of a given file
        """
        os_attr = self.sftp.lstat( os.path.join(internal_dir,path) )
        aida_attr = FileAttribute()
        # map the paramiko class into the aida one
        # note that paramiko object contains more informations than the aida
        for key in aida_attr._valid_fields:
            aida_attr[key] = getattr(os_attr,key)
        return aida_attr
        
    def listdir(self,path=internal_dir):
        return os.listdir( os.path.join( internal_dir,path ) )

    def remove(self,path):
        os.remove( os.path.join( internal_dir,path ) )
    
    def isfile(self,path):
        return os.path.isdir( os.path.join( internal_dir,path ) )

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
