# -*- coding: utf-8 -*-
from .identifier import IdentifierParam


class GroupParam(IdentifierParam):

    name = 'Group'

    @property
    def orm_class(self):
        from aiida.orm import Group
        return Group

    def orm_entity_loader(self, identifier, identifier_type):
        from aiida.orm.utils.loaders import GroupEntityLoader
        loader = GroupEntityLoader(self.orm_class)
        return loader.load_entity(identifier, identifier_type)
