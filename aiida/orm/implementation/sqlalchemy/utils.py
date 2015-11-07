# -*- coding: utf-8 -*-

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

