# -*- coding: utf-8 -*-
from aiida.common.exceptions import InvalidOperation

class _GlobalSession(object):
    def __get__(self, obj, _type):
        if not hasattr(_GlobalSession, "session"):
            raise InvalidOperation("You need to call load_dbenv before "
                                     "accessing the session of SQLALchemy.")
        return _GlobalSession.session

session = _GlobalSession()
