# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from sqlalchemy import inspect
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.types import Integer, Boolean


__all__ = ['django_filter', 'get_attr']


def iter_dict(attrs):
    if isinstance(attrs, dict):
        for key in sorted(attrs.iterkeys()):
            it = iter_dict(attrs[key])
            for k, v in it:
                new_key = key
                if k:
                    new_key += "." + str(k)
                yield new_key, v
    elif isinstance(attrs, list):
        for i, val in enumerate(attrs):
            it = iter_dict(val)
            for k, v  in it:
                new_key = str(i)
                if k:
                    new_key += "." + str(k)
                yield new_key, v
    else:
        yield "", attrs


def get_attr(attrs, key):
    path = key.split('.')

    d = attrs
    for p in path:
        if p.isdigit():
            p = int(p)
        # Let it raise the appropriate exception
        d = d[p]

    return d


def _create_op_func(op):
    def f(attr, val):
        return getattr(attr, op)(val)

    return f


_from_op = {
    'in': _create_op_func('in_'),
    'gte': _create_op_func('__ge__'),
    'gt': _create_op_func('__gt__'),
    'lte': _create_op_func('__le__'),
    'lt': _create_op_func('__lt__'),
    'eq': _create_op_func('__eq__'),
    'startswith': lambda attr, val: attr.like('{}%'.format(val)),
    'contains': lambda attr, val: attr.like('%{}%'.format(val)),
    'endswith': lambda attr, val: attr.like('%{}'.format(val)),
    'istartswith': lambda attr, val: attr.ilike('{}%'.format(val)),
    'icontains': lambda attr, val: attr.ilike('%{}%'.format(val)),
    'iendswith': lambda attr, val: attr.ilike('%{}'.format(val))
}


def django_filter(cls_query, **kwargs):
    # Pass the query object you want to use.
    # This also assume a AND between each arguments

    cls = inspect(cls_query)._entity_zero().type
    q = cls_query

    # We regroup all the filter on a relationship at the same place, so that
    # when a join is done, we can filter it, and then reset to the original
    # query.
    current_join = None


    tmp_attr = dict(key=None, val=None)
    tmp_extra = dict(key=None, val=None)

    for key in sorted(kwargs.iterkeys()):
        val = kwargs[key]

        join, field, op = [None]*3

        splits = key.split("__")
        if len(splits) > 3:
            raise ValueError("Too many parameters to handle.")
        # something like "computer__id__in"
        elif len(splits) == 3:
            join, field, op = splits
        # we have either "computer__id", which means join + field quality or
        # "id__gte" which means field + op
        elif len(splits) == 2:
            if splits[1] in _from_op.iterkeys():
                field, op = splits
            else:
                join, field = splits
        else:
            field = splits[0]

        if "dbattributes" == join:
            if "val" in field:
                field = "val"
            if field in ["key", "val"]:
                tmp_attr[field] = val
            continue
        elif "dbextras" == join:
            if "val" in field:
                field = "val"
            if field in ["key", "val"]:
                tmp_extra[field] = val
            continue

        current_cls = cls
        if join:
            if current_join != join:
                q = q.join(join, aliased=True)
                current_join = join

            current_cls = filter(lambda r: r[0] == join,
                                 inspect(cls).relationships.items()
                                 )[0][1].argument
            if isinstance(current_cls, Mapper):
                current_cls = current_cls.class_
            else:
                current_cls = current_cls()

        else:
            if current_join is not None:
                # Filter on the queried class again
                q = q.reset_joinpoint()
                current_join = None

        if field == "pk":
            field = "id"

        filtered_field = getattr(current_cls, field)
        if not op:
            op = "eq"
        f = _from_op[op]

        q = q.filter(f(filtered_field, val))

    # We reset one last time
    q.reset_joinpoint()

    key = tmp_attr["key"]
    if key:
        val = tmp_attr["val"]
        if val:
            q = q.filter(apply_json_cast(cls.attributes[key], val) == val)
        else:
            q = q.filter(cls.attributes.has_key(tmp_attr["key"]))
    key = tmp_extra["key"]
    if key:
        val = tmp_extra["val"]
        if val:
            q = q.filter(apply_json_cast(cls.extras[key], val) == val)
        else:
            q = q.filter(cls.extras.has_key(tmp_extra["key"]))

    return q


def apply_json_cast(attr, val):
    if isinstance(val, basestring):
        attr = attr.astext
    if isinstance(val, int) or isinstance(val, long):
        attr = attr.astext.cast(Integer)
    if isinstance(val, bool):
        attr = attr.astext.cast(Boolean)

    return attr


def get_foreign_key_infos(foreign_key):
    """
    takes a foreignkey sqlalchemy object and returns the referent column
    name and the referred relation and column names
    :param foreign_key: a sqlalchemy ForeignKey object
    :return: a tuple of strings
    """
    column_name = foreign_key.column.name
    (referred_table_name, referred_field_name) = tuple(
        foreign_key.target_fullname.split('.'))
    return (column_name, referred_table_name, referred_field_name)


def get_db_columns(db_class):
    """
    This function returns a dictionary where the keys are the columns of
    the table corresponding to the db_class and the values are the column
    properties such as type, is_foreign_key and if so, the related table
    and column.
    :param db_class: the database model whose schema has to be returned
    :return: a dictionary
    """

    ## Retrieve the columns of the table corresponding to the present class
    # and its foreignkeys
    table = db_class.metadata.tables[db_class.__tablename__]
    columns = table.columns
    foreign_keys = [get_foreign_key_infos(foreign_key) for foreign_key in
                    table.foreign_keys]

    ## retrieve the types and convert them in python types
    column_names = columns.keys()
    column_types = map(lambda x: x.type, columns.values())
    column_python_types = []

    from sqlalchemy.dialects.postgresql import UUID, JSONB

    for type in column_types:
        # Treat the case where there is no natural python_type
        # counterpart to the column type (specifically because of usage
        # of sqlalchemy dialect)
        try:
            column_python_types.append(type.python_type)
        except NotImplementedError:
            if isinstance(type, UUID):
                column_python_types.append(unicode)
            elif isinstance(type, JSONB):
                column_python_types.append(dict)
            else:
                raise NotImplementedError("Unknown type from the "
                                          "database schema")

    ## Fill in the returned dictionary
    schema = {}

    # Fill in the keys based on the column names and the types. By default we
    #  assume that columns are no foreign keys
    for k, v in iter(zip(column_names, column_python_types)):
        schema[k] = {'type': v, 'is_foreign_key': False}

    # Add infos about the foreign relationships
    for k, referred_table_name, referred_field_name  in foreign_keys:

        print k, referred_field_name, referred_table_name
        schema[k].update({
            'is_foreign_key': True,
            'related_table': referred_table_name,
            'related_column': referred_field_name,
        })

    return schema

