"""Legacy workflow parameter type."""
from .identifier import IdentifierParamType


class LegacyWorkflowParamType(IdentifierParamType):
    """The ParamType for identifying legacy workflows."""

    name = 'LegacyWorkflow'

    @property
    def orm_class_loader(self):
        """Return the orm entity loader class which should be a subclass of OrmEntityLoader."""
        from aiida.orm.utils.loaders import LegacyWorkflowLoader
        return LegacyWorkflowLoader
