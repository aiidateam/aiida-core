from aiida.restapi.translator.data import DataTranslator

class StructureDataTransaltor(DataTranslator):
    """

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "structures"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "data.array.structure.StructureData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(StructureDataTranslator, self).__init__(Class=self.__class__, **kwargs)


    # def get_json_for_visualizer(cell, relcoords, atomic_numbers):
    #     system = (np.array(cell), np.array(relcoords), np.array(atomic_numbers))
    #     res = seekpath.hpkot.get_path(system, with_time_reversal=False)
    #
    #     real_lattice = res['primitive_lattice']
    #     #rec_lattice = np.linalg.inv(real_lattice).T # Missing 2pi!
    #     rec_lattice = np.array(
    #         seekpath.hpkot.tools.get_reciprocal_cell_rows(real_lattice))
    #     b1, b2, b3 = rec_lattice
    #
    #     faces_data = brillouinzone.get_BZ(
    #         b1 = b1, b2=b2, b3=b3)
    #
    #     response = {}
    #     response['faces_data'] = faces_data
    #     response['b1'] = b1.tolist()
    #     response['b2'] = b2.tolist()
    #     response['b3'] = b3.tolist()
    #     ## Convert to absolute
    #     response['kpoints'] = {k: (v[0] * b1 + v[1] * b2 + v[2] * b3).tolist()
    #         for k,v in res['point_coords'].items()}
    #     response['kpoints_rel'] = {k: [v[0], v[1], v[2]]
    #         for k,v in res['point_coords'].items()}
    #     response['path'] = res['path']
    #
    #     # It should use the same logic, so give the same cell as above
    #     res_explicit = seekpath.get_explicit_k_path(
    #         system, with_time_reversal=False)
    #     for k in res_explicit:
    #         if k == 'segments' or k.startswith('explicit_'):
    #             if isinstance(res_explicit[k], np.ndarray):
    #                 response[k] = res_explicit[k].tolist()
    #             else:
    #                 response[k] = res_explicit[k]
    #
    #     if np.sum(np.abs(np.array(res_explicit['reciprocal_primitive_lattice']) -
    #         np.array(res['reciprocal_primitive_lattice']))) > 1.e-7:
    #         raise AssertionError("Got different reciprocal cells...")
    #
    #     # Response for JS, and path_results
    #     return response, res


