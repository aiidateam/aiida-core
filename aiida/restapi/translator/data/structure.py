from aiida.restapi.translator.data import DataTranslator
from aiida.restapi.common.exceptions import RestValidationError


# def atom_kinds_to_html(atom_kind):
#     """
#
#     Construct in html format
#
#     an alloy with 0.5 Ge, 0.4 Si and 0.1 vacancy is represented as
#     Ge<sub>0.5</sub> + Si<sub>0.4</sub> + vacancy<sub>0.1</sub>
#
#     Args:
#         atom_kind: a string with the name of the atomic kind
#
#     Returns:
#         html code for rendered formula
#     """
#
#
#
#     for


class StructureDataTranslator(DataTranslator):
    """
    Translator relative to resource 'structures' and aiida class StructureData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "structures"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
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
    def get_visualization_data(node, supercell_factors=[1, 1, 1]):
        """

        Returns: data in a format required by chemdoodle to visualize a
        structure.

        """
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

                atoms_json.append(
                    {'kind_name': atom_kinds_to_html(base_site[
                                                             'kind_name']),
                     'x': base_site['position'][0] + shift[0],
                     'y': base_site['position'][1] + shift[1],
                     'z': base_site['position'][2] + shift[2]}
                )

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
        json_content = {"s": [cell_json],
                        "m": [{"a": atoms_json}],
                        "units": '&Aring;'
                        }
        return json_content

