"""
This module contains routines to help in managing the local
AIDA repository.
"""
import os, os.path
import tempfile
from aida.djsite.settings.settings import LOCAL_REPOSITORY
from django.core.exceptions import ImproperlyConfigured
from aida.common.classes.folder import Folder

# I use realpath to consider correctly also symlinks
# Check if the LOCAL_REPOSITORY exists, mainly to avoid to write in
# random places
# .. todo:: See if this 'global' place is the right place to do it or not
if not os.path.isdir(LOCAL_REPOSITORY):
    raise ImproperlyConfigured(
        "The LOCAL_REPOSITORY variable is not setup correctly.")
sandbox_folder = os.path.realpath(os.path.join(LOCAL_REPOSITORY,'sandbox'))
perm_repository = os.path.realpath(os.path.join(LOCAL_REPOSITORY,'repository'))


class SandboxFolder(Folder):
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

        abspath = tempfile.mkdtemp(dir=sandbox_folder)
        super(SandboxFolder, self).__init__(abspath=abspath)
       
    def __enter__(self):
        """
        Called when entering in the with statement
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        In exit, I remove the sandbox folder from disk, if it still exists
        """
        self.erase()
 

class RepositoryFolder(Folder):
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

        # Internal variable of this class 
        self._subfolder=subfolder

        # This will also do checks on the folder limits
        super(RepositoryFolder, self).__init__(abspath=dest, folder_limit=entity_dir)

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
        
        Overrides the base class Folder get_subfolder method by creating a new instance of
        a RepositoryFolder object, instead of a simple Folder object.

        Args:
            subfolder: the required subfolder.
                Can also contain .. but cannot go beyond the entity folder
                (i.e., the section/uuid folder).
        """
        return RepositoryFolder(self.section,self.uuid,
            subfolder=os.path.normpath(os.path.join(self.subfolder,subfolder)))


if __name__ == "__main__":
    # .. todo:: implement tests here
    pass
