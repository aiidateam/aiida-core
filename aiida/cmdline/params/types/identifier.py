# -*- coding: utf-8 -*-
from abc import abstractmethod, abstractproperty

import click

from aiida.cmdline.utils.decorators import with_dbenv


class IdentifierParam(click.ParamType):
    """
    An extension of click.ParamType for a generic identifier parameters. In AiiDA, ORM entities can often be
    identified by their ID, UUID or optionally some STRING based label identifier. This parameter type implements
    the convert method, to automatically distinguish which type is implied for the given value. The strategy
    is to first attempt to convert the value to an integer. If successful, it is assumed that the value
    represents an ID. If that fails, we attempt to interpret the value as a base 16 encoded integer, after having
    removed any dashes from the string. If that succeeds, it is most likely a UUID. If it seems to be neither an ID
    nor a UUID, it is assumed to be a STRING label.

    With this approach there is the possibility for ambiguity. Since it is allowed to pass a partial UUID, it is
    possible that the partial UUID is also a valid ID. Likewise, a STRING identifier might also be a valid ID, or a
    valid (partial) UUID. Fortunately, these ambiguities can be solved though:

     * ID/UUID: can always be solved by passing a partial UUID with at least one dash
     * ID/STRING: appending an exclamation point ! to the identifier, will force STRING interpretation
     * UUID/STRING: appending an exclamation point ! to the identifier, will force STRING interpretation

    The approach for the latter is the only surefire way for the user to always be able to break ambiguity.
    """

    LABEL_AMBIGUITY_BREAKER_CHARACTER = '!'

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
    def orm_load_entity(self, identifier, identifier_type):
        """
        Attempt to load an ORM entity, of the class defined by the orm_class property, for the given identifier
        and identifier type

        :param identifier: the entity identifier
        :param identifier_type: the type of the identifier, ID, UUID or STRING
        :return: the entity if the identifier can be uniquely resolved
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
        represents a generic string label. If the value ends with the LABEL_AMBIGUITY_BREAKER_CHARACTER
        it is stripped and the value will be interpreted as a STRING

        :return: the loaded ORM entity if successful
        :raises click.BadParameter: if the value is ambiguous and leads to multiple entities
        :raises click.BadParameter: if the value cannot be mapped onto an existing instance of the ORM class
        :raises click.BadParameter: if the loaded entity's class does not correspond to the ORM class
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm.utils.loaders import IdentifierType

        if not value:
            raise click.BadParameter('the value for the identifier cannot be empty')

        # If the final character of the value is the special marker, we enforce STRING interpretation
        if value[-1] == self.LABEL_AMBIGUITY_BREAKER_CHARACTER:

            identifier = value.rstrip(self.LABEL_AMBIGUITY_BREAKER_CHARACTER)
            identifier_type = IdentifierType.STRING

        else:

            # If the value can be cast into an integer, interpret it as an ID
            try:
                identifier = int(value)
                identifier_type = IdentifierType.ID
            except ValueError:

                # If the value is a valid base sixteen encoded integer, after dashes are removed, interpret it as a UUID
                try:
                    hexadecimal = int(value.replace('-', ''), 16)
                    identifier = value
                    identifier_type = IdentifierType.UUID

                # If that fails, interpret it as a STRING
                except ValueError:
                    identifier = value
                    identifier_type = IdentifierType.STRING

        try:
            entity = self.orm_load_entity(identifier, identifier_type)
        except MultipleObjectsError:
            error = 'multiple {} entries found with {}<{}>'.format(self.name, identifier_type.value, identifier)
            raise click.BadParameter(error)
        except NotExistent:
            error = 'no {} found with {}<{}>'.format(self.name, identifier_type.value, identifier)
            raise click.BadParameter(error)
        except ValueError as exception:
            error = exception.message
            raise click.BadParameter(error)

        if not isinstance(entity, self.orm_class):
            error = 'entity with {}<{}> is not a {}'.format(identifier_type.value, identifier, self.orm_class.__name__)
            raise click.BadParameter(error)

        return entity
