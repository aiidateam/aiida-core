# -*- coding: utf-8 -*-
from aiida.orm.calculation.quantumespresso.namelists import NamelistsCalculation
import os
from aiida.orm.calculation.quantumespresso.ph import PhCalculation
from aiida.orm.data.folder import FolderData
from aiida.common.utils import classproperty

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class Q2rCalculation(NamelistsCalculation):
    """
    q2r.x code of the Quantum ESPRESSO distribution, used to obtain the
    interatomic force constants in real space after a phonon calculation.
    For more information, refer to http://www.quantum-espresso.org/
    """    
    def _init_internal_params(self):
        super(Q2rCalculation, self)._init_internal_params()
                
        self._default_namelists = ['INPUT']   
        self.INPUT_SUBFOLDER = os.path.join('.',
                                PhCalculation.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX)
        #_internal_retrieve_list = [FORCE_CONSTANTS_NAME]
        self._blocked_keywords = [('INPUT','fildyn',PhCalculation.OUTPUT_DYNAMICAL_MATRIX_PREFIX),
                             ('INPUT','flfrc',self.FORCE_CONSTANTS_NAME),
                            ]
        self._parent_folder_type = FolderData
        self.OUTPUT_SUBFOLDER = PhCalculation.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX
        
        self._retrieve_singlefile_list = [[self.get_linkname_force_matrix(),'singlefile',self.FORCE_CONSTANTS_NAME]]
        
        # Default PW output parser provided by AiiDA
        self._default_parser = 'quantumespresso.q2r'
        
    @classproperty
    def FORCE_CONSTANTS_NAME(cls):
        return 'real_space_force_constants.dat'
   
    def set_parent_calc(self,calc):
        """
        Set the parent calculation, 
        from which it will inherit the outputsubfolder.
        The link will be created from parent RemoteData and NamelistCalculation 
        """
        if not isinstance(calc,PhCalculation):
            raise ValueError("Parent calculation must be a PhCalculation")

        from aiida.common.exceptions import UniquenessError
        localdatas = [_[1] for _ in calc.get_outputs(also_labels=True)
                      if _[0] == calc.get_linkname_retrieved()]
        if len(localdatas) == 0:
            raise UniquenessError("No output retrieved data found in the parent "
                                  "calc, probably it did not finish yet, "
                                  "or it crashed")
        if len(localdatas) != 1:
            raise UniquenessError("More than one output retrieved data found")
        localdata = localdatas[0]
        
        self.use_parent_folder(localdata)

    @classmethod
    def get_linkname_force_matrix(self):
        """
        Return the name of the link between Q2rCalculation and the output 
        force constants produced
        """
        return 'force_constants'
    
    