###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that contains the class definitions necessary to offer support for queries to Materials Project."""

import pytest

from aiida.plugins import DbImporterFactory


def run_materialsproject_api_tests():
    from aiida.manage.configuration import get_profile

    profile = get_profile()
    return profile.dictionary.get('run_materialsproject_api_tests', False)


class TestMaterialsProject:
    """Contains the tests to verify the functionality of the Materials Project importer
    functions.
    """

    def test_invalid_api_key(self):
        """Test if Materials Project rejects an invalid API key and that we catch the error.
        Please enable the test in the profile configurator.
        """
        if not run_materialsproject_api_tests():
            pytest.skip('MaterialsProject API tests not enabled')

        importer_class = DbImporterFactory('materialsproject')
        importer_parameters = {'api_key': 'thisisawrongkey'}

        with pytest.raises(Exception):
            importer_class(**importer_parameters)
