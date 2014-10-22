# -*- coding: utf-8 -*-
"""
This module is used to interface AiiDA with the Moka GUI.
"""
from xmlrpclib import ServerProxy, Error

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

moka_server = ServerProxy("http://localhost:8088")

start_prefix = "####----start:"
end_prefix  = "####----end:"

def get_structures(lines):

    structs = []
    buff = ""
    
    in_structure = False;
    for line in lines.split("\n"):
        
        if line.startswith(start_prefix):
            in_structure = True;
        
        elif line.startswith(end_prefix):
            if (in_structure):
                structs.append(buff)
            buff=""
            in_structure = False;
        
        else:
            if (in_structure):
                buff+=line+"\n"
    
    return structs

def view(s):
    
    try:
        data = start_prefix+"\n"+dirty_qe(s)+end_prefix
        moka_server.RpcOpener.importQeInput(data)
    except Error as v:
        print "ERROR", v

def get():

    import tempfile
    import ase.io

    try:
        data    = moka_server.RpcOpener.exportInp("Xsf")
        pwin     = get_structures(data)[0]
        
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(pwin)
            temp.flush()
            ase_s = ase.io.read(temp.name, format="xsf")

        return ase_s

    except Error as v:
        print "ERROR", v

def get_many(verbose=False):

    import tempfile
    import ase.io

    try:
        data     = moka_server.RpcOpener.exportAllInp("Xsf")
        if verbose:
            print data
        all_pwin = get_structures(data)
        all_ase  = []
        
        for pwin in all_pwin:
            
            with tempfile.NamedTemporaryFile() as temp:
                temp.write(pwin)
                temp.flush()
                all_ase.append(ase.io.read(temp.name, format="xsf"))

        return all_ase

    except Error as v:
        print "ERROR", v

def dirty_qe(s, fout=None, force_kind_order = False, velocities=None):
    import aiida.orm.data.structure as struct
    import StringIO
    
    if not isinstance(s, struct.StructureData):
        return
    
    output = StringIO.StringIO()
    
    output.write("&system\n");
    output.write("nat="+str(len(s.sites))+", ntyp="+str(len(s.kinds))+",\n");
    output.write("ibrav=0, celldm(1)=1.88972687000");
    output.write("\n");
    
    #   Species
    output.write("\nATOMIC_SPECIES\n")
    for k in s.kinds:
        output.write("{0}\t{1:7.2f}\t{2}\n".format(k.name,k.mass,k.symbol+".UPF"))

    #   Positions
    output.write("\nATOMIC_POSITIONS (angstrom)\n")
    
    if force_kind_order:
        for k in s.kinds:
            for i in s.sites:
                if i.kind == k.symbol:
                    output.write("{0}\t{1:15.10f}\t{2:15.10f}\t{3:15.10f}\n".format(i.kind, i.position[0], i.position[1], i.position[2]))
    else:
        for i in s.sites:
            for k in s.kinds:
                if i.kind == k.symbol:
                    output.write("{0}\t{1:15.10f}\t{2:15.10f}\t{3:15.10f}\n".format(i.kind, i.position[0], i.position[1], i.position[2]))
        
    
    #   Cell    
    output.write("\nCELL_PARAMETERS\n")
    for i in range(3):
        output.write("{0:15.10f}\t{1:15.10f}\t{2:15.10f}\n".format(s.cell[i][0], s.cell[i][1], s.cell[i][2]))
   
    # Velocities
    if velocities is not None:
        output.write("\nATOMIC_VELOCITIES\n")
        for v in velocities:
            output.write("{0}\t{1:15.10f}\t{2:15.10f}\t{3:15.10f}\n".format(v[0], v[1][0], v[1][1], v[1][2]))
   
    data =  output.getvalue()
    output.close()
    
    if fout is not None:
         with open(fout, "w") as f:
            f.write(data)
   
    return data