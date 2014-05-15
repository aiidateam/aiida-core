#!/usr/bin/python
from tempfile import mkstemp
import os
import ase
import json

def arr2json(arr):
    return json.dumps(arr.tolist())

def json2arr(astr, dtype=None):
    if not dtype==None:
      return np.array(json.loads(astr))
    else:
      return np.array(json.loads(astr),dtype=dtype)

def storeDataToFile(cif):

  fd, temp_path = mkstemp()
  f = open(temp_path, "w")
  f.write(cif)
  f.close()
  os.close(fd)

  return temp_path

def loadXYZs(fname, limit=None):

  structs = []

  f = open(fname)
  
  nat = 0
  i = 0
  while 1:
    check = f.readline() 
    if not check: break

    nat  = int(check)
    #s    = ase.atoms.Atoms(cell=[[20.0, 0.0, 0.0],[0.0, 20.0, 0.0],[0.0, 0.0, 20.0]],pbc=(True, True, True))
    xyz  = str(nat)+"\n"

    name = f.readline()
    xyz += name

    for j in range(nat):
      pos_all = f.readline()
      xyz    += pos_all
      #parts   = pos_all.split()
      #s.append(ase.atom.Atom(symbol=parts[0],position=[float(parts[1]), float(parts[2]), float(parts[3])]))

    #structs.append([s,xyz])
    structs.append(xyz)
    i+=1

    if (not limit==None):
      if (i>=limit):
        break

  f.close()
  return structs

