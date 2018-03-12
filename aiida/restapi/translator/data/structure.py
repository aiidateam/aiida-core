# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.restapi.translator.data import DataTranslator
from aiida.restapi.common.exceptions import RestValidationError
from aiida.common.exceptions import LicensingException
import numpy as np

def atom_kinds_to_html(atom_kind):
    """

    Construct in html format

    an alloy with 0.5 Ge, 0.4 Si and 0.1 vacancy is represented as
    Ge<sub>0.5</sub> + Si<sub>0.4</sub> + vacancy<sub>0.1</sub>

    Args:
        atom_kind: a string with the name of the atomic kind, as printed by 
        kind.get_symbols_string(), e.g. Ba0.80Ca0.10X0.10

    Returns:
        html code for rendered formula
    """

    # Parse the formula (TODO can be made more robust though never fails if
    # it takes strings generated with kind.get_symbols_string())
    import re
    elements = re.findall(r'([A-Z][a-z]*)([0-1][.[0-9]*]?)?', atom_kind)

    # Compose the html string
    html_formula_pieces = []

    for element in elements:

        # replace element X by 'vacancy'
        species = element[0] if element[0] != 'X' else 'vacancy'
        weight = element[1] if element[1] != '' else None

        if weight is not None:
            html_formula_pieces.append(species + '<sub>' + weight +
                                   '</sub>')
        else:
            html_formula_pieces.append(species)

    html_formula = ' + '.join(html_formula_pieces)

    return html_formula


class StructureDataTranslator(DataTranslator):
    """
    Translator relative to resource 'structures' and aiida class StructureData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "structures"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm.data.structure import StructureData
    _aiida_class = StructureData
    # The string name of the AiiDA class
    _aiida_type = "data.structure.StructureData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(StructureDataTranslator, self).__init__(Class=self.__class__,
                                                      **kwargs)


    @staticmethod
    def get_visualization_data(node, format=None, supercell_factors=[1, 1, 1]):
        """
        Returns: data in specified format. If format is not specified returns data
        in a format required by chemdoodle to visualize a structure.
        """
        response = {}
        response["str_viz_info"] = {}

        if format in node.get_export_formats():
            try:
                response["str_viz_info"]["data"] = node._exportstring(format)[0]
                response["str_viz_info"]["format"] = format
            except LicensingException as e:
                response = e.message

        else:
            import numpy as np
            from itertools import product


            # Validate supercell factors
            if type(supercell_factors) is not list:
                raise RestValidationError('supercell factors have to be a list of three integers')

            for fac in supercell_factors:
                if type(fac) is not int:
                    raise RestValidationError('supercell factors have to be '
                                              'integers')

            # Get cell vectors and atomic position
            lattice_vectors = np.array(node.get_attr('cell'))
            base_sites = node.get_attr('sites')

            start1 = -int(supercell_factors[0] / 2)
            start2 = -int(supercell_factors[1] / 2)
            start3 = -int(supercell_factors[2] / 2)

            stop1 = start1 + supercell_factors[0]
            stop2 = start2 + supercell_factors[1]
            stop3 = start3 + supercell_factors[2]

            grid1 = range(start1, stop1)
            grid2 = range(start2, stop2)
            grid3 = range(start3, stop3)

            atoms_json = []

            # Manual recenter of the structure
            center = (lattice_vectors[0] + lattice_vectors[1] +
                      lattice_vectors[2])/2.

            for ix, iy, iz in product(grid1, grid2, grid3):
                for base_site in base_sites:

                    shift = (ix*lattice_vectors[0] + iy*lattice_vectors[1] + \
                    iz*lattice_vectors[2] - center).tolist()

                    kind_name = base_site['kind_name']
                    kind_string = node.get_kind(kind_name).get_symbols_string()

                    atoms_json.append(
                        {'l': kind_string,
                         'x': base_site['position'][0] + shift[0],
                         'y': base_site['position'][1] + shift[1],
                         'z': base_site['position'][2] + shift[2],
                         # 'atomic_elements_html': kind_string
                         'atomic_elements_html': atom_kinds_to_html(kind_string)
                        })

            cell_json = {
                    "t": "UnitCell",
                    "i": "s0",
                    "o": (-center).tolist(),
                    "x": (lattice_vectors[0]-center).tolist(),
                    "y": (lattice_vectors[1]-center).tolist(),
                    "z": (lattice_vectors[2]-center).tolist(),
                    "xy": (lattice_vectors[0] + lattice_vectors[1]
                           - center).tolist(),
                    "xz": (lattice_vectors[0] + lattice_vectors[2]
                           - center).tolist(),
                    "yz": (lattice_vectors[1] + lattice_vectors[2]
                           - center).tolist(),
                    "xyz": (lattice_vectors[0] + lattice_vectors[1]
                            + lattice_vectors[2] - center).tolist(),
                }

            # These will be passed to ChemDoodle
            response["str_viz_info"]["data"] = {"s": [cell_json],
                            "m": [{"a": atoms_json}],
                            "units": '&Aring;'
                            }
            response["str_viz_info"]["format"] = "default (ChemDoodle)"

        # Add extra information
        response["dimensionality"] = node.get_dimensionality()
        response["pbc"] = node.pbc
        response["formula"] = node.get_formula()

        return response


    @staticmethod
    def get_downloadable_data(node, format=None):
        """
        Generic function extented for structure data

        :param node: node object that has to be visualized
        :param format: file extension format
        :returns: data in selected format to download
        """

        response = {}

        if format is None:
            format = "cif"

        if format in node.get_export_formats():
            try:
                response["data"] = node._exportstring(format)[0]
                response["status"] = 200
                response["filename"] = node.uuid + "_structure." + format
            except LicensingException as e:
                response["status"] = 500
                response["data"] = e.message

        return response

