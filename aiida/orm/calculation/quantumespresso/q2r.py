from aiida.orm.calculation.quantumespresso.namelists import NamelistsCalculation
import os
from aiida.orm.calculation.quantumespresso.ph import PhCalculation
from aiida.orm.data.folder import FolderData

class Q2rCalculation(NamelistsCalculation):
    """
    q2r.x code of the Quantum ESPRESSO distribution, used to obtain the
    interatomic force constants in real space after a phonon calculation.
    For more information, refer to http://www.quantum-espresso.org/
    """    
    FORCE_CONSTANTS_NAME = 'real_space_force_constants.dat'
    _default_namelists = ['INPUT']   
    _default_parent_output_folder = os.path.join('.',
                            PhCalculation.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX)
    _internal_retrieve_list = [FORCE_CONSTANTS_NAME]
    _blocked_keywords = [('INPUT','fildyn',PhCalculation.OUTPUT_DYNAMICAL_MATRIX_PREFIX),
                         ('INPUT','flfrc',FORCE_CONSTANTS_NAME),
                        ]
    _parent_folder_type = FolderData
    OUTPUT_SUBFOLDER = PhCalculation.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX
    
    def set_parent_calc(self,calc):
        """
        Set the parent calculation, 
        from which it will inherit the outputsubfolder.
        The link will be created from parent RemoteData and NamelistCalculation 
        """
        if not isinstance(calc,PhCalculation):
            raise ValueError("Parent calculation must be a PhCalculation")

        from aiida.common.exceptions import UniquenessError
        localdatas = calc.get_outputs(type=self._parent_folder_type)
        if len(localdatas) != 1:
            raise UniquenessError("More than one output remotedata found")
        localdata = localdatas[0]
        
        self.use_parent_folder(localdata)

    def export_force_constants(self,abs_path,overwrite=False):
        """
        Export the file of force constants in real space,
        :param abs_path: absolute path to the folder where the force 
               constants will be copied
        """ 
        import shutil
        from aiida.common.exceptions import UniquenessError,NotExistent
        
        if not os.path.isabs(abs_path):
            raise ValueError("Input path must be the local absolute path")
        elif os.path.isfile(abs_path) and not overwrite:
            raise IOError("Output file is already existing, by default can't be"
                          " overwritten")
        else:
            folders = self.get_outputs(type=FolderData)
            if not folders:
                raise NotExistent("No output FolderData found.")
            if len(folders)>1:
                raise UniquenessError("More than one output FolderData found.")
            folder = folders[0]
            src = folder.get_abs_path(self.FORCE_CONSTANTS_NAME)
            shutil.copy(src,abs_path)        
