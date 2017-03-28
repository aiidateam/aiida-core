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
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation

class PpCalculation(NamelistsCalculation):
    """
    Pp.x code of the Quantum ESPRESSO distribution, handles the 
    post-processing of charge-densities, potentials, ...
    For more information, refer to http://www.quantum-espresso.org/
    """
    def _init_internal_params(self):
        super(PpCalculation, self)._init_internal_params()
        self._default_namelists = ['INPUTPP', 'PLOT']
        self._FILPLOT = "aiida.filplot"
        self._blocked_keywords = [
                                  ('INPUTPP','outdir',self._OUTPUT_SUBFOLDER),
                                  ('INPUTPP','prefix',self._PREFIX),
                                  ('INPUTPP','filplot',self._FILPLOT),
                                 ]
        self._default_parser = None
        self._internal_retrieve_list = [self._FILPLOT]

    def use_parent_calculation(self,calc):
        """
        Set the parent calculation,
        from which it will inherit the outputsubfolder.
        The link will be created from parent RemoteData and NamelistCalculation
        """
        if not isinstance(calc,PwCalculation):
            raise ValueError("Parent calculation must be a PwCalculation")
        from aiida.common.exceptions import UniquenessError
        localdatas = [_[1] for _ in calc.get_outputs(also_labels=True)]
        if len(localdatas) == 0:
            raise UniquenessError("No output retrieved data found in the parent"
                                  "calc, probably it did not finish yet, "
                                  "or it crashed")

        localdata = [_[1] for _ in calc.get_outputs(also_labels=True)
                              if _[0] == 'remote_folder']
        localdata = localdata[0]
        self.use_parent_folder(localdata)
