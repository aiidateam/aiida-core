# -*- coding: utf-8 -*-

from aiida.orm.impl.django.computer import Computer

from aiida.common.exceptions import InvalidOperation
from django.db.models.deletion import ProtectedError

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

    # TODO SP: abstract the ProtectedError
    try:
        computer.dbcomputer.delete()
    except ProtectedError:
        raise InvalidOperation("Unable to delete the requested computer: there"
                               "is at least one node using this computer")

