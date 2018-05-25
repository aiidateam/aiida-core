# -*- coding: utf-8 -*-
from .identifier import IdentifierParam


class GroupParam(IdentifierParam):

    name = 'Group'

    @property
    def orm_class(self):
        """
        Return the ORM class to which any converted values should be mapped

        :return: the ORM class to which values should be mapped
        """
        from aiida.orm import Group
        return Group

    def orm_load_entity(self, identifier, identifier_type):
        """
        Attempt to load an ORM entity, of the class defined by the orm_class property, for the given identifier
        and identifier type

        :param identifier: the entity identifier
        :param identifier_type: the type of the identifier, ID, UUID or STRING
        :return: the entity if the identifier can be uniquely resolved
        """
        from aiida.orm.utils.loaders import GroupEntityLoader
        return GroupEntityLoader().load_entity(identifier, identifier_type)
