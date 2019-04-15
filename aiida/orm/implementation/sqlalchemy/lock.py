# -*- coding: utf-8 -*-

from sqlalchemy.exc import SQLAlchemyError

from aiida.backends.sqlalchemy import session
from aiida.backends.sqlalchemy.models.lock import DbLock
from aiida.common.exceptions import (InternalError, ModificationNotAllowed,
                                     LockPresent)
from aiida.orm.implementation.general.lock import AbstractLockManager, AbstractLock


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

class LockManager(AbstractLockManager):
    def aquire(self, key, timeout=3600, owner="None"):
        try:
            with session.begin(subtransactions=True):
                dblock = DbLock(key=key, timeout=timeout, owner=owner)
                session.add(dblock)

            return Lock(dblock)

        except SQLAlchemyError:

            old_lock = DbLock.query.filter_by(key=key).first()

            timeout_secs = time.mktime(old_lock.creation.timetuple()) + old_lock.timeout
            now_secs = time.mktime(timezone.now().timetuple())

            if now_secs > timeout_secs:
                raise InternalError(
                    "A lock went over the limit timeout, this could mine the integrity of the system. Reload the Daemon to fix the problem.")
            else:
                raise LockPresent("A lock is present.")

        except:
            raise InternalError("Something went wrong, try to keep on.")

    def clear_all(self):
        with session.begin(subtransactions=True):
            DbLock.query.delete()

class Lock(AbstractLock):

    def release(self, owner="None"):
        if self.dblock == None:
            raise InternalError("No dblock present.")

        try:
            if (self.dblock.owner == owner):
                session.delete(self.dblock)
                session.commit()
                self.dblock = None
            else:
                raise ModificationNotAllowed("Only the owner can release the lock.")

        except:
            raise InternalError("Cannot release a lock, Reload the Daemon to fix the problem.")

    @property
    def isexpired(self):
        if self.dblock == None:
            return False

        timeout_secs = time.mktime(self.dblock.creation.timetuple()) + self.dblock.timeout
        now_secs = time.mktime(timezone.now().timetuple())

        if now_secs > timeout_secs:
            return True
        else:
            return False

    @property
    def key(self):
        if self.dblock == None:
            return None

        return self.dblock.key
