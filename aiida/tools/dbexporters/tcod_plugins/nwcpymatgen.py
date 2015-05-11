# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.4.1"

from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator

class NwcpymatgenTcodtranslator(BaseTcodtranslator):
    """
    NWChem's output parameter translator to TCOD CIF dictionary tags.
    """
    _plugin_type_string = "nwchem.nwcpymatgen.NwcpymatgenCalculation"

    @classmethod
    def get_software_package(cls,parameters,**kwargs):
        """
        Returns the package or program name that was used to produce
        the structure. Only package or program name should be used,
        e.g. 'VASP', 'psi3', 'Abinit', etc.
        """
        return 'NWChem'
