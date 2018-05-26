# -*- coding: utf-8 -*-
from .identifier import IdentifierParamType


class NodeParamType(IdentifierParamType):
    """
    The ParamType for identifying Node entities or its subclasses
    """

    name = 'Node'

    @property
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier 

        :return: the orm entity loader class for this ParamType
        """
        from aiida.orm.utils.loaders import NodeEntityLoader
        return NodeEntityLoader
