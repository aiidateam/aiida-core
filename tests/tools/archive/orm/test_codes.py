###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Code tests for the export and import routines"""

import uuid

from aiida import orm
from aiida.common.links import LinkType
from aiida.tools.archive import create_archive, import_archive
from tests.tools.archive.utils import get_all_node_links


def test_that_solo_code_is_exported_correctly(aiida_profile, tmp_path, aiida_localhost):
    """This test checks that when a calculation is exported then the
    corresponding code is also exported.
    """
    code_label = uuid.uuid4().hex

    code = orm.InstalledCode(label=code_label, computer=aiida_localhost, filepath_executable='/bin/true').store()
    code_uuid = code.uuid

    export_file = tmp_path / 'export.aiida'
    create_archive([code], filename=export_file)

    aiida_profile.reset_storage()

    import_archive(export_file)

    assert orm.load_node(code_uuid).label == code_label


def test_input_code(aiida_profile_clean, tmp_path, aiida_localhost):
    """This test checks that when a calculation is exported then the
    corresponding code is also exported. It also checks that the links
    are also in place after the import.
    """
    code_label = uuid.uuid4().hex

    code = orm.InstalledCode(label=code_label, computer=aiida_localhost, filepath_executable='/bin/true').store()
    code_uuid = code.uuid

    calc = orm.CalcJobNode()
    calc.computer = aiida_localhost
    calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})

    calc.base.links.add_incoming(code, LinkType.INPUT_CALC, 'code')
    calc.store()
    calc.seal()
    links_count = 1

    export_links = get_all_node_links()

    export_file = tmp_path / 'export.aiida'
    create_archive([calc], filename=export_file)

    aiida_profile_clean.reset_storage()

    import_archive(export_file)

    # Check that the code node is there
    assert orm.load_node(code_uuid).label == code_label

    # Check that the link is in place
    import_links = get_all_node_links()
    assert sorted(export_links) == sorted(import_links)
    assert (
        len(export_links) == links_count
    ), f'Expected to find only one link from code to the calculation node before export. {len(export_links)} found.'
    assert (
        len(import_links) == links_count
    ), f'Expected to find only one link from code to the calculation node after import. {len(import_links)} found.'


def test_solo_code(aiida_profile, tmp_path, aiida_localhost):
    """This test checks that when a calculation is exported then the
    corresponding code is also exported.
    """
    code_label = uuid.uuid4().hex

    code = orm.InstalledCode(label=code_label, computer=aiida_localhost, filepath_executable='/bin/true').store()
    code_uuid = code.uuid

    export_file = tmp_path / 'export.aiida'
    create_archive([code], filename=export_file)

    aiida_profile.reset_storage()

    import_archive(export_file)

    assert orm.load_node(code_uuid).label == code_label
