# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
def get_db_columns(db_class):
    """
    This function returns a dictionary where the keys are the columns of
    the table corresponding to the db_class and the values are the column
    properties such as type, is_foreign_key and if so, the related table
    and column.
    
    The function applies only to the sqlalchemy backend and for other 
    backends it requires a mapping sqlalchemy-->new_backend. For Django this 
    mapping is the dummy_model.
     
    A similar logic applies to the QueryBuilder that is entirely built upon 
    SQLAlchemy (+ dummy model, for Django)
    
    :param db_class: the database model whose schema has to be returned
    :return: a dictionary
    """

    ## Retrieve the columns of the table corresponding to the present class
    # and its foreignkeys
    table = db_class.metadata.tables[db_class.__tablename__]

    # Here we check both columns, column properties, and hybrid properties
    from sqlalchemy.orm import class_mapper
    from sqlalchemy.orm.properties import ColumnProperty

    from sqlalchemy.ext.hybrid import hybrid_property

    # column_properties = [_ for _ in class_mapper(db_class).iterate_properties
    column_properties = [_ for _ in class_mapper(db_class).all_orm_descriptors
                         if isinstance(_, ColumnProperty)]

    hybrid_properties = [_ for _ in class_mapper(db_class).all_orm_descriptors
                         if isinstance(_, hybrid_property)]

    # Ordinary columns
    columns = table.columns

    # Determine the keys (for hybrid_properties I rely on __name__)
    column_property_keys = map(lambda x: x.key, column_properties)
    hybrid_property_keys = map(lambda x: x.__name__, hybrid_properties)
    column_keys = map(lambda x: x.key, columns)

    # Check whether properties contain objects that are not columns
    property_keys = [_ for _ in column_property_keys if _ not in column_keys]

    column_types = map(lambda x: x.type, columns.values())

    # Assume None for the time being for column_property and hybrid_property
    # types
    # TODO find a way to assess the type
    column_property_types = [None] * len(property_keys)
    hybrid_property_types = [None] * len(hybrid_property_keys)


    foreign_keys = [get_foreign_key_infos(foreign_key) for foreign_key in
                    table.foreign_keys]

    ## merge first column_keys and than column_property_keys
    column_names = column_keys + property_keys + hybrid_property_keys
    column_types.extend(column_property_types)
    column_types.extend(hybrid_property_types)

    column_python_types = []

    from sqlalchemy.dialects.postgresql import UUID, JSONB

    for column_type in column_types:
        # Treat the case where there is no natural python_type
        # counterpart to the column type (specifically because of usage
        # of sqlalchemy dialect)
        if column_type is not None:
            try:
                column_python_types.append(column_type.python_type)
            except NotImplementedError:
                if isinstance(column_type, UUID):
                    column_python_types.append(unicode)
                elif isinstance(column_type, JSONB):
                    column_python_types.append(dict)
                else:
                    raise NotImplementedError("Unknown type from the "
                                              "database schema: {}".format(
                        column_type))
        else:
            column_python_types.append(None)

    ## Fill in the returned dictionary
    schema = {}

    # Fill in the keys based on the column names and the types. By default we
    #  assume that columns are no foreign keys
    for k, v in iter(zip(column_names, column_python_types)):
        schema[k] = {'type': v, 'is_foreign_key': False}

    # Add infos about the foreign relationships
    for k, referred_table_name, referred_field_name in foreign_keys:
        schema[k].update({
            'is_foreign_key': True,
            'related_table': referred_table_name,
            'related_column': referred_field_name,
        })

    return schema


def get_foreign_key_infos(foreign_key):
    """
    takes a foreignkey sqlalchemy object and returns the referent column
    name and the referred relation and column names
    :param foreign_key: a sqlalchemy ForeignKey object
    :return: a tuple of strings
    """
    referent_column_name = foreign_key.parent.name
    (referred_table_name, referred_field_name) = tuple(
        foreign_key.target_fullname.split('.'))
    return (referent_column_name, referred_table_name, referred_field_name)