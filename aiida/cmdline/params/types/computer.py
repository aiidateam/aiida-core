# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Module for the custom click param type computer
"""
from click.shell_completion import CompletionItem
from click.types import StringParamType

from ...utils import decorators  # pylint: disable=no-name-in-module
from .identifier import IdentifierParamType

__all__ = ('ComputerParamType', 'ShebangParamType', 'MpirunCommandParamType')


class ComputerParamType(IdentifierParamType):
    """
    The ParamType for identifying Computer entities or its subclasses
    """

    name = 'Computer'

    @property
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier

        :return: the orm entity loader class for this ParamType
        """
        from aiida.orm.utils.loaders import ComputerEntityLoader
        return ComputerEntityLoader

    @decorators.with_dbenv()
    def shell_complete(self, ctx, param, incomplete):  # pylint: disable=unused-argument
        """Return possible completions based on an incomplete value.

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        return [CompletionItem(option) for option, in self.orm_class_loader.get_options(incomplete, project='label')]


class ShebangParamType(StringParamType):
    """
    Custom click param type for shebang line
    """
    name = 'shebangline'

    def convert(self, value, param, ctx):
        newval = super().convert(value, param, ctx)
        if newval is None:
            return None
        if not newval.startswith('#!'):
            self.fail(f'The shebang line should start with the two caracters #!, it is instead: {newval}')
        return newval

    def __repr__(self):
        return 'SHEBANGLINE'


class MpirunCommandParamType(StringParamType):
    """
    Custom click param type for mpirun-command

    .. note:: requires also a scheduler to be provided, and the scheduler
       must be called first!

    Validate that the provided 'mpirun' command only contains replacement fields
    (e.g. ``{tot_num_mpiprocs}``) that are known.

    Return a list of arguments (by using 'value.strip().split(" ") on the input string)
    """
    name = 'mpiruncommandstring'

    def __repr__(self):
        return 'MPIRUNCOMMANDSTRING'

    def convert(self, value, param, ctx):
        newval = super().convert(value, param, ctx)

        scheduler_ep = ctx.params.get('scheduler', None)
        if scheduler_ep is not None:
            try:
                job_resource_keys = scheduler_ep.load().job_resource_class.get_valid_keys()
            except ImportError:
                self.fail(f"Unable to load the '{scheduler_ep.name}' scheduler")
        else:
            self.fail(
                'Scheduler not specified for this computer! The mpirun-command must always be asked '
                'after asking for the scheduler.'
            )

        # Prepare some substitution values to check if it is all ok
        subst = {i: 'value' for i in job_resource_keys}
        subst['tot_num_mpiprocs'] = 'value'

        try:
            newval.format(**subst)
        except KeyError as exc:
            self.fail(f"In workdir there is an unknown replacement field '{exc.args[0]}'")
        except ValueError as exc:
            self.fail(f"Error in the string: '{exc}'")

        return newval
