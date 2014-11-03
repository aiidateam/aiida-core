# -*- coding: utf-8 -*-
import os

import aiida.common

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

logger       = aiida.common.aiidalogger.getChild('input')

def import_qeinput(fname):
    """
    This function imports a AiiDA structure from a Quantum ESPRESSO
    input file.
    
    :param fname: the file name that should be read
    """
    import ase
    import aiida.orm.data.structure as struct
    
    
    bohr          = 0.52917720859
    one_over_bohr = 1.0/bohr
    
    cell_types      = ["alat","bohr","angstrom"]
    pos_types       = ["alat","bohr","angstrom","crystal"]
    
    def generate_cell(ibrav, parameters):

        cellAlat = np.zeros((3,3))

        if ibrav==1:
            cellAlat[0][0] = 1; cellAlat[0][1] = 0; cellAlat[0][2] = 0;
            cellAlat[1][0] = 0; cellAlat[1][1] = 1; cellAlat[1][2] = 0;
            cellAlat[2][0] = 0; cellAlat[2][1] = 0; cellAlat[2][2] = 1;

        elif ibrav==2:
            cellAlat[0][0] = -0.5; cellAlat[0][1] = 0; cellAlat[0][2] = 0.5;
            cellAlat[1][0] = 0; cellAlat[1][1] = 0.5; cellAlat[1][2] = 0.5;
            cellAlat[2][0] = -0.5; cellAlat[2][1] = 0.5; cellAlat[2][2] = 0;

        elif ibrav==3:
            cellAlat[0][0] = 0.5; cellAlat[0][1] = 0.5; cellAlat[0][2] = 0.5;
            cellAlat[1][0] = -0.5; cellAlat[1][1] = 0.5; cellAlat[1][2] = 0.5;
            cellAlat[2][0] = -0.5; cellAlat[2][1] = -0.5; cellAlat[2][2] = 0.5;

        elif ibrav==4:
            cellAlat[0][0] = 1; cellAlat[0][1] = 0; cellAlat[0][2] = 0;
            cellAlat[1][0] = -0.5; cellAlat[1][1] = np.sqrt(3)/2; cellAlat[1][2] = 0;
            cellAlat[2][0] = 0; cellAlat[2][1] = 0; cellAlat[2][2] = parameters[2];

        elif ibrav==5:

            tx = np.sqrt((1-parameters[3])/2);
            ty = np.sqrt((1-parameters[3])/6);
            tz = np.sqrt((1+2*parameters[3])/3);

            cellAlat[0][0] = tx; cellAlat[0][1] = -ty; cellAlat[0][2] = tz;
            cellAlat[1][0] = 0; cellAlat[1][1] = 2*ty; cellAlat[1][2] = tz;
            cellAlat[2][0] = -tx; cellAlat[2][1] = -ty; cellAlat[2][2] = tz;

        elif ibrav==-5:

            tx = np.sqrt((1-parameters[3])/2);
            ty = np.sqrt((1-parameters[3])/6);
            tz = np.sqrt((1+2*parameters[3])/3);
            
            u = tz - 2.0*np.sqrt(2.0)*ty
            v = tz + np.sqrt(2.0)*ty
            a1 = 1/np.sqrt(3.0)
             
            cellAlat[0][0] = a1*u; cellAlat[0][1] = a1*v; cellAlat[0][2] = a1*v;
            cellAlat[1][0] = a1*v; cellAlat[1][1] = a1*u; cellAlat[1][2] = a1*v;
            cellAlat[2][0] = a1*v; cellAlat[2][1] = a1*v; cellAlat[2][2] = a1*u;

        elif ibrav==6:

            cellAlat[0][0] = 1; cellAlat[0][1] = 0; cellAlat[0][2] = 0;
            cellAlat[1][0] = 0; cellAlat[1][1] = 1; cellAlat[1][2] = 0;
            cellAlat[2][0] = 0; cellAlat[2][1] = 0; cellAlat[2][2] = parameters[2];

        elif ibrav==7:

            cellAlat[0][0] = 0.5; cellAlat[0][1] = -0.5; cellAlat[0][2] = parameters[2]/2;
            cellAlat[1][0] = 0.5; cellAlat[1][1] = 0.5; cellAlat[1][2] = parameters[2]/2;
            cellAlat[2][0] = -0.5; cellAlat[2][1] = -0.5; cellAlat[2][2] = parameters[2]/2;

        elif ibrav==8:

            cellAlat[0][0] = 1; cellAlat[0][1] = 0; cellAlat[0][2] = 0;
            cellAlat[1][0] = 0; cellAlat[1][1] = parameters[1]; cellAlat[1][2] = 0;
            cellAlat[2][0] = 0; cellAlat[2][1] = 0; cellAlat[2][2] = parameters[2];

        elif ibrav==9:

            cellAlat[0][0] = 0.5; cellAlat[0][1] = parameters[1]/2; cellAlat[0][2] = 0;
            cellAlat[1][0] = -0.5; cellAlat[1][1] = parameters[1]/2; cellAlat[1][2] = 0;
            cellAlat[2][0] = 0; cellAlat[2][1] = 0; cellAlat[2][2] = parameters[1];
        
        elif ibrav==-9:

            cellAlat[0][0] = 0.5; cellAlat[0][1] = -parameters[1]/2; cellAlat[0][2] = 0;
            cellAlat[1][0] = 0.5; cellAlat[1][1] = -parameters[1]/2; cellAlat[1][2] = 0;
            cellAlat[2][0] = 0; cellAlat[2][1] = 0; cellAlat[2][2] = parameters[1];
            
        elif ibrav==10:

            cellAlat[0][0] = 0.5; cellAlat[0][1] = 0; cellAlat[0][2] = parameters[2]/2;
            cellAlat[1][0] = 0.5; cellAlat[1][1] = parameters[1]/2; cellAlat[1][2] = 0;
            cellAlat[2][0] = 0; cellAlat[2][1] = parameters[1]/2; cellAlat[2][2] = parameters[1]/2;

        elif ibrav==11:

            cellAlat[0][0] = 0.5; cellAlat[0][1] = parameters[1]/2; cellAlat[0][2] = parameters[2]/2;
            cellAlat[1][0] = -0.5; cellAlat[1][1] = parameters[1]/2; cellAlat[1][2] = parameters[2]/2;
            cellAlat[2][0] = -0.5; cellAlat[2][1] = -parameters[1]/2; cellAlat[2][2] = parameters[2]/2;

        elif ibrav==12:

            gamma = np.arccos(parameters[3]);

            cellAlat[0][0] = 1; cellAlat[0][1] = 0; cellAlat[0][2] = 0;
            cellAlat[1][0] = parameters[1]*np.cos(gamma); cellAlat[1][1] = parameters[1]*np.sin(gamma); cellAlat[1][2] = 0;
            cellAlat[2][0] = 0; cellAlat[2][1] = 0; cellAlat[2][2] = parameters[2];
        
        elif ibrav==-12:

            beta = np.arccos(parameters[4]);

            cellAlat[0][0] = 1; cellAlat[0][1] = 0; cellAlat[0][2] = 0;
            cellAlat[1][0] = 0; cellAlat[1][1] = parameters[1]; cellAlat[1][2] = 0;
            cellAlat[2][0] = parameters[2]*np.sin(beta); cellAlat[2][1] = 0; cellAlat[2][2] = parameters[2]*np.cos(beta);

        elif ibrav==13:

            gamma = np.arccos(parameters[3]);

            cellAlat[0][0] = 0.5; cellAlat[0][1] = 0; cellAlat[0][2] = -parameters[2]/2;
            cellAlat[1][0] = parameters[1]*np.cos(gamma); cellAlat[1][1] = parameters[1]*np.sin(gamma); cellAlat[1][2] = 0;
            cellAlat[2][0] = 0.5; cellAlat[2][1] = 0; cellAlat[2][2] = parameters[2]/2;

        elif ibrav==14:

            alpha = np.arccos(parameters[3]);
            beta  = np.arccos(parameters[4]);
            gamma = np.arccos(parameters[5]);

            cellAlat[0][0] = 1; cellAlat[0][1] = 0; cellAlat[0][2] = 0;
            cellAlat[1][0] = parameters[1]*np.cos(gamma); cellAlat[1][1] = parameters[1]*np.sin(gamma); cellAlat[1][2] = 0;

            cellAlat[2][0] = parameters[2]*np.cos(beta); 
            cellAlat[2][1] = parameters[2]*(np.cos(alpha)-np.cos(beta)*np.cos(gamma))/(np.sin(gamma)); 
            cellAlat[2][2] = parameters[2]*np.sqrt(1+2*np.cos(alpha)*np.cos(beta)*np.cos(gamma) - (np.cos(beta)*np.cos(beta))-(np.cos(alpha)*np.cos(alpha))-(np.cos(gamma)*np.cos(gamma)))/(np.sin(gamma));
        
        else:
            raise Exception("ibrav [{0}] is not defined !".format(ibrav))
        
    
    def get_pos(pos, coord_type, alat, cell):
        
        if coord_type == pos_types[0]: return np.array(pos)*alat*bohr
        if coord_type == pos_types[1]: return np.array(pos)*alat
        if coord_type == pos_types[3]: return np.dot(np.array(pos),np.array(cell))
    
        return pos

    def get_num_from_name(name):
        
        import ase.data
        for i in range(len(ase.data.chemical_symbols)):
            if ase.data.chemical_symbols[i].lower() == name.lower():
                return i
             
        return -0
    
    def sanitize(line_raw, sec=None):
        if sec is not None:
            return line_raw.split("!")[0].split(sec)[0]
        else:
            return line_raw.split("!")[0]
        
    import re
    import numpy as np
    from fortranformat import FortranRecordReader
    
    nat   = 0
    ntyp  = 0
    ibrav = 0
    
    celldm = None
    a      = None
    b      = None
    c      = None
    cosab  = None
    cosac  = None
    cosbc  = None
    
    cell   = None
    
    atomic_raw_kinds    = None
    atomic_kinds        = None
    atomic_nums         = None
    atomic_pos          = None
    atomic_masses_table = None
    
    #group(3)
    nat_search    = re.compile(r'nat([\t ]+)?=([\t ]+)?([0-9]+)', re.IGNORECASE)
    ntyp_search   = re.compile(r'ntyp([\t ]+)?=([\t ]+)?([0-9]+)', re.IGNORECASE)
    ibrav_search  = re.compile(r'ibrav([\t ]+)?=([\t ]+)?(-?[0-9]+)', re.IGNORECASE)
    
    celldm_search = re.compile(r'celldm([\t ]+)?\(([\t ]+)?([0-9]+)([\t ]+)?\)([\t ]+)?=([\t ]+)?([0-9\.DdeE-]*)', re.IGNORECASE)
    
    a_search  = re.compile(r'a([\t ]+)?=([\t ]+)?(-?[0-9]+)', re.IGNORECASE)
    b_search  = re.compile(r'b([\t ]+)?=([\t ]+)?(-?[0-9]+)', re.IGNORECASE)
    c_search  = re.compile(r'c([\t ]+)?=([\t ]+)?(-?[0-9]+)', re.IGNORECASE)
    cosab_search  = re.compile(r'cosab([\t ]+)?=([\t ]+)?(-?[0-9]+)', re.IGNORECASE)
    cosac_search  = re.compile(r'cosac([\t ]+)?=([\t ]+)?(-?[0-9]+)', re.IGNORECASE)
    cosbc_search  = re.compile(r'cosbc([\t ]+)?=([\t ]+)?(-?[0-9]+)', re.IGNORECASE)
    
    atomic_species  = re.compile(r'ATOMIC_SPECIES', re.IGNORECASE)
    atomic_position = re.compile(r'ATOMIC_POSITIONS', re.IGNORECASE)
    cell_parameters = re.compile(r'CELL_PARAMETERS', re.IGNORECASE)
    
    #group(3) e group(7)
    
    ff_float = FortranRecordReader('F15.9')
    
    f = open(fname, "rw+")
    line = sanitize(f.readline())
    while line:
        
        if nat_search.search(line): nat = int(nat_search.search(line).group(3))
        if ntyp_search.search(line): ntyp = int(ntyp_search.search(line).group(3))
        if ibrav_search.search(line): 
            ibrav = int(ibrav_search.search(line).group(3))
        
        if celldm_search.search(line) and cell is None:
            
            if celldm is None: celldm = [0.0,0.0,0.0,0.0,0.0,0.0]
            for c in celldm_search.findall(line):
                celldm[int(c[2])-1] = ff_float.read(c[6])[0]
            
        if a_search.search(line): a = float(a_search.search(line).group(3))
        if b_search.search(line): b = float(b_search.search(line).group(3))
        if c_search.search(line): c = float(c_search.search(line).group(3))
        if cosab_search.search(line): cosab = float(cosab_search.search(line).group(3))
        if cosac_search.search(line): cosac = float(cosac_search.search(line).group(3))
        if cosbc_search.search(line): cosbc = float(cosbc_search.search(line).group(3))
            
        if cell_parameters.search(line) and nat>0 and ibrav==0 and cell is None:
            
            if celldm is not None and a is not None:
                raise Exception("Cannot declare both celldm and A, B, C, cosAB, cosAC, cosBC")
    
            if a is not None:
                alat = a
            else:
                if celldm is None: 
                    celldm = [one_over_bohr,0.0,0.0,0.0,0.0,0.0]
                alat = celldm[0]
                
            cell_type = cell_types[0] #Alat
            for ct in cell_types: 
                if ct in line.lower(): cell_type = ct

            cell = np.zeros((3,3))
            cell_ax = 0
            while cell_ax<3:
                line = sanitize(f.readline())
                while (line.strip()=="" or line.strip().startswith("!"))=="": line = sanitize(f.readline(), sec="#")
                cell_ax_val = np.array([ff_float.read(p)[0] for p in line.strip().split()])
                
                if cell_type==cell_types[0]: cell_ax_val*=alat*bohr
                if cell_type==cell_types[1]: cell_ax_val*=alat
                
                cell[cell_ax] = cell_ax_val
                cell_ax+=1
        
        if atomic_species.search(line) and ntyp>0:
            atomic_raw_kinds    = [None]*ntyp
            atomic_kinds    = [None]*ntyp
            atomic_masses_table = {}
            
            type_count = 0
            while type_count<ntyp:
                line = sanitize(f.readline())
                while (line.strip()=="" or line.strip().startswith("!")): line = sanitize(f.readline(), sec="#")
                p = line.strip().split()
                
                raw = {'symbols':p[0],'weights':1.0,'name':p[0],'mass':float(p[1])}
                
                _n  = get_num_from_name(p[0])
                atomic_masses_table[_n] = float(p[1])
                
                atomic_raw_kinds[type_count] = raw
                atomic_kinds[type_count] = struct.Kind(symbols=p[0],weights=1.0,name=p[0],mass=float(p[1]))
                
                type_count+=1
        
        if atomic_position.search(line) and nat>0:
            pos_type = "alat"
            for pt in pos_types: 
                if pt in line.lower(): pos_type = pt
            
            atomic_pos   = [[0]*3]*nat
            atomic_nums  = [0]*nat
            
            pos_count = 0
            while pos_count<nat:

                line = sanitize(f.readline())
                while (line.strip()=="" or line.strip().startswith("!")): line = sanitize(f.readline(), sec="#")
                
                p = line.strip().split()
                atomic_nums[pos_count] = get_num_from_name(p[0])
                atomic_pos[pos_count] = [ff_float.read(p[i])[0] for i in range(1,4)]

                pos_count+=1
                
        line = sanitize(f.readline())
    
    # Cell generation
    if celldm is not None and a is not None:
        raise Exception("Cannot declare both celldm and A, B, C, cosAB, cosAC, cosBC")
    
    if a is not None and \
       b is not None and \
       c is not None and \
       cosbc is not None and \
       cosac is not None and \
       cosbc is not None and \
       cell is None:
        
        celldm = [a,b/a,c/a,cosab,cosac,cosbc,0.0]
        cell = generate_cell(ibrav, celldm)
        
    if celldm is not None and ibrav>0 and cell is None: 
        cell = generate_cell(ibrav, celldm)
    
    
    # Positions generation
    for i in range(len(atomic_pos)):
        atomic_pos[i] = get_pos(atomic_pos[i], pos_type, celldm[0], cell)

    # print "nat:", nat
    # print "ntyp:", ntyp
    # print "ibrav:", ibrav
    # print "celldm:", celldm
    # print "cell:", cell
    # print "atomic_types:", atomic_types
    # print "atomic_nums:", atomic_nums#, atomic_pos
    # #print "atomic_pos:", atomic_pos#, atomic_pos
    
    atomic_masses = np.zeros(nat)
    for i in range(len(atomic_nums)):
        atomic_masses[i] = atomic_masses_table[atomic_nums[i]]
    
    
#     s = struct.StructureData(cell=cell, pbc=True)
#     for k in atomic_kinds:
#         s.append_kind(Kind(k))
#      
#     sites = zip(atomic_nums, atomic_pos)
#      
#     for s in sites:
#         s.append_site(Site())

    s_ase = ase.Atoms(numbers=atomic_nums,positions=atomic_pos,cell=cell,pbc=True, masses=atomic_masses)
    return struct.StructureData(ase = s_ase, raw_kinds = atomic_raw_kinds)


    


