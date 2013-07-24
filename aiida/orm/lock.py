
import aiida.common
from aiida.common.exceptions import (InternalError, ModificationNotAllowed, LockPresent)
from aiida.djsite.db.models import DbLock
from django.utils import timezone

class LockManager(object):
    
    def aquire(self, key, timeout=3600, owner="None"):
        
        from django.db import IntegrityError, transaction
        
        import time
        
        try:
            
            sid = transaction.savepoint()
            dblock = DbLock.objects.create(key=key, timeout=timeout, owner=owner)
            transaction.savepoint_commit(sid)
            return Lock(dblock)
        
        except IntegrityError:
            
            transaction.savepoint_rollback(sid)
            
            old_lock       = DbLock.objects.get(key=key)
            timeout_secs   = time.mktime(old_lock.creation.timetuple())+old_lock.timeout
            now_secs       = time.mktime(timezone.now().timetuple())
            
            if now_secs > timeout_secs:
                raise InternalError("A lock went over the limit timeout, this could mine the integrity of the system. Reload the Daemon to fix the problem.")            
            else:
                raise LockPresent("A lock is present.") 
        
        except:
            raise InternalError("Something went wrong, try to keep on.")
        
class Lock(object):
    
    def __init__(self, dblock):
        
        self.dblock  = dblock
        
    def release(self, owner="None"):
        
        if self.dblock == None:
            raise InternalError("No dblock present.")
            
        try:
            if (self.dblock.owner==owner):
                self.dblock.delete()
                self.dblock = None
            else:
                raise ModificationNotAllowed("Only the owner can release the lock.")
            
        except:
            raise InternalError("Cannot release a lock, Reload the Daemon to fix the problem.")

    @property
    def isexpired(self):
        import time
        
        if self.dblock == None:
            return False
    
        timeout_secs   = time.mktime(self.dblock.creation.timetuple())+self.dblock.timeout
        now_secs       = time.mktime(timezone.now().timetuple())
            
        if now_secs > timeout_secs:
            return True
        else:
            return False
    
    @property
    def key(self):
        
        if self.dblock == None:
            return None
        
        return self.dblock.key