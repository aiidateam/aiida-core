# -*- coding: utf-8 -*-
"""
This module defines the classes related to band structures or dispersions
in a Brillouin zone, and how to operate on them.
"""

from aiida.orm.data.array.kpoints import KpointsData

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class MeshKpointsData(KpointsData):

    def set_kpoint_mesh(self,mesh,offset=[0.,0.,0.]):
        """
        """
        # validate
        try:
            the_mesh = tuple(int(i) for i in mesh)
            if len(the_mesh) != 3:
                raise ValueError
        except (IndexError,ValueError,TypeError):
            raise ValueError("The kpoint mesh must be a lits of three integers")
        try:
            the_offset = tuple(float(i) for i in offset)
            if len(the_offset) != 3:
                raise ValueError
        except (IndexError,ValueError,TypeError):
            raise ValueError("The offset must be a list of three integers")
        # store
        self.set_attr('mesh',the_mesh)
        self.set_attr('mesh_offset',the_offset)
