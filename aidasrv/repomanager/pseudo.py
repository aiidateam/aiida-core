"""
This module manages the pseudopotentials in the local repository and their
maintainance also in the database table 'potential'.
"""
import hashlib
from aidadb.models import Potential, PotentialAttrTxt, PotentialAttrTxtVal
from aidadb.models import Element
import logging
import os, os.path
import re
from aidasrv.repomanager.file import copy_to_repo
from django.core.exceptions import ObjectDoesNotExist
from aidalib.exceptions import ValidationError

logger = logging.getLogger(__name__)

def md5_file(filename, block_size_factor=128):
    """
    Open a file and return its md5sum (hexdigested).

    Args:
        filename: the filename of the file for which we want the md5sum
        block_size_factor: the file is read at chunks of size
            block_size_factor * md5.block_size,
        where md5.block_size is the block_size used internally by the
        hashlib module.

    Returns:
        a string with the hexdigest md5.

    Raises:
        No checks are done on the file, so if it doesn't exists it may
        raise IOError.
    """
    md5 = hashlib.md5()
    with open(filename,'rb') as f:
        # I read 128 bytes at a time until it returns the empty string b''
        for chunk in iter(
            lambda: f.read(block_size_factor*md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def get_pseudo_from_md5(md5str):
    """
    Checks if a pseudopotential with given md5sum string is already
    present in the database.
    
    Note:
        It only checks those potentials which have a (correctly set)
        'md5sum' attribute in the AttrTxt table.
        
    Args:
        md5str: the md5sum string

    Returns:
        None if no pseudopotential with given md5sum exists,
        a Potential django object otherwise (the first found in the
        table). A warning is issued if more than one pseudopotential
        with given md5sum is found.
    """
    matching_md5 = PotentialAttrTxtVal.objects.filter(attr__title='md5sum',
                                                      val=md5str)
    matching_pot = [i.item for i in matching_md5]
    if len(matching_pot) > 1:
        logger.warning('More than one pseudo found with md5sum '
                       '"{}".'.format(md5str))
    if len(matching_pot) == 0:
        return None
    else:
        return matching_pot[0]

def add_pseudo_file(filename,description,element_symbols,
                    pot_type,pot_status,user):
    """
    Adds a pseudopotential file to the DB and to the local repository.

    As a first step, the function checks that if a pseudo with the same
    md5sum is already present (this is done in the DB, so this is fast).
    If a potential is found, the first match is returned.
    Otherwise, the pseudopotential file is copied to the local repository,
    and a new entry is added to the database table Potential.

    Note that the 'title' field of the Potential entry corresponds
    to the filename in the 'potentials' section of the aida local repository.
    This title is generated starting from the provided filename, using the
    following rule:
    * the basename (without extensions) is retrieved
    * the system checks if the string begins with the following pattern
      (case insensitive):
      - a list of elements associated to this pseudo, separated by underscores
        if more than one element is present (in this case elements are sorted
        alphabetically)
      - one of the following characters: '-', '_', '.'
      (For instance, if it is a pseudo for Ba, it checks if it starts with 
       one of the following: 'Ba-', 'Ba_', 'Ba.')
      If not, the string is prepended to the basename (with capitalized 
      element names), with a dot as separator
    * Any characters that are not numbers, letters, or one of ._- are stripped
      out
    * The same stripping is applied to the original extension of the filename
      provided in input
    * The extension is trimmed to 10 characters, the basename to 230
    * Names of the form "basename-NNN.ext" are tried until an 'empty' name
      is found, where
      - basename and ext are the basename and the extension obtained after
        the procedure above
      - NNN is an integer number starting from the number of items in the
        Potential table that start with the basename, and increasing 
        until an unused name is found.

    Note however that one should always check again the title provided 
    in the return value, because if a pseudo with the same md5sum is found,
    this pseudo is returned (and the filename of the existing pseudo does not
    have any relationship with the provided filename, in general).

    Args:
        filename: the name of the pseudopotential file on the disk
        description: The description to be added to the 'description' field
            of the database
        element_symbols: a list of strings, one for each of the elements to 
            which this pseudopotential refers. Typically, it is a list of
            one element only, as ['Si']. They must be present in the
            Element table.
        pot_type: a django object of the PotentialType model, to be associated
            to this pseudo
        pot_status: a django object of the PotentialStatus model, to be
            associated to this pseudo
        user: a django user object to be associated to this pseudo

    Returns: a django object of the Potential model pointing to the pseudo.

    Raises:
        ValidationError: if an element provided in the element_symbols
            list is not found in the Element table
        IOError, OSError: possible errors while accessing/copying the files
    """
    # Check if all elements exist in the Element table.
    # If everything goes smoothly, add elements as M2M fields later on
    # (once the pseudopotential has been added to the Potential table)
    try:
        elements = [Element.objects.get(title=el) for el in element_symbols]
    except ObjectDoesNotExist as e:
        raise ValidationError("On of the elements provided in elements_symbols"
                              "does not exist in the Element table.")
            
    # Calculate md5sum, compare with database, and return the existing
    # object, if any
    md5str = md5_file(filename)
    existing_pot = get_pseudo_from_md5(md5str)
    if existing_pot:
        return existing_pot
    else:
        # Create an unique title name
        basename, ext = os.path.splitext(os.path.basename(filename))

        # Check that the title starts with the symbol followed by one
        # of the following symbols: ['.','_','-'], otherwise prepend
        # symbol+dot
        # If there are more than one symbol, I sort them alphabetically
        # and I join them by underscores
        # In this way, I am also sure that I don't get an empty string
        # when, in the next step, I remove the 'bad' characters
        prepend_str = "_".join(sorted(
                el.capitalize() for el in element_symbols))
        if not any(basename.lower().startswith((prepend_str+sep).lower())
                    for sep in ['.', '_', '-']):
            basename = prepend_str + '.' + basename

        # Remove 'bad' characters
        leave_only_allowed_chars = re.compile('[^0-9A-Za-z._-]+')
        basename = leave_only_allowed_chars.sub('',basename)
        ext = leave_only_allowed_chars.sub('',ext)
        # I cut the extension to length 10 (if it is longer).
        # Note that ext contains also the extension separator
        ext = ext[:10]      

        # cut the string if it is too long; I leave enough space
        # for a reasonably-big number + extension
        basename = basename[:230]

        # I render the name unique appending a dash and a number
        existing_names = [pot.title.lower() for pot in 
            Potential.objects.filter(title__istartswith=basename)]
        idx=len(existing_names)
        while True:
            title = basename + "-{0}{1}".format(idx,ext)
            if title.lower() not in existing_names:
                break
            idx=idx+1

        # Copy the file in the repository
        # Due to overwrite==False, an exception is raised if the
        # file already exists or cannot be copied, so that we
        # never create the entry in the Potential table if an error 
        # occurs
        copy_to_repo(source=filename, section='potentials',
                     filename=title,overwrite=False)

        # Create the new entry in the potential table
        newpot = Potential.objects.create(title=title,
                 description=description, user=user,
                 type=pot_type,status=pot_status)

        # Add the M2M links to the elements
        for el in elements:
            newpot.element.add(el)
        
        newpot.save()

        # Store the md5sum attribute
        md5sum_attr, was_created = PotentialAttrTxt.objects.get_or_create(
            title='md5sum')
        if was_created:
            md5sum_attr.description=('md5sum string of the corresponding '
                'potential file stored in the local repository.')
        PotentialAttrTxtVal.objects.create(val=md5str,item=newpot,
            attr=md5sum_attr)

        return newpot
        
                                         
        
