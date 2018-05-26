# -*- coding: utf-8 -*-
from .identifier import IdentifierParamType


class GroupParamType(IdentifierParamType):
    """
    The ParamType for identifying Group entities or its subclasses
    """

    name = 'Group'

    @property
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier 

        :return: the orm entity loader class for this ParamType
        """
        from aiida.orm.utils.loaders import GroupEntityLoader
        return GroupEntityLoader
