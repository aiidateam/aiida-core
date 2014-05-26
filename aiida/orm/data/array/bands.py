"""
This module defines the classes related to band structures or dispersions
in a Brillouin zone, and how to operate on them.
"""

from aiida.orm.data.array.kpoints import KpointsData
import numpy

class BandsData(KpointsData):
    
    def set_bands(self,bands):
        """
        Sets an array of band energies of dimension (nkpoints x nbands)
        """
        try:
            kpoints = self.get_kpoints_relative()
        except AttributeError:
            raise AttributeError("Must first set the kpoints")
        if bands.shape[0] != len(kpoints):
            raise ValueError("There must be energy values for every kpoint") 
        if bands.dtype != numpy.dtype(numpy.float):
            raise ValueError("Input bands must be an array of floats")
        
        self.set_array('bands',bands)
        

    def get_bands(self,bands):
        """
        Returns an array (nkpoints x num_bands) of energies.
        """
        return self.get_array('bands')
         
