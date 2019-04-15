# -*- coding: utf-8 -*-
"""
Testing the workfunction wrappers
"""

#from sqlalchemy.orm import sessionmaker, aliased
import time

from aiida.workflows2.specs.lib.wflib import *

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

@threadit
@workit_factory()
def top_func(self, **inp):
    self.test = True
    x = inp['x']
    print x.content
#    session4 = Session()
#    session4.add(self)
#    session4.add(x)
#    print "I am", self   # direct access to self will not work unless there is a session during execution
    print inp['x'].content
#    session4.close()
    er = IntData(5)
    print er.content['value']
    a = func10(self)
    b = func20(self, d=er)
    #c = a + b
    c = w4(a).update(w4(b))
    a1 = func10(self, e=er)
    a2 = func10(self, e=er)
    a3 = func10(self, e=er)
    a4 = func10(self)
    a5 = func10(self)

    #k = w4(a1)
    result = c
    print c
    return result

@threadit
@workit_factory()
def ex1(self):
    a = func10()
    b = func20()
    c = func10(w4(a))
    d = func10(w4(b))


@threadit
@workit_factory()
def func10(self, **inp):
    d = IntData(5)
    inp3 = {'a':IntData(3), 'b':d}
    result2 = w4(func20(self, **inp3))
    print inp3['a'].content['value']
    print result2
    time.sleep(1)
    return result2


@threadit
@workit_factory()
def func20(self, **inp):
    v= firstcomp(self, c=IntData(6))
    #result = StringData('result_2 ' + str(inp))
    result = {'f20res': StringData('result_3 ')}
    #print w4(v)
    #a = func10(self)
    #time.sleep(5)
    #print "---cdcd", inp['a'].content
    return result


@threadit
@workit_factory()
def firstcomp(self, c, d=IntData(8)):
    return {'first': IntData(6)}

#session5 = Session()
c = Calc(name='start')
x = IntData(88)
#session5.add_all([c, x])
#session5.commit()

top_func(c, x=x)
res = w4(top_func(c, x=x))
print "result {0}".format(res)
#for item in res:
#    item.roots.append(x)
#session5.commit()

#*******************************

@threadit
@workit_factory()
def func0(self, **inp):
    N = inp['x']
    M = inp['y']
    K = IntData(37)
    output = {'N':N, 'M':M, 'K':K}
    time.sleep(5)
    return output


@threadit
@workit_factory()
def func1(self, **inp):
    n = inp['number']
    double = n * 2
    triple = n * 3
    output = {'outA':double, 'outB':triple}
    time.sleep(n)
    return output


@threadit
@workit_factory()
def func2(self, **inp):
    n = inp['number']
    square = n * n
    cube = n * n * n
    output = {'outC':square, 'outD':cube}
    time.sleep(n)
    return output


@threadit
@workit_factory()
def func3(self, inE, inF):
    #e = inp['inE']
    #f = inp['inF']
    e = inE
    f = inF
    output= {'combined':e + f}
    return output


@threadit
@workit_factory()
def Workflow3(self, **inp):
    step0 = func0(self, x=inp['first'], y=inp['second'])
    result0 = w4(step0)

    step1 = func1(self, number=result0['N'])  #these two are started in parallel
    step2 = func2(self, number=result0['M'])

    result1 = w4(step1)
    result2 = w4(step2)   # block and wait for both results before proceeding

    step3 = func3(self, inE=result1['outB'], inF=result2['outC'])
    result3 = w4(step3)
    output = {'subsum':result3['combined']}
    return output

@threadit
@workit_factory()
def collect4(self, arr):
    output = {'sum': sum(arr)}
    return output

@threadit
@workit_factory()
def Workflow4(self, **inp):
    step = []   #initiate lists
    result = []
    N = inp['Nmax']

    # start multiple parallel runs
    for n in xrange(N):
        step.append(Workflow3(self, first=n, second=n))

    # collect the results once they are all finished
    for n in xrange(N):
        x = w4(step[n])
        result.append(x['subsum'])

    print result
    output = collect4(self, arr = tuple(result))   #tuple to make hashable value
    return w4(output)


#b = Workflow4(c, Nmax=IntData(5))
#print w4(b)

#b = Workflow4(Wstart, Nmax=4)
#print w4(b)
