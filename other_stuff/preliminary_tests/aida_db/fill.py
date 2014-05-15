#!/usr/bin/python
from django.core.management import setup_environ
from scalingtest import settings

import logging
import signal
import sys
import traceback
import os
import random

db = None
machines = ["workstation", "bellatrix", "aires", "titan"]

def signal_handler(signal, frame):
  logging.info('Killing the db connection...')
  db.shutdown()
  sys.exit(0)

# def fillFromICSD():

#   # Run an ICSD query
#   j = icsd.query({"elements":"Pd H C"})

#   for c in j["structures"]:
    
#     try:
      
#       # Get node
#       icdsConf = icsd.asDataNode(c["id"])

#       # Store it in the DB
#       icdsConf.store(db)

#       # Make configuration
#       logging.info("Storing values")
#       confNodeIn = sdk.convertIcsd(icdsConf)
    
#     except:
#       logging.error("Error in %s", c["id"])
#       traceback.print_exc()

#
#
#
def fillFromXYZ(num):

  import aidadb.nodes as nodes
  import aidadb.tools.icsd as icsd
  import aidadb.tools.utils as utils
  import aidadb.sdk as sdk

  global db

  # Init the DB
  db = sdk.getDb('neo4j/data/graph.db')

  # Load many ASE Structures
  sAll = utils.loadXYZs("resources/GDB7_PBE0.xyz", num)
  
  for s in range(len(sAll)):
    
    try:
      
      sdk.setMachine(random.choice(machines))

      print "-----------------------------------"
      print "      Running "+str(s)+"/"+str(num)+"  on "+sdk.machine
      print "-----------------------------------"
      
      logging.info("Converting XYZ")
      xyz  = sdk.xyzToDataNode(sAll[s], db)
      
      logging.info("Building configuration")
      conf = sdk.convertXYZ(xyz, db)
      
      logging.info("Calculating stress")
      res_stress = sdk.stress(conf, db)

      logging.info("Relaxing")
      conf_relaxed, res_relax = sdk.relax(conf, db)

      logging.info("Calculating stress (new conf)")
      res_stres_new = sdk.stress(conf_relaxed, db)

      logging.info("Calculating distance")
      res_distance = sdk.distance(conf, conf_relaxed, db)      

    except:
      traceback.print_exc()

  
  db.shutdown()

def main():

  # Setup Django
  os.environ['DJANGO_SETTINGS_MODULE'] = 'scalingtest.settings'
  if not 'LAMMPS_COMMAND' in os.environ:
    os.environ['LAMMPS_COMMAND'] = '/home/sabatini/lammps-22Feb13/src/lmp_serial'

  # Start and import
  fillFromXYZ(5000);
  
  
if __name__ == "__main__":
  signal.signal(signal.SIGINT, signal_handler)
  main()

