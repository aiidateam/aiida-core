"""
Plugin to create a Quantum Espresso pw.x file.

TODO: COPY OUTDIR FROM PREVIOUS CALCULATION! Should be an input node of type
     RemoteData (or maybe subclass it?).
TODO: tests!
TODO: DOC + implementation of SETTINGS
TODO: preexec, postexec
TODO: Check that no further parameters are passed in SETTINGS
TODO: many cards missing: check and implement
      e.g.: ['CONSTRAINTS', 'OCCUPATIONS']
TODO: implement pre... and post... hooks to add arbitrary strings before
      and after a namelist, and a 'final_string' (all optional); useful 
      for development when new cards are needed
TODO: all a lot of logger.debug stuff
"""
import os

from aiida.orm import Calculation, DataFactory
from aiida.orm.calculation.quantumespresso import BasePwCpInputGenerator

ParameterData = DataFactory('parameter')
  
class PwCalculation(BasePwCpInputGenerator, Calculation):   

    DATAFILE_XML = os.path.join(BasePwCpInputGenerator.OUTPUT_SUBFOLDER, 
                               '{}.save'.format(BasePwCpInputGenerator.PREFIX), 
                               BasePwCpInputGenerator.DATAFILE_XML_BASENAME)

    # Default PW output parser provided by AiiDA
    _default_parser = 'quantumespresso.pw'
    
    _automatic_namelists = {
        'scf':   ['CONTROL', 'SYSTEM', 'ELECTRONS'],
        'nscf':  ['CONTROL', 'SYSTEM', 'ELECTRONS'],
        'bands': ['CONTROL', 'SYSTEM', 'ELECTRONS'],
        'relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
        'md':    ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
        'vc-md':    ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
        'vc-relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
        }

    # Keywords that cannot be set
    _blocked_keywords = [('CONTROL', 'pseudo_dir'), # set later
         ('CONTROL', 'outdir'),  # set later
         ('CONTROL', 'prefix'),  # set later
         ('SYSTEM', 'ibrav'),  # set later
         ('SYSTEM', 'celldm'),
         ('SYSTEM', 'nat'),  # set later
         ('SYSTEM', 'ntyp'),  # set later
         ('SYSTEM', 'a'), ('SYSTEM', 'b'), ('SYSTEM', 'c'),
         ('SYSTEM', 'cosab'), ('SYSTEM', 'cosac'), ('SYSTEM', 'cosbc'),
    ]
    
    _use_kpoints = True
    

    def use_kpoints(self, data):
        """
        Set the kpoints for this calculation
        """
        if not isinstance(data, ParameterData):
            raise ValueError("The data must be an instance of the ParameterData class")

        self.replace_link_from(data, self.get_linkname_kpoints())

    def get_linkname_kpoints(self):
        """
        The name of the link used for the kpoints
        """
        return "kpoints"
