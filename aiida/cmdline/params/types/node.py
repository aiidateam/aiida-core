# -*- coding: utf-8 -*-
from .identifier import IdentifierParam


class NodeParam(IdentifierParam):

    name = 'Node'

    @property
    def orm_class(self):
        from aiida.orm import Node
        return Node

    def orm_entity_loader(self, identifier, identifier_type):
        from aiida.orm.utils.loaders import OrmEntityLoader
        loader = OrmEntityLoader(self.orm_class)
        return loader.load_entity(identifier, identifier_type)
