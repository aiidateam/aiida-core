from aiida.restapi.translator.data import DataTranslator

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


    def get_visualization_data(self, node):
        """

        Returns: data in a format required by chemdoodle to visualize a
        structure.

        """
        import numpy as np

        # Get cell vectors and atomic position
        lattice_vectors = np.array(node.get_attr('cell'))
        sites = node.get_attr('sites')

        # Manual recenter of the structure
        center = (lattice_vectors[0] + lattice_vectors[1] +
                  lattice_vectors[2])/2.

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

        atoms_json = [
                    {"l": site['kind_name'],
                    "x": site['position'][0]-center[0],
                    "y": site['position'][1]-center[1],
                    "z": site['position'][2]-center[2]
                    }
                    for site in sites]

        # These will be passed to ChemDoodle
        json_content = {"s": [cell_json],
                        "m": [{"a": atoms_json}]
                        }
        return json_content

