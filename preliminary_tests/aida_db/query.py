#!/usr/bin/python
from django.core.management import setup_environ
from scalingtest import settings

import logging
import signal
import sys
import traceback
import os
import random
import time

db = None

def signal_handler(signal, frame):
  logging.info('Killing the db connection...')
  db.shutdown()
  sys.exit(0)

class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print 'elapsed time: %f ms' % self.msecs

def queryDjango(q, en):

  from scaling.models import DataCalc, Attribute
  from django.db.models import Q

  res = None
  out = None
  t   = None
  #
  #
  #
  if q==0:
    with Timer() as t:
      res = DataCalc.objects.filter(datatype = "Configuration",
        children__datatype = "Calculation",
        children__attribute__key = "machine",
        children__attribute__val_text__startswith = "bellatrix",
        children__children__datatype= "Results",
        children__children__attribute__key = "energy",
        children__children__attribute__val_num__lt = en).distinct()
    
      attrs = {a["datacalc__id"]:int(a["val_num"]) for a in Attribute.objects.filter(datacalc__in=res, key="nat").values("datacalc__id","val_num")}
      out = [[attrs[p["id"]],p["children__children__attribute__val_num"]] for p in res.values("children__children__attribute__val_num", "id")]
      out.sort(key=lambda x: (x[0], x[1]))

    #print "Query DJANGODB took "+str(t.secs)
    t = t.secs

  if q == 1:
    with Timer() as t:
      res = DataCalc.objects.filter(datatype = "Data",
        destinations__datatype = "Calculation",
        destinations__attribute__key = "machine",
        destinations__attribute__val_text__startswith = "aires",
        destinations__destinations__datatype = "Results",
        destinations__destinations__attribute__key = "energy",
        destinations__destinations__attribute__val_num__lt = en).distinct()
      attrs = {a["datacalc__id"]:a["val_text"] for a in Attribute.objects.filter(datacalc__in=res, key="title").values("datacalc__id","val_text")}
      
      out = [[attrs[p["id"]],p["destinations__destinations__attribute__val_num"]] for p in res.values("destinations__destinations__attribute__val_num", "id")]
      out.sort(key=lambda x: (x[0], x[1]))

    #print "Query DJANGODB took "+str(t.secs)
    t = t.secs

  return out, t

def queryNeo(qid, en):

  import aidadb.nodes as nodes
  import aidadb.tools.icsd as icsd
  import aidadb.tools.utils as utils
  import aidadb.sdk as sdk

  global db

  q = []

  # Filter starting configuration from results value
  q.append("""START res=node:all(type = 'Results')
  MATCH res-[:OUTPUT]->calc<-[:INPUT]-conf

  WHERE calc.machine =~ "bellatrix" 
  AND res.content =~ "energy" 
  AND res.energy < """+str(en)+""" 
  AND conf.type = "Configuration"
  
  RETURN res.energy, conf.nat""");

  q.append("""START data=node:all(type = 'Data:xyz')
  MATCH data-[*]->calc<-[*]-out

  WHERE out.type = 'Results' 
  AND out.content="energy" 
  AND out.energy < """+str(en)+""" 
  AND calc.type = 'Calculation' 
  AND calc.machine =~ "aires"
  
  RETURN data.title, out.energy""")

  # Init the DB
  db = sdk.getDb('neo4j/data/graph.db')
  print dir(db)

  out = None
  t   = None

  if qid==0:
    with Timer() as t:
      res = db.query(q[0])
      
      out = [[r["conf.nat"].intValue(),r["res.energy"].doubleValue()] for r in res]
      out.sort(key=lambda x: (x[0], x[1]))
    
    #print "Query NEO4J took "+str(t.secs)
    t = t.secs

  if qid==1:
    with Timer() as t:
      res = db.query(q[1])

      out = [[r["data.title"],r["out.energy"].doubleValue()] for r in res]
      out.sort(key=lambda x: (x[0], x[1]))

    #print "Query took "+str(t.secs)
    t = t.secs
 
  db.shutdown()

  return out, t

def testQuery(qid, en):

  out_neo, t_neo = queryNeo(qid, en);
  out_dj, t_django  = queryDjango(qid, en);

  if out_neo==out_dj:
    print "%s\t%s\t%s\t%s" %(t_neo, t_django, len(out_dj), en)
  

def main():

  # Setup Django
  os.environ['DJANGO_SETTINGS_MODULE'] = 'scalingtest.settings'
  if not 'LAMMPS_COMMAND' in os.environ:
    os.environ['LAMMPS_COMMAND'] = '/home/sabatini/lammps-22Feb13/src/lmp_serial'

  print "#Forward 0"
  for i in range(20):
    testQuery(0, -i-20)

  print "#Backward 0"
  for i in range(20)[::-1]:
    testQuery(0, -i-20)

  print "#Forward 1"
  for i in range(20):
    testQuery(1, -i-20)

  print "#Backward 1"
  for i in range(20)[::-1]:
    testQuery(1, -i-20)

if __name__ == "__main__":
  signal.signal(signal.SIGINT, signal_handler)
  main()

