"""
This module manages the UPF pseudopotentials in the local repository.
"""
from aiida.orm.data.singlefile import SinglefileData
import re

UPFGROUP_TYPE = 'data.upf.family'

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

def get_pseudos_from_structure(structure, family_name):       
    pseudo_list = {}
    for kind in structure.kinds:
        symbol = kind.symbol
        # Will raise the correct exception if not found, or too many found
        pseudo_list[kind.name] = get_upf_from_family(family_name, symbol)

    return pseudo_list

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
        DbGroup.objects.get(name=family_name, type=UPFGROUP_TYPE)
    except ObjectDoesNotExist:
        raise NotExistent("UPF family named {} does not exist".format(family_name))
    
    match = UpfData.query(dbgroups__name=family_name,
                          dbgroups__type=UPFGROUP_TYPE,
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
    
    from django.core.exceptions import ObjectDoesNotExist
    
    import aiida.common
    from aiida.common import aiidalogger
    from aiida.djsite.db.models import DbGroup, DbNode
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
    
    try:
        group = DbGroup.objects.get(name=group_name, type=UPFGROUP_TYPE)
        group_created = False
    except ObjectDoesNotExist:
        group = DbGroup(name=group_name, type=UPFGROUP_TYPE,
                        user=get_automatic_user())
        group_created = True
        
    if group.user != get_automatic_user():
        raise UniquenessError("There is already a UpfFamily group with name {}"
                              ", but it belongs to user {}, therefore you "
                              "cannot modify it".format(group_name,
                                                        group.user.email))
         
    # Always update description, even if the group already existed
    group.description = group_description

    # NOTE: GROUP SAVED ONLY AFTER CHECKS OF UNICITY
    
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
    elements = [ (i[0].element, i[0].md5sum) for i in pseudo_and_created ]
    # If group already exists, check also that I am not inserting more than
    # once the same element
    if group.pk is not None:
        for n in group.dbnodes.distinct().all():
            aiida_n = n.get_aiida_class()
            # Skip non-pseudos
            if not isinstance(aiida_n, UpfData):
                continue
            elements.append((aiida_n.element, aiida_n.md5sum))
    
    elements = set(elements) # Discard elements with the same MD5, that would
                             # not be stored twice
    elements_names = [e[0] for e in elements]
       
    if not len(elements_names) == len(set(elements_names) ):
        duplicates = set([x for x in elements_names
                          if elements_names.count(x) > 1])
        duplicates_string = ", ".join(i for i in duplicates)
        raise UniquenessError("More than one UPF found for the elements: " +
                              duplicates_string+".")    
    
    # At this point, save the group
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
        
        pseudos = cls.from_md5(md5)
        if len(pseudos) == 0:
            if store_upf:
                instance = cls(file=filename).store()
                return (instance, True)
            else:
                instance = cls(file=filename)
                return (instance, True)
        else:
            if len(pseudos) > 1:
                if use_first:
                    return (pseudos[0], False)
                else:
                    raise ValueError("More than one copy of a pseudopotential "
                        "with the same MD5 has been found in the "
                        "DB. pks={}".format(
                          ",".join([str(i.pk) for i in pseudos])))
            else:        
                return (pseudos[0], False)

    def store(self):
        """
        Store the node, reparsing the file so that the md5 and the element 
        are correctly reset.
        """
        from aiida.common.exceptions import ParsingError, ValidationError
        import aiida.common.utils

        upf_abspath = self.get_file_abs_path()
        if not upf_abspath:
            raise ValidationError("No valid UPF was passed!")

        parsed_data = parse_upf(upf_abspath)
        md5sum = aiida.common.utils.md5_file(upf_abspath)
        
        try:
            element = parsed_data['element']
        except KeyError:
            raise ParsingError("No 'element' parsed in the UPF file {};"
                               " unable to store".format(self.filename))
        
        self.set_attr('element', str(element))
        self.set_attr('md5', md5sum)

        return super(UpfData, self).store()


    @classmethod
    def from_md5(cls, md5):
        """
        Return a list of all UPF pseudopotentials that match a given MD5 hash.
        
        Note that the hash has to be stored in a _md5 attribute, otherwise
        the pseudo will not be found.
        """
        queryset = cls.query(dbattributes__key='md5', dbattributes__tval=md5)
        return list(queryset)

    def set_file(self, filename):
        """
        I pre-parse the file to store the attributes.
        """
        from aiida.common.exceptions import ParsingError
        import aiida.common.utils

        parsed_data = parse_upf(filename)
        md5sum = aiida.common.utils.md5_file(filename)
        
        try:
            element = parsed_data['element']
        except KeyError:
            raise ParsingError("No 'element' parsed in the UPF file {};"
                               " unable to store".format(self.filename))
        
        super(UpfData,self).set_file(filename)
            
        self.set_attr('element', str(element))
        self.set_attr('md5', md5sum)
        
    @property
    def element(self):
        return self.get_attr('element', None)
 
    @property
    def md5sum(self):
        return self.get_attr('md5', None)

    def validate(self):
        from aiida.common.exceptions import ValidationError, ParsingError
        import aiida.common.utils

        super(UpfData,self).validate()


        upf_abspath = self.get_file_abs_path()
        if not upf_abspath:
            raise ValidationError("No valid UPF was passed!")

        try:
            parsed_data = parse_upf(upf_abspath)
        except ParsingError:
            raise ValidationError("The file '{}' could not be "
                                  "parsed".format(upf_abspath))
        md5 = aiida.common.utils.md5_file(upf_abspath)
        
        try:
            element = parsed_data['element']
        except KeyError:
            raise ValidationError("No 'element' could be parsed in the UPF "
                                  "file {}".format(upf_abspath))
        
        try:
            attr_element = self.get_attr('element')
        except AttributeError:
            raise ValidationError("attribute 'element' not set.")

        try:
            attr_md5 = self.get_attr('md5')
        except AttributeError:
            raise ValidationError("attribute 'md5' not set.")

        if attr_element != element:
            raise ValidationError("Attribute 'element' says '{}' but '{}' was "
                                  "parsed instead.".format(
                    attr_element, element))

        if attr_md5 != md5:
            raise ValidationError("Attribute 'md5' says '{}' but '{}' was "
                                  "parsed instead.".format(
                    attr_md5, md5))

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
        
        #        q_object = Q(dbnodes__type__startswith=self._plugin_type_string)
        q_object = Q(type=UPFGROUP_TYPE)
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
        