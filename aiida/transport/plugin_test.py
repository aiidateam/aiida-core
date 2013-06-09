"""
This module contains a set of unittest test classes that can be loaded from the plugin.
Every transport plugin should be able to pass all of these common tests.
Plugin specific tests will be written in the plugin itself.
"""

# TODO : test for copy with pattern
# TODO : test for copy with/without patterns, overwriting folder
# TODO : test for exotic cases of copy with source = destination
# TODO : silly cases of copy/put/get from self to self

import unittest

custom_transport = None

class TestDirectoryManipulation(unittest.TestCase):
    """
    Test to check, create and delete folders.
    """
    def test_makedirs(self):
        """
        Verify the functioning of makedirs command
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

            # define folder structure
            dir_tree = os.path.join('1','2')
            # I create the tree
            t.makedirs(dir_tree)
            # verify the existence
            self.assertTrue( t.isdir('1') )
            self.assertTrue( dir_tree )

            # try to recreate the same folder
            with self.assertRaises(OSError):
                t.makedirs(dir_tree)

            # recreate but with ignore flag
            t.makedirs(dir_tree,True)

            t.rmdir(dir_tree)
            t.rmdir('1')
                
            t.chdir('..')
            t.rmdir(directory)


    def test_rmtree(self):
        """
        Verify the functioning of makedirs command
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

            # define folder structure
            dir_tree = os.path.join('1','2')
            # I create the tree
            t.makedirs(dir_tree)
            # remove it
            t.rmtree('1')
            # verify the removal
            self.assertFalse( t.isdir('1') )
                
            t.chdir('..')
            t.rmdir(directory)


    
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
            list_of_dir=['1','-f a&','as','a2','a4f']
            for this_dir in list_of_dir:
                t.mkdir(this_dir)
            list_of_dir_found = t.listdir('.')
            self.assertTrue(sorted(list_of_dir_found)==sorted(list_of_dir))    

            self.assertTrue( sorted(t.listdir('.','a*')), sorted(['as','a2','a4f']) )
            self.assertTrue( sorted(t.listdir('.','a?')), sorted(['as','a2']) )
            self.assertTrue( sorted(t.listdir('.','a[2-4]*')), sorted(['a2','a4f']) )

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
        import os

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
        import os

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

            text = 'Viva Verdi\n'
            with open(local_file_name,'w') as f:
                f.write(text)

            # here use full path in src and dst
            for i in range(2):
                if i==0:
                    t.put(local_subfolder,remote_subfolder)
                    t.get(remote_subfolder,retrieved_subfolder)
                else:
                    t.puttree(local_subfolder,remote_subfolder)
                    t.gettree(remote_subfolder,retrieved_subfolder)

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
            
            os.remove(os.path.join(local_subfolder,'file.txt'))
            os.rmdir(local_subfolder)
            os.remove(os.path.join(retrieved_subfolder,'file.txt'))
            os.rmdir(retrieved_subfolder)
            t.remove(os.path.join(remote_subfolder,'file.txt'))
            t.rmdir(remote_subfolder)
            
            t.chdir('..')
            t.rmdir(directory)
            

    def test_put_and_get_overwrite(self):
        import os, shutil
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

            text = 'Viva Verdi\n'
            with open(local_file_name,'w') as f:
                f.write(text)


            t.put(local_subfolder,remote_subfolder)
            t.get(remote_subfolder,retrieved_subfolder)

            # by defaults rewrite everything
            t.put(local_subfolder,remote_subfolder)
            t.get(remote_subfolder,retrieved_subfolder)

            with self.assertRaises(OSError):
                t.put(local_subfolder,remote_subfolder,overwrite=False)
            with self.assertRaises(OSError):
                t.get(remote_subfolder,retrieved_subfolder,overwrite=False)
            with self.assertRaises(OSError):
                t.puttree(local_subfolder,remote_subfolder,overwrite=False)
            with self.assertRaises(OSError):
                t.gettree(remote_subfolder,retrieved_subfolder,overwrite=False)

            shutil.rmtree(local_subfolder)
            shutil.rmtree(retrieved_subfolder)
            t.rmtree(remote_subfolder)
            # t.rmtree(remote_subfolder)
            # here I am mixing inevitably the local and the remote folder
            t.chdir('..')
            t.rmtree(directory)



    def test_put_and_get_pattern(self):
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
            local_subsubfolder = os.path.join(local_subfolder,'subdir')
            remote_subfolder = 'tmp2'
            retrieved_subfolder = os.path.join(local_dir,directory,'tmp3')
            
            os.mkdir(os.path.join(local_dir,directory))
            os.mkdir(os.path.join(local_dir,directory,local_subfolder))            
            os.mkdir(os.path.join(local_dir,directory,local_subsubfolder))
            t.chdir(directory)

            # create a tree with files
            local_file_name_1 = os.path.join(local_subfolder,'a.txt')
            local_file_name_2 = os.path.join(local_subfolder,'b.tmp')
            local_file_name_3 = os.path.join(local_subfolder,'c.txt')
            local_file_name_4 = os.path.join(local_subsubfolder,'d.txt')
            text = 'Viva Verdi\n'
            for filename in [local_file_name_1,local_file_name_2,
                             local_file_name_3,local_file_name_4]:
                with open(filename,'w') as f:
                    f.write(text)
            
            t.put(local_subfolder,remote_subfolder,pattern='*.txt')
            # copies a.txt and c.txt but not the subsubfolder
            self.assertEquals( set(['a.txt','c.txt']), set(t.listdir(remote_subfolder)) )

            # test a more nested pattern
            t.rmtree(remote_subfolder)
            t.put(local_subfolder,remote_subfolder,pattern='*/*.txt')
            # copies d.txt in the subsubfolder
            self.assertEquals( ['subdir'], t.listdir(remote_subfolder) )
            self.assertEquals( ['d.txt'],t.listdir(os.path.join(remote_subfolder,'subdir')) )

            # now copy everything
            t.put(local_subfolder,remote_subfolder)

            # analogous test for get
            t.get(remote_subfolder,retrieved_subfolder,pattern='*.txt')
            # copies a.txt and c.txt but not the subsubfolder
            self.assertEquals( set(['a.txt','c.txt']), set(os.listdir(retrieved_subfolder)) )

            # more nested
            t.rmtree(retrieved_subfolder)
            t.get(remote_subfolder,retrieved_subfolder,pattern='*/*.txt')
            # copies a.txt and c.txt but not the subsubfolder
            self.assertEquals( ['subdir'],os.listdir(retrieved_subfolder))
            self.assertEquals( ['d.txt'],
                               os.listdir(os.path.join(retrieved_subfolder,'subdir')) )

            t.chdir('..')
            t.rmtree(directory)


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

            f = open(local_file_name,'w')
            f.close()

            # 'tmp1' is not an abs path
            with self.assertRaises(ValueError):
                t.put('tmp1',remote_subfolder)
            with self.assertRaises(ValueError):
                t.putfile('tmp1',remote_subfolder)
            with self.assertRaises(ValueError):
                t.puttree('tmp1',remote_subfolder)

            # 'tmp3' does not exist
            with self.assertRaises(OSError):
                t.put(retrieved_subfolder,remote_subfolder)
            with self.assertRaises(OSError):
                t.putfile(retrieved_subfolder,remote_subfolder)
            with self.assertRaises(OSError):
                t.puttree(retrieved_subfolder,remote_subfolder)
                
            # remote_file_name does not exist
            with self.assertRaises(IOError):
                t.get('non_existing',retrieved_subfolder)
            with self.assertRaises(IOError):
                t.getfile('non_existing',retrieved_subfolder)
            with self.assertRaises(IOError):
                t.gettree('non_existing',retrieved_subfolder)
            
            t.put(local_subfolder,remote_subfolder)
            
            # local filename is not an abs path
            with self.assertRaises(ValueError):
                t.get(remote_subfolder,'delete_me_tree')
            with self.assertRaises(ValueError):
                t.getfile(remote_subfolder,'delete_me_tree')
            with self.assertRaises(ValueError):
                t.gettree(remote_subfolder,'delete_me_tree')

            os.remove(os.path.join(local_subfolder,'file.txt'))
            os.rmdir(local_subfolder)
            t.rmtree(remote_subfolder)

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

            text = 'Viva Verdi\n'
            with  open(local_file_name,'w') as f:
                f.write(text)
            
            # localpath is an empty string
            # ValueError because it is not an abs path
            with self.assertRaises(ValueError):
                t.puttree('',remote_subfolder)

            # remote path is an empty string
            with self.assertRaises(IOError):
                t.puttree(local_subfolder,'')

            t.puttree(local_subfolder,remote_subfolder)
            
            # remote path is an empty string
            with self.assertRaises(IOError):
                t.gettree('',retrieved_subfolder)

            # local path is an empty string
            # ValueError because it is not an abs path
            with self.assertRaises(ValueError):
                t.gettree(remote_subfolder,'')

            # TODO : get doesn't retrieve empty files.
            # Is it what we want?
            t.gettree(remote_subfolder,retrieved_subfolder)


            os.remove(os.path.join(local_subfolder,'file.txt'))
            os.rmdir(local_subfolder)
            t.remove(os.path.join(remote_subfolder,'file.txt'))
            t.rmdir(remote_subfolder)
            # If it couldn't end the copy, it leaves what he did on local file
            # here I am mixing local with remote
            self.assertTrue( 'file.txt' in t.listdir('tmp3') )
            os.remove(os.path.join(retrieved_subfolder,'file.txt'))
            os.rmdir(retrieved_subfolder)

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
                _ = t.exec_command_wait(
                    'cat', stdin=1)



