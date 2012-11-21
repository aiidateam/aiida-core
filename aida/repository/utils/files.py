"""
This module contains routines to help in managing the local
AIDA repository.
"""
import os, os.path
import shutil
import tempfile
from aida.djsite.settings.settings import LOCAL_REPOSITORY
from django.core.exceptions import ImproperlyConfigured

# I use realpath to consider correctly also symlinks
# Check if the LOCAL_REPOSITORY exists, mainly to avoid to write in
# random places
if not os.path.isdir(LOCAL_REPOSITORY):
    raise ImproperlyConfigured(
        "The LOCAL_REPOSITORY variable is not setup correctly.")
sandbox_folder = os.path.realpath(os.path.join(LOCAL_REPOSITORY,'sandbox'))
perm_repository = os.path.realpath(os.path.join(LOCAL_REPOSITORY,'repository'))

def is_subfolder(subfolder,parent):
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


class SandboxFolder(object):
    """
    A class to manage the creation and management of a sandbox folder.
    
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
        
    def insert_file(self,src,subfolder=os.curdir,dest_name=None):
        """
        Copy a file to the sandbox folder, possibly in a subfolder of it
        (by default, it copies to the top directory).
        
        Args:
            src: the source filename to copy
            subfolder: the relative path of the subfolder where to create
                the file. If it does not exist, it is created first.
            dest_name: if None, the same basename of src is used. Otherwise,
                the destination filename will have this file name.
        """
        if dest_name is None:
            dest_filename = unicode(os.path.basename(src))
        else:
            dest_filename = unicode(dest_name)

        # create the subdirectory, if needed; first check that we are not
        # trying to write outside the sandbox (e.g. because the user passed
        # ".." as subfolder parameter)
        dest_abs_dir = os.path.realpath(os.path.join(
                self.abspath,unicode(subfolder)))
        if not is_subfolder(dest_abs_dir,self.abspath):
            raise ValueError("You specified a subfolder that goes out of the "
                             "boundaries of the sandbox folder!\nSandbox={}, "
                             "subfolder={}".format(self.abspath,dest_abs_dir))
        if not os.path.exists(dest_abs_dir):
            os.makedirs(dest_abs_dir)

        dest_abs_path = os.path.join(dest_abs_dir,dest_filename)
        shutil.copyfile(src,dest_abs_path)

        return dest_abs_path

    @property
    def abspath(self):
        """
        The absolute path of the sandbox.
        """
        return self._abspath

def move_folder_to_repo(src, section, uuid, subfolder=os.curdir,
                     overwrite=False):
    """
    This routine moves the source folder 'src' to the local AIDA repository,
    in the subdirectory 'section' (that can be 'calculations', 'potentials', 
    ...).
    The destination folder will then be:
    perm_repository/section/uuid/subfolder/
       
    Args:
        src: the source folder on the disk
        section: the section on the code, as 'calculations', 'potentials', ...
            Only a finite list of section names are allowed, otherwise a
            ValueError is returned.
        uuid: the UUID within the given section, as stored in the database
        subfolder: the subfolder in which the srcdir content should be copied.
            Empty directories will be automatically created, if needed.
            By default, subfolder = os.curdir, and thus the content of the
            srcdir directory are copied within perm_repository/section/uuid/
        overwrite: if True, existing files are overwritten without asking.
            if False, a IOError is raised if the file already exists.
            Note that empty folders are created anyway, independent of the
            value of this flag.

    Raises:
        OSError or IOError: in case of problems accessing or writing the files.
        ValueError: if the section is not recognized.
    """
    if section not in ['calculations', 'potentials','structures']:
        retstr = "Repository section '{}' not allowed.".format(section)
        raise ValueError(retstr)

    entity_dir=os.path.realpath(os.path.join(perm_repository, unicode(section), 
                                             unicode(uuid)))
    dest = os.path.realpath(os.path.join(entity_dir,unicode(subfolder)))

    # Directory boundary check
    if not is_subfolder(dest,entity_dir):
            raise ValueError("You specified a subfolder that goes out of the "
                             "boundaries of the entity folder!\nEntity folder"
                             "={}, subfolder={}".format(entity_dir,dest))
        
    # Create parent dir, if needed
    pardir = os.path.dirname(dest)
    if not os.path.exists(pardir):
        os.makedirs(pardir)
        
    # check if the file already exists if overwrite==False. If this is the
    # case, raise a IOError. If instead overwrite==True, delete the directory
    # first (otherwise, the directory is copied as a subfolder)
    if os.path.exists(dest):
        if overwrite:
            shutil.rmtree(dest)
        else:
            raise IOError("Location {} already exists, and overwrite is set to "
                          "False".format(dest))

    shutil.move(src,dest)
        
