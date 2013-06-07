import os

import aiida.common

logger       = aiida.common.aiidalogger.getChild('input')

def import_cif(fname):
    
    import ase.io
    import aiida.orm.data.structure as struct
    
    ase_s = ase.io.read("icsd_246817.cif", format="cif")
    s = struct.StructureData(ase=ase_s)
    s.store()
    s.add_comment("Origin: "+fname)
    
    return s


def dirty_qe(s, fout=None):
    
    import aiida.orm.data.structure as struct
    import StringIO
    
    if not isinstance(s, struct.StructureData):
        return
    
    output = StringIO.StringIO()
    
    output.write("""&system
  nat="""+str(len(s.sites))+""", ntyp="""+str(len(s.get_elements()))+""",
  ibrav=0, celldm(1)=1.88972687000
/\n
""")
    
    output.write("\nATOMIC_SPECIES\n")
    for i in s.get_elements():
        output.write("{0}\t{1:7.2f}\t{2}\n".format(i,struct._atomic_masses[i],i+".UPF"))

    output.write("\nATOMIC_POSITIONS (angstrom)\n")
    
    for i in s.sites:
        output.write("{0}\t{1:15.10f}\t{2:15.10f}\t{3:15.10f}\n".format(i.kind, i.position[0], i.position[1], i.position[2]))
        
    output.write("\nCELL_PARAMETERS\n")
     
    for i in range(3):
        output.write("{0:15.10f}\t{1:15.10f}\t{2:15.10f}\n".format(s.cell[i][0], s.cell[i][1], s.cell[i][2]))
        
    if not fout==None:
         with open(fout, "w") as f:
            f.write(output.getvalue())
    else:
        print output.getvalue()
    output.close()
