import time
from threading import Thread
from wflib import *

#@threaded
@Memoize
def func1(**inp):
    n = inp['number']
    double = n * 2
    triple = n * 3
    output = {'outA':double, 'outB':triple}
    time.sleep(n)
    return output

#@threaded
@Memoize
def func2(**inp):
    n = inp['number']
    square = n * n
    cube = n * n * n
    output = {'outC':square, 'outD':cube}
    time.sleep(n)
    return output

#@Memoize
def func3(**inp):
    e = inp['inE']
    f = inp['inF']
    output= {'sum':e + f}
    return output

#@Memoize    
def Workflow1(**inp):
    #N = 4
    #inp1 = {'number': N}
    #result1 = step1(**inp1)
    result1 = func1(number=inp['N'])
    
    #M = 5
    #inp2 = {'number': M}
    #result2 = step2(**inp2)
    result2 = func2(number=inp['M'])
    
    #inp3 = {'inE':result1['outB'], 'inF':result2['outC']}
    #result3 = step3(**inp3)
    result3 = func3(inE=result1['outB'], inF=result2['outC'])
    return result3


#print Workflow1(N=2,M=7)    
#Workflow1(N=3,M=4)
#Workflow1(N=4,M=5)
#Workflow1(N=2,M=4)
#print Workflow1(N=2,M=7)  
#print Workflow1(N=6,M=7)  

##############################################

#@Memoize
def Workflow2(**inp):
    step1 = threaded(func1)(number=inp['N'])
    step2 = threaded(func2)(number=inp['M'])
    result1 = step1.result_queue.get()
    result2 = step2.result_queue.get()
    print result1
    print result2
    result3 = func3(inE=result1['outB'], inF=result2['outC'])
    return result3
#    inp1 = {'number': N}
#    step1 = Thread(target=func1, kwargs=inp1)
#    inp1 = {'number': M}
#    step2 = Thread(target=func2, kwargs=inp2)
#    inp3 = {'inE':result1['outB'], 'inF':result2['outC']}


print Workflow2(N=6, M=7)
print Workflow2(N=6, M=3)
    


