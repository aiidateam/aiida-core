from celery.task import task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from celery import Task
from aiida.common import aiidalogger
import os

logger = get_task_logger(__name__)

LOCK_EXPIRE = 60 * 1000 # Expire time for the retriever, in seconds; should
                        # be a very large number!

@task
def update_and_retrieve():

    from aiida.execmanager import daemon_main_loop
    
    pid = os.getpid()
        
    acquire_lock = lambda: cache.add('update_and_retrieve', 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete('update_and_retrieve')
    
    if acquire_lock():
        aiidalogger.debug("update_and_retrieve called (PID={}), "
                          "and running".format(pid))
        try:
            daemon_main_loop()
        finally:
            release_lock()
    else:
        aiidalogger.debug("update_and_retrieve called (PID={}), but did not "
                          "run due to lock".format(pid))

@task
def workflow_stepper():
    from aiida.workflowmanager import daemon_main_loop
    
    pid = os.getpid()
    
    acquire_lock = lambda: cache.add('workflow_stepper', 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete('workflow_stepper')
    
    if acquire_lock():
        aiidalogger.debug("workflow_stepper called (PID={}), "
                          "and running".format(pid))
        try:
            daemon_main_loop()
        finally:
            release_lock()
    else:
        aiidalogger.debug("workflow_stepper called (PID={}), but did not "
                          "run due to lock".format(pid))

