from celery.task import task
from time import sleep
 
@task
def poll(_i,_s):

    print "Polling with args "+str(_i)+" and "+str(_s)+" ..."
    sleep(5)
    print "Polled"

@task
def collector(_var):
    
  print "Collactor has been called with value: "
  print "---------------------------------------"
  print _var
  print "---------------------------------------"

