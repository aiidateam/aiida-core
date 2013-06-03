from celery.task import task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from celery import Task

logger = get_task_logger(__name__)

LOCK_EXPIRE = 60 * 1000 # Expire time for the retriever 

@task
def update_and_retrieve():

    from aida.execmanager import daemon_main_loop
        
    acquire_lock = lambda: cache.add('update_and_retrieve', 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete('update_and_retrieve')
    
    if acquire_lock():
        try:
            daemon_main_loop()
        finally:
            release_lock()

@task
def workflow_stepper():
    
    from aida.workflowmanager import daemon_main_loop
    
    acquire_lock = lambda: cache.add('workflow_stepper', 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete('workflow_stepper')
    
    if acquire_lock():
        try:
            daemon_main_loop()
        finally:
            release_lock()

