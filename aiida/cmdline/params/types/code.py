# -*- coding: utf-8 -*-
from .identifier import IdentifierParamType


class CodeParamType(IdentifierParamType):
    """
    The ParamType for identifying Code entities or its subclasses
    """

    name = 'Code'

    @property
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier 

        :return: the orm entity loader class for this ParamType
        """
        from aiida.orm.utils.loaders import CodeEntityLoader
        return CodeEntityLoader
