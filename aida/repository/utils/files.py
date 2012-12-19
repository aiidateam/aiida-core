"""
This module contains routines to help in managing the local
AIDA repository.

.. todo:: Understand if it makes sense to have a common base class for
    both kind of Folder objects.
"""
import os, os.path
import shutil
import tempfile
from aida.djsite.settings.settings import LOCAL_REPOSITORY
from django.core.exceptions import ImproperlyConfigured

# I use realpath to consider correctly also symlinks
# Check if the LOCAL_REPOSITORY exists, mainly to avoid to write in
# random places
# .. todo:: See if this 'global' place is the right place to do it or not
if not os.path.isdir(LOCAL_REPOSITORY):
    raise ImproperlyConfigured(
        "The LOCAL_REPOSITORY variable is not setup correctly.")
sandbox_folder = os.path.realpath(os.path.join(LOCAL_REPOSITORY,'sandbox'))
perm_repository = os.path.realpath(os.path.join(LOCAL_REPOSITORY,'repository'))

def _is_subfolder(subfolder,parent):
    """
    Check if a given folder is a subfolder of a parent folder.
    
    Useful to avoid that the user tries to write outside of the 'parent'
    folder, e.g. by specifying a subfolder='..'.

    .. todo:: It uses os.path.commonprefix, to check whether this works on all
    supported platforms...

    Args:
        subfolder: the folder to check
        parent: the parent folder in which subfolder should be contained
    """
    return os.path.commonprefix([subfolder,parent]) == parent


def _join_folder_file(folder,filename):
    """
    Joins a folder with a filename. Folder should be an absolute path
    for this to work.

    Also checks that the filename is valid, e.g. that is not .., or
    contains slashes, etc., by checking that after joining the two parts
    together, and splitting them back, we get the tuple (folder, filename).

    .. todo:: check if this check works, and if it is sufficient. Probably
        something stronger is needed.
    """
    dest_abs_path = os.path.join(folder,filename)

    if not os.path.split(dest_abs_path) == (folder,filename):
        errstr = "You didn't specify a valid filename: {}".format(filename)
        raise ValueError(errstr)

    return dest_abs_path


class SandboxFolder(object):
    """
    A class to manage the creation and management of a sandbox folder.
    
    Note: this class must be used within a context manager, i.e.:
    
    with SandboxFolder as f:
        ## do something with f

    In this way, the sandbox folder is removed from disk
    (if it wasn't removed already) when exiting the 'with' block.

    .. todo:: Implement check of whether the folder has been removed.
    """
    def __init__(self):
        """
        Initializes the object by creating a new temporary folder in the 
        sandbox.
        """
        # First check if the sandbox folder already exists
        if not os.path.exists(sandbox_folder):
            os.makedirs(sandbox_folder)

        self._abspath = tempfile.mkdtemp(dir=sandbox_folder)
       
    def __enter__(self):
        """
        Called when entering in the with statement
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        In exit, I remove the sandbox folder from disk, if it still exists
        """
        if os.path.exists(self.abspath):
            shutil.rmtree(self.abspath)
 
    def get_file_path(self, filename, subfolder=os.curdir,
                      create_subfolders=False):
        """
        Return the absolute path of a given file in the folder, possibly
        within a subfolder.

        Can also be used for instance to start creating a file in the
        sandbox.

        Check that the subfolder is actually within the sandbox folder 
        (can be False if subfolder='..', for instance).

        Args:
            src: the source filename to copy
            filename: The file name.
            subfolder: the relative path of the subfolder where to create
                the file.
            create_subfolders: if True, creates the required subfolders, if
                they don't exists. Note that the file itself is never created.
        """
        dest_abs_dir = os.path.realpath(os.path.join(
                self.abspath,unicode(subfolder)))
        if not _is_subfolder(dest_abs_dir,self.abspath):
            raise ValueError("You specified a subfolder that goes out of the "
                             "boundaries of the sandbox folder!\nSandbox={}, "
                             "subfolder={}".format(self.abspath,dest_abs_dir))

        if create_subfolders and not os.path.exists(dest_abs_dir):
            os.makedirs(dest_abs_dir)

        return _join_folder_file(dest_abs_dir,filename)


    def insert_file(self,src,dest_name=None,subfolder=os.curdir):
        """
        Copy a file to the sandbox folder, possibly in a subfolder of it
        (by default, it copies to the top directory).
        
        Args:
            src: the source filename to copy
            dest_name: if None, the same basename of src is used. Otherwise,
                the destination filename will have this file name.
            subfolder: the relative path of the subfolder where to create
                the file. If it does not exist, it is created first.
        """
        if dest_name is None:
            dest_filename = unicode(os.path.basename(src))
        else:
            dest_filename = unicode(dest_name)

        dest_abs_path = self.get_file_path(dest_filename, subfolder=subfolder,
                      create_subfolders=True)

        shutil.copyfile(src,dest_abs_path)

        return dest_abs_path

    @property
    def abspath(self):
        """
        The absolute path of the sandbox.
        """
        return self._abspath


class RepositoryFolder(object):
    """
    A class to manage the local AIDA repository folders.
    """
    def __init__(self, section, uuid, subfolder=os.curdir):
        """
        Initializes the object by pointing it to a folder in the repository.
        """
        if section not in ['calculations', 'potentials','structures']:
            retstr = "Repository section '{}' not allowed.".format(section)
            raise ValueError(retstr)
        self._section = section
        self._uuid = uuid

        entity_dir=os.path.realpath(os.path.join(
                perm_repository, unicode(section), 
                unicode(uuid)))
        dest = os.path.realpath(os.path.join(entity_dir,unicode(subfolder)))

        # Directory boundary check
        if not _is_subfolder(dest,entity_dir):
            raise ValueError("You specified a subfolder that goes out of the "
                             "boundaries of the entity folder!\nEntity folder"
                             "={}, subfolder={}".format(entity_dir,dest))

        self._subfolder=subfolder
        self._abspath=dest
 
    def insert_file(self,src,dest_name=None):
        """
        Copy a file to the folder.
        
        Args:
            src: the source filename to copy
            dest_name: if None, the same basename of src is used. Otherwise,
                the destination filename will have this file name.
        """
        if dest_name is None:
            filename = unicode(os.path.basename(src))
        else:
            filename = unicode(dest_name)

        # I get the full path of the filename, checking also that I don't
        # go beyond the folder limits
        dest_abs_path = self.get_filename(filename)
    
        shutil.copyfile(src,dest_abs_path)

        return dest_abs_path

    def get_filename(self,filename):
        """
        Return an absolute path for a filename in this folder.
        
        The advantage of using this method is that it checks that we are
        not going beyond the limits of the folder.
        
        Args:
            filename: The filename to open.
        """
        dest_abs_path = _join_folder_file(self.abspath,filename)
    
        return dest_abs_path

    @property
    def abspath(self):
        """
        The absolute path of the folder.
        """
        return self._abspath

    @property
    def section(self):
        """
        The section to which this folder belongs.
        """
        return self._section

    @property
    def uuid(self):
        """
        The uuid to which this folder belongs.
        """
        return self._uuid

    @property
    def subfolder(self):
        """
        The subfolder within the section/uuid folder.
        """
        return self._subfolder

    def get_topdir(self):
        """
        Returns the top directory, i.e., the section/uuid folder object.
        """
        return RepositoryFolder(self.section,self.uuid)

    def get_subfolder(self,subfolder):
        """
        Returns a subdirectory object of the current directory.
        
        Args:
            subfolder: the required subfolder.
                Can also contain .. but cannot go beyond the entity folder
                (i.e., the section/uuid folder).
        """
        return RepositoryFolder(self.section,self.uuid,
            subfolder=os.path.normpath(os.path.join(self.subfolder,subfolder)))

    def exists(self):
        """
        Return True if the folder exists, False otherwise.
        """
        return os.path.exists(self.abspath)

    def erase(self,create_empty_folder=False):
        """
        Erases the folder. Should be called only in very specific cases,
        in general folder should not be erased!

        Doesn't complain if the folder does not exist.

        Args:
            create_empty_folder: if True, after erasing, creates an empty dir.
        """
        if self.exists():
            shutil.rmtree(self.abspath)

        if create_empty_folder:
            self.create()

    def create(self):
        """
        Creates the folder, if it does not exist on the disk yet.

        It will also create top directories, if absent.

        It is always safe to call it, it will do nothing if the folder
        already exists.
        """
        if not self.exists():
            os.makedirs(self.abspath)
            

    def replace_with_folder(self, srcdir, move=False, overwrite=False):
        """
        This routine copies or moves the source folder 'srcdir' to the local
        AIDA repository, in the place pointed by the RepositoryFolder object.
        
        Args:
            srcdir: the source folder on the disk
            move: if True, the srcdir is moved to the repository. Otherwise, it
                is only copied.
            overwrite: if True, the folder will be erased first.
                if False, a IOError is raised if the folder already exists.
                Whatever the value of this flag, parent directories will be
                created, if needed.

        Raises:
            OSError or IOError: in case of problems accessing or writing
                the files.
            ValueError: if the section is not recognized.
        """
        if overwrite:
            self.erase()
        elif self.exists():
            raise IOError("Location {} already exists, and overwrite is set to "
                          "False".format(self.abspath))

        # Create parent dir, if needed
        pardir = os.path.dirname(self.abspath)
        if not os.path.exists(pardir):
            os.makedirs(pardir)

        if move:
            shutil.move(srcdir,self.abspath)
        else:
            shutil.copytree(srcdir,self.abspath)


if __name__ == "__main__":
    # .. todo:: implement tests here
    pass
