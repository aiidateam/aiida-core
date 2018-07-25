# -*- coding: utf-8 -*-
"""
Module for the custom click param type computer
"""
from click.types import StringParamType
from .identifier import IdentifierParamType


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


class ShebangParamType(StringParamType):
    """
    Custom click param type for shebang line
    """
    name = 'shebangline'

    def convert(self, value, param, ctx):
        newval = super(ShebangParamType, self).convert(value, param, ctx)
        if newval is None:
            return None
        if not newval.startswith('#!'):
            self.fail('The shebang line should start with the two caracters #!, it is instead: {}'.format(newval))
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
        newval = super(MpirunCommandParamType, self).convert(value, param, ctx)

        scheduler_ep = ctx.params['scheduler']
        if scheduler_ep is not None:
            try:
                job_resource_keys = scheduler_ep.load()._job_resource_class.get_valid_keys()  # pylint: disable=protected-access
            except ImportError:
                self.fail("Unable to load the '{}' scheduler".format(scheduler_ep.name))
        else:
            self.fail("Scheduler not specified for this computer! The mpirun-command must always be asked "
                      "after asking for the scheduler.")

        # Prepare some substitution values to check if it is all ok
        subst = {i: 'value' for i in job_resource_keys}
        subst['tot_num_mpiprocs'] = 'value'

        try:
            newval.format(**subst)
        except KeyError as exc:
            self.fail("In workdir there is an unknown replacement " "field '{}'".format(exc.message))
        except ValueError as exc:
            self.fail("Error in the string: '{}'".format(exc.message))

        return newval
