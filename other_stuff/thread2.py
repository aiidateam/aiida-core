import time
from threading import Thread
from wflib import *

@threaded
@Memoize
def func0(**inp):
    N = inp['x']
    M = inp['y']
    K = 37
    output = {'N':N, 'M':M, 'K':K}
    time.sleep(5)
    return output

@threaded
@Memoize
def func1(**inp):
    n = inp['number']
    double = n * 2
    triple = n * 3
    output = {'outA':double, 'outB':triple}
    time.sleep(n)
    return output

@threaded
@Memoize
def func2(**inp):
    n = inp['number']
    square = n * n
    cube = n * n * n
    output = {'outC':square, 'outD':cube}
    time.sleep(n)
    return output

@threaded
@Memoize
def func3(**inp):
    e = inp['inE']
    f = inp['inF']
    output= {'combined':e + f}
    return output

@threaded
@Memoize
def Workflow3(**inp):
    step0 = func0(x=inp['first'], y=inp['second'])
    result0 = step0.result.get()
    
    step1 = func1(number=result0['N'])
    step2 = func2(number=result0['M'])
  
    result1 = step1.result.get()
    result2 = step2.result.get()
  
    step3 = func3(inE=result1['outB'], inF=result2['outC'])
    result3 = step3.result.get()
    output = {'subsum':result3['combined']}
    return output

#a = Workflow3(first=6, second=7)
#print a.result_queue.get()

@threaded
@Memoize
def Workflow4(**inp):
    step = []   #initiate lists
    result = []
    N = inp['Nmax']
    
    for n in xrange(N):
        step.append(Workflow3(first=n, second=n))
        
    for n in xrange(N):
        x = step[n].result.get()
        result.append(x['subsum'])

    output = {'sum':sum(result)}
    return output


b = Workflow4(Nmax=10)
print b.result.get()

b = Workflow4(Nmax=11)
print b.result.get()

b = Workflow4(Nmax=8)
print b.result.get()