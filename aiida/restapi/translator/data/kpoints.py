# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Translator for kpoints data
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.data import DataTranslator


class KpointsDataTranslator(DataTranslator):
    """
    Translator relative to resource 'kpoints' and aiida class KpointsData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "kpoints"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import KpointsData
    _aiida_class = KpointsData
    # The string name of the AiiDA class
    _aiida_type = "data.array.kpoints.KpointsData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(KpointsDataTranslator, self).__init__(Class=self.__class__, **kwargs)

    @staticmethod
    def get_visualization_data(node, visformat=None):
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        """

        Returns: data in a format required by dr.js to visualize a 2D plot
        with multiple data series.

        Strategy: For the time being rely on the function implemented in
        seekpath to calculate brillouin zone faces, and triangulate them. The
        other fielsd of the response are retrieved
        by ordniary kpointsdata methods, except the logic to create an list
        of explicit keypoints from the mesh and the cell vectors.
        """

        import numpy as np

        # First, check whether it contains the cell => BZ and explicit kpoints
        # can be plotted
        try:
            cell = node.reciprocal_cell
        except AttributeError:
            has_cell = False
        else:
            has_cell = True

        # Then, check whether kpoint node has an explicit list including b
        # vectors
        try:
            explicit_kpoints_rel = node.get_kpoints()
        except AttributeError:
            explicit_kpoints = False
        else:
            explicit_kpoints = True

        # Check if it has kpoint mesh (still compatible with the explicit
        # list of kpoints)
        try:
            (mesh, offset) = node.get_kpoints_mesh()
        except AttributeError:
            has_mesh = False
        else:
            has_mesh = True
            explicit_kpoints_rel = node.get_kpoints_mesh(print_list=True)

        # Initialize response
        json_visualization = {}

        # First dump out the kpoints in relative coordinates (which are
        # always available)
        json_visualization['explicit_kpoints_rel'] = \
            explicit_kpoints_rel.tolist()

        # For kpoints objects that have an explicit list of kpoints we can
        # construct BZ and return an explicit list of kpoint coordinates
        if has_cell:
            # Retrieve b1, b2, b3 and add them to the json
            (coords1, coords2, coords3) = (cell[0], cell[1], cell[2])

            json_visualization['b1'] = coords1.tolist()
            json_visualization['b2'] = coords2.tolist()
            json_visualization['b3'] = coords3.tolist()

            json_visualization['reciprocal_vectors_unit'] = u'1/\u212b'

            # Get BZ facesa and add them to the json. Fields: faces,
            # triangles, triangle_vertices. Most probably only faces is needed.
            from seekpath.brillouinzone.brillouinzone import get_BZ
            json_visualization['faces_data'] = get_BZ(coords1, coords2, coords3)

            # Provide kpoints cooridnates in absolute units ...
            explicit_kpoints_abs = np.dot(explicit_kpoints_rel, cell)
            json_visualization['explicit_kpoints_abs'] = \
                explicit_kpoints_abs.tolist()

            # ... and units!
            json_visualization['kpoints_abs_unit'] = u'1/\u212b'

        # Add labels field
        has_labels = False
        if explicit_kpoints:

            if node.labels is not None:

                has_labels = True
                high_symm_rel = {}
                path = []
                old_label = None

                for idx, label in node.labels:
                    high_symm_rel[label] = explicit_kpoints_rel[idx].tolist()

                    if idx > 0:
                        path.append([old_label, label])
                    old_label = label

                json_visualization['kpoints_rel'] = high_symm_rel
                json_visualization['path'] = path

                # If absolute coordinates can be calculated also provide them
                if has_cell:
                    high_symm_abs = {}

                    for idx, label in node.labels:
                        high_symm_abs[label] = explicit_kpoints_abs[idx].tolist()

                    json_visualization['kpoints'] = high_symm_abs

        # Return mesh and offset lists to be represented in a table
        if has_mesh:
            json_visualization['mesh'] = mesh
            json_visualization['offset'] = offset

        # Populate json content with booleans to make it easy to determine
        # how to visualize the node.

        # plot_bz: whether to make the plot (BZ, cell vectors, and explicit
        # kpoints)
        # tab_mesh: whether to include a table with the mesh and offsets

        bool_fields = dict(has_cell=has_cell, has_mesh=has_mesh, has_labels=has_labels)

        json_visualization.update(bool_fields)

        # Construct json and return it
        return json_visualization

    @staticmethod
    def get_downloadable_data(node, download_format=None):
        """
        Generic function extented for kpoints data. Currently
        it is not implemented.

        :param node: node object that has to be visualized
        :param download_format: file extension format
        :returns: raise RestFeatureNotAvailable exception
        """

        from aiida.restapi.common.exceptions import RestFeatureNotAvailable

        raise RestFeatureNotAvailable("This endpoint is not available for Kpoints.")
