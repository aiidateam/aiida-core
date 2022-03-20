# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for custom click param type group."""
import click

from aiida.cmdline.utils import decorators
from aiida.common.lang import type_check

from .identifier import IdentifierParamType

__all__ = ('GroupParamType',)


class GroupParamType(IdentifierParamType):
    """The ParamType for identifying Group entities or its subclasses."""

    name = 'Group'

    def __init__(self, create_if_not_exist=False, sub_classes=('aiida.groups:core',)):
        """Construct the parameter type.

        The `sub_classes` argument can be used to narrow the set of subclasses of `Group` that should be matched. By
        default all subclasses of `Group` will be matched, otherwise it is restricted to the subclasses that correspond
        to the entry point names in the tuple of `sub_classes`.

        To prevent having to load the database environment at import time, the actual loading of the entry points is
        deferred until the call to `convert` is made. This is to keep the command line autocompletion light and
        responsive. The entry point strings will be validated, however, to see if they correspond to known entry points.

        :param create_if_not_exist: boolean, if True, will create the group if it does not yet exist. By default the
            group created will be of class `Group`, unless another subclass is specified through `sub_classes`. Note
            that in this case, only a single entry point name can be specified
        :param sub_classes: a tuple of entry point strings from the `aiida.groups` entry point group.
        """
        type_check(sub_classes, tuple, allow_none=True)

        if create_if_not_exist and len(sub_classes) > 1:
            raise ValueError('`sub_classes` can at most contain one entry point if `create_if_not_exist=True`')

        self._create_if_not_exist = create_if_not_exist
        super().__init__(sub_classes=sub_classes)

    @property
    def orm_class_loader(self):
        """Return the orm entity loader class, which should be a subclass of `OrmEntityLoader`.

        This class is supposed to be used to load the entity for a given identifier.

        :return: the orm entity loader class for this `ParamType`
        """
        from aiida.orm.utils.loaders import GroupEntityLoader
        return GroupEntityLoader

    @decorators.with_dbenv()
    def shell_complete(self, ctx, param, incomplete):  # pylint: disable=unused-argument
        """Return possible completions based on an incomplete value.

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        return [
            click.shell_completion.CompletionItem(option)
            for option, in self.orm_class_loader.get_options(incomplete, project='label')
        ]

    @decorators.with_dbenv()
    def convert(self, value, param, ctx):
        try:
            group = super().convert(value, param, ctx)
        except click.BadParameter:
            if self._create_if_not_exist:
                # The particular subclass to load will be stored in `_sub_classes` as loaded by `convert` of the super.
                cls = self._sub_classes[0]
                group = cls(label=value).store()
            else:
                raise

        return group
