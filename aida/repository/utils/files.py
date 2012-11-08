"""
This module contains routines to help in managing the local
AIDA repository.
"""
import os, os.path
import shutil

def copy_to_repo(source, section, filename, overwrite=False):
    """
    This routine copies the source file 'source' to the local AIDA repository,
    in the subdirectory 'section' (that can be 'calcs', 'potentials', ...)
    to a file with name 'filename'.
    
    Only a finite list of section names are allowed, otherwise a ValueError
    is returned.

    Args:
        source: the source file on the disk
        section: the section on the code, as 'calcs', 'potentials', ...
        filename: the filename relative to aidarepository/section.
            It can contain also subdirectories, and in this case this
            function will take care of creating empty directories if needed.
        overwrite: if True, existing files are overwritten without asking.
            if False, a IOError is raised if the file already exists.
            Note that empty folders are created anyway, independent of the
            value of this flag.

    Raises:
        OSError or IOError: in case of problems accessing or writing the files.
        ValueError: if the section is not recognized.
    """
    if section not in ['calcs', 'potentials']:
        retstr = "Section '{}' not allowed in copy_to_repo.".format(section)
        raise ValueError(retstr)

    from aida.djsite.settings.settings import LOCAL_REPOSITORY
    # Check if the LOCAL_REPOSITORY exists, mainly to avoid to write in
    # random places
    if not os.path.isdir(LOCAL_REPOSITORY):
        raise ImproperlyConfigured(
        "The LOCAL_REPOSITORY variable is not setup correctly.")

    dest = os.path.join(LOCAL_REPOSITORY, unicode(section), unicode(filename))
    pardir = os.path.dirname(dest)
    if not os.path.exists(pardir):
        os.makedirs(pardir)

    # check if the file already exists if overwrite==False. If this is the
    # case, raise a IOError
    if not overwrite and os.path.exists(dest):
        raise IOError("File {} already exists. I stop since you called "
                      "copy_to_repo with overwrite=False.".format(dest))
    
    shutil.copyfile(source,dest)
        
