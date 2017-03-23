from aiida.restapi.translator.data import DataTranslator


class KpointsDataTranslator(DataTranslator):
    """
    Translator relative to resource 'kpoints' and aiida class KpointsData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "kpoints"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "data.array.kpoints.KpointsData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(KpointsDataTranslator, self).__init__(Class=self.__class__,
                                                    **kwargs)

    @staticmethod
    def get_visualization_data(node):
        """

        Returns: data in a format required by dr.js to visualize a 2D plot
        with multiple data series.

        """

        """
        Strategy: For the time being rely on the function implemented in seekpath to calculate brillouin zone faces, and triangulate them
        """

        # First, check whether kpoint node has an explicit list including b vectors
        try:
            kpoints = node.get_kpoints(cartesian=True).tolist()
        except AttributeError:
            explicit_kpoints = False
        else:
            explicit_kpoints = True

        # Check if it has kpoint mesh (still compatible with the explicit list of kpoints)
        try:
            (mesh, offset) = node.get_kpoint_mesh()
        except AttributeError:
            has_mesh = False
        else:
            has_mesh = True

        # Then check whether it contains the cell => BZ and explicit kpoints can be plotted
        try:
            cell = node.reciprocal_cell.tolist()
        except AttributeError:
            has_cell = False
        else:
            has_cell = True


        json_content = {}

        # For kpoints objects that have an explicit list of kpoints we can construct BZ and return an explicit list of kpoint coordinates
        if has_cell:
            # Retrieve b1, b2, b3 and add them to the json
            (b1, b2, b3) = (cell[0], cell[1], cell[2])

            json_content['b1'] = b1
            json_content['b2'] = b2
            json_content['b3'] = b3

            json_content['reciprocal_vectors_unit'] = '1/Ang.'

            # Get BZ facesa and add them to the json. Fields: faces, triangles, triangle_vertices. Most probably only faces is needed.
            from seekpath.brillouinzone.brillouinzone import get_BZ
            json_content['faces_data'] = get_BZ(b1, b2, b3)

            if explicit_kpoints:
                # Retrieve explicit list of kpoints in abs coordinates and add it
                json_content['explicit_kpoints_abs'] = kpoints
                json_content['kpoints_unit'] = '1/Ang.'

            # Calculate explicit list from mesh if needed (possible since we know the cell)
            if has_mesh and not explicit_kpoints:

                (N1, N2, N3) = tuple(mesh)
                (off1, off2, off3) = tuple(offset)

                kpoints = []

                offvector = off1 * b1 + off2 * b2 + off3 * b3

                for i1 in range(N1):
                    for i2 in range(N2):
                        for i3 in range(N3):
                            kpoint = b1 / N1 * i1 + b2 / N2 * i2 + b3 / N3 * i3 + offvector
                            kpoints.append(kpoint.tolist())

                json_content['explicit_kpoints_abs'] = kpoints
                json_content['kpoints_unit'] = '1/Ang.'

                explicit_kpoints = True

        if has_mesh:
            # Return a generic mesh and offset to be represented in a table
            json_content['mesh'] = mesh
            json_content['offset'] = offset

        """
        # Populate json content with booleans to make it easy to determine how to visualize the node.

        plot_bz: whether to make the plot (BZ, cell vectors, and explicit kpoints)
        tab_mesh: whether to include a table with the mesh and offsets
        """
        bool_fields = dict(plot_bz=explicit_kpoints,
             tab_mesh=has_mesh)
        json_content.update(bool_fields)

        # Construct json and return it
        return json_content