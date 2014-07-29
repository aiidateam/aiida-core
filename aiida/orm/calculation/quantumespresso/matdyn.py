# -*- coding: utf-8 -*-
from aiida.orm.calculation.quantumespresso.namelists import NamelistsCalculation
import os
from aiida.orm.calculation.quantumespresso.q2r import Q2rCalculation
from aiida.orm.data.folder import FolderData
from aiida.orm.data.remote import RemoteData
from aiida.orm.data.array.kpoints import KpointsData
from aiida.common.utils import classproperty

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class MatdynCalculation(NamelistsCalculation):
    """
    matdyn.x code of the Quantum ESPRESSO distribution, used to obtain the
    phonon frequencies in reciprocal space from the interatomic force constants given by q2r.
    For more information, refer to http://www.quantum-espresso.org/
    """    
    def _init_internal_params(self):
        super(MatdynCalculation, self)._init_internal_params()
                
        self.PHONON_FREQUENCIES_NAME = 'phonon_frequencies.dat'
        self.PHONON_MODES_NAME = ''
    
        self._default_namelists = ['INPUT']   
        
        self._blocked_keywords = [('INPUT','flfrq',self.PHONON_FREQUENCIES_NAME), # output
                                  ('INPUT','flvec',self.PHONON_MODES_NAME), # output
                                  ('INPUT','q_in_cryst_coord',True), # kpoints always in crystal coordinates
                                  # this is dynamically added in the _prepare_for_submission
                                  #('INPUT','flfrc',Q2rCalculation.FORCE_CONSTANTS_NAME), # input
                                 ]
    
        self._internal_retrieve_list = [self.PHONON_FREQUENCIES_NAME]
        
        # Default PW output parser provided by AiiDA
        self._default_parser = None
        # TODO : matdyn parser 
    
    @classproperty
    def _use_methods(cls):
        """
        Use_* methods for the matdyn class.
        """
        retdict = NamelistsCalculation._use_methods
        retdict.update({
            "kpoints": {
               'valid_types': (KpointsData),
               'additional_parameter': None,
               'linkname': 'kpoints',
               'docstring': ("Kpoints on which to calculate the phonon "
                             "frequencies"),
               },                        
            })
        return retdict
    
    def set_parent_calc(self,calc):
        """
        Set the parent calculation, 
        from which it will inherit the outputsubfolder.
        The link will be created from parent RemoteData and NamelistCalculation 
        """
        if not isinstance(calc,Q2rCalculation):
            raise ValueError("Parent calculation must be a Q2rCalculation")

        from aiida.common.exceptions import UniquenessError
        localdatas = [_[1] for _ in calc.get_outputs(also_labels=True)
                      if _[0] == calc.get_linkname_force_matrix()]
        if len(localdatas) == 0:
            raise UniquenessError("No output retrieved data found in the parent "
                                  "calc, probably it did not finish yet, "
                                  "or it crashed")
        if len(localdatas) != 1:
            raise UniquenessError("More than one output retrieved data found")
        localdata = localdatas[0]
        
        self.use_parent_folder(localdata)
   
    # TODO: add the q-points at the end    
    def _get_following_text(self, inputdict, settings):
        """
        Add the kpoints after the namelist.
        
        This function should consume the content of inputdict (if it requires
        a different node) or the keys inside settings, using the 'pop' method,
        so that inputdict and settings should remain empty at the end of 
        _prepare_for_submission, if all flags/nodes were recognized
        """
        from aiida.djsite.utils import get_dblogger_extra
        logger_extra = get_dblogger_extra(self)    
        
        #self.logger.warning("inputdict={}, settings={}".format(
        #    inputdict, settings), extra=logger_extra)
    
        try:
            kpoints = inputdict.pop(self.get_linkname('kpoints'))
        except KeyError:
            raise InputValidationError("No kpoints specified for this calculation")
        if not isinstance(kpoints, KpointsData):
            raise InputValidationError("kpoints is not of type KpointsData")
         
        klist = kpoints.get_kpoints()
        
        retlist = ["{}".format(len(klist))]
        for k in klist:
            retlist.append("{:18.10f} {:18.10f} {:18.10f}".format(*k))
        
        return "\n".join(retlist)
    
    def _prepare_for_submission(self,tempfolder, inputdict): 
        from aiida.orm.data.singlefile import SinglefileData
        
        parent_calc_folder = inputdict.get(self.get_linkname('parent_folder'),
                                           None)
        
        
        if isinstance(parent_calc_folder, SinglefileData):
            self._blocked_keywords.append(
                ('INPUT', 'flfrc', os.path.split(
                    parent_calc_folder.get_file_abs_path())[1]  ))
        else:
            raise NotImplementedError(
                "Input different from SinglefileData is not supported"
                " yet for MatdynCalculation; it is {}".format(
                type(parent_calc_folder)))
            self._blocked_keywords.append(
                ('INPUT', 'flfrc',  Q2rCalculation.FORCE_CONSTANTS_NAME ))
                
        calcinfo = super(MatdynCalculation, self)._prepare_for_submission(
            tempfolder, inputdict)
        return calcinfo
         