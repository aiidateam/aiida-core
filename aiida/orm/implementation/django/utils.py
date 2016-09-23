# -*- coding: utf-8 -*-

from aiida.orm.implementation.django.computer import Computer

from aiida.common.exceptions import InvalidOperation, DbContentError

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


def delete_computer(computer):
    """
    Delete a computer from the DB.
    It assumes that the DB backend does the proper checks and avoids
    to delete computers that have nodes attached to them.

    Implemented as a function on purpose, otherwise complicated logic would be
    needed to set the internal state of the object after calling
    computer.delete().
    """
    if not isinstance(computer, Computer):
        raise TypeError("computer must be an instance of "
                        "aiida.orm.computer.Computer")

    # TODO: abstract the ProtectedError, to the corresponding one with
    # SQLAlchemy. This will probably be a bit tedious because the error from
    # SQLAlchemy don't expose the error.
    from django.db.models.deletion import ProtectedError
    try:
        computer.dbcomputer.delete()
    except ProtectedError:
        raise InvalidOperation("Unable to delete the requested computer: there"
                               "is at least one node using this computer")


def get_db_columns(db_class):
    """
    This function returns a dictionary where the keys are the columns of
    the table corresponding to the db_class and the values are the column
    properties such as type, is_foreign_key and if so, the related table
    and column.
    :param db_class: the database model whose schema has to be returned
    :return: a dictionary
    """

    import datetime
    from django.db.models import ForeignKey

    django2python_map = {
        'AutoField': int,
        'BooleanField': bool,
        'CharField': str,
        'DateTimeField': datetime.datetime,
        'EmailField': str,
        'FloatField': float,
        'IntegerField': int,
        'TextField': str,
        'UUIDField': str,
    }

    ## Retrieve the columns of the table corresponding to the present class
    columns = db_class._meta.fields

    column_names = []
    column_types = []
    column_python_types = []
    foreign_keys = []

    ## retrieve names, types, and convert types in python types.
    for column in columns:

        name = column.get_attname()
        type = column.get_internal_type()

        column_names.append(name)

        # Check for foreignkeys and compile a dictionary with the required
        # informations
        if type is 'ForeignKey':
            # relation is a tuple with the related table and the related field
            relation = column.resolve_related_fields()
            if len(relation) == 0:
                raise DbContentError(' "{}" field has no foreign '
                                     'relationship')
            elif len(relation) > 1:
                raise DbContentError(' "{}" field has not a unique foreign '
                                     'relationship')
            else:
                #Collect infos of the foreing key
                foreign_keys.append((name, relation[0][0], relation[0][1]))
                #Change the type according to the type of the related column
                type = relation[0][1].get_internal_type()

        column_types.append(type)


    column_python_types = map(lambda x: django2python_map[x], column_types)

    ## Fill in the returned dictionary
    schema = {}

    # Fill in the keys based on the column names and the types. By default we
    #  assume that columns are no foreign keys
    for k, v in iter(zip(column_names, column_python_types)):
        schema[k] = {'type': v, 'is_foreign_key': False}

    # Add infos about the foreign relationships
    for k, related_class, related_field in foreign_keys:
        schema[k].update({
            'is_foreign_key': True,
            'related_table': related_class.rel.to.__name__,
            'related_column': related_field.get_attname()
        })

    return schema
