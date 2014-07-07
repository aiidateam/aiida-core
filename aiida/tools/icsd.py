#!/usr/bin/python
# -*- coding: utf-8 -*-
import pymysql
import re
import shlex
from ase.parallel import paropen
from ase.lattice.spacegroup import crystal
from ase.lattice.spacegroup.spacegroup import spacegroup_from_data
import numpy as np

import requests, json
import unicodedata
import aiida.common


__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

icsd_addr = "theospc12.epfl.ch"
apiUrl    = "http://"+icsd_addr+"/icsd/api/"
debug     = False

db        = pymysql.connect(host=icsd_addr, port=3306, user='dba', passwd='sql', database='icsd')


def do_shlex(value):

    lex = shlex.shlex(value, posix=True)
    lex.quotes = '\'"'
    lex.escapedquotes = '\'"'
    lex.whitespace_split = True
    #lex.commenters = ''
    return list(lex)


def get_atoms(idnum):

    symbols = []
    x       = []
    y       = []
    z       = []
    
    cur_elements = db.cursor()
    cur_elements.execute("SELECT * FROM p_record where idnum={0}".format(idnum))
    for row_elements in cur_elements.fetchall() :
    
        _element = row_elements[2].strip()
        _multi   = row_elements[5]
        _multi_l = row_elements[6]
        _x       = row_elements[10]
        _y       = row_elements[11]
        _z       = row_elements[12]
        _occ     = row_elements[14]
        
        #print "{0} [{1}, {2}, {3}] - {4}{5} [{6}]".format(_element, _x,_y,_z, _multi, _multi_l, _occ)
        if (_x==None or _y==None or _z==None):
            if not _multi_l=="*":
                raise Exception("Cannot add element with no positions")
        elif not _occ==1 and not _occ==None:
            raise Exception("Not able to handle partial occupancies")
        else:
        
            symbols.append(_element)
            x.append(float(_x))
            y.append(float(_y))
            z.append(float(_z))
    
      #print "{0} [{1}, {2}, {3}] - {4}{5}".format(_element, _x,_y,_z, _multi, _multi_l)
    
    return symbols, x, y, z

def get_spacegroup(sgr):

    cur_sp = db.cursor()
    cur_sp.execute("SELECT smat_genrpos, sgr_disp, sgr_num FROM space_group where sgr='{0}'".format(sgr))
    
    row_sp      = cur_sp.fetchone()
    genrpos_raw = row_sp[0]
    sgr_disp    = row_sp[1].replace(' Z','').replace(' S','').replace(' H','')
    sgr_num     = int(row_sp[2])
    genrpos     = []
    
    for l in genrpos_raw.splitlines():
        parts = do_shlex(l)
        #genrpos.append([int(parts[0]),parts[1]])
        genrpos.append(parts[1])
    
    #print "{0} {1}".format(sgr_disp, sgr_num)
    #print "{0}".format(genrpos)
    
    try:
        spacegroup = spacegroup_from_data(no=sgr_num, symbol=sgr_disp,sitesym=genrpos)
        return spacegroup
    except:
        raise Exception("Error generating spacegroup")

def get_structure(idnum, idtype="coll_code"):
    from aiida.djsite.utils import get_automatic_user
    import aiida.orm.data.structure as struct
    
    # Sql starting
    cur = db.cursor()
    cur.execute("SELECT * FROM icsd where {0}={1}".format(idtype,idnum))
    
    row = cur.fetchone()
    idnum       = row[0]
    chem_name   = row[2]
    a           = float(row[22])
    b           = float(row[23])
    c           = float(row[24])
    alpha       = float(row[25])
    beta        = float(row[26])
    gamma       = float(row[27])
    sgr         = row[4]
    coll_code   = row[6]
    
  #print "{0} {1} [{2}, {3}, {4}] [{5}, {6}, {7}] {8}".format(idnum, chem_name, a,b,c, alpha,beta,gamma, sgr)
    
    try:
    
        #print "Getting symbols"
        symbols, x, y, z = get_atoms(idnum)
        scaled_positions = np.array([x,y,z]).T
        
        spacegroup = get_spacegroup(sgr) 
        
        s = crystal(symbols, basis=scaled_positions,
                cellpar=[a, b, c, alpha, beta, gamma],
                spacegroup=spacegroup, ondublicates='replace')
      
        aiida_s = struct.StructureData(ase=s)
        aiida_s.store()
        # TODO: Better: add a DbExtra!!
        aiida_s.add_comment("Origin: ICSD {0}={1}".format(idtype,idnum),
                            user=get_automatic_user())
        
        return aiida_s
    
    except Exception as e:
      raise Exception(e)


def query(params_in):

    r = requests.get(apiUrl+"search.php", params=params_in)
    if r.status_code == requests.codes.ok:
        if debug: print "Respose query received"
        #return json.loads(r.text)
        return json.loads(unicodedata.normalize('NFKD', r.text).encode('ascii','ignore'))
    
    else:
        if debug: print "Error query [code "+r.status_code+"]"
        return None


