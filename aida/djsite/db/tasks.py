from celery.task import task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from celery import Task
from aida.execmanager import daemon_main_loop

logger = get_task_logger(__name__)

LOCK_EXPIRE = 60 * 1000 # Expire time for the retriever 

@task
def update_and_retrieve():
    
    acquire_lock = lambda: cache.add('update_and_retrieve', 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete('update_and_retrieve')
    
    if acquire_lock():
        try:
            daemon_main_loop()
        finally:
            release_lock()

@task
def collector(_var):
    
  print "Collactor has been called with value: "
  print "---------------------------------------"
  print _var
  print "---------------------------------------"


# @task
# class WorkflowLauncherTask(Task):

# 	def __init__(self, ):
		
# 		Task.__init__(self)

#     def run(self, x, y):
#         return x + y
