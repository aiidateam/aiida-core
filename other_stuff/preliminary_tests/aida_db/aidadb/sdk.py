#!/usr/bin/python
from scaling.models import DataCalc, Attribute;

from neo4j import GraphDatabase

from ase import Atoms, Atom
from ase.calculators.lammps import LAMMPS
from ase.optimize import BFGS
import ase.io

import json
import os.path

import logging
import copy
import numpy as np
import nodes
import tools.utils as utils
import numpy as np

calc = LAMMPS()
machine = 'laptop'

def getDb(dbName='db.tests/demo1'):

  if (os.path.isdir(dbName)):
    logging.info('GraphDb found, loading...')
    return GraphDatabase(dbName)
  else:
    logging.info('GraphDb not found, generating...')
    db = GraphDatabase(dbName)
    setUpDB(db)
    return db


def setUpDB(db):

  """Generates the initial DB structure, indexes and nodes

  Keyword arguments:
  db -- the GraphDatabase object initialized
  
  """

  # All write operations happen in a transaction
  with db.transaction:
 
    # Nodes indexes
    if (not db.node.indexes.exists("configurations")):
      db.node.indexes.create('configurations', type='fulltext')
    if (not db.node.indexes.exists("parameters")):
      db.node.indexes.create('parameters', type='fulltext')
    if (not db.node.indexes.exists("results")):
      db.node.indexes.create('results', type='fulltext')
    if (not db.node.indexes.exists("calculations")):
      db.node.indexes.create('calculations')
    if (not db.node.indexes.exists("all")):
      db.node.indexes.create('all', type='fulltext')

    # Relationships indexes
    #db.relationship.indexes.create("aaa")


#
#
#

def xyzToDataNode(xyz, db):
  
  title = xyz.split("\n")[1]
  data = {'xyz':xyz};  
  data_n = nodes.Data('xyz', title, data)
  data_n.store(db)
  data_n.storeInDjango()

  return data_n


def convertIcsd(dataNode, db):

  if (not dataNode.getContent()=='icsd'):
    raise Exception("Not and ICSD Data node!")

  try:
    
    f = utils.storeDataToFile(dataNode.getData()['cif'])
    ase_s = ase.io.read(f, format="cif")
    ase_n = Configuration(ase=ase_s)
    ase_n.store(db)

    with db.transaction:
      dataNode.getNode().ORIGIN_OF(ase_n.getNode())

  except:
    raise Exception("Error -- DEBUG")

  return ase_n

def convertXYZ(dataNode, db):

  if (not dataNode.getContent()=='xyz'):
    raise Exception("Not and XYZ Data node!")

  try:
    
    f = utils.storeDataToFile(dataNode.getData()['xyz'])
    ase_s = ase.io.read(f, format="xyz")
    
    ase_s.set_cell([20.0, 20.0, 20.0])
    ase_s.set_pbc([ True,  True,  True])
    
    conf_n = nodes.Configuration(ase=ase_s)
    conf_n.store(db)
    conf_n.storeInDjango()

    if (not dataNode.isStored()):
      dataNode.store(db)

    if (not dataNode.isStoredInDjango()):
      dataNode.storeInDjango()

    with db.transaction:
      dataNode.getNode().ORIGIN_OF(conf_n.getNode())

    dataNode.getNodeInDjango().children.add(conf_n.getNodeInDjango())
    dataNode.getNodeInDjango().save();

    return conf_n

  except:
    raise Exception("Error -- DEBUG")

  return None

def stress(conf_in_n, db):

  ase_s = conf_in_n.toAse()
  ase_s.set_calculator(calc)
  stress = ase_s.get_stress()
  
  calc_n = nodes.Calculation('StressLAMMPS','3.6.1.3043',machine)
  calc_n.store(db)
  calc_n.storeInDjango()

  res_n  = nodes.Results('stress', 'LAMMPS stress', '{"stress":"'+utils.arr2json(stress)+'"}')
  res_n.store(db)
  res_n.storeInDjango()

  if (not conf_in_n.isStored()):
    conf_in_n.store(db)

  if (not conf_in_n.isStoredInDjango()):
    conf_in_n.storeInDjango()

  with db.transaction:
    conf_in_n.getNode().INPUT(calc_n.getNode())
    conf_in_n.getNodeInDjango().children.add(calc_n.getNodeInDjango())

    res_n.getNode().OUTPUT(calc_n.getNode())
    calc_n.getNodeInDjango().children.add(res_n.getNodeInDjango())

  return res_n


def relax(conf_in_n, db):

  ase_s = conf_in_n.toAse()
  ase_s.set_calculator(calc)
  
  dyn = BFGS(ase_s, logfile=None)
  dyn.run(fmax=0.05,steps=10)
  en = ase_s.get_potential_energy()

  calc_n = nodes.Calculation('RelaxLAMMPS','3.6.1.3043',machine)
  calc_n.store(db)
  calc_n.storeInDjango()

  conf_new = nodes.Configuration(ase=ase_s)
  conf_new.store(db)
  conf_new.storeInDjango()

  res_n  = nodes.Results('energy', 'LAMMPS energy', '{"energy":'+str(en)+'}')
  res_n.store(db)
  res_n.storeInDjango()

  if (not conf_in_n.isStored()):
    conf_in_n.store(db)

  if (not conf_in_n.isStoredInDjango()):
    conf_in_n.storeInDjango()

  with db.transaction:
    conf_in_n.getNode().INPUT(calc_n.getNode())
    conf_in_n.getNodeInDjango().children.add(calc_n.getNodeInDjango())

    res_n.getNode().OUTPUT(calc_n.getNode())
    calc_n.getNodeInDjango().children.add(res_n.getNodeInDjango())

    conf_new.getNode().OUTPUT(calc_n.getNode())
    calc_n.getNodeInDjango().children.add(conf_new.getNodeInDjango())

  return conf_new, res_n


def distance(conf_a, conf_b, db):

  if (not conf_a.getNat()==conf_b.getNat()):
    return None

  d = 0.0
  for i in range(len(conf_a.getPositions())):
    d += np.linalg.norm(conf_a.getPositions()[i]-conf_b.getPositions()[i])
  d /= conf_a.getNat()
  
  calc_n = nodes.Calculation('EuclidDist','3.6.1.3043',machine)
  calc_n.store(db)
  calc_n.storeInDjango()

  res_n  = nodes.Results('distance', 'Euclidean distance', '{"distance":'+str(d)+'}')
  res_n.store(db)
  res_n.storeInDjango()

  if (not conf_a.isStored()):
    conf_a.store(db)
  
  if (not conf_a.isStoredInDjango()):
    conf_a.storeInDjango()

  if (not conf_b.isStored()):
    conf_b.store(db)

  if (not conf_b.isStoredInDjango()):
    conf_b.storeInDjango()

  with db.transaction:
    conf_a.getNode().INPUT(calc_n.getNode())
    conf_a.getNodeInDjango().children.add(calc_n.getNodeInDjango())

    conf_b.getNode().INPUT(calc_n.getNode())
    conf_b.getNodeInDjango().children.add(calc_n.getNodeInDjango())

    res_n.getNode().OUTPUT(calc_n.getNode())
    calc_n.getNodeInDjango().children.add(res_n.getNodeInDjango())

  return res_n

def setMachine(_machine):

  global machine
  machine = _machine
