# -*- coding: utf-8 -*-

__all__ = ['delete_computer', 'django_filter']

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from aiida.backends.sqlalchemy import session
from aiida.common.exceptions import InvalidOperation
from aiida.orm.implementation.sqlalchemy.computer import Computer


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

    try:
        session.delete(computer.dbcomputer)
        session.commit()
    except SQLAlchemyError:
        raise InvalidOperation("Unable to delete the requested computer: there"
                               "is at least one node using this computer")

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

def django_filter(cls, **kwargs):
    # Only handle filter like workflow_step=foo or id__gte=5
    # cls in the cls in which you are filtering
    # This also assume a AND between each arguments

    q = cls.query

    # We regroup all the filter on a relationship at the same place, so that
    # when a join is done, we can filter it, and then reset to the original
    # query.
    current_join = None

    for key in sorted(kwargs.iterkeys()):
        val = kwargs[key]

        join, field, op = [None]*3

        splits = key.split("__")
        if len(splits) > 3:
            raise ValueError("Too many parameters to handle.")
        elif len(splits) == 3:
            join, field, op = splits
        elif len(splits) == 2:
            if splits[1] in _from_op.iterkeys():
                field, op = splits
            else:
                join, field = splits
        else:
            field = splits[0]

        if "dbattributes" in [join, field]:
            # We don't handle this right now.
            continue

        current_cls = cls
        if join:
            if current_join != join:
                q = q.join(join, aliased=True)
                current_join = join

            current_cls = filter(lambda r: r[0] == join,
                                 inspect(cls).relationships.items()
                                 )[0][1].argument()
        else:
            if current_join is not None:
                # Filter on the queried class again
                q = q.reset_joinpoint()
                current_join = None

        filtered_field = getattr(current_cls, field)
        if not op:
            op = "eq"
        f = _from_op[op]

        q = q.filter(f(filtered_field, val))

    # We reset one last time
    q.reset_joinpoint()

    return q
