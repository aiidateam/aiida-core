from aiida.common import aiidalogger
import celery
from aiida.common.exceptions import *

#from celery.utils.log import get_task_logger
## I use the aiidalogger so that the logging is managed in the same way
logger = aiidalogger.getChild('tasks')

LOCK_EXPIRE = 60 * 1000 # Expire time for the retriever, in seconds; should
                        # be a very large number!

class SingleTask(celery.Task):
    
    abstract = True
    lock = None
    
    def __call__(self, *args, **kwargs):
        
        from aiida.orm.lock import LockManager
        logger.debug('TASK STARTING: %s[%s]' % (self.name, self.request.id))
        
        try:
            self.lock = LockManager().aquire(self.name, timeout=LOCK_EXPIRE, owner=self.request.id)
            logger.debug("GOT lock for {0} by {1}".format(self.name, self.request.id))
            return self.run(*args, **kwargs)
        
        except LockPresent:
            logger.debug("LOCK: Another task is running, I {0} can't start.".format(self.request.id))
            self.lock = None
            return
        
        except InternalError:
            logger.error("ERROR: A lock went over the limit timeout, this could mine the integrity of the system. Reload the Daemon to fix the problem.")
            self.lock = None
            return
            
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        
        if not self.lock==None:
            
            try:
                self.lock.release(owner=self.request.id)
                logger.debug("RELEASED lock for {0} by {1}".format(self.name, self.request.id))
            except ModificationNotAllowed:
                logger.error("ERROR cannot remove the lock for {0} by {1}".format(self.lock.key, self.request.id))
    
    
@celery.task(base=SingleTask)
def submitter():
    from aiida.execmanager import submit_jobs
    submit_jobs()

@celery.task(base=SingleTask)
def updater():
    from aiida.execmanager import update_jobs
    update_jobs()

@celery.task(base=SingleTask)
def retriever():
    from aiida.execmanager import retrieve_jobs
    retrieve_jobs()
        
@celery.task(base=SingleTask)
def workflow_stepper():
    
    from aiida.workflowmanager import daemon_main_loop
    daemon_main_loop()
    
