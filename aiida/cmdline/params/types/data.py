# -*- coding: utf-8 -*-
"""
Module for the custom click param type for data
"""
from .identifier import IdentifierParamType


class DataParamType(IdentifierParamType):
    """
    The ParamType for identifying Data entities or its subclasses
    """

    name = 'Data'

    @property
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier

        :return: the orm entity loader class for this ParamType
        """
        from aiida.orm.utils.loaders import DataEntityLoader
        return DataEntityLoader
