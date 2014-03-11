"""
This module manages the UPF pseudopotentials in the local repository.
"""
from aiida.orm.data.singlefile import SinglefileData
import re

_upfversion_regexp = re.compile(
    r"""
    \s*<UPF\s+version\s*="
       (?P<version>.*)">
   """, re.VERBOSE)

_element_v1_regexp = re.compile(
    r"""
    ^
    \s*
    (?P<element_name>[a-zA-Z]{1,2})
    \s+
    Element
    \s*
    $
   """, re.VERBOSE)

_element_v2_regexp = re.compile(
    r"""
    \s*
    element\s*=\s*(?P<quote_symbol>['"])\s*
    (?P<element_name>[a-zA-Z]{1,2})\s*
    (?P=quote_symbol).*
   """, re.VERBOSE)


def get_upf_from_family(family_name, element):
    """
    Given a family name (a group in the DB) and the element name, return
    the corresponding UpfData node.
    
    :raise MultipleObjectsError: if more than one UPF for the given element is
            found in the group.
    :raise NotExistent: if no UPF for the given element are found in the group.
    """
    from aiida.djsite.db.models import DbGroup
    from django.core.exceptions import ObjectDoesNotExist
    from aiida.common.exceptions import NotExistent, MultipleObjectsError
    
    try:
        DbGroup.objects.get(name=family_name)
    except ObjectDoesNotExist:
        raise NotExistent("Family named {} does not exist".format(family_name))
    
    match = UpfData.query(dbgroups__name=family_name,
                           dbattributes__key="element",
                           dbattributes__tval=element)
    if len(match) == 0:
        raise NotExistent("No UPF for element {} found in family {}".format(
            element, family_name))
    elif len(match) > 1:
        raise MultipleObjectsError("More than one UPF for element {} found in "
                                   "family {}".format(
            element, family_name))
    else:
        return match[0]


def upload_upf_family(folder, group_name, group_description,
                        stop_if_existing=True):
    """
    Upload a set of UPF files in a given group.
    
    Args:
        folder: a path containing all UPF files to be added.
            Only files ending in .UPF (case-insensitive) are considered. 
        group_name: the name of the group to create. If it exists and is
            non-empty, a UniquenessError is raised.
        group_description: a string to be set as the group description.
            Overwrites previous descriptions, if the group was existing.
        stop_if_existing: if True, check for the md5 of the files and, if the
            file already exists in the DB, raises a MultipleObjectsError.
            If False, simply adds the existing UPFData node to the group.
    """
    import os
    import aiida.common
    from aiida.common import aiidalogger
    from aiida.djsite.db.models import DbGroup
    from aiida.common.exceptions import UniquenessError, MultipleObjectsError
    from aiida.djsite.utils import get_automatic_user

    if not os.path.isdir(folder):
        raise ValueError("folder must be a directory")
    
    # only files, and only those ending with .upf or .UPF;
    # go to the real file if it is a symlink
    files = [os.path.realpath(os.path.join(folder,i))
             for i in os.listdir(folder) if 
             os.path.isfile(os.path.join(folder,i)) and 
             i.lower().endswith('.upf')]
    
    nfiles = len(files)
    
    group,group_created = DbGroup.objects.get_or_create(
        name=group_name, defaults={'user': get_automatic_user()})
    if len(group.dbnodes.all()) != 0:
        raise UniquenessError("DbGroup with name {} already exists and is "
                              "non-empty".format(group_name))
    group.description = group_description
    # note that the group will be saved only after the check on upf uniqueness
    
    pseudo_and_created = []
    
    for f in files:
        md5sum = aiida.common.utils.md5_file(f)
        existing_upf = UpfData.query(dbattributes__key="md5",
                                     dbattributes__tval = md5sum)
        
        if len(existing_upf) == 0:
            # return the upfdata instances, not stored
            pseudo, created = UpfData.get_or_create(f, use_first = True,
                                                    store_upf = False)
            # to check whether only one upf per element exists
            # NOTE: actually, created has the meaning of "to_be_created"
            pseudo_and_created.append( (pseudo,created) )
        else:
            if stop_if_existing:
                raise ValueError("A UPF with identical MD5 to "+f+" cannot be added with stop_if_existing")
            pseudo = existing_upf[0]
            pseudo_and_created.append( (pseudo,False) )
    
    # check whether pseudo are unique per element
    elements = [ i[0].element for i in pseudo_and_created ]
    if not len(pseudo_and_created) == len( 
                            set(elements) ):
        duplicates = set([x for x in elements if elements.count(x) > 1])
        duplicates_string = ", ".join(i for i in duplicates)
        raise UniquenessError("More than one UPF found for the elements: " +
                              duplicates_string+".")
    
    # save the group in the database
    if not group_created: # enforce the user if the group was empty and already there
        group.user = get_automatic_user()
        group.save()
    
    # save the upf in the database, and add them to group    
    for pseudo,created in pseudo_and_created:
        if created:
            pseudo.store()
                
        group.dbnodes.add(pseudo.dbnode)

        if created:
            aiidalogger.debug("New node {} created for file {}".format(
               pseudo.uuid, pseudo.filename))
        else:
            aiidalogger.debug("Reusing node {} for file {}".format(
               pseudo.uuid, pseudo.filename))
    
    nuploaded = len([i for i in pseudo_and_created if i[1]])
     
    return nfiles, nuploaded
        
            
def parse_upf(fname, check_filename = True):
    """
    Try to get relevant information from the UPF. For the moment, only the 
    element name. Note that even UPF v.2 cannot be parsed with the XML minidom!
    (e.g. due to the & characters in the human-readable section).
    
    If check_filename is True, raise a ParsingError exception if the filename 
    does not start with the element name.
    """
    import os
    
    from aiida.common.exceptions import ParsingError
    from aiida.common import aiidalogger
    # TODO: move these data in a 'chemistry' module
    from aiida.orm.data.structure import _valid_symbols

    parsed_data = {}

    with open(fname) as f:
        first_line = f.readline().strip()
        match = _upfversion_regexp.match(first_line)
        if match:
            version = match.group('version')
            aiidalogger.debug("Version found: {} for file {}".format(
                version, fname))
        else:
            aiidalogger.debug("Assuming version 1 for file {}".format(fname))
            version = "1"
        
        parsed_data['version'] = version
        try:
            version_major = int(version.partition('.')[0])
        except ValueError:
            # If the version string does not start with a dot, fallback
            # to version 1
            aiidalogger.debug("Falling back to version 1 for file {}, "
                              "version string '{}' unrecognized".format(
                                  fname, version))
            version_major = 1
        
        element = None
        if version_major == 1:
            for l in f:
                match = _element_v1_regexp.match(l.strip())
                if match:
                    element = match.group('element_name')
                    break
        else: # all versions > 1
            for l in f:
                match = _element_v2_regexp.match(l.strip())
                if match: 
                    element = match.group('element_name')
                    break
            
        if element is None:
            raise ParsingError("Unable to find the element of UPF {}".format(
                fname))
        element = element.capitalize()
        if element not in _valid_symbols:
            raise ParsingError("Unknown element symbol {} for file {}".format(
                element, fname))
        if check_filename:
            if not os.path.basename(fname).lower().startswith(
                  element.lower()):
                raise ParsingError("Filename {0} was recognized for element "
                                   "{1}, but the filename does not start "
                                   "with {1}".format(fname, element))

        parsed_data['element'] = element


    return parsed_data
    
#def test_parser(folder):
#    import os
#    from aiida.common.exceptions import ParsingError
#    
#    for fn in os.listdir(folder):
#        if os.path.isfile(fn) and fn.lower().endswith('.upf'):
#            try:
#                data = parse_upf(os.path.join(folder, fn))
#            except ParsingError as e:
#                print ">>>>>>>>>>>>>>>> ERROR: %s" % e.message

                

class UpfData(SinglefileData): 
    """
    Function not yet documented.
    """
    
    @classmethod
    def get_or_create(cls,filename,use_first = False,store_upf=True):
        """
        Pass the same parameter of the init; if a file with the same md5
        is found, that UpfData is returned. 
        
        :param filename: an absolute filename on disk
        :param use_first: if False (default), raise an exception if more than \
                one potential is found.\
                If it is True, instead, use the first available pseudopotential.
        :param bool store_upf: If false, the UpfData objects are not stored in 
                the database. default=True.
        :return (upf, created): where upf is the UpfData object, and create is either\
            True if the object was created, or False if the object was retrieved\
            from the DB.
        """
        import aiida.common.utils
        import os
        from aiida.common.exceptions import ParsingError
        
        if not os.path.abspath(filename):
            raise ValueError("filename must be an absolute path")
        md5 = aiida.common.utils.md5_file(filename)

        # already raises a ParsingError if the file cannot be recognized
        parsed_data = parse_upf(filename)
        try:
            element = parsed_data['element']
        except KeyError:
            raise ParsingError("No 'element' parsed in the UPF file {}".format(
                filename))
        
        pseudos = cls.from_md5(md5)
        if len(pseudos) == 0:
            if store_upf:
                instance = cls(filename=filename, element=element).store()
                return (instance, True)
            else:
                instance = cls(filename=filename, element=element)
                return (instance, True)
        else:
            filtered_pseudos = []
            for p in pseudos:
                if (p.get_attr("element", None) == element):
                    filtered_pseudos.append(p)
            if len(filtered_pseudos) == 0:
                raise ValueError("At least one UPF found with the same md5, "
                    "but the element is different. "
                    "pks={}".format(
                        ",".join([str(i.pk) for i in pseudos])))
            elif len(filtered_pseudos) > 1:
                if use_first:
                    return (filtered_pseudos[0], False)
                else:
                    raise ValueError("More than one copy of a pseudopotential "
                        "with the same MD5 has been found in the "
                        "DB. pks={}".format(
                          ",".join([str(i.pk) for i in filtered_pseudos])))
            else:        
                return (filtered_pseudos[0], False)

    @classmethod
    def from_md5(cls, md5):
        """
        Return a list of all UPF pseudopotentials that match a given MD5 hash.
        
        Note that the hash has to be stored in a _md5 attribute, otherwise
        the pseudo will not be found.
        """
        queryset = cls.query(dbattributes__key='md5', dbattributes__tval=md5)
        return list(queryset)


    def __init__(self, **kwargs):
        import aiida.common.utils
        
        
        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            if kwargs:
                raise TypeError("You cannot pass other arguments if one of"
                                "the arguments is uuid")
            super(UpfData,self).__init__(uuid=uuid)
            return
        
        super(UpfData,self).__init__()
        
        try:
            filename = kwargs.pop("filename")
        except KeyError:
            raise TypeError("You have to specify the filename")
        try:
            element = kwargs.pop("element")
        except KeyError:
            raise TypeError("You have to specify the element to which this "
                            "pseudo refers to")
                    
        self.add_path(filename)
        md5sum = aiida.common.utils.md5_file(self.get_file_abs_path())
        
        self.set_attr('element', str(element))
        self.set_attr('md5', md5sum)

    @property
    def element(self):
        return self.get_attr('element')

    @property
    def filename(self):
        return self.get_attr('filename')

    def validate(self):
        from aiida.common.exceptions import ValidationError

        super(UpfData,self).validate()
        
        try:
            self.get_attr('element')
        except AttributeError:
            raise ValidationError("attribute 'element' not set.")

        try:
            self.get_attr('md5')
        except AttributeError:
            raise ValidationError("attribute 'md5' not set.")

    @classmethod
    def get_upf_groups(self,filter_elements=None):
        """
        Return all groups that contains UpfDatas
            
        :param filter_elements: A list of strings. 
               If present, returns only the groups that contains one Upf for
               every element present in the list. Default=None
        """
        # Get all groups that contain at least one upf
        from django.db.models import Q
        from aiida.djsite.db.models import DbGroup
        
        q_object = Q(dbnodes__type__startswith=self._plugin_type_string)
        groups = DbGroup.objects.filter(q_object)
        
        if filter_elements is not None:
            # add a filter to the previous query, one f per element
            # to get only groups with desired element
            for el in filter_elements:
                groups = groups.filter( dbnodes__dbattributes__key='element',
                                 dbnodes__dbattributes__tval=el.capitalize() )
            
        # find all groups matching the desired filters
        groups = groups.distinct().order_by("name")
            
        return groups
        