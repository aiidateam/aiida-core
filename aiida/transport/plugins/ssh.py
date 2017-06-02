# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from stat import S_ISDIR,S_ISREG
import StringIO
import paramiko
import os
import glob

import aiida.transport
from aiida.common.utils import escape_for_bash
from aiida.transport import FileAttribute
from aiida.common import aiidalogger


# TODO : callback functions in paramiko are currently not used much and probably broken
def parse_sshconfig(computername):
    config = paramiko.SSHConfig()
    try:
        config.parse(open(os.path.expanduser('~/.ssh/config')))
    except IOError:
        # No file found, so empty configuration
        pass
    
    return config.lookup(computername)

def convert_to_bool(string):
    upstring = str(string).upper()
    
    if upstring in ['Y', 'YES', 'T', 'TRUE']:
        return True
    elif upstring in ['N', 'NO', 'F', 'FALSE']:
        return False
    else:
        raise ValueError("Invalid boolean value provided")

class SshTransport(aiida.transport.Transport):
    """
    Support connection, command execution and data transfer to remote computers via SSH+SFTP.
    """
    # Valid keywords accepted by the connect method of paramiko.SSHClient
    # I disable 'password' and 'pkey' to avoid these data to get logged in the
    # aiida log file.
    _valid_connect_params = ['username', 'port', 'look_for_keys', 
                             'key_filename', 'timeout', 'allow_agent',
                             'proxy_command', # Managed 'manually' in connect
                             'compress',
                             'gss_auth','gss_kex','gss_deleg_creds','gss_host', # for Kerberos support through python-gssapi
                             ]
    
    # Valid parameters for the ssh transport
    # For each param, a class method with name
    # _convert_PARAMNAME_fromstring
    # should be defined, that returns the value converted from a string to
    # a correct type, or raise a ValidationError 
    #
    # moreover, if you want to help in the default configuration, you can 
    # define a _get_PARAMNAME_suggestion_string
    # to return a suggestion; it must accept only one parameter, being a Computer
    # instance
    _valid_auth_params = _valid_connect_params + [
        'load_system_host_keys',
        'key_policy',
        ]
    
    @classmethod
    def _convert_username_fromstring(cls, string):
        """
        Convert the username from string.
        """
        return string

    @classmethod
    def _get_username_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        import getpass
        
        config = parse_sshconfig(computer.hostname)
        # Either the configured user in the .ssh/config, or the current username
        return str(config.get('user',getpass.getuser())) 
    

    @classmethod
    def _convert_port_fromstring(cls, string):
        """
        Convert the port from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return int(string)
        except ValueError:
            raise ValidationError("The port must be an integer")

    @classmethod
    def _get_port_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        config = parse_sshconfig(computer.hostname)
        # Either the configured user in the .ssh/config, or the default SSH port
        return str(config.get('port',22))

    @classmethod
    def _convert_key_filename_fromstring(cls, string):
        """
        Convert the port from string.
        """
        from aiida.common.exceptions import ValidationError
        
        path = os.path.expanduser(string)
        
        if not os.path.isabs(path):
            raise ValidationError("The key filename must be an absolute path")

        if not os.path.exists(path):
            raise ValidationError("The key filename must exist")

        return path
    
    @classmethod
    def _get_key_filename_suggestion_string(cls, computer):        
        """
        Return a suggestion for the specific field.
        """
        config = parse_sshconfig(computer.hostname)
        
        try:
            identities = config['identityfile']
            # In paramiko > 0.10, identity file is a list of strings.
            if isinstance(identities,basestring):
                identity = identities
            elif isinstance(identities,(list,tuple)):
                if not identities:
                    # An empty list should not be provided; to be sure,
                    # anyway, behave as if no identityfile were defined
                    raise KeyError
                # By default we suggest only the first one
                identity = identities[0]
            else:
                # If the parser provides an unknown type, just skip to
                # the 'except KeyError' section, as if no identityfile 
                # were provided (hopefully, this should never happen)
                raise KeyError
        except KeyError:
            # No IdentityFile defined: return an empty string
            return ""
        
        return os.path.expanduser(identity)

    @classmethod
    def _convert_timeout_fromstring(cls, string):
        """
        Convert the port from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return int(string)
        except ValueError:
            raise ValidationError("The timeout must be an integer")

    @classmethod
    def _get_timeout_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        
        Provide 60s as a default timeout for connections.
        """
        config = parse_sshconfig(computer.hostname)
        return str(config.get('connecttimeout',"60"))

    @classmethod
    def _convert_allow_agent_fromstring(cls, string):
        """
        Convert the port from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return convert_to_bool(string)
        except ValueError:
            raise ValidationError("Allow_agent must be an boolean")

    @classmethod
    def _get_allow_agent_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        return ""

    @classmethod
    def _convert_look_for_keys_fromstring(cls, string):
        """
        Convert the port from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return convert_to_bool(string)
        except ValueError:
            raise ValidationError("look_for_keys must be an boolean")

    @classmethod
    def _get_look_for_keys_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        return ""

    @classmethod
    def _convert_proxy_command_fromstring(cls, string):
        """
        Convert the proxy command from string.
        """
        from aiida.common.exceptions import ValidationError
        
        if str(string).strip():
            return str(string)
        else:
            return None

    @classmethod
    def _get_proxy_command_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        config = parse_sshconfig(computer.hostname)
        # Either the configured user in the .ssh/config, or the default SSH port
        raw_string = str(config.get('proxycommand',''))
        # Note: %h and %p get already automatically substituted with 
        # hostname and port by the config parser!
        
        pieces = raw_string.split()
        new_pieces = []
        for piece in pieces:
            if '>' in piece:
                # If there is a piece with > to readdress stderr or stdout,
                # skip from here on (anything else can only be readdressing)
                break
            else:
                new_pieces.append(piece)
        return " ".join(new_pieces)

    @classmethod
    def _convert_compress_fromstring(cls, string):
        """
        Convert the port from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return convert_to_bool(string)
        except ValueError:
            raise ValidationError("compress must be an boolean")

    @classmethod
    def _get_compress_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        return "True"
    
    @classmethod
    def _convert_load_system_host_keys_fromstring(cls, string):
        """
        Convert the port from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return convert_to_bool(string)
        except ValueError:
            raise ValidationError("compress must be an boolean")

    @classmethod
    def _get_load_system_host_keys_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        return "True"
    
    @classmethod
    def _convert_key_policy_fromstring(cls, string):
        """
        Convert the port from string.
        """
        return string
    
    @classmethod
    def _get_key_policy_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        return "RejectPolicy"
    
    @classmethod
    def _convert_gss_auth_fromstring(cls, string):
        """
        Convert the gss auth. command from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return convert_to_bool(string)
        except ValueError:
            raise ValidationError("gss_auth must be an boolean")

    @classmethod
    def _get_gss_auth_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        config = parse_sshconfig(computer.hostname)
        return str(config.get('gssapiauthentication',"no"))

    @classmethod
    def _convert_gss_kex_fromstring(cls, string):
        """
        Convert the gss key exchange command from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return convert_to_bool(string)
        except ValueError:
            raise ValidationError("gss_kex must be an boolean")

    @classmethod
    def _get_gss_kex_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        config = parse_sshconfig(computer.hostname)
        return str(config.get('gssapikeyexchange',"no"))

    @classmethod
    def _convert_gss_deleg_creds_fromstring(cls, string):
        """
        Convert the gss auth. command from string.
        """
        from aiida.common.exceptions import ValidationError
        
        try:
            return convert_to_bool(string)
        except ValueError:
            raise ValidationError("gss_deleg_creds must be an boolean")

    @classmethod
    def _get_gss_deleg_creds_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        config = parse_sshconfig(computer.hostname)
        return str(config.get('gssapidelegatecredentials',"no"))

    @classmethod
    def _convert_gss_host_fromstring(cls, string):
        """
        Convert the gss auth. command from string.
        """
        from aiida.common.exceptions import ValidationError
        
        return str(string)

    @classmethod
    def _get_gss_host_suggestion_string(cls, computer):
        """
        Return a suggestion for the specific field.
        """
        config = parse_sshconfig(computer.hostname)
        return str(config.get('gssapihostname',computer.hostname))


    def __init__(self, machine, **kwargs):
        """
        Initialize the SshTransport class.
        
        :param machine: the machine to connect to
        :param load_system_host_keys: (optional, default False): if False, do not
                load the system host keys
        :param key_policy: (optional, default = paramiko.RejectPolicy()): the
                policy to use for unknown keys
        Other parameters valid for the ssh connect function (see the 
        self._valid_connect_params list) are passed to the connect
        function (as port, username, password, ...); taken from the
        accepted paramiko.SSHClient.connect() params)
        """
        super(SshTransport,self).__init__()

        self._is_open = False
        self._sftp = None
        
        self._machine = machine

        self._client = paramiko.SSHClient()
        self._load_system_host_keys = kwargs.pop(
            'load_system_host_keys', False)
        if self._load_system_host_keys:
            self._client.load_system_host_keys()

        self._missing_key_policy = kwargs.pop(
            'key_policy','RejectPolicy') # This is paramiko default
        if self._missing_key_policy == 'RejectPolicy':
            self._client.set_missing_host_key_policy(paramiko.RejectPolicy())
        elif self._missing_key_policy == 'WarningPolicy':
            self._client.set_missing_host_key_policy(paramiko.WarningPolicy())
        elif self._missing_key_policy == 'AutoAddPolicy':
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            raise ValueError("Unknown value of the key policy, allowed values "
                             "are: RejectPolicy, WarningPolicy, AutoAddPolicy")

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

    def open(self):
        """
        Open a SSHClient to the machine possibly using the parameters given
        in the __init__. 
        
        Also opens a sftp channel, ready to be used.
        The current working directory is set explicitly, so it is not None.
        
        :raise InvalidOperation: if the channel is already open
        """
        from aiida.common.exceptions import InvalidOperation
        
        if self._is_open:
            raise InvalidOperation("Cannot open the transport twice")
        # Open a SSHClient
        connection_arguments = self._connect_args
        proxystring = connection_arguments.pop('proxy_command', None)
        if proxystring is not None:
            proxy = paramiko.ProxyCommand(proxystring)
            connection_arguments['sock'] = proxy
            
        try:
            self._client.connect(self._machine,**connection_arguments)
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
        
    def close(self):
        """
        Close the SFTP channel, and the SSHClient.
        
        :todo: correctly manage exceptions
        
        :raise InvalidOperation: if the channel is already open
        """
        from aiida.common.exceptions import InvalidOperation
        
        if not self._is_open:
            raise InvalidOperation("Cannot close the transport: "
                                         "it is already closed")

        self._sftp.close()
        self._client.close()
        self._is_open = False

    @property
    def sshclient(self):
        if not self._is_open:
            raise aiida.transport.TransportInternalError(
                "Error, ssh method called for SshTransport "
                "without opening the channel first")
        return self._client

    @property
    def sftp(self):
        if not self._is_open:
            raise aiida.transport.TransportInternalError(
                "Error, sftp method called for SshTransport "
                "without opening the channel first")
        return self._sftp

    def __str__(self):
        """
        Return a useful string.
        """
        conn_info = self._machine
        try:
            conn_info = "{}@{}".format(self._connect_args['username'],
                                       conn_info)
        except KeyError:
            # No username explicitly defined: ignore
            pass
        try:
            conn_info += ':{}'.format(self._connect_args['port'])
        except KeyError:
        # No port explicitly defined: ignore
            pass
            
        return "{} [{}]".format("OPEN" if self._is_open else "CLOSED",
                                conn_info)

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

        :param path: directory to create (string)
        :param ignore_existing: if set to true, it doesn't give any error
            if the leaf directory does already exist (bool)

        :raise OSError: If the directory already exists.
        """
        # check to avoid creation of empty dirs
        path = os.path.normpath(path)
        
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

        :param path: name of the folder to create
        :param ignore_existing: if True, does not give any error if the directory
                  already exists

        :raise OSError: If the directory already exists.
        """
        if ignore_existing and self.isdir(path):
            return
        
        try:
            self.sftp.mkdir(path)
        except IOError as e:
            if os.path.isabs(path):
                raise OSError(
                    "Error during mkdir of '{}', "
                    "maybe you don't have the permissions to do it, "
                    "or the directory already exists? ({})".format(
                        path, e.message))
            else:
                raise OSError(
                    "Error during mkdir of '{}' from folder '{}', "
                    "maybe you don't have the permissions to do it, "
                    "or the directory already exists? ({})".format(
                        path, self.getcwd(), e.message))

    # TODO : implement rmtree
    def rmtree(self,path):
        """
        Remove a file or a directory at path, recursively
        Flags used: -r: recursive copy; -f: force, makes the command non interactive;

        :param path: remote path to delete

        :raise IOError: if the rm execution failed.
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

        :param path: path to file
        :param mode: new permission bits (integer)
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
            

    def put(self,localpath,remotepath,callback=None,dereference=True,overwrite=True,
            ignore_nonexisting=False):
        """
        Put a file or a folder from local to remote.
        Redirects to putfile or puttree.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param dereference: follow symbolic links (boolean).
            Default = True (default behaviour in paramiko). False is not implemented.
        :param  overwrite: if True overwrites files and folders (boolean).
            Default = False.

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist
        """
        # TODO: flag confirm exists since v1.7.7. What is the paramiko
        # version supported?

        # TODO : add dereference
        if not dereference:
            raise NotImplementedError

        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")

        if self.has_magic(localpath):
            if self.has_magic(remotepath):
                raise ValueError("Pathname patterns are not allowed in the "
                                 "destination")

            # use the imported glob to analyze the path locally
            to_copy_list = glob.glob(localpath)
            
            rename_remote = False
            if len(to_copy_list)>1:
                # I can't scp more than one file on a single file
                if self.isfile(remotepath):
                    raise OSError("Remote destination is not a directory")
                # I can't scp more than one file in a non existing directory
                elif not self.path_exists(remotepath):  # questo dovrebbe valere solo per file
                    raise OSError("Remote directory does not exist")
                else: # the remote path is a directory
                    rename_remote=True

            for s in to_copy_list:
                if os.path.isfile(s):
                    if rename_remote: # copying more than one file in one directory 
                        # here is the case isfile and more than one file
                        r = os.path.join(remotepath,os.path.split(s)[1])
                        self.putfile(s,r,callback,dereference,overwrite )
                        
                    elif self.isdir(remotepath): # one file to copy in '.'
                        r = os.path.join(remotepath,os.path.split(s)[1])
                        self.putfile(s,r,callback,dereference,overwrite )
                    else: # one file to copy on one file
                        self.putfile(s,remotepath,callback,dereference,overwrite )
                else:
                    self.puttree(s,remotepath,callback,dereference,overwrite )

        else:
            if os.path.isdir(localpath):
                self.puttree( localpath,remotepath,callback,dereference,overwrite )
            elif os.path.isfile(localpath):
                if self.isdir(remotepath):
                    r = os.path.join(remotepath,os.path.split(localpath)[1])
                    self.putfile( localpath,r,callback,dereference,overwrite )
                else:
                    self.putfile( localpath,remotepath,callback,dereference,overwrite )
            else:
                if ignore_nonexisting:
                    pass
                else:
                    raise OSError("The local path {} does not exist"
                                  .format(localpath))


    def putfile(self,localpath,remotepath,callback=None,dereference=True,overwrite=True):
        """
        Put a file from local to remote.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param overwrite: if True overwrites files and folders (boolean).
            Default = True.

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist,
                    or unintentionally overwriting
        """
        # TODO : add dereference
        if not dereference:
            raise NotImplementedError

        # TODO : check what happens if I give in input a directory
        
        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")

        if self.isfile(remotepath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')
        
        return self.sftp.put(localpath,remotepath,callback=callback)


    def puttree(self,localpath,remotepath,callback=None,dereference=True,overwrite=True): # by default overwrite
        """
        Put a folder recursively from local to remote.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param dereference: follow symbolic links (boolean)
            Default = True (default behaviour in paramiko). False is not implemented.
        :param overwrite: if True overwrites files and folders (boolean).
            Default = True

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist, or trying to overwrite
        :raise IOError: if remotepath is invalid

        .. note:: setting dereference equal to True could cause infinite loops.
              see os.walk() documentation
        """
        # TODO : add dereference
        if not dereference:
            raise NotImplementedError

        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")
        
        if not os.path.exists(localpath):
            raise OSError("The localpath does not exists")

        if not os.path.isdir(localpath):
            raise ValueError("Input localpath is not a folder: {}".format(localpath))

        if not remotepath:
            raise IOError("remotepath must be a non empty string")

        if self.path_exists(remotepath) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if self.isfile(remotepath):
            raise OSError("Cannot copy a directory into a file")
        
        if not self.isdir(remotepath):  # in this case copy things in the remotepath directly
            self.mkdir(remotepath) # and make a directory at its place
        else: # remotepath exists already: copy the folder inside of it!
            remotepath = os.path.join(remotepath,os.path.split(localpath)[1])
            self.mkdir(remotepath) # create a nested folder
        
        # TODO, NOTE: we are not using 'onerror' because we checked above that
        # the folder exists, but it would be better to use it
        for this_source in os.walk(localpath):
            # Get the relative path
            this_basename = os.path.relpath(path=this_source[0],
                                            start=localpath)
            
            try:
                self.sftp.stat( os.path.join(remotepath,this_basename) )
            except IOError as e:
                import errno
                if e.errno == errno.ENOENT: # Missing file
                    self.mkdir( os.path.join(remotepath,this_basename) )
                else:
                    raise
                
            for this_file in this_source[2]:
                this_local_file = os.path.join(localpath,this_basename,this_file)        
                this_remote_file = os.path.join(remotepath,this_basename,this_file)
                self.putfile(this_local_file,this_remote_file)


    def get(self,remotepath,localpath,callback=None,dereference=True,overwrite=True,
            ignore_nonexisting=False):
        """
        Get a file or folder from remote to local.
        Redirects to getfile or gettree.

        :param remotepath: a remote path
        :param localpath: an (absolute) local path
        :param dereference: follow symbolic links.
            Default = True (default behaviour in paramiko). 
            False is not implemented.
        :param overwrite: if True overwrites files and folders.
            Default = False

        :raise ValueError: if local path is invalid
        :raise IOError: if the remotepath is not found
        """
        # TODO : add dereference
        if not dereference:
            raise NotImplementedError

        if not os.path.isabs(localpath):
            raise ValueError("The localpath must be an absolute path")

        if self.has_magic(remotepath):
            if self.has_magic(localpath):
                raise ValueError("Pathname patterns are not allowed in the "
                                 "destination")
            # use the self glob to analyze the path remotely
            to_copy_list = self.glob(remotepath)
            
            rename_local = False
            if len(to_copy_list)>1:
                # I can't scp more than one file on a single file
                if os.path.isfile(localpath):
                    raise IOError("Remote destination is not a directory")
                # I can't scp more than one file in a non existing directory
                elif not os.path.exists(localpath):  # this should hold only for files
                    raise OSError("Remote directory does not exist")
                else: # the remote path is a directory
                    rename_local=True
      
            for s in to_copy_list:
                if self.isfile(s):
                    if rename_local: # copying more than one file in one directory 
                        # here is the case isfile and more than one file
                        r = os.path.join(localpath,os.path.split(s)[1])
                        self.getfile(s,r,callback,dereference,overwrite )
                    else: # one file to copy on one file
                        self.getfile(s,localpath,callback,dereference,overwrite )
                else:
                    self.gettree(s,localpath,callback,dereference,overwrite )

        else:
            if self.isdir(remotepath):
                self.gettree( remotepath,localpath,callback,dereference,overwrite )
            elif self.isfile(remotepath):
                if os.path.isdir(localpath):
                    r = os.path.join(localpath,os.path.split(remotepath)[1])
                    self.getfile( remotepath,r,callback,dereference,overwrite )
                else:
                    self.getfile( remotepath,localpath,callback,dereference,overwrite )
            else:
                if ignore_nonexisting:
                    pass
                else:
                    raise IOError("The remote path {} does not exist"
                                  .format(remotepath))

    def getfile(self,remotepath,localpath,callback=None,dereference=True,overwrite=True):
        """
        Get a file from remote to local.

        :param remotepath: a remote path
        :param  localpath: an (absolute) local path
        :param  overwrite: if True overwrites files and folders.
                Default = False

        :raise ValueError: if local path is invalid
        :raise OSError: if unintentionally overwriting
        """
        # TODO : add dereference

        if not os.path.isabs(localpath):
            raise ValueError("localpath must be an absolute path")

        if os.path.isfile(localpath) and not overwrite:            
            raise OSError('Destination already exists: not overwriting it')

        if not dereference:
            raise NotImplementedError
            
        # Workaround for bug #724 in paramiko -- remove localpath on IOError
        try:
            return self.sftp.get(remotepath,localpath,callback)
        except IOError as e:
            try:
                os.remove(localpath)
            except OSError:
                pass
            raise e
        
        
    def gettree(self,remotepath,localpath,callback=None,dereference=True,overwrite=True):
        """
        Get a folder recursively from remote to local.

        :param remotepath: a remote path
        :param localpath: an (absolute) local path
        :param dereference: follow symbolic links. 
            Default = True (default behaviour in paramiko). 
            False is not implemented.
        :param  overwrite: if True overwrites files and folders.
            Default = False

        :raise ValueError: if local path is invalid
        :raise IOError: if the remotepath is not found
        :raise OSError: if unintentionally overwriting
        """
        # TODO : add dereference
        if not dereference:
            raise NotImplementedError

        if not remotepath:
            raise IOError("Remotepath must be a non empty string")
        if not localpath:
            raise ValueError("Localpaths must be a non empty string")

        if not os.path.isabs(localpath):
            raise ValueError("Localpaths must be an absolute path")

        if not self.isdir(remotepath):
            raise IOError("Input remotepath is not a folder: {}".format(localpath))

        if os.path.exists(localpath) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if os.path.isfile(localpath):
            raise OSError("Cannot copy a directory into a file")
        
        if not os.path.isdir(localpath):  # in this case copy things in the remotepath directly
            os.mkdir(localpath) # and make a directory at its place
        else: # localpath exists already: copy the folder inside of it!
            localpath = os.path.join(localpath,os.path.split(remotepath)[1])
            os.mkdir(localpath) # create a nested folder
        
        item_list = self.listdir(remotepath)
        dest = str(localpath)

        for item in item_list:
            item = str(item)

            if self.isdir( os.path.join(remotepath,item) ):
                self.gettree( os.path.join(remotepath,item) , os.path.join(dest,item) )
            else:
                self.getfile( os.path.join(remotepath,item) , os.path.join(dest,item) )


    def get_attribute(self,path):
        """
        Returns the object Fileattribute, specified in aiida.transport
        Receives in input the path of a given file.
        """
        paramiko_attr = self.sftp.lstat(path)
        aiida_attr = FileAttribute()
        # map the paramiko class into the aiida one
        # note that paramiko object contains more informations than the aiida
        for key in aiida_attr._valid_fields:
            aiida_attr[key] = getattr(paramiko_attr,key)
        return aiida_attr


    def copyfile(self,remotesource,remotedestination,dereference=False,
                 pattern=None):
        """
        Copy a file from remote source to remote destination
        Redirects to copy().
        
        :param remotesource: 
        :param remotedestination:
        :param dereference:
        :param pattern:
        """
        cp_flags = '-f'
        return self.copy(remotesource,remotedestination,dereference,cp_flags,pattern)


    def copytree(self,remotesource,remotedestination,dereference=False,
                 pattern=None):
        """
        copy a folder recursively from remote source to remote destination
        Redirects to copy()

        :param remotesource:
        :param remotedestination:
        :param dereference:
        :param pattern:
        """
        cp_flags = '-r -f'
        return self.copy(remotesource,remotedestination,dereference,cp_flags,pattern)


    def copy(self,remotesource,remotedestination,dereference=False):
        """
        Copy a file or a directory from remote source to remote destination.
        Flags used: ``-r``: recursive copy; ``-f``: force, makes the command non interactive;
        ``-L`` follows symbolic links

        :param  remotesource: file to copy from
        :param remotedestination: file to copy to
        :param dereference: if True, copy content instead of copying the symlinks only
            Default = False.
        :raise IOError: if the cp execution failed.

        .. note:: setting dereference equal to True could cause infinite loops.
        """
        # In the majority of cases, we should deal with linux cp commands
        
        # TODO : do we need to avoid the aliases when calling cp_exe='cp'? Call directly /bin/cp?
        
        # TODO: verify that it does not re
        
        # For the moment, these are hardcoded. They may become parameters
        # as soon as we see the need.
        cp_flags='-r -f'
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
        
        if self.has_magic(remotedestination):
            raise ValueError("Pathname patterns are not allowed in the "
                             "destination")

        if self.has_magic(remotesource):
            to_copy_list = self.glob(remotesource)
            
            if len(to_copy_list)>1:
                if not self.path_exists(remotedestination) or self.isfile(remotedestination): 
                    raise OSError("Can't copy more than one file in the same "
                                  "destination file")
            
            for s in to_copy_list:
                self._exec_cp(cp_exe,cp_flags,s,remotedestination)

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
            raise IOError("Error while executing cp. Exit code: {}, "
                          "stdout: '{}', stderr: '{}', "
                          "command: '{}'".format(retval, stdout, stderr,
                                                 command) )

                
    def _local_listdir(self,path,pattern=None):
        """
        Acts on the local folder, for the rest, same as listdir
        """
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

        :param path: default = '.'
        :param filter: returns the list of files matching pattern.
                             Unix only. (Use to emulate ``ls *`` for example)
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

    def rename(self,src,dst):
        """
        Rename a file or folder from src to dst.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises IOError: if src/dst is not found
        :raises ValueError: if src/dst is not a valid string
        """
        if not src:
            raise ValueError("Source {} is not a valid string".format(src))
        if not dst:
            raise ValueError("Destination {} is not a valid string".format(dst))
        if not self.isfile( src ):
            if not self.isdir( src ):
                raise IOError("Source {} does not exist".format(src))
        if not self.isfile( dst ):
            if not self.isdir( dst ):
                raise IOError("Destination {} does not exist".format(dst))

        return self.sftp.rename(src,dst)
    
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

        :param  command: the command to execute
        :param combine_stderr: (default False) if True, combine stdout and
                stderr on the same buffer (i.e., stdout).
                Note: If combine_stderr is True, stderr will always be empty.
        :param bufsize: same meaning of the one used by paramiko.
        
        :return: a tuple with (stdin, stdout, stderr, channel),
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
        
        :param command: the command to execute
        :param stdin: (optional,default=None) can be a string or a
                   file-like object.
        :param combine_stderr: (optional, default=False) see docstring of
                   self._exec_command_internal()
        :param bufsize: same meaning of paramiko.

        :return: a tuple with (return_value, stdout, stderr) where stdout and stderr
            are strings.
        """
        #TODO: To see if like this it works or hangs because of buffer problems.
        
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

    def gotocomputer_command(self, remotedir):
        """
        Specific gotocomputer string to connect to a given remote computer via
        ssh and directly go to the calculation folder.
        """
        
        #TODO: add also ProxyCommand and Timeout support

        further_params = []
        if 'username' in self._connect_args:
            further_params.append("-l {}".format(escape_for_bash(
                self._connect_args['username'])))
        
        if 'port' in self._connect_args:
            further_params.append("-p {}".format(self._connect_args['port']))

        if 'key_filename' in self._connect_args:
            further_params.append("-i {}".format(escape_for_bash(
                self._connect_args['key_filename'])))
        
        further_params_str = " ".join(further_params)
        connect_string = """ssh -t {machine} {further_params} "if [ -d {escaped_remotedir} ] ; then cd {escaped_remotedir} ; bash -l ; else echo '  ** The directory' ; echo '  ** {remotedir}' ; echo '  ** seems to have been deleted, I logout...' ; fi" """.format(
            further_params=further_params_str,
            machine=self._machine,
            escaped_remotedir="'{}'".format(remotedir),
            remotedir=remotedir)

        # print connect_string
        return connect_string
        
        #return """ssh -Y -t {machine} "if [ -d {escaped_remotedir} ] ; then cd {escaped_remotedir} ; bash -c "{bash_call_escaped}" ; else echo '  ** The directory' ; echo '  ** {remotedir}' ; echo '  ** seems to have been deleted, I logout...' ; fi" """.format(
        #    machine=self._machine, escaped_remotedir="'{}'".format(remotedir), remotedir=remotedir,
        #    bash_call_escaped=escape_for_bash("""bash --rcfile <(echo 'if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi ; export PS1="\[\033[01;31m\][AiiDA]\033[00m\]$PS1"')"""))
        
    def symlink(self,remotesource,remotedestination):
        """
        Create a symbolic link between the remote source and the remote 
        destination.
        
        :param remotesource: remote source. Can contain a pattern. 
        :param remotedestination: remote destination
        """
        # paramiko gives some errors if path is starting with '.'
        s = os.path.normpath(remotesource)
        d = os.path.normpath(remotedestination)
        
        if self.has_magic(s):
            if self.has_magic(d):
                # if there are patterns in dest, I don't know which name to assign
                raise ValueError("Remotedestination cannot have patterns")
            
            # find all files matching pattern
            for this_s in self.glob(s):
                # create the name of the link: take the last part of the path
                this_d = os.path.join(remotedestination,
                                      os.path.split(this_s)[-1])
                self.sftp.symlink(this_s, this_d)
        else:
            self.sftp.symlink(s,d)
    
    def path_exists(self,path):
        """
        Check if path exists
        """
        import errno
        try:
            self.sftp.stat(path)
        except IOError, e:
            if e.errno == errno.ENOENT:
                return False
            raise
        else:
            return True
    
