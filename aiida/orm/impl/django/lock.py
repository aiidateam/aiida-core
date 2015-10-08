# -*- coding: utf-8 -*-

import time

from aiida.orm.abstract.lock import AbstractLockManager, AbstractLock

from aiida.common.exceptions import (InternalError, ModificationNotAllowed, LockPresent)

from aiida.djsite.db.models import DbLock

from django.db import IntegrityError, transaction
# TODO SP: to replace
from django.utils import timezone

class LockManager(AbstractLockManager):
    def aquire(self, key, timeout=3600, owner="None"):
        try:
            sid = transaction.savepoint()
            dblock = DbLock.objects.create(key=key, timeout=timeout, owner=owner)
            transaction.savepoint_commit(sid)
            return Lock(dblock)

        except IntegrityError:
            transaction.savepoint_rollback(sid)

            old_lock = DbLock.objects.get(key=key)
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
        try:
            sid = transaction.savepoint()
            DbLock.objects.all().delete()
        except IntegrityError:
            transaction.savepoint_rollback(sid)

class Lock(AbstractLock):

    def release(self, owner="None"):
        if self.dblock == None:
            raise InternalError("No dblock present.")

        try:
            if (self.dblock.owner == owner):
                self.dblock.delete()
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
