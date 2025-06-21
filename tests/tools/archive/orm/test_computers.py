###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Computer tests for the export and import routines"""

import pytest

from aiida import orm
from aiida.tools.archive import create_archive, import_archive
from aiida.tools.archive.imports import DUPLICATE_LABEL_TEMPLATE
from tests.utils.archives import import_test_archive


def test_same_computer_import(aiida_profile, tmp_path, aiida_localhost):
    """Test that you can import nodes in steps without any problems. In this
    test we will import a first calculation and then a second one. The
    import should work as expected and have in the end two job
    calculations.

    Each calculation is related to the same computer. In the end we should
    have only one computer
    """
    # Use local computer
    comp = aiida_localhost

    # Store two job calculation related to the same computer
    calc1_label = 'calc1'
    calc1 = orm.CalcJobNode()
    calc1.computer = comp
    calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    calc1.label = calc1_label
    calc1.store()
    calc1.seal()

    calc2_label = 'calc2'
    calc2 = orm.CalcJobNode()
    calc2.computer = comp
    calc2.set_option('resources', {'num_machines': 2, 'num_mpiprocs_per_machine': 2})
    calc2.label = calc2_label
    calc2.store()
    calc2.seal()

    # Store locally the computer name
    comp_name = str(comp.label)
    comp_uuid = str(comp.uuid)

    # Export the first job calculation
    filename1 = tmp_path / 'export1.aiida'
    create_archive([calc1], filename=filename1)

    # Export the second job calculation
    filename2 = tmp_path / 'export2.aiida'
    create_archive([calc2], filename=filename2)

    # Clean the local database
    aiida_profile.reset_storage()

    # Check that there are no computers
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['*'])
    assert builder.count() == 0, 'There should not be any computers in the database at this point.'

    # Check that there are no calculations
    builder = orm.QueryBuilder()
    builder.append(orm.CalcJobNode, project=['*'])
    assert builder.count() == 0, 'There should not be any calculations in the database at this point.'

    # Import the first calculation
    import_archive(filename1)

    # Check that the calculation computer is imported correctly.
    builder = orm.QueryBuilder()
    builder.append(orm.CalcJobNode, project=['label'])
    assert builder.count() == 1, 'Only one calculation should be found.'
    assert str(builder.first(flat=True)) == calc1_label, 'The calculation label is not correct.'

    # Check that the referenced computer is imported correctly.
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['label', 'uuid', 'id'])
    assert builder.count() == 1, 'Only one computer should be found.'
    assert str(builder.first()[0]) == comp_name, 'The computer name is not correct.'
    assert str(builder.first()[1]) == comp_uuid, 'The computer uuid is not correct.'

    # Store the id of the computer
    comp_id = builder.first()[2]

    # Import the second calculation
    import_archive(filename2)

    # Check that the number of computers remains the same and its data
    # did not change.
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['label', 'uuid', 'id'])
    assert builder.count() == 1, f'Found {builder.count()} computersbut only one computer should be found.'
    assert str(builder.first()[0]) == comp_name, 'The computer name is not correct.'
    assert str(builder.first()[1]) == comp_uuid, 'The computer uuid is not correct.'
    assert builder.first()[2] == comp_id, 'The computer id is not correct.'

    # Check that now you have two calculations attached to the same
    # computer.
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, tag='comp')
    builder.append(orm.CalcJobNode, with_computer='comp', project=['label'])
    assert builder.count() == 2, 'Two calculations should be found.'
    ret_labels = set(_ for [_] in builder.all())
    assert ret_labels == set([calc1_label, calc2_label]), 'The labels of the calculations are not correct.'


def test_same_computer_different_name_import(aiida_profile, tmp_path, aiida_localhost):
    """This test checks that if the computer is re-imported with a different
    name to the same database, then the original computer will not be
    renamed. It also checks that the names were correctly imported (without
    any change since there is no computer name collision)
    """
    # Get computer
    comp1 = aiida_localhost

    # Store a calculation
    calc1_label = 'calc1'
    calc1 = orm.CalcJobNode()
    calc1.computer = aiida_localhost
    calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    calc1.label = calc1_label
    calc1.store()
    calc1.seal()

    # Store locally the computer name
    comp1_name = str(comp1.label)

    # Export the first job calculation
    filename1 = tmp_path / 'export1.aiida'
    create_archive([calc1], filename=filename1)

    # Rename the computer
    comp1.label = f'{comp1_name}_updated'

    # Store a second calculation
    calc2_label = 'calc2'
    calc2 = orm.CalcJobNode()
    calc2.computer = aiida_localhost
    calc2.set_option('resources', {'num_machines': 2, 'num_mpiprocs_per_machine': 2})
    calc2.label = calc2_label
    calc2.store()
    calc2.seal()

    # Export the second job calculation
    filename2 = tmp_path / 'export2.aiida'
    create_archive([calc2], filename=filename2)

    # Clean the local database
    aiida_profile.reset_storage()

    # Check that there are no computers
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['*'])
    assert builder.count() == 0, 'There should not be any computers in the database at this point.'

    # Check that there are no calculations
    builder = orm.QueryBuilder()
    builder.append(orm.CalcJobNode, project=['*'])
    assert builder.count() == 0, 'There should not be any calculations in the database at this point.'

    # Import the first calculation
    import_archive(filename1)

    # Check that the calculation computer is imported correctly.
    builder = orm.QueryBuilder()
    builder.append(orm.CalcJobNode, project=['label'])
    assert builder.count() == 1, 'Only one calculation should be found.'
    assert str(builder.first(flat=True)) == calc1_label, 'The calculation label is not correct.'

    # Check that the referenced computer is imported correctly.
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['label', 'uuid', 'id'])
    assert builder.count() == 1, 'Only one computer should be found.'
    assert str(builder.first()[0]) == comp1_name, 'The computer name is not correct.'

    # Import the second calculation
    import_archive(filename2)

    # Check that the number of computers remains the same and its data
    # did not change.
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['label'])
    assert builder.count() == 1, f'Found {builder.count()} computersbut only one computer should be found.'
    assert str(builder.first(flat=True)) == comp1_name, 'The computer name is not correct.'


def test_different_computer_same_name_import(aiida_profile, tmp_path, aiida_localhost_factory):
    """This test checks that if there is a name collision, the imported
    computers are renamed accordingly.
    """
    # Set the computer name
    comp1_name = 'localhost_1'

    # Store a calculation
    calc1_label = 'calc1'
    calc1 = orm.CalcJobNode()
    calc1.computer = aiida_localhost_factory(comp1_name)
    calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    calc1.label = calc1_label
    calc1.store()
    calc1.seal()

    # Export the first job calculation
    filename1 = tmp_path / 'export1.aiida'
    create_archive([calc1], filename=filename1)

    # Reset the database
    aiida_profile.reset_storage()

    # Store a second calculation
    calc2_label = 'calc2'
    calc2 = orm.CalcJobNode()
    calc2.computer = aiida_localhost_factory(comp1_name)
    calc2.set_option('resources', {'num_machines': 2, 'num_mpiprocs_per_machine': 2})
    calc2.label = calc2_label
    calc2.store()
    calc2.seal()

    # Export the second job calculation
    filename2 = tmp_path / 'export2.aiida'
    create_archive([calc2], filename=filename2)

    # Reset the database
    aiida_profile.reset_storage()

    # Store a third calculation
    calc3_label = 'calc3'
    calc3 = orm.CalcJobNode()
    calc3.computer = aiida_localhost_factory(comp1_name)
    calc3.set_option('resources', {'num_machines': 2, 'num_mpiprocs_per_machine': 2})
    calc3.label = calc3_label
    calc3.store()
    calc3.seal()

    # Export the third job calculation
    filename3 = tmp_path / 'export3.aiida'
    create_archive([calc3], filename=filename3)

    # Clean the local database
    aiida_profile.reset_storage()

    # Check that there are no computers
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['*'])
    assert builder.count() == 0, 'There should not be any computers in the database at this point.'

    # Check that there are no calculations
    builder = orm.QueryBuilder()
    builder.append(orm.CalcJobNode, project=['*'])
    assert builder.count() == 0, 'There should not be any ' 'calculations in the database at ' 'this point.'

    # Import all the calculations
    import_archive(filename1)
    import_archive(filename2)
    import_archive(filename3)

    # Retrieve the calculation-computer pairs
    builder = orm.QueryBuilder()
    builder.append(orm.CalcJobNode, project=['label'], tag='jcalc')
    builder.append(orm.Computer, project=['label'], with_node='jcalc')
    assert builder.count() == 3, 'Three combinations expected.'
    res = builder.all()
    assert [calc1_label, comp1_name] in res, 'Calc-Computer combination not found.'
    assert [calc2_label, DUPLICATE_LABEL_TEMPLATE.format(comp1_name, 0)] in res, 'Calc-Computer combination not found.'
    assert [calc3_label, DUPLICATE_LABEL_TEMPLATE.format(comp1_name, 1)] in res, 'Calc-Computer combination not found.'


def test_import_of_computer_json_params(aiida_profile_clean, tmp_path, aiida_localhost):
    """This test checks that the metadata and transport params are exported and imported correctly in both backends."""
    # Set the computer name
    comp1_name = 'localhost_1'
    comp1_metadata = {'workdir': '/tmp/aiida'}
    aiida_localhost.label = comp1_name
    aiida_localhost.metadata = comp1_metadata

    # Store a calculation
    calc1_label = 'calc1'
    calc1 = orm.CalcJobNode()
    calc1.computer = aiida_localhost
    calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    calc1.label = calc1_label
    calc1.store()
    calc1.seal()

    # Export the first job calculation
    filename1 = tmp_path / 'export1.aiida'
    create_archive([calc1], filename=filename1)

    # Clean the local database
    aiida_profile_clean.reset_storage()

    # Import the data
    import_archive(filename1)

    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['metadata'], tag='comp')
    assert builder.count() == 1, 'Expected only one computer'

    res = builder.dict()[0]
    assert res['comp']['metadata'] == comp1_metadata, 'Not the expected metadata were found'


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('backend', ['django', 'sqlalchemy'])
def test_import_of_django_sqla_export_file(aiida_localhost, backend):
    """Check that import manages to import the archive file correctly for legacy storage backends."""
    archive = f'{backend}.aiida'

    # Import the needed data
    import_test_archive(archive, filepath='export/compare')

    # The expected metadata
    comp1_metadata = {'workdir': '/tmp/aiida'}

    # Check that we got the correct metadata
    # Make sure to exclude the default computer
    builder = orm.QueryBuilder()
    builder.append(orm.Computer, project=['metadata'], tag='comp', filters={'label': {'!==': aiida_localhost.label}})
    assert builder.count() == 1, 'Expected only one computer'

    res = builder.dict()[0]

    assert res['comp']['metadata'] == comp1_metadata


def test_filter_size(tmp_path, aiida_profile_clean):
    """Tests if the query still works when the number of computer is beyond the `filter_size limit."""
    nb_nodes = 5
    nodes = []
    for i in range(nb_nodes):
        node = orm.CalcJobNode()
        node.computer = orm.Computer(
            label=f'{i}', hostname='localhost', transport_type='core.local', scheduler_type='core.direct'
        ).store()
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        node.label = f'{i}'
        node.store()
        node.seal()
        nodes.append(node)

    builder = orm.QueryBuilder().append(orm.Computer, project=['uuid', 'label'])
    builder = builder.all()

    # Export DB
    export_file_existing = tmp_path.joinpath('export.aiida')
    create_archive(nodes, filename=export_file_existing)

    # Clean database and reimport DB
    aiida_profile_clean.reset_storage()
    import_archive(export_file_existing, filter_size=2)

    # Check correct import
    builder = orm.QueryBuilder().append(orm.Computer, project=['uuid', 'label'])
    builder = builder.all()

    assert len(builder) == nb_nodes
