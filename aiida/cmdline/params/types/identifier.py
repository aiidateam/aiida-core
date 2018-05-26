# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractproperty

import click

from aiida.cmdline.utils.decorators import with_dbenv


class IdentifierParamType(click.ParamType):
    """
    An extension of click.ParamType for a generic identifier parameter. In AiiDA, orm entities can often be
    identified by either their ID, UUID or optionally some LABEL identifier. This parameter type implements
    the convert method, which attempts to convert a value passed to the command for a parameter with this type,
    to an orm entity. The actual loading of the entity is delegated to the orm class loader. Subclasses of this
    parameter type should implement the `orm_class_loader` method to return the appropriate orm class loader,
    which should be a subclass of `aiida.orm.utils.loaders.OrmEntityLoader` for the corresponding orm class.
    """

    __metaclass__ = ABCMeta

    name = 'entity'

    @abstractproperty
    @with_dbenv()
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier 

        :return: the orm entity loader class for this ParamType
        """
        pass

    @with_dbenv()
    def convert(self, value, param, ctx):
        """
        Attempt to convert the given value to an instance of the orm class using the orm class loader.

        :return: the loaded orm entity
        :raises click.BadParameter: if the value is ambiguous and leads to multiple entities
        :raises click.BadParameter: if the value cannot be mapped onto any existing instance
        :raises RuntimeError: if the defined orm class loader is not a subclass of the OrmEntityLoader class
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm.utils.loaders import OrmEntityLoader

        if not value:
            raise click.BadParameter('the value for the identifier cannot be empty')

        loader = self.orm_class_loader

        if not issubclass(loader, OrmEntityLoader):
            raise RuntimeError('the orm class loader should be a subclass of OrmEntityLoader')

        try:
            entity = loader.load_entity(value)
        except (MultipleObjectsError, NotExistent, ValueError) as exception:
            raise click.BadParameter(exception.message)

        return entity
