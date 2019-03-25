# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module manages the UPF pseudopotentials in the local repository.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import io
import re

import six

import aiida.orm.users
from aiida.common.lang import classproperty
from .singlefile import SinglefileData
from aiida.orm import GroupTypeString

__all__ = ('UpfData',)


UPFGROUP_TYPE = GroupTypeString.UPFGROUP_TYPE

_upfversion_regexp = re.compile(
    r"""
    \s*<UPF\s+version\s*="
       (?P<version>.*)">
   """, re.VERBOSE)

_element_v1_regexp = re.compile(
    r"""
    (?P<element_name>[a-zA-Z]{1,2})
    \s+
    Element
   """, re.VERBOSE)

_element_v2_regexp = re.compile(
    r"""
    \s*
    element\s*=\s*(?P<quote_symbol>['"])\s*
    (?P<element_name>[a-zA-Z]{1,2})\s*
    (?P=quote_symbol)
   """, re.VERBOSE)


def get_pseudos_from_structure(structure, family_name):
    """
    Given a family name (a UpfFamily group in the DB) and a AiiDA
    structure, return a dictionary associating each kind name with its
    UpfData object.

    :raise aiida.common.MultipleObjectsError: if more than one UPF for the same element is
       found in the group.
    :raise aiida.common.NotExistent: if no UPF for an element in the group is
       found in the group.
    """
    from aiida.common.exceptions import NotExistent, MultipleObjectsError

    family_pseudos = {}
    family = UpfData.get_upf_group(family_name)
    for node in family.nodes:
        if isinstance(node, UpfData):
            if node.element in family_pseudos:
                raise MultipleObjectsError(
                    "More than one UPF for element {} found in "
                    "family {}".format(node.element, family_name))
            family_pseudos[node.element] = node

    pseudo_list = {}
    for kind in structure.kinds:
        symbol = kind.symbol
        try:
            pseudo_list[kind.name] = family_pseudos[symbol]
        except KeyError:
            raise NotExistent("No UPF for element {} found in family {}".format(
                symbol, family_name))

    return pseudo_list


def get_pseudos_dict(structure, family_name):
    """
    Get a dictionary of {kind: pseudo} for all the elements within the given
    structure using a the given pseudo family name.

    :param structure: The structure that will be used.
    :param family_name: the name of the group containing the pseudos
    """
    from collections import defaultdict

    # A dict {kind_name: pseudo_object}
    kind_pseudo_dict = get_pseudos_from_structure(structure, family_name)

    # We have to group the species by pseudo, I use the pseudo PK
    # pseudo_dict will just map PK->pseudo_object
    pseudo_dict = {}
    # Will contain a list of all species of the pseudo with given PK
    pseudo_species = defaultdict(list)

    for kindname, pseudo in kind_pseudo_dict.items():
        pseudo_dict[pseudo.pk] = pseudo
        pseudo_species[pseudo.pk].append(kindname)

    pseudos = {}
    for pseudo_pk in pseudo_dict:
        pseudo = pseudo_dict[pseudo_pk]
        kinds = pseudo_species[pseudo_pk]
        for kind in kinds:
            pseudos[kind] = pseudo

    return pseudos


def upload_upf_family(folder, group_label, group_description,
                      stop_if_existing=True):
    """
    Upload a set of UPF files in a given group.

    :param folder: a path containing all UPF files to be added.
        Only files ending in .UPF (case-insensitive) are considered.
    :param group_label: the name of the group to create. If it exists and is
        non-empty, a UniquenessError is raised.
    :param group_description: a string to be set as the group description.
        Overwrites previous descriptions, if the group was existing.
    :param stop_if_existing: if True, check for the md5 of the files and,
        if the file already exists in the DB, raises a MultipleObjectsError.
        If False, simply adds the existing UPFData node to the group.
    """
    import os

    from aiida import orm
    from aiida.common import AIIDA_LOGGER
    from aiida.common.exceptions import UniquenessError
    from aiida.common.files import md5_file

    if not os.path.isdir(folder):
        raise ValueError("folder must be a directory")

    # only files, and only those ending with .upf or .UPF;
    # go to the real file if it is a symlink
    files = [os.path.realpath(os.path.join(folder, i))
             for i in os.listdir(folder) if
             os.path.isfile(os.path.join(folder, i)) and
             i.lower().endswith('.upf')]

    nfiles = len(files)

    automatic_user = orm.User.objects.get_default()
    group, group_created = orm.Group.objects.get_or_create(label=group_label, type_string=UPFGROUP_TYPE,
                                                           user=automatic_user)

    if group.user.email != automatic_user.email:
        raise UniquenessError("There is already a UpfFamily group with label {}"
                              ", but it belongs to user {}, therefore you "
                              "cannot modify it".format(group_label,
                                                        group.user.email))

    # Always update description, even if the group already existed
    group.description = group_description

    # NOTE: GROUP SAVED ONLY AFTER CHECKS OF UNICITY

    pseudo_and_created = []

    for f in files:
        md5sum = md5_file(f)
        qb = orm.QueryBuilder()
        qb.append(UpfData, filters={'attributes.md5': {'==': md5sum}})
        existing_upf = qb.first()

        if existing_upf is None:
            # return the upfdata instances, not stored
            pseudo, created = UpfData.get_or_create(f, use_first=True,
                                                    store_upf=False)
            # to check whether only one upf per element exists
            # NOTE: actually, created has the meaning of "to_be_created"
            pseudo_and_created.append((pseudo, created))
        else:
            if stop_if_existing:
                raise ValueError(
                    "A UPF with identical MD5 to "
                    " {} cannot be added with stop_if_existing"
                    "".format(f)
                )
            existing_upf = existing_upf[0]
            pseudo_and_created.append((existing_upf, False))

    # check whether pseudo are unique per element
    elements = [(i[0].element, i[0].md5sum) for i in pseudo_and_created]
    # If group already exists, check also that I am not inserting more than
    # once the same element
    if not group_created:
        for aiida_n in group.nodes:
            # Skip non-pseudos
            if not isinstance(aiida_n, UpfData):
                continue
            elements.append((aiida_n.element, aiida_n.md5sum))

    elements = set(elements)  # Discard elements with the same MD5, that would
    # not be stored twice
    elements_names = [e[0] for e in elements]

    if not len(elements_names) == len(set(elements_names)):
        duplicates = set([x for x in elements_names
                          if elements_names.count(x) > 1])
        duplicates_string = ", ".join(i for i in duplicates)
        raise UniquenessError("More than one UPF found for the elements: " +
                              duplicates_string + ".")

        # At this point, save the group, if still unstored
    if group_created:
        group.store()

    # save the upf in the database, and add them to group
    for pseudo, created in pseudo_and_created:
        if created:
            pseudo.store()

            AIIDA_LOGGER.debug("New node {} created for file {}".format(
                pseudo.uuid, pseudo.filename))
        else:
            AIIDA_LOGGER.debug("Reusing node {} for file {}".format(
                pseudo.uuid, pseudo.filename))

    # Add elements to the group all togetehr
    group.add_nodes([pseudo for pseudo, created in pseudo_and_created])

    nuploaded = len([_ for _, created in pseudo_and_created if created])

    return nfiles, nuploaded


def parse_upf(fname, check_filename=True):
    """
    Try to get relevant information from the UPF. For the moment, only the
    element name. Note that even UPF v.2 cannot be parsed with the XML minidom!
    (e.g. due to the & characters in the human-readable section).

    If check_filename is True, raise a ParsingError exception if the filename
    does not start with the element name.
    """
    import os

    from aiida.common.exceptions import ParsingError
    from aiida.common import AIIDA_LOGGER
    # TODO: move these data in a 'chemistry' module
    from aiida.orm.nodes.data.structure import _valid_symbols

    parsed_data = {}

    try:
        upf_contents = fname.read()
        fname = fname.name
    except AttributeError:
        with io.open(fname, encoding='utf8') as f:
            upf_contents = f.read()

    match = _upfversion_regexp.search(upf_contents)
    if match:
        version = match.group('version')
        AIIDA_LOGGER.debug("Version found: {} for file {}".format(
            version, fname))
    else:
        AIIDA_LOGGER.debug("Assuming version 1 for file {}".format(fname))
        version = "1"

    parsed_data['version'] = version
    try:
        version_major = int(version.partition('.')[0])
    except ValueError:
        # If the version string does not contain a dot, fallback
        # to version 1
        AIIDA_LOGGER.debug("Falling back to version 1 for file {}, "
                           "version string '{}' unrecognized".format(
            fname, version))
        version_major = 1

    element = None
    if version_major == 1:
        match = _element_v1_regexp.search(upf_contents)
        if match:
            element = match.group('element_name')
    else:  # all versions > 1
        match = _element_v2_regexp.search(upf_contents)
        if match:
            element = match.group('element_name')

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


class UpfData(SinglefileData):
    """
    Function not yet documented.
    """

    def __init__(self, file=None, source=None, **kwargs):

        super(UpfData, self).__init__(file, **kwargs)

        if source is not None:
            self.set_source(source)

    @classmethod
    def get_or_create(cls, filepath, use_first=False, store_upf=True):
        """
        Pass the same parameter of the init; if a file with the same md5
        is found, that UpfData is returned.

        :param filepath: an absolute filepath on disk
        :param use_first: if False (default), raise an exception if more than \
                one potential is found.\
                If it is True, instead, use the first available pseudopotential.
        :param bool store_upf: If false, the UpfData objects are not stored in
                the database. default=True.
        :return (upf, created): where upf is the UpfData object, and create is either\
            True if the object was created, or False if the object was retrieved\
            from the DB.
        """
        import os
        from aiida.common.files import md5_file

        if not os.path.isabs(filepath):
            raise ValueError("filepath must be an absolute path")
        md5 = md5_file(filepath)

        pseudos = cls.from_md5(md5)
        if len(pseudos) == 0:
            if store_upf:
                instance = cls(file=filepath).store()
                return (instance, True)
            else:
                instance = cls(file=filepath)
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

    @classproperty
    def upffamily_type_string(cls):
        return UPFGROUP_TYPE

    def store(self, *args, **kwargs):
        """
        Store the node, reparsing the file so that the md5 and the element
        are correctly reset.
        """
        from aiida.common.exceptions import ParsingError
        from aiida.common.files import md5_from_filelike

        if self.is_stored:
            return self

        with self.open(mode='r') as handle:
            parsed_data = parse_upf(handle)

        # Open in binary mode which is required for generating the md5 checksum
        with self.open(mode='rb') as handle:
            md5 = md5_from_filelike(handle)

        try:
            element = parsed_data['element']
        except KeyError:
            raise ParsingError("No 'element' parsed in the UPF file {};"
                               " unable to store".format(self.filename))

        self.set_attribute('element', str(element))
        self.set_attribute('md5', md5)

        return super(UpfData, self).store(*args, **kwargs)

    @classmethod
    def from_md5(cls, md5):
        """
        Return a list of all UPF pseudopotentials that match a given MD5 hash.

        Note that the hash has to be stored in a _md5 attribute, otherwise
        the pseudo will not be found.
        """
        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        qb.append(cls, filters={'attributes.md5': {'==': md5}})
        return [_ for [_] in qb.all()]

    def set_file(self, file):
        """
        I pre-parse the file to store the attributes.
        """
        from aiida.common.exceptions import ParsingError
        from aiida.common.files import md5_file, md5_from_filelike

        parsed_data = parse_upf(file)

        try:
            md5sum = md5_file(file)
        except TypeError:
            md5sum = md5_from_filelike(file)

        try:
            element = parsed_data['element']
        except KeyError:
            raise ParsingError("No 'element' parsed in the UPF file {}; unable to store".format(self.filename))

        super(UpfData, self).set_file(file)

        self.set_attribute('element', str(element))
        self.set_attribute('md5', md5sum)

    def get_upf_family_names(self):
        """Get the list of all upf family names to which the pseudo belongs."""
        from aiida.orm import Group
        from aiida.orm import QueryBuilder

        query = QueryBuilder()
        query.append(Group, filters={'type':{'==':self.upffamily_type_string}}, tag='group', project='name')
        query.append(UpfData, filters={'id': {'==':self.id}}, with_group='group')
        return [ _[0] for _ in query.all()]

    @property
    def element(self):
        return self.get_attribute('element', None)

    @property
    def md5sum(self):
        return self.get_attribute('md5', None)

    def _validate(self):
        from aiida.common.exceptions import ValidationError
        from aiida.common.files import md5_from_filelike

        super(UpfData, self)._validate()

        with self.open(mode='r') as handle:
            parsed_data = parse_upf(handle)

        # Open in binary mode which is required for generating the md5 checksum
        with self.open(mode='rb') as handle:
            md5 = md5_from_filelike(handle)

        try:
            element = parsed_data['element']
        except KeyError:
            raise ValidationError("No 'element' could be parsed in the UPF "
                                  "file {}".format(upf_abspath))

        try:
            attr_element = self.get_attribute('element')
        except AttributeError:
            raise ValidationError("attribute 'element' not set.")

        try:
            attr_md5 = self.get_attribute('md5')
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
    def get_upf_group(cls, group_label):
        """
        Return the UpfFamily group with the given name.
        """
        from aiida.orm import Group

        return Group.get(label=group_label, type_string=cls.upffamily_type_string)

    @classmethod
    def get_upf_groups(cls, filter_elements=None, user=None):
        """
        Return all names of groups of type UpfFamily, possibly with some filters.

        :param filter_elements: A string or a list of strings.
               If present, returns only the groups that contains one Upf for
               every element present in the list. Default=None, meaning that
               all families are returned.
        :param user: if None (default), return the groups for all users.
               If defined, it should be either a DbUser instance, or a string
               for the username (that is, the user email).
        """
        from aiida.orm import Group
        from aiida.orm import QueryBuilder
        from aiida.orm import User

        query = QueryBuilder()
        filters = {'type': {'==': cls.upffamily_type_string}}

        query.append(Group, filters=filters, tag='group', project='*')

        if user:
            query.append(User, filters={'email':{'==':user}}, with_group='group')

        if isinstance(filter_elements, six.string_types):
            filter_elements = [filter_elements]

        if filter_elements is not None:
            actual_filter_elements = [_ for _ in filter_elements]
            query.append(UpfData, filters={'attributes.element':{'in': filter_elements}}, with_group='group')

        query.order_by({Group:{'id':'asc'}}) 
        return [_[0] for _ in query.all()]
