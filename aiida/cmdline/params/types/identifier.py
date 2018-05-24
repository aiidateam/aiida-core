# -*- coding: utf-8 -*-
from abc import abstractmethod, abstractproperty

import click

from aiida.cmdline.utils.decorators import with_dbenv


class IdentifierParam(click.ParamType):
    """
    An extension of click.ParamType for a generic identifier parameters. In AiiDA, ORM entities can often
    be identified by their ID, UUID or optionally some string based LABEL. This parameter type implements
    the convert method, to automatically distinguish which type is implied for the given value. The strategy
    is to first attempt to convert the value to an integer. If successful, it is assumed that the value
    represents an ID. If that fails, we attempt to convert it to an integer in base16, after having removed
    any dashes from the string. If that succeeds, it is most likely a UUID. If it seems to be neither an ID
    nor a UUID, it is assumed to be a STRING label.
    """

    name = 'entity'

    @abstractproperty
    @with_dbenv()
    def orm_class(self):
        """
        Return the ORM class to which any converted values should be mapped

        :return: the ORM class to which values should be mapped
        """
        pass

    @abstractmethod
    @with_dbenv()
    def orm_entity_loader(self):
        """
        Return the function that is responsible for loading the ORM entity for a given identifier
        and identifier type

        :return: the function that takes `identifier` and `identifier_type` and attempts to load the ORM
            entity that corresponds to that identifier
        """
        pass

    @with_dbenv()
    def convert(self, value, param, ctx):
        """
        Convert the provided value to an ORM entity. The value will be considered to be one of:

            * ID
            * UUID
            * STRING

        in that order. If the value is neither an ID nor a UUID, it is assumed that the value
        represents a generic string label.

        :return: the loaded ORM entity if successful
        :raises click.BadParameter: if the value is ambiguous and leads to multiple entities
        :raises click.BadParameter: if the value cannot be mapped onto an existing instance of the ORM class
        :raises click.BadParameter: if the loaded entity's class does not correspond to the ORM class
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm.utils.loaders import IdentifierType

        if not value:
            raise click.BadParameter('the value for the identifier cannot be empty')

        # If we can successfully convert it into a string we assume the identifier is an ID
        try:
            identifier = int(value)
            identifier_type = IdentifierType.ID
        except ValueError:

            # If we can successfully convert it into a base sixteen integer, it is most likely a UUID
            try:
                hexadecimal = int(value.replace('-', ''), 16)
                identifier = value
                identifier_type = IdentifierType.UUID
            except ValueError:
                identifier = value
                identifier_type = IdentifierType.LABEL

        try:
            entity = self.orm_entity_loader(identifier, identifier_type)
        except MultipleObjectsError:
            error = 'multiple {} entries found with {}<{}>'.format(self.name, identifier_type.value, identifier)
            raise click.BadParameter(error)
        except NotExistent:
            error = 'no {} found with {}<{}>'.format(self.name, identifier_type.value, identifier)
            raise click.BadParameter(error)

        if not isinstance(entity, self.orm_class):
            error = 'entity with {}<{}> is not a {}'.format(identifier_type.value, identifier, self._orm_class.__name__)
            raise click.BadParameter(error)

        return entity
