# -*- coding: utf-8 -*-
from .identifier import IdentifierParam


class ComputerParam(IdentifierParam):

    name = 'Computer'

    @property
    def orm_class(self):
        from aiida.orm import Computer
        return Computer

    def orm_entity_loader(self, identifier, identifier_type):
        from aiida.orm.utils.loaders import ComputerEntityLoader
        loader = ComputerEntityLoader(self.orm_class)
        return loader.load_entity(identifier, identifier_type)
