# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Translator for kpoints data
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.nodes.data import DataTranslator


class KpointsDataTranslator(DataTranslator):
    """
    Translator relative to resource 'kpoints' and aiida class KpointsData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'kpoints'
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import KpointsData
    _aiida_class = KpointsData
    # The string name of the AiiDA class
    _aiida_type = 'data.array.kpoints.KpointsData'

    _result_type = __label__

    @staticmethod
    def get_derived_properties(node):
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        """

        Returns: data in a format required by dr.js to visualize a 2D plot
        with multiple data series.

        Strategy: For the time being rely on the function implemented in
        seekpath to calculate brillouin zone faces, and triangulate them. The
        other fields of the response are retrieved
        by ordinary kpointsdata methods, except the logic to create a list
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
        response = {}

        # First dump out the kpoints in relative coordinates (which are
        # always available)
        response['explicit_kpoints_rel'] = explicit_kpoints_rel.tolist()

        # For kpoints objects that have an explicit list of kpoints we can
        # construct BZ and return an explicit list of kpoint coordinates
        if has_cell:
            # Retrieve b1, b2, b3
            (coords1, coords2, coords3) = (cell[0], cell[1], cell[2])

            # Get BZ faces and add them to the json. Fields: faces,
            # triangles, triangle_vertices. Most probably only faces is needed.
            from seekpath.brillouinzone.brillouinzone import get_BZ  # pylint: disable=import-error,no-name-in-module
            response['faces_data'] = get_BZ(coords1, coords2, coords3)

            # Provide kpoints cooridnates in absolute units ...
            explicit_kpoints_abs = np.dot(explicit_kpoints_rel, cell)
            response['explicit_kpoints_abs'] = explicit_kpoints_abs.tolist()

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

                response['labelled_kpoints_rel'] = high_symm_rel
                response['labelled_path'] = path

                # If absolute coordinates can be calculated also provide them
                if has_cell:
                    high_symm_abs = {}

                    for idx, label in node.labels:
                        high_symm_abs[label] = explicit_kpoints_abs[idx].tolist()

                    response['labelled_kpoints_abs'] = high_symm_abs

        # Return mesh and offset lists to be represented in a table
        if has_mesh:
            response['mesh'] = mesh
            response['offset'] = offset

        # Populate json content with booleans to make it easy to determine
        # how to visualize the node.

        # plot_bz: whether to make the plot (BZ, cell vectors, and explicit
        # kpoints)
        # tab_mesh: whether to include a table with the mesh and offsets

        bool_fields = dict(has_cell=has_cell, has_mesh=has_mesh, has_labels=has_labels)

        response.update(bool_fields)

        # Return json response
        return response
