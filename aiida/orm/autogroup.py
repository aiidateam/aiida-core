# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to manage the autogrouping functionality by ``verdi run``."""
import warnings

from aiida.common import exceptions, timezone
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.orm import GroupTypeString
from aiida.plugins import load_entry_point_from_string

CURRENT_AUTOGROUP = None

VERDIAUTOGROUP_TYPE = GroupTypeString.VERDIAUTOGROUP_TYPE.value


class Autogroup:
    """
    An object used for the autogrouping of objects.
    The autogrouping is checked by the Node.store() method.
    In the store(), the Node will check if CURRENT_AUTOGROUP is != None.
    If so, it will call Autogroup.is_to_be_grouped, and decide whether to put it in a group.
    Such autogroups are going to be of the VERDIAUTOGROUP_TYPE.

    The exclude/include lists, can have values 'all' if you want to include/exclude all classes.
    Otherwise, they are lists of strings like: calculation.quantumespresso.pw, data.array.kpoints, ...
    i.e.: a string identifying the base class, than the path to the class as in Calculation/Data -Factories
    """

    def __init__(self):
        """Initialize with defaults."""
        self.exclude = []
        self.exclude_with_subclasses = []
        self.include = ['all']
        self.include_with_subclasses = []

        now = timezone.now()
        gname = 'Verdi autogroup on ' + now.strftime('%Y-%m-%d %H:%M:%S')
        self.group_label = gname

    @staticmethod
    def validate(param, allow_all=True):
        """
        Used internally to verify the sanity of exclude, include lists

        :param param: should be a list of valid entrypoint strings
        """
        for string in param:
            if allow_all and string == 'all':
                continue
            load_entry_point_from_string(string)  # This will raise a MissingEntryPointError if invalid

    def get_exclude(self):
        """Return the list of classes to exclude from autogrouping."""
        return self.exclude

    def get_exclude_with_subclasses(self):
        """
        Return the list of classes to exclude from autogrouping.
        Will also exclude their derived subclasses
        """
        return self.exclude_with_subclasses

    def get_include(self):
        """Return the list of classes to include in the autogrouping."""
        return self.include

    def get_include_with_subclasses(self):
        """Return the list of classes to include in the autogrouping.
        Will also include their derived subclasses."""
        return self.include_with_subclasses

    def get_group_label(self):
        """Get the name of the group.
        If no group name was set, it will set a default one by itself."""
        return self.group_label

    def get_group_name(self):
        """Get the label of the group.
        If no group label was set, it will set a default one by itself.

        .. deprecated:: 1.1.0
            Will be removed in `v2.0.0`, use :py:meth:`.get_group_label` instead.
        """
        warnings.warn('function is deprecated, use `get_group_label` instead', AiidaDeprecationWarning)  # pylint: disable=no-member
        return self.get_group_label()

    def set_exclude(self, exclude):
        """Return the list of classes to exclude from autogrouping.

        :param exclude: a list of valid entry point strings (one of which could be the string 'all')
        """
        self.validate(exclude)
        if 'all' in self.get_include():
            if 'all' in exclude:
                raise exceptions.ValidationError('Cannot exclude and include all classes')
        self.exclude = exclude

    def set_exclude_with_subclasses(self, exclude):
        """
        Set the list of classes to exclude from autogrouping.
        Will also exclude their derived subclasses

        :param exclude: a list of valid entry point strings (one of which could be the string 'all')
        """
        self.validate(exclude)
        self.exclude_with_subclasses = exclude

    def set_include(self, include):
        """
        Set the list of classes to include in the autogrouping.

        :param include: a list of valid entry point strings (one of which could be the string 'all')
        """
        self.validate(include)
        if 'all' in self.get_exclude():
            if 'all' in include:
                raise exceptions.ValidationError('Cannot exclude and include all classes')

        self.include = include

    def set_include_with_subclasses(self, include):
        """
        Set the list of classes to include in the autogrouping.
        Will also include their derived subclasses.

        :param include: a list of valid entry point strings (one of which could be the string 'all')
        """
        self.validate(include)
        self.include_with_subclasses = include

    def set_group_label(self, label):
        """
        Set the label of the group to be created
        """
        if not isinstance(label, str):
            raise exceptions.ValidationError('group label must be a string')
        self.group_label = label

    def set_group_name(self, gname):
        """Set the name of the group.

        .. deprecated:: 1.1.0
            Will be removed in `v2.0.0`, use :py:meth:`.set_group_label` instead.
        """
        warnings.warn('function is deprecated, use `set_group_label` instead', AiidaDeprecationWarning)  # pylint: disable=no-member
        return self.set_group_label(label=gname)

    def is_to_be_grouped(self, the_class):
        """
        Return whether the given class has to be included in the autogroup according to include/exclude list

        :return (bool): True if the_class is to be included in the autogroup
        """
        # strings, including possibly 'all'
        include_exact = self.get_include()
        include_with_subclasses = self.get_include_with_subclasses()

        # actual classes, with 'all' stripped out
        include_exact_classes = tuple(
            load_entry_point_from_string(ep_string) for ep_string in include_exact if ep_string != 'all'
        )
        include_with_subclasses_classes = tuple(
            load_entry_point_from_string(ep_string) for ep_string in include_with_subclasses if ep_string != 'all'
        )

        if (
            'all' in include_exact or the_class in include_exact_classes or
            issubclass(the_class, include_with_subclasses_classes)
        ):
            # According to the include, this class should be included
            # strings, including possibly 'all'
            exclude_exact = self.get_exclude()
            exclude_with_subclasses = self.get_exclude_with_subclasses()

            # actual classes, with 'all' stripped out
            exclude_exact_classes = tuple(
                load_entry_point_from_string(ep_string) for ep_string in exclude_exact if ep_string != 'all'
            )
            exclude_with_subclasses_classes = tuple(
                load_entry_point_from_string(ep_string) for ep_string in exclude_with_subclasses if ep_string != 'all'
            )

            if (the_class not in exclude_exact_classes and not issubclass(the_class, exclude_with_subclasses_classes)):
                # If we are here, it's not excluded
                return True
            # If we're here, it's both in the include and in the exclude - exclude it
            return False
        # If we're here, the class is not in the include - return False
        return False
