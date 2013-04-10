from stat import S_ISDIR,S_ISREG
import StringIO
import paramiko

import aida.transport
from aida.common.utils import escape_for_bash
from aida.common import aidalogger

class SshTransport(aida.transport.Transport):
    def __init__(self, machine, **kwargs):
        """
        Initialize the SshTransport class. 
        
        Args:
            machine: the machine to connect to
            load_system_host_keys (optional, default True): if False, do not load the
                system host keys
            key_policy (optional, default = paramiko.RejectPolicy()): the policy to use
                for unknown keys
            Other parameters are passed to the connect function (as port, username,
            password, ...) (see the __enter__ function of this class, or the
            documentation of paramiko.SSHClient.connect())
        """

        ## First call the parent __init__ to setup the logger!
        super(SshTransport,self).__init__()
        self._logger = super(SshTransport,self).logger.getChild('ssh')

        self._machine = machine
        self._further_init_args = kwargs
        self._client = paramiko.SSHClient()
        if kwargs.get('load_system_host_keys', True):
            self._client.load_system_host_keys()

        self._missing_key_policy = kwargs.get(
            'key_policy',paramiko.RejectPolicy()) # This is paramiko default
        self._client.set_missing_host_key_policy(self._missing_key_policy)

    def __unicode__(self):
        """
        Return a useful string.
        """
        conn_info = unicode(self._machine)
        try:
            conn_info = unicode(self._further_init_args['username']) + u'@' + conn_info
        except KeyError:
            # No username explicitly defined: ignore
            pass
        try:
            conn_info += u':{}'.format(self._further_init_args['port'])
        except KeyError:
        # No port explicitly defined: ignore
            pass
            
        return u'{}({})'.format(self.__class__.__name__, conn_info)
    
    def __enter__(self):
        """
        Open a SSHClient to the machine possibly using the parameters given
        in the __init__. 
        
        Also opens a sftp channel, ready to be used.
        The current working directory is set explicitly, so it is not None.
        """
        # Valid keywords accepted by the connect method of paramiko.SSHClient
        valid_kw_params = ['port', 'username', 'password', 'pkey',
                           'key_filename', 'timeout', 'allow_agent',
                           'look_for_keys', 'compress']
        
        further_args = {k: v for k, v in self._further_init_args.iteritems()
                        if k in valid_kw_params}

        # Open a SSHClient
        self._client.connect(self._machine,**further_args)

        # Open also a SFTPClient
        self._sftp = self._client.open_sftp()
        # Set the current directory to a explicit path, and not to None
        self._sftp.chdir(self._sftp.normalize('.'))

        return self
        
    def __exit__(self, type, value, traceback):
        """
        Close the SFTP channel, and the SSHClient.
        """
        self._sftp.close()
        self._client.close()

    def chdir(self, path):
        """
        Change directory of the SFTP session. Emulated internally by
        paramiko. 

        Differently from paramiko, if you pass None to chdir, nothing
        happens and the cwd is unchanged.
        """
        if path is not None:
            self._sftp.chdir(path)

    def normalize(self, path):
        return self._sftp.normalize(path)
        
    def getcwd(self):
        """
        Return the current working directory for this SFTP session, as
        emulated by paramiko. If no directory has been set with chdir,
        this method will return None. But in __enter__ this is set explicitly,
        so this should never happen within this class.
        """
        return self._sftp.getcwd()

    def mkdir(self, path, mode=511):
        """
        Create a folder (directory) named path with numeric mode mode.
        The default mode is 0777 (octal). On some systems, mode is
        ignored. Where it is used, the current umask value is first
        masked out.

        Args:
            path: the folder to create. Relative paths refer to the\
                current working directory.
            mode: the numeric mode for the new folder.
        """
        self._sftp.mkdir(path,mode)

    def rmdir(self, path):
        """
        Remove the folder named 'path'.
        """
        self._sftp.rmdir(path)

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
            return S_ISDIR(self._sftp.stat(path).st_mode)
        except IOError as e:
            if getattr(e,"errno",None) == 2:
                # errno=2 means path does not exist: I return False
                return False
            else:
                raise # Typically if I don't have permissions (errno=13)

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
                    path, self._sftp.normalize(path),
                    self._sftp.stat(path),self._sftp.stat(path).st_mode))
            return S_ISREG(self._sftp.stat(path).st_mode)
        except IOError as e:
            if getattr(e,"errno",None) == 2:
                # errno=2 means path does not exist: I return False
                return False
            else:
                raise # Typically if I don't have permissions (errno=13)

    def exec_command(self,command,combine_stderr=False,bufsize=-1):
        """
        Executes the specified command, first changing directory to the
        current working directory are returned by
        self.getcwd().
        Does not wait for the calculation to finish.

        For a higher-level exec_command that automatically waits for the
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
        channel = self._client.get_transport().open_session()
        channel.set_combine_stderr(combine_stderr)

        if self.getcwd() is not None:
            escaped_folder = escape_for_bash(self.getcwd())
            command_to_execute = ("cd {escaped_folder} ; "
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
            combine_stderr: (optional, default=False) see docstring of self.exec_command()
            bufsize: same meaning of paramiko.

        Returns:
            a tuple with (return_value, stdout, stderr) where stdout and stderr
            are strings.
        """
        ssh_stdin, stdout, stderr, channel = self.exec_command(
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
    import unittest

    class TestBasicConnection(unittest.TestCase):
        """
        Test basic connections.
        """
        
        def test_auto_add_policy(self):
            with SshTransport(machine='localhost', timeout=30, 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                pass

        def test_no_host_key(self):
            with self.assertRaises(paramiko.SSHException):
                with SshTransport(machine='localhost', timeout=30, 
                                  load_system_host_keys = False) as t:
                    pass

    class TestDirectoryManipulation(unittest.TestCase):
        """
        Test to check, create and delete folders.
        """
        
        def test_listdir(self):
            """
            create directories, verify listdir, delete a folder with subfolders
            """
            # Imports required later
            import random
            import string
            import os

            with SshTransport(machine='localhost', timeout=30, 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                location = t.normalize(os.path.join('/','tmp'))
                directory = 'temp_dir_test'
                t.chdir(location)
                
                self.assertEquals(location, t.getcwd())
                while t.isdir(directory):
                    # I append a random letter/number until it is unique
                    directory += random.choice(
                        string.ascii_uppercase + string.digits)
                t.mkdir(directory)
                t.chdir(directory)
                list_of_dir=['1','-f a&','as']
                for this_dir in list_of_dir:
                    t.mkdir(this_dir)
                list_of_dir_found = t.listdir('.')
                self.assertTrue(sorted(list_of_dir_found)==sorted(list_of_dir))    
                t.chdir('..')
                t.rmdir(directory)

        def test_dir_creation_deletion(self):
            # Imports required later
            import random
            import string
            import os

            with SshTransport(machine='localhost', timeout=30, 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                location = t.normalize(os.path.join('/','tmp'))
                directory = 'temp_dir_test'
                t.chdir(location)
                
                self.assertEquals(location, t.getcwd())
                while t.isdir(directory):
                    # I append a random letter/number until it is unique
                    directory += random.choice(
                        string.ascii_uppercase + string.digits)
                t.mkdir(directory)
                t.isdir(directory)
                self.assertFalse(t.isfile(directory))
                t.rmdir(directory)

        def test_dir_copy(self):
            """
            Verify if in the copy of a directory also the protection bits are carried over
            """
            # Imports required later
            import random
            import string
            import os

            with SshTransport(machine='localhost', timeout=30, 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                location = t.normalize(os.path.join('/','tmp'))
                directory = 'temp_dir_test'
                t.chdir(location)
                
                while t.isdir(directory):
                    # I append a random letter/number until it is unique
                    directory += random.choice(
                        string.ascii_uppercase + string.digits)
                t.mkdir(directory,mode=777)
                dest_directory = directory+'_copy'
                t.copy(directory,dest_directory)
                attr_obj = t.get_attribute(dest_directory)
                attr_obj_dest = t.get_attribute(dest_directory)
                self.assertEquals(attr_obj.st_mode,777)
                self.assertEquals(attr_obj,attr_obj_dest)
                t.rmdir(directory)
                t.rmdir(dest_directory)
                

        def test_dir_permissions_creation_modification(self):
            """
            verify if chmod raises IOError when trying to change bits on a non-existing folder
            """
            # Imports required later
            import random
            import string
            import os

            with SshTransport(machine='localhost', timeout=30, 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                location = t.normalize(os.path.join('/','tmp'))
                directory = 'temp_dir_test'
                t.chdir(location)

                while t.isdir(directory):
                    # I append a random letter/number until it is unique
                    directory += random.choice(
                        string.ascii_uppercase + string.digits)
                t.mkdir(directory,mode=500)
                t.chmod(directory,777)
                ## TODO: probably here we should then check for 
                ## the new directory modes. To see if we want a higher
                ## level function to ask for the mode, or we just
                ## use get_attribute
                t.chdir(directory)

                fake_dir=''
                with self.assertRaises(IOError):
                    t.chmod(fake_dir,777)

                fake_dir='pippo'
                with self.assertRaises(IOError):
                    t.chmod(fake_dir,777)

                t.chdir('..')
                t.rmdir(directory)

                
        def test_isfile_isdir_to_empty_string(self):
            """
            I check that isdir or isfile return False when executed on an empty string
            """
            import os

            with SshTransport(machine='localhost', timeout=30, 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                location = t.normalize(os.path.join('/','tmp'))
                t.chdir(location)
                self.assertFalse(t.isdir(""))
                self.assertFalse(t.isfile(""))


        def test_isfile_isdir_to_non_existing_string(self):
            """
            I check that isdir or isfile return False when executed on an empty string
            """
            import os
            with SshTransport(machine='localhost', timeout=30, 
                              key_policy=paramiko.AutoAddPolicy()) as t:

                location = t.normalize(os.path.join('/','tmp'))
                t.chdir(location)
                fake_folder = 'pippo'
                self.assertFalse(t.isfile(fake_folder))
                self.assertFalse(t.isdir(fake_folder))
                with self.assertRaises(IOError):
                    t.chdir(fake_folder)

               
        def test_chdir_to_empty_string(self):
            """
            I check that if I pass an empty string to chdir, the cwd does not change
            (this is a paramiko default behavior), but getcwd() is still correctly 
            defined.
            """
            import os
            with SshTransport(machine='localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:

                new_dir = t.normalize(os.path.join('/','tmp'))
                t.chdir(new_dir)
                t.chdir("")
                self.assertEquals(new_dir, t.getcwd())

    class TestPutGet(unittest.TestCase):
        """
        Test to verify whether the put and get functions behave correctly.
        1) thy work, 2) need abs path where necessary 3) reject empy strings
        """

        def test_put_and_get(self):
            import os
            import random
            import string
            
            local_dir = os.path.join('/','tmp')
            directory = 'tmp_try'

            with SshTransport(machine='localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:

                t.chdir(local_dir)
                while t.isdir(directory):
                    # I append a random letter/number until it is unique
                    directory += random.choice(
                        string.ascii_uppercase + string.digits)
                    
                t.mkdir(directory)
                t.chdir(directory)

                local_file_name = os.path.join(local_dir,directory,'file.txt')
                remote_file_name = os.path.join(local_dir,directory,'file_remote.txt')
                retrieved_file_name = os.path.join(local_dir,directory,'file_retrieved.txt')

                f = open(local_file_name,'w')
                f.close()

                # here use full path in src and dst
                t.put(local_file_name,remote_file_name)
                t.get(remote_file_name,retrieved_file_name)
                
                list_of_file = t.listdir('.')
                self.assertTrue(local_file_name not in list_of_file)
                self.assertTrue(remote_file_name not in list_of_file)
                self.assertTrue(retrieved_file_name not in list_of_file)

                t.chdir('..')
                t.rmdir(directory)
                    
        def test_put_get_abs_path(self):
            """
            test of exception for non existing files and abs path
            """
            import os
            import random
            import string
            local_dir = os.path.join('/','tmp')
            directory = 'tmp_try'

            with SshTransport(machine='localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:

                t.chdir(local_dir)
                while t.isdir(directory):
                    # I append a random letter/number until it is unique
                    directory += random.choice(
                        string.ascii_uppercase + string.digits)

                t.mkdir(directory)
                t.chdir(directory)

                partial_file_name = 'file.txt'
                local_file_name = os.path.join(local_dir,directory,'file.txt')
                remote_file_name = 'file_remote.txt'
                retrieved_file_name = os.path.join(local_dir,directory,'file_retrieved.txt')
                
                f = open(local_file_name,'w')
                f.close()

                with self.assertRaises(ValueError):
                    # file is not abs_path
                    t.put(partial_file_name,remote_file_name)
                with self.assertRaises(OSError):
                    # file does not exist
                    t.put(retrieved_file_name,remote_file_name)                    
                    t.get(remote_file_name,retrieved_file_name)
                
                t.put(local_file_name,remote_file_name)
                with self.assertRaises(ValueError):
                    # file is not abs_path
                    t.get(remote_file_name,'delete_me.txt')

                t.chdir('..')
                t.rmdir(directory)

        def test_put_get_empty_string(self):
            """
            test of exception put/get of empty strings
            """
            import os
            import random
            import string
            local_dir = os.path.join('/','tmp')
            directory = 'tmp_try'

            with SshTransport(machine='localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:

                t.chdir(local_dir)
                while t.isdir(directory):
                    # I append a random letter/number until it is unique
                    directory += random.choice(
                        string.ascii_uppercase + string.digits)

                t.mkdir(directory)
                t.chdir(directory)

                local_file_name = os.path.join(local_dir,directory,'file_local.txt')
                remote_file_name = 'file_remote.txt'
                retrieved_file_name = os.path.join(local_dir,directory,'file_retrieved.txt')
                
                f = open(local_file_name,'w')
                f.close()

                with self.assertRaises(ValueError):
                    # file is empty string
                    t.put('',remote_file_name)
                    t.put(local_file_name,'')

                t.put(local_file_name,remote_file_name)
                
                with self.assertRaises(ValueError):
                    # file is empty string
                    t.get('',retrieved_file_name)
                    t.get(remote_file_name,'')

                t.chdir('..')
                t.rmdir(directory)


    class TestExecuteCommandWait(unittest.TestCase):
        """
        Test some simple command executions and stdin/stdout management.
        
        It also checks for escaping of the folder names.
        """

        def test_exec_pwd(self):
            """
            I create a strange subfolder with a complicated name and
            then see if I can run pwd. This also checks the correct
            escaping of funny characters, both in the directory
            creation (which should be done by paramiko) and in the command 
            execution (done in this module, in the exec_command function).
            """
            import os
            
            # Start value
            delete_at_end = False

            with SshTransport('localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:

                # To compare with: getcwd uses the normalized ('realpath') path
                location = t.normalize('/tmp')
                subfolder = """_'s f"#""" # A folder with characters to escape
                subfolder_fullpath = os.path.join(location,subfolder)

                t.chdir(location)
                if not t.isdir(subfolder):
                    # Since I created the folder, I will remember to
                    # delete it at the end of this test
                    delete_at_end = True 
                    t.mkdir(subfolder)

                self.assertTrue(t.isdir(subfolder))
                t.chdir(subfolder)

                self.assertEquals(subfolder_fullpath, t.getcwd())
                retcode, stdout, stderr = t.exec_command_wait('pwd')
                self.assertEquals(retcode, 0)
                # I have to strip it because 'pwd' returns a trailing \n
                self.assertEquals(stdout.strip(), subfolder_fullpath)
                self.assertEquals(stderr, "")
                
                if delete_at_end:
                    t.chdir(location)
                    t.rmdir(subfolder)

        def test_exec_with_stdin_string(self):
            test_string = str("some_test String")
            with SshTransport('localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                retcode, stdout, stderr = t.exec_command_wait(
                    'cat', stdin=test_string)
                self.assertEquals(retcode, 0)
                self.assertEquals(stdout, test_string)
                self.assertEquals(stderr, "")

        def test_exec_with_stdin_unicode(self):
            test_string = u"some_test String"
            with SshTransport('localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                retcode, stdout, stderr = t.exec_command_wait(
                    'cat', stdin=test_string)
                self.assertEquals(retcode, 0)
                self.assertEquals(stdout, test_string)
                self.assertEquals(stderr, "")

        def test_exec_with_stdin_filelike(self):
            test_string = "some_test String"
            stdin = StringIO.StringIO(test_string)
            with SshTransport('localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                retcode, stdout, stderr = t.exec_command_wait(
                    'cat', stdin=stdin)
                self.assertEquals(retcode, 0)
                self.assertEquals(stdout, test_string)
                self.assertEquals(stderr, "")

        def test_exec_with_wrong_stdin(self):
            # I pass a number
            with SshTransport('localhost', 
                              key_policy=paramiko.AutoAddPolicy()) as t:
                with self.assertRaises(ValueError):
                    retcode, stdout, stderr = t.exec_command_wait(
                        'cat', stdin=1)
            
    import logging
#    aidalogger.setLevel(logging.DEBUG)
    
    unittest.main()
    
