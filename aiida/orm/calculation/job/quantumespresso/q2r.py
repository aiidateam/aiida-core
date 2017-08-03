# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.calculation.job.quantumespresso.namelists import NamelistsCalculation
import os
from aiida.orm.calculation.job.quantumespresso.ph import PhCalculation
from aiida.orm.data.folder import FolderData
from aiida.common.utils import classproperty

class Q2rCalculation(NamelistsCalculation):
    """
    q2r.x code of the Quantum ESPRESSO distribution, used to obtain the
    interatomic force constants in real space after a phonon calculation.
    For more information, refer to http://www.quantum-espresso.org/
    """    
    def _init_internal_params(self):
        super(Q2rCalculation, self)._init_internal_params()
                
        self._default_namelists = ['INPUT']   
        self._INPUT_SUBFOLDER = os.path.join('.',
                           PhCalculation._FOLDER_DYNAMICAL_MATRIX)
        #_internal_retrieve_list = [FORCE_CONSTANTS_NAME]
        self._blocked_keywords = [('INPUT','fildyn',
                                 PhCalculation._OUTPUT_DYNAMICAL_MATRIX_PREFIX),
                                 ('INPUT','flfrc',self._FORCE_CONSTANTS_NAME),
                            ]
        self._parent_folder_type = FolderData
        self._OUTPUT_SUBFOLDER = PhCalculation._FOLDER_DYNAMICAL_MATRIX
        
        self._retrieve_singlefile_list = [[self.get_linkname_force_matrix(),
                                           'forceconstants',
                                           self._FORCE_CONSTANTS_NAME]]
        
        # Default Q2r output parser provided by AiiDA
        self._default_parser = 'quantumespresso.q2r'
        
    @classproperty
    def _FORCE_CONSTANTS_NAME(cls):
        return 'real_space_force_constants.dat'
   
    def use_parent_calculation(self,calc):
        """
        Set the parent calculation, 
        from which it will inherit the outputsubfolder.
        The link will be created from parent RemoteData and NamelistCalculation 
        """
        if not isinstance(calc,PhCalculation):
            raise ValueError("Parent calculation must be a PhCalculation")

        localdata = calc.get_retrieved_node()
        
        self.use_parent_folder(localdata)

    @classmethod
    def get_linkname_force_matrix(self):
        """
        Return the name of the link between Q2rCalculation and the output 
        force constants produced
        """
        return 'force_constants'
    
    
