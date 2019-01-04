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
Module for custom click param type identifier
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from abc import ABCMeta, abstractproperty

import six
import click

from aiida.cmdline.utils.decorators import with_dbenv
from aiida.plugins.entry_point import get_entry_point_from_string


@six.add_metaclass(ABCMeta)
class IdentifierParamType(click.ParamType):
    """
    An extension of click.ParamType for a generic identifier parameter. In AiiDA, orm entities can often be
    identified by either their ID, UUID or optionally some LABEL identifier. This parameter type implements
    the convert method, which attempts to convert a value passed to the command for a parameter with this type,
    to an orm entity. The actual loading of the entity is delegated to the orm class loader. Subclasses of this
    parameter type should implement the `orm_class_loader` method to return the appropriate orm class loader,
    which should be a subclass of `aiida.orm.utils.loaders.OrmEntityLoader` for the corresponding orm class.
    """

    def __init__(self, sub_classes=None):
        """
        Construct the parameter type, optionally specifying a tuple of entry points that reference classes
        that should be a sub class of the base orm class of the orm class loader. The classes pointed to by
        these entry points will be passed to the OrmEntityLoader when converting an identifier and they will
        restrict the query set by demanding that the class of the corresponding entity matches these sub classes.

        To prevent having to load the database environment at import time, the actual loading of the entry points
        is deferred until the call to `convert` is made. This is to keep the command line autocompletion light
        and responsive. The entry point strings will be validated, however, to see if the correspond to known
        entry points.

        :param sub_classes: a tuple of entry point strings that can narrow the set of orm classes that values
            will be mapped upon. These classes have to be strict sub classes of the base orm class defined
            by the orm class loader
        """
        from aiida.common.exceptions import MissingEntryPointError, MultipleEntryPointError

        self._sub_classes = None
        self._entry_points = []

        if sub_classes is not None:

            if not isinstance(sub_classes, tuple):
                raise TypeError('sub_classes should be a tuple of entry point strings')

            for entry_point_string in sub_classes:

                try:
                    entry_point = get_entry_point_from_string(entry_point_string)
                except (ValueError, MissingEntryPointError, MultipleEntryPointError) as exception:
                    raise ValueError('{} is not a valid entry point string: {}'.format(entry_point_string, exception))
                else:
                    self._entry_points.append(entry_point)

    @abstractproperty
    @with_dbenv()
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier

        :return: the orm entity loader class for this ParamType
        """

    @with_dbenv()
    def convert(self, value, param, ctx):
        """
        Attempt to convert the given value to an instance of the orm class using the orm class loader.

        :return: the loaded orm entity
        :raises click.BadParameter: if the value is ambiguous and leads to multiple entities
        :raises click.BadParameter: if the value cannot be mapped onto any existing instance
        :raises RuntimeError: if the defined orm class loader is not a subclass of the OrmEntityLoader class
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm.utils.loaders import OrmEntityLoader

        if not value:
            raise click.BadParameter('the value for the identifier cannot be empty')

        loader = self.orm_class_loader

        if not issubclass(loader, OrmEntityLoader):
            raise RuntimeError('the orm class loader should be a subclass of OrmEntityLoader')

        # If entry points where in the constructor, we load their corresponding classes, validate that they are valid
        # sub classes of the orm class loader and then pass it as the sub_class parameter to the load_entity call.
        # We store the loaded entry points in an instance variable, such that the loading only has to be done once.
        if self._entry_points and self._sub_classes is None:

            sub_classes = []

            for entry_point in self._entry_points:
                try:
                    sub_class = entry_point.load()
                except ImportError as exception:
                    raise RuntimeError('failed to load the entry point {}: {}'.format(entry_point, exception))

                if not issubclass(sub_class, loader.orm_base_class):
                    raise RuntimeError('the class {} of entry point {} is not a sub class of {}'.format(
                        sub_class, entry_point, loader.orm_base_class))
                else:
                    sub_classes.append(sub_class)

            self._sub_classes = tuple(sub_classes)

        try:
            entity = loader.load_entity(value, sub_classes=self._sub_classes)
        except (MultipleObjectsError, NotExistent, ValueError) as exception:
            raise click.BadParameter(str(exception))

        return entity
