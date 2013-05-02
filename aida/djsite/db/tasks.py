from celery.task import task
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)
from celery import Task

from aida.execmanager import daemon_main_loop

@task
def update_and_retrieve():
    daemon_main_loop()

#@task
#def poll(_i,_s):
#    from time import sleep
#
#    print "Polling with args "+str(_i)+" and "+str(_s)+" ..."
#    sleep(5)
#    print "Polled"

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
