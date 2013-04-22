#!/usr/bin/python
from scaling.models import DataCalc, Attribute;
import uuid
import tools.utils as utils
import ase.io
import ase
import logging
import json

class StorableClass(object):

  node = None
  djnode = None

  stored = False
  djstored = False

  def __init__(self):
    pass

  def store(self, db):
    pass

  def getNode(self):
    return self.node
  
  def isStored(self):
    return self.stored

  def getNodeInDjango(self):
    return self.djnode
  
  def isStoredInDjango(self):
    return self.djstored

#
#
#

class Configuration(StorableClass):

  """A simple example class"""
  
  def __init__(self, *args, **kwargs):

    #super(StorableClass, self).__init__()
    
    if ('ase' in kwargs):
    	self.initFromAse(kwargs['ase'])

    elif ('icsd' in kwargs):
    	self.initFromIcsdNode(kwargs['icsd'])

    else:

      self.type     = 'Configuration'
      self.formula  = ''
      self.nat      = 0
      self.cell     = ''
      self.position = ''
      self.atoms    = ''

  def store(self, db):

    with db.transaction:

        conf_n = db.node()
        conf_n['type']      = self.type
        conf_n['formula']   = self.formula
        conf_n['nat']       = self.nat
        conf_n['cell']      = utils.arr2json(self.cell)
        conf_n['positions'] = utils.arr2json(self.positions)
        conf_n['atoms']     = utils.arr2json(self.atoms)

        # Indexes
        all_idx = db.node.indexes.get("all")
        all_idx['type'][self.type] = conf_n
        all_idx['text'][self.formula] = conf_n

        conf_idx = db.node.indexes.get("configurations")
        conf_idx['nat'][self.nat] = conf_n
        conf_idx['formula'][self.formula] = conf_n

    self.node = conf_n
    self.stored = True

  def storeInDjango(self):

    c = DataCalc(uuid=str(uuid.uuid4()), isdata=True, datatype=self.type)
    c.save();
    
    Attribute(datacalc=c, key="formula", val_text=self.formula).save();
    Attribute(datacalc=c, key="nat", val_num=self.nat).save();
    Attribute(datacalc=c, key="cell", val_text=utils.arr2json(self.cell)).save();
    Attribute(datacalc=c, key="positions", val_text=utils.arr2json(self.positions)).save();
    Attribute(datacalc=c, key="atoms", val_text=utils.arr2json(self.atoms)).save();

    self.djnode = c
    self.djstored = True

  def load(self, db, nid):

    with db.transaction:

      conf_n       = db.node[nid]
      
      self.formula = conf_n['formula']
      self.nat     = conf_n['nat']
      self.cell      = utils.json2arr(conf_n['cell'])
      self.positions = utils.json2arr(conf_n['positions'])
      self.atoms     = utils.json2arr(conf_n['atoms'])

      self.node = conf_n
      self.stored = True

  def initFromAse(self, ase_in):

    self.type      = 'Configuration'
    self.formula   = ase_in.get_chemical_formula()
    self.nat       = ase_in.get_number_of_atoms()
    self.cell      = ase_in.get_cell()
    self.positions = ase_in.get_positions()
    self.atoms     = ase_in.get_atomic_numbers()

  def initFromIcsdNode(self, n_icsd):

    if (not n_icsd.getContent() == 'icsd'):
    	pass

    f = utils.storeDataToFile(n_icsd.getData()['cif'])
    self.initFromAse(ase.io.read(f, format="cif"))

  def toAse(self):

    return ase.Atoms(numbers=self.atoms, positions=self.positions, cell=self.cell, pbc=[ True,  True,  True])

  def getNat(self):
  	return self.nat

  def getAtomNumbers(self):
  	return self.atoms

  def getCell(self):
  	return self.cell

  def getPositions(self):
  	return self.positions


#
#
#

class Data(StorableClass):

  """A simple example class"""
  
  def __init__(self):

    #super(StorableClass, self).__init__()

    self.type    = 'Data'
    self.content = 'NoContent'
    self.title   = 'NoTitle'
    self.data    = {}
    
  def __init__(self, content_in, title_in, data_in):

    #super(StorableClass, self).__init__()

    self.type    = 'Data'
    self.content = content_in
    self.title   = title_in
    self.data    = data_in

  def store(self, db):

    with db.transaction:

      data_n = db.node()

      data_n['type']      = self.type
      data_n['content']   = self.content
      data_n['title']     = self.title

      for k in self.data:
      	if (not k=='type' and not k=='title' and not k=='content'):
      		data_n[k] = self.data[k]
      
      # Indexes
      all_idx = db.node.indexes.get("all")
      all_idx['type'][self.type+":"+self.content] = data_n
      all_idx['text'][self.title] = data_n

      self.node = data_n
      self.stored = True

  def storeInDjango(self):

    c = DataCalc(uuid=str(uuid.uuid4()), isdata=True, datatype=self.type)
    c.save();
    
    Attribute(datacalc=c, key="content", val_text=self.type).save();
    Attribute(datacalc=c, key="title", val_text=self.title).save();

    for k in self.data:
        if (not k=='type' and not k=='title' and not k=='content'):
          Attribute(datacalc=c, key=k, val_text=self.data[k]).save();

    self.djnode = c
    self.djstored = True

  def load(self, db, nid):

    with db.transaction:

      data_n       = db.node[nid]

      self.content = data_n['content']
      self.title   = data_n['title']
      
      for k in data_n:
        	if (not k=='type' and not k=='title' and not k=='content'):
        		self.data[k] = data_n[k]

      self.node = data_n
      self.stored = True
    
  def getTitle(self):
  	return self.title

  def getContent(self):
  	return self.content

  def getData(self):
  	return self.data


#
#
#

class Calculation(StorableClass):

  """A simple example class"""
  
  def __init__(self):

    #super(StorableClass, self).__init__()

    self.type    = 'Calculation'
    self.code = 'NoCode'
    self.version   = 'NoVersion'
    self.machine    = 'NoMachine'
    
  def __init__(self, code, version, machine):

    #super(StorableClass, self).__init__()

    self.type    = 'Calculation'
    self.code = code
    self.version   = version
    self.machine    = machine
    
  def store(self, db):

    with db.transaction:

        calc_n = db.node()
        calc_n['type'] = self.type
        calc_n['code'] = self.code
        calc_n['version'] = self.version
        calc_n['machine'] = self.machine

        # Indexes
        all_idx = db.node.indexes.get("all")
        all_idx['type'][self.type] = calc_n
        all_idx['text'][self.code] = calc_n

        calc_idx = db.node.indexes.get("calculations")
        calc_idx['code'][self.code] = calc_n
        calc_idx['machine'][self.machine] = calc_n

        self.node = calc_n
        self.stored = True

  def storeInDjango(self):

    c = DataCalc(uuid=str(uuid.uuid4()), isdata=False, datatype=self.type)
    c.save();
    
    Attribute(datacalc=c, key="code", val_text=self.code).save();
    Attribute(datacalc=c, key="version", val_text=self.version).save();
    Attribute(datacalc=c, key="machine", val_text=self.machine).save();

    self.djnode = c
    self.djstored = True

  def load(self, db, nid):

    with db.transaction:

      calc_n       = db.node[nid]

      self.code   = calc_n['code']
      self.version   = calc_n['version']
      self.machine   = calc_n['machine']

      self.node = calc_n
      self.stored = True

  def getCode(self):
    return self.code

  def getVersion(self):
    return self.version

  def getMachine(self):
    return self.machine


#
#
#

class Results(StorableClass):

  """A simple example class"""
  
  def __init__(self):

    #super(StorableClass, self).__init__()

    self.type    = 'Results'
    self.content = 'NoContent'
    self.data    = {}
    
  def __init__(self, content_in, title_in, data_in):

    #super(StorableClass, self).__init__()

    self.type    = 'Results'
    self.content = content_in
    self.data    = data_in
    
  def store(self, db):

    with db.transaction:

        res_n = db.node()

        res_n['type']      = self.type
        res_n['content']   = self.content

        jsond = json.loads(self.data)
        for k in jsond:
          if (not k=='type' and not k=='title' and not k=='content'):
            res_n[k] = jsond[k]
        
        # Indexes
        all_idx = db.node.indexes.get("all")
        all_idx['type'][self.type] = res_n
        all_idx['text'][self.content] = res_n

        jsond = json.loads(self.data)
        res_idx = db.node.indexes.get("results")
        for key in jsond:
          res_idx[key][jsond[key]] = res_n

        self.node = res_n
        self.stored = True
    
  def storeInDjango(self):

    c = DataCalc(uuid=str(uuid.uuid4()), isdata=True, datatype=self.type)
    c.save();
    
    Attribute(datacalc=c, key="content", val_text=self.type).save();

    jsond = json.loads(self.data)
    for k in jsond:
      if (not k=='type' and not k=='title' and not k=='content'):
        Attribute(datacalc=c, key=k, val_text=jsond[k]).save();
    
    self.djnode = c
    self.djstored = True

  def load(self, db, nid):

    with db.transaction:

      res_n       = db.node[nid]
      self.content = conf_n['content']
      
      jsond = json.loads(self.content)
      for k in jsond:
        if (not k=='type' and not k=='title' and not k=='content'):
          res_n[k] = jsond[k]

      self.node = res_n
      self.stored = True
    
  def getContent(self):
    return self.content

  def getData(self):
    return self.data


