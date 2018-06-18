# -*- coding: utf-8 -*-
"""
Module for the custom click param type computer
"""
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
