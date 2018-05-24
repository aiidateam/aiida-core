# -*- coding: utf-8 -*-
from .identifier import IdentifierParam


class CodeParam(IdentifierParam):

    name = 'Code'

    @property
    def orm_class(self):
        from aiida.orm import Code
        return Code

    def orm_entity_loader(self, identifier, identifier_type):
        from aiida.orm.utils.loaders import CodeEntityLoader
        loader = CodeEntityLoader(self.orm_class)
        return loader.load_entity(identifier, identifier_type)
