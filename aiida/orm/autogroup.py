# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from aiida.common import timezone
from aiida.common.exceptions import ValidationError, MissingPluginError
from aiida.orm import GroupTypeString


current_autogroup = None

VERDIAUTOGROUP_TYPE = GroupTypeString.VERDIAUTOGROUP_TYPE

# TODO: make the Autogroup usable to the user, and not only to the verdi run

class Autogroup(object):
    """
    An object used for the autogrouping of objects.
    The autogrouping is checked by the Node.store() method.
    In the store(), the Node will check if current_autogroup is != None.
    If so, it will call Autogroup.is_to_be_grouped, and decide whether to put it in a group.
    Such autogroups are going to be of the VERDIAUTOGROUP_TYPE.

    The exclude/include lists, can have values 'all' if you want to include/exclude all classes.
    Otherwise, they are lists of strings like: calculation.quantumespresso.pw, data.array.kpoints, ...
    i.e.: a string identifying the base class, than the path to the class as in Calculation/Data -Factories
    """

    def _validate(self, param, is_exact=True):
        """
        Used internally to verify the sanity of exclude, include lists
        """
        from aiida.plugins import CalculationFactory, DataFactory

        for i in param:
            if not any([i.startswith('calculation'),
                        i.startswith('code'),
                        i.startswith('data'),
                        i == 'all',
            ]):
                raise ValidationError("Module not recognized, allow prefixes "
                                      " are: calculation, code or data")
        the_param = [i + '.' for i in param]

        factorydict = {'calculation': locals()['CalculationFactory'],
                       'data': locals()['DataFactory']}

        for i in the_param:
            base, module = i.split('.', 1)
            if base == 'code':
                if module:
                    raise ValidationError("Cannot have subclasses for codes")
            elif base == 'all':
                continue
            else:
                if is_exact:
                    try:
                        factorydict[base](module.rstrip('.'))
                    except MissingPluginError:
                        raise ValidationError("Cannot find the class to be excluded")
        return the_param

    def get_exclude(self):
        """Return the list of classes to exclude from autogrouping."""
        try:
            return self.exclude
        except AttributeError:
            return []

    def get_exclude_with_subclasses(self):
        """
        Return the list of classes to exclude from autogrouping.
        Will also exclude their derived subclasses
        """
        try:
            return self.exclude_with_subclasses
        except AttributeError:
            return []

    def get_include(self):
        """Return the list of classes to include in the autogrouping."""
        try:
            return self.include
        except AttributeError:
            return []

    def get_include_with_subclasses(self):
        """Return the list of classes to include in the autogrouping.
        Will also include their derived subclasses."""
        try:
            return self.include_with_subclasses
        except AttributeError:
            return []

    def get_group_name(self):
        """Get the name of the group.
        If no group name was set, it will set a default one by itself."""
        try:
            return self.group_name
        except AttributeError:
            now = timezone.now()
            gname = "Verdi autogroup on " + now.strftime("%Y-%m-%d %H:%M:%S")
            self.set_group_name(gname)
            return self.group_name

    def set_exclude(self, exclude):
        """Return the list of classes to exclude from autogrouping."""
        the_exclude_classes = self._validate(exclude)
        if self.get_include() is not None:
            if 'all.' in self.get_include():
                if 'all.' in the_exclude_classes:
                    raise ValidationError("Cannot exclude and include all classes")
        self.exclude = the_exclude_classes

    def set_exclude_with_subclasses(self, exclude):
        """
        Set the list of classes to exclude from autogrouping.
        Will also exclude their derived subclasses
        """
        the_exclude_classes = self._validate(exclude, is_exact=False)
        self.exclude_with_subclasses = the_exclude_classes

    def set_include(self, include):
        """
        Set the list of classes to include in the autogrouping.
        """
        the_include_classes = self._validate(include)
        if self.get_exclude() is not None:
            if 'all.' in self.get_exclude():
                if 'all.' in the_include_classes:
                    raise ValidationError("Cannot exclude and include all classes")

        self.include = the_include_classes

    def set_include_with_subclasses(self, include):
        """
        Set the list of classes to include in the autogrouping.
        Will also include their derived subclasses.
        """
        the_include_classes = self._validate(include, is_exact=False)
        self.include_with_subclasses = the_include_classes

    def set_group_name(self, gname):
        """
        Set the name of the group to be created
        """
        if not isinstance(gname, six.string_types):
            raise ValidationError("group name must be a string")
        self.group_name = gname

    def is_to_be_grouped(self, the_class):
        """
        Return whether the given class has to be included in the autogroup according to include/exclude list

        :return (bool): True if the_class is to be included in the autogroup
        """
        include = self.get_include()
        include_ws = self.get_include_with_subclasses()
        if (('all.' in include) or
                (the_class._plugin_type_string in include) or
                any([the_class._plugin_type_string.startswith(i) for i in include_ws])
        ):
            exclude = self.get_exclude()
            exclude_ws = self.get_exclude_with_subclasses()
            if ((not 'all.' in exclude) or
                    (the_class._plugin_type_string in exclude) or
                    any([the_class._plugin_type_string.startswith(i) for i in exclude_ws])
            ):
                return True
            else:
                return False
        else:
            return False
