"""
This module contains a set of unittest test classes that can be loaded from the plugin.
Every transport plugin should be able to pass all of these common tests.
Plugin specific tests will be written in the plugin itself.
"""

import unittest
from aida.common.pluginloader import load_plugin

custom_transport = None
        
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

        with custom_transport as t:
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

            for this_dir in list_of_dir:
                t.rmdir(this_dir)

            t.chdir('..')
            t.rmdir(directory)

    def test_dir_creation_deletion(self):
        # Imports required later
        import random
        import string
        import os

        with custom_transport as t:
            location = t.normalize(os.path.join('/','tmp'))
            directory = 'temp_dir_test'
            t.chdir(location)

            self.assertEquals(location, t.getcwd())
            while t.isdir(directory):
                # I append a random letter/number until it is unique
                directory += random.choice(
                    string.ascii_uppercase + string.digits)
            t.mkdir(directory)

            with self.assertRaises(OSError):
                # I create twice the same directory
                t.mkdir(directory)
            
            t.isdir(directory)
            self.assertFalse(t.isfile(directory))
            t.rmdir(directory)

    def test_dir_copy(self):
        """
        Verify if in the copy of a directory also the protection bits
        are carried over
        """
        # Imports required later
        import random
        import string
        import os

        with custom_transport as t:
            location = t.normalize(os.path.join('/','tmp'))
            directory = 'temp_dir_test'
            t.chdir(location)
            
            while t.isdir(directory):
                # I append a random letter/number until it is unique
                directory += random.choice(
                    string.ascii_uppercase + string.digits)
            t.mkdir(directory)
            
            dest_directory = directory+'_copy'
            t.copy(directory,dest_directory)
            
            with self.assertRaises(ValueError):
                t.copy(directory,'')

            with self.assertRaises(ValueError):
                t.copy('',directory)

            t.rmdir(directory)
            t.rmdir(dest_directory)
            

    def test_dir_permissions_creation_modification(self):
        """
        verify if chmod raises IOError when trying to change bits on a
        non-existing folder
        """
        # Imports required later
        import random
        import string
        import os,stat

        with custom_transport as t:
            location = t.normalize(os.path.join('/','tmp'))
            directory = 'temp_dir_test'
            t.chdir(location)

            while t.isdir(directory):
                # I append a random letter/number until it is unique
                directory += random.choice(
                    string.ascii_uppercase + string.digits)
            
            # create directory with non default permissions
            t.mkdir(directory)

            # change permissions
            t.chmod(directory, 0777)                

            # test if the security bits have changed
            self.assertEquals( t.get_mode(directory) , 0777 )

            # change permissions
            t.chmod(directory, 0511)

            # test if the security bits have changed
            self.assertEquals( t.get_mode(directory) , 0511 )
            
            # TODO : bug in paramiko. When changing the directory to very low \
            # I cannot set it back to higher permissions
            
            ## TODO: probably here we should then check for 
            ## the new directory modes. To see if we want a higher
            ## level function to ask for the mode, or we just
            ## use get_attribute
            t.chdir(directory)
            
            # change permissions of an empty string, non existing folder.
            fake_dir=''
            with self.assertRaises(IOError):
                t.chmod(fake_dir,0777)

            fake_dir='pippo'
            with self.assertRaises(IOError):
                # chmod to a non existing folder
                t.chmod(fake_dir,0777)

            t.chdir('..')
            t.rmdir(directory)


    def test_dir_reading_permissions(self):
        """
        Try to enter a directory with no read permissions.
        Verify that the cwd has not changed after failed try.
        """
        # Imports required later
        import random
        import string
        import os,stat

        with custom_transport as t:
            location = t.normalize(os.path.join('/','tmp'))
            directory = 'temp_dir_test'
            t.chdir(location)

            while t.isdir(directory):
                # I append a random letter/number until it is unique
                directory += random.choice(
                    string.ascii_uppercase + string.digits)
            
            # create directory with non default permissions
            t.mkdir(directory)

            # change permissions to low ones
            t.chmod(directory, 0)

            # test if the security bits have changed
            self.assertEquals( t.get_mode(directory) , 0 )

            old_cwd = t.getcwd()

            with self.assertRaises( IOError ):
                t.chdir(directory)

            new_cwd = t.getcwd()
            
            self.assertEquals(old_cwd,new_cwd)
            
            # TODO : the test leaves a directory even if it is successful
            #        The bug is in paramiko. After lowering the permissions,
            #        I cannot restore them to higher values
            #t.rmdir(directory)

            
    def test_isfile_isdir_to_empty_string(self):
        """
        I check that isdir or isfile return False when executed on an
        empty string
        """
        import os

        with custom_transport as t:
            location = t.normalize(os.path.join('/','tmp'))
            t.chdir(location)
            self.assertFalse(t.isdir(""))
            self.assertFalse(t.isfile(""))


    def test_isfile_isdir_to_non_existing_string(self):
        """
        I check that isdir or isfile return False when executed on an
        empty string
        """
        import os
        with custom_transport as t:

            location = t.normalize(os.path.join('/','tmp'))
            t.chdir(location)
            fake_folder = 'pippo'
            self.assertFalse(t.isfile(fake_folder))
            self.assertFalse(t.isdir(fake_folder))
            with self.assertRaises(IOError):
                t.chdir(fake_folder)

           
    def test_chdir_to_empty_string(self):
        """
        I check that if I pass an empty string to chdir, the cwd does
        not change (this is a paramiko default behavior), but getcwd()
        is still correctly defined.
        """
        import os
        with custom_transport as t:

            new_dir = t.normalize(os.path.join('/','tmp'))
            t.chdir(new_dir)
            t.chdir("")
            self.assertEquals(new_dir, t.getcwd())

class TestPutGetFile(unittest.TestCase):
    """
    Test to verify whether the put and get functions behave correctly on files.
    1) they work
    2) they need abs paths where necessary, i.e. for local paths
    3) they reject empty strings
    """

    def test_put_and_get(self):
        import os
        import random
        import string
        
        local_dir = os.path.join('/','tmp')
        remote_dir = local_dir
        directory = 'tmp_try'

        with custom_transport as t:

            t.chdir(remote_dir)
            while t.isdir(directory):
                # I append a random letter/number until it is unique
                directory += random.choice(
                    string.ascii_uppercase + string.digits)
                
            t.mkdir(directory)
            t.chdir(directory)

            local_file_name = os.path.join(local_dir,directory,'file.txt')
            remote_file_name = 'file_remote.txt'
            retrieved_file_name = os.path.join(local_dir,directory,'file_retrieved.txt')

            text = 'Viva Verdi\n'
            with open(local_file_name,'w') as f:
                f.write(text)

            # here use full path in src and dst
            t.put(local_file_name,remote_file_name)
            t.get(remote_file_name,retrieved_file_name)
            t.putfile(local_file_name,remote_file_name)
            t.getfile(remote_file_name,retrieved_file_name)
            
            list_of_files = t.listdir('.')
            # it is False because local_file_name has the full path,
            # while list_of_files has not
            self.assertFalse(local_file_name in list_of_files)
            self.assertTrue(remote_file_name in list_of_files)
            self.assertFalse(retrieved_file_name in list_of_files)

            os.remove(local_file_name)
            t.remove(remote_file_name)
            os.remove(retrieved_file_name)

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
        remote_dir = local_dir
        directory = 'tmp_try'

        with custom_transport as t:
            t.chdir(remote_dir)
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

            # partial_file_name is not an abs path
            with self.assertRaises(ValueError):
                t.put(partial_file_name,remote_file_name)
            with self.assertRaises(ValueError):
                t.putfile(partial_file_name,remote_file_name)

            # retrieved_file_name does not exist
            with self.assertRaises(OSError):
                t.put(retrieved_file_name,remote_file_name)
            with self.assertRaises(OSError):
                t.putfile(retrieved_file_name,remote_file_name)
                
            # remote_file_name does not exist
            with self.assertRaises(IOError):
                t.get(remote_file_name,retrieved_file_name)
            with self.assertRaises(IOError):
                t.getfile(remote_file_name,retrieved_file_name)
            
            t.put(local_file_name,remote_file_name)
            t.putfile(local_file_name,remote_file_name)
            
            # local filename is not an abs path
            with self.assertRaises(ValueError):
                t.get(remote_file_name,'delete_me.txt')
            with self.assertRaises(ValueError):
                t.getfile(remote_file_name,'delete_me.txt')

            t.remove(remote_file_name)
            os.remove(local_file_name)

            t.chdir('..')
            t.rmdir(directory)

    def test_put_get_empty_string(self):
        """
        test of exception put/get of empty strings
        """
        # TODO : verify the correctness of \n at the end of a file
        import os
        import random
        import string

        local_dir = os.path.join('/','tmp')
        remote_dir = local_dir
        directory = 'tmp_try'

        with custom_transport as t:

            t.chdir(remote_dir)
            while t.isdir(directory):
                # I append a random letter/number until it is unique
                directory += random.choice(
                    string.ascii_uppercase + string.digits)

            t.mkdir(directory)
            t.chdir(directory)

            local_file_name = os.path.join(local_dir,directory,'file_local.txt')
            remote_file_name = 'file_remote.txt'
            retrieved_file_name = os.path.join(local_dir,directory,'file_retrieved.txt')
            
            text = 'Viva Verdi\n'
            with  open(local_file_name,'w') as f:
                f.write(text)

            # localpath is an empty string
            # ValueError because it is not an abs path
            with self.assertRaises(ValueError):
                t.put('',remote_file_name)
            with self.assertRaises(ValueError):
                t.putfile('',remote_file_name)

            # remote path is an empty string
            with self.assertRaises(IOError):
                t.put(local_file_name,'')
            with self.assertRaises(IOError):
                t.putfile(local_file_name,'')

            t.put(local_file_name,remote_file_name)
            # overwrite the remote_file_name
            t.putfile(local_file_name,remote_file_name)
            
            # remote path is an empty string
            with self.assertRaises(IOError):
                t.get('',retrieved_file_name)
            with self.assertRaises(IOError):
                t.getfile('',retrieved_file_name)

            # local path is an empty string
            # ValueError because it is not an abs path
            with self.assertRaises(ValueError):
                t.get(remote_file_name,'')
            with self.assertRaises(ValueError):
                t.getfile(remote_file_name,'')

            # TODO : get doesn't retrieve empty files.
            # Is it what we want?
            t.get(remote_file_name,retrieved_file_name)
            # overwrite retrieved_file_name
            t.getfile(remote_file_name,retrieved_file_name)

            os.remove(local_file_name)
            t.remove(remote_file_name)
            # If it couldn't end the copy, it leaves what he did on
            # local file
            self.assertTrue( 'file_retrieved.txt' in t.listdir('.') )
            os.remove(retrieved_file_name)

            t.chdir('..')
            t.rmdir(directory)


class TestPutGetTree(unittest.TestCase):
    """
    Test to verify whether the put and get functions behave correctly on folders.
    1) they work
    2) they need abs paths where necessary, i.e. for local paths
    3) they reject empty strings
    """

    def test_put_and_get(self):
        import os
        import random
        import string
        
        local_dir = os.path.join('/','tmp')
        remote_dir = local_dir
        directory = 'tmp_try'

        with custom_transport as t:

            t.chdir(remote_dir)
            
            while os.path.exists(os.path.join(local_dir,directory) ):
                # I append a random letter/number until it is unique
                directory += random.choice(
                    string.ascii_uppercase + string.digits)

            local_subfolder = os.path.join(local_dir,directory,'tmp1')
            remote_subfolder = 'tmp2'
            retrieved_subfolder = os.path.join(local_dir,directory,'tmp3')
            
            os.mkdir(os.path.join(local_dir,directory))
            os.mkdir(os.path.join(local_dir,directory,local_subfolder))
            
            t.chdir(directory)

            local_file_name = os.path.join(local_subfolder,'file.txt')
            # remote_file_name = os.path.join(remote_subfolder,'file_remote.txt')
            # retrieved_file_name = os.path.join(local_dir,directory,local_subfolder,
            #                                   'file_retrieved.txt')

            text = 'Viva Verdi\n'
            with open(local_file_name,'w') as f:
                f.write(text)

            # here use full path in src and dst
            t.put(local_subfolder,remote_subfolder)
            t.get(remote_subfolder,retrieved_subfolder)

            # Here I am mixing the local with the remote fold
            list_of_dirs = t.listdir('.')
            # # it is False because local_file_name has the full path,
            # # while list_of_files has not
            self.assertFalse( local_subfolder in list_of_dirs)
            self.assertTrue( remote_subfolder in list_of_dirs)
            self.assertFalse( retrieved_subfolder in list_of_dirs)
            self.assertTrue( 'tmp1' in list_of_dirs)
            self.assertTrue( 'tmp3' in list_of_dirs)

            list_pushed_file = t.listdir('tmp2')
            list_retrieved_file = t.listdir('tmp3')
            self.assertTrue( 'file.txt' in list_pushed_file )
            self.assertTrue( 'file.txt' in list_retrieved_file )
            
            # os.remove(local_file_name)
            # t.remove(remote_file_name)
            # os.remove(retrieved_file_name)

            # t.chdir('..')
            # t.rmdir(directory)
            


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
        execution (done in this module, in the _exec_command_internal function).
        """
        import os
        
        # Start value
        delete_at_end = False

        with custom_transport as t:

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
        with custom_transport as t:
            retcode, stdout, stderr = t.exec_command_wait(
                'cat', stdin=test_string)
            self.assertEquals(retcode, 0)
            self.assertEquals(stdout, test_string)
            self.assertEquals(stderr, "")

    def test_exec_with_stdin_unicode(self):
        test_string = u"some_test String"
        with custom_transport as t:
            retcode, stdout, stderr = t.exec_command_wait(
                'cat', stdin=test_string)
            self.assertEquals(retcode, 0)
            self.assertEquals(stdout, test_string)
            self.assertEquals(stderr, "")

    def test_exec_with_stdin_filelike(self):
        import StringIO
        test_string = "some_test String"
        stdin = StringIO.StringIO(test_string)
        with custom_transport as t:
            retcode, stdout, stderr = t.exec_command_wait(
                'cat', stdin=stdin)
            self.assertEquals(retcode, 0)
            self.assertEquals(stdout, test_string)
            self.assertEquals(stderr, "")

    def test_exec_with_wrong_stdin(self):
        # I pass a number
        with custom_transport as t:
            with self.assertRaises(ValueError):
                retcode, stdout, stderr = t.exec_command_wait(
                    'cat', stdin=1)


def run_tests(transport_to_test):
    """
    This function has to be called in the transport plugin.
    It loads the correct transport class that will be called in the test classes.
    """
    if transport_to_test == 'ssh':
        import paramiko
        from aida.transport import Transport
        global custom_transport
        PluginTransport = load_plugin(
            Transport,'aida.transport.plugins', transport_to_test)
        custom_transport = PluginTransport(
            machine='localhost', timeout=30, 
            load_system_host_keys=True,
            key_policy = paramiko.AutoAddPolicy())

    elif transport_to_test == 'local':
        from aida.transport import Transport
        global custom_transport
        PluginTransport = load_plugin(
            Transport,'aida.transport.plugins', transport_to_test)
        custom_transport = PluginTransport()
    
    else:
        raise ValueError("The transport {} is not implemented.".format(
            transport_to_test))
    


