# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=missing-docstring,invalid-name

import mock
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.common.datastructures import calc_states
from aiida.utils.capturing import Capturing

# Common computer information
computer_common_info = [
    "localhost",
    "",
    "True",
    "ssh",
    "torque",
    "#!/bin/bash",
    "/scratch/{username}/aiida_run",
    "mpirun -np {tot_num_mpiprocs}",
    "1",
    EOFError,
    EOFError,
]

# Computer #1
computer_name_1 = "torquessh1"
computer_setup_input_1 = [computer_name_1] + computer_common_info

# Computer #2
computer_name_2 = "torquessh2"
computer_setup_input_2 = [computer_name_2] + computer_common_info

# Common code information
code_common_info_1 = [
    "simple script",
    "False",
    "simpleplugins.templatereplacer",
]
code_common_info_2 = [
    "/usr/local/bin/doubler.sh",
    EOFError,
    EOFError,
]

# Code #1
code_name_1 = "doubler_1"
code_setup_input_1 = (
    [code_name_1] + code_common_info_1 + [computer_name_1] + code_common_info_2)
# Code #2
code_name_2 = "doubler_2"
code_setup_input_2 = (
    [code_name_2] + code_common_info_1 + [computer_name_2] + code_common_info_2)

# User #1
user_1 = {
    'email': "testuser1@localhost",
    'first_name': "Max",
    'last_name': "Mueller",
    'institution': "Testing Instiute"
}
# User #2
user_2 = {
    'email': "testuser2@localhost",
    'first_name': "Sabine",
    'last_name': "Mueller",
    'institution': "Testing Instiute"
}


# pylint: disable=protected-access
class TestVerdiCalculationCommands(AiidaTestCase):

    # pylint: disable=no-member
    # pylint says: Method 'computer' has no 'name' / 'id' member
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create some calculations with various states
        """
        super(TestVerdiCalculationCommands, cls).setUpClass()

        from aiida.orm import JobCalculation

        # Create some calculation
        calc1 = JobCalculation(
            computer=cls.computer,
            resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()
        calc1._set_state(calc_states.TOSUBMIT)
        calc2 = JobCalculation(
            computer=cls.computer.name,
            resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()
        calc2._set_state(calc_states.COMPUTED)
        calc3 = JobCalculation(
            computer=cls.computer.id,
            resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()
        calc3._set_state(calc_states.FINISHED)

    def test_calculation_list(self):
        """
        Do some calculation listing to ensure that verdi calculation list
        works and gives at least to some extent the expected results.
        """
        from aiida.cmdline.commands.calculation import Calculation
        calc_cmd = Calculation()

        with Capturing() as output:
            calc_cmd.calculation_list()

        out_str = ''.join(output)
        self.assertTrue(
            calc_states.TOSUBMIT in out_str,
            "The TOSUBMIT calculations should be part fo the "
            "simple calculation list.")
        self.assertTrue(
            calc_states.COMPUTED in out_str,
            "The COMPUTED calculations should be part fo the "
            "simple calculation list.")
        self.assertFalse(
            calc_states.FINISHED in out_str,
            "The FINISHED calculations should not be part fo the "
            "simple calculation list.")

        with Capturing() as output:
            calc_cmd.calculation_list(*['-a'])

        out_str = ''.join(output)
        self.assertTrue(
            calc_states.FINISHED in out_str,
            "The FINISHED calculations should be part fo the "
            "simple calculation list.")


class TestVerdiCodeCommands(AiidaTestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create the computers and setup a codes
        """
        super(TestVerdiCodeCommands, cls).setUpClass()

        # Setup computer #1
        from aiida.cmdline.commands.computer import Computer
        cmd_comp = Computer()
        with mock.patch(
                '__builtin__.raw_input', side_effect=computer_setup_input_1):
            with Capturing():
                cmd_comp.computer_setup()

        # Setup a code for computer #1
        from aiida.cmdline.commands.code import Code
        code_cmd = Code()
        with mock.patch(
                '__builtin__.raw_input', side_effect=code_setup_input_1):
            with Capturing():
                cls.code1 = code_cmd.code_setup()

        # Setup computer #2
        with mock.patch(
                '__builtin__.raw_input', side_effect=computer_setup_input_2):
            with Capturing():
                cmd_comp.computer_setup()

        # Setup a code for computer #2
        with mock.patch(
                '__builtin__.raw_input', side_effect=code_setup_input_2):
            with Capturing():
                cls.code2 = code_cmd.code_setup()

    def test_code_list(self):
        """
        Do some code listing test to ensure the correct behaviour of
        verdi code list
        """
        from aiida.cmdline.commands.code import Code
        code_cmd = Code()

        # Run a simple verdi code list, capture the output and check the result
        with Capturing() as output:
            code_cmd.code_list()
        out_str_1 = ''.join(output)
        self.assertTrue(
            computer_name_1 in out_str_1,
            "The computer 1 name should be included into this list")
        self.assertTrue(code_name_1 in out_str_1,
                        "The code 1 name should be included into this list")
        self.assertTrue(
            computer_name_2 in out_str_1,
            "The computer 2 name should be included into this list")
        self.assertTrue(code_name_2 in out_str_1,
                        "The code 2 name should be included into this list")

        # Run a verdi code list -a, capture the output and check if the result
        # is the same as the previous one
        with Capturing() as output:
            code_cmd.code_list(*['-a'])
        out_str_2 = ''.join(output)
        self.assertEqual(
            out_str_1, out_str_2,
            "verdi code list & verdi code list -a should provide "
            "the same output in this experiment.")

        # Run a verdi code list -c, capture the output and check the result
        with Capturing() as output:
            code_cmd.code_list(*['-c', computer_name_1])
        out_str = ''.join(output)
        self.assertTrue(
            computer_name_1 in out_str,
            "The computer 1 name should be included into this list")
        self.assertFalse(
            computer_name_2 in out_str,
            "The computer 2 name should not be included into this list")

        # Hide code 2
        self.code2._hide()

        # Run verdi code list again, checking that code 2 is now not shown
        with Capturing() as output:
            code_cmd.code_list()
        out_str_3 = ''.join(output)
        self.assertTrue(
            computer_name_1 in out_str_3,
            "The computer 1 name should be included into this list")
        self.assertTrue(code_name_1 in out_str_3,
                        "The code 1 name should be included into this list")
        self.assertFalse(
            computer_name_2 in out_str_3,
            "The computer 2 name should not be included into this list")
        self.assertFalse(
            code_name_2 in out_str_3,
            "The code 2 name should not be included into this list")


class TestVerdiWorkCommands(AiidaTestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create a simple workchain and run it.
        """
        super(TestVerdiWorkCommands, cls).setUpClass()
        from aiida.work.run import run
        from aiida.work.workchain import WorkChain
        TEST_STRING = 'Test report.'
        cls.test_string = TEST_STRING

        # pylint: disable=abstract-method
        class Wf(WorkChain):

            @classmethod
            def define(cls, spec):
                super(Wf, cls).define(spec)
                spec.outline(cls.create_logs)

            def create_logs(self):
                self.report(TEST_STRING)

            # Note: Method 'get_exec_engine' is abstract in class 'Process'
            # but is not overridden.

        _, cls.workchain_pid = run(Wf, _return_pid=True)

    def test_report(self):
        """
        Test that 'verdi work report' contains the report message.
        """
        from aiida.cmdline.commands.work import report

        result = CliRunner().invoke(
            report, [str(self.workchain_pid)], catch_exceptions=False)
        self.assertTrue(self.test_string in result.output)

    def test_report_debug(self):
        """
        Test that 'verdi work report' contains the report message when called with levelname DEBUG.
        """
        from aiida.cmdline.commands.work import report

        result = CliRunner().invoke(
            report, [str(self.workchain_pid), '--levelname', 'DEBUG'],
            catch_exceptions=False)
        self.assertTrue(self.test_string in result.output)

    def test_report_error(self):
        """
        Test that 'verdi work report' does not contain the report message when called with levelname ERROR.
        """
        from aiida.cmdline.commands.work import report

        result = CliRunner().invoke(
            report, [str(self.workchain_pid), '--levelname', 'ERROR'],
            catch_exceptions=False)
        self.assertTrue(self.test_string not in result.output)


# pylint: disable=no-self-use
class TestVerdiUserCommands(AiidaTestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create a user
        """
        super(TestVerdiUserCommands, cls).setUpClass()

        # Setup user #1
        from aiida.cmdline.commands.user import do_configure

        with mock.patch(
                '__builtin__.raw_input', side_effect=computer_setup_input_1):
            with Capturing():
                do_configure(
                    user_1['email'],
                    user_1['first_name'],
                    user_1['last_name'],
                    user_1['institution'],
                    no_password=True,
                    force_reconfigure=True)

    def test_user_list(self):
        """
        verdi user list
        """
        from aiida.cmdline.commands.user import list as list_user

        result = CliRunner().invoke(list_user, [], catch_exceptions=False)
        self.assertTrue(user_1['email'] in result.output)

    def test_user_configure(self):
        """
        Try configuring a new user
        verdi user configure
        """
        from aiida.cmdline.commands.user import configure

        cli_options = [
            user_2['email'], '--first-name', user_2['first_name'],
            '--last-name', user_2['last_name'], '--institution',
            user_2['institution'], '--no-password', '--force-reconfigure'
        ]

        # configure user
        result = CliRunner().invoke(
            configure, cli_options, catch_exceptions=False)
        self.assertTrue(user_2['email'] in result.output)
        self.assertTrue("is already present" not in result.output)

        # reconfigure user
        result = CliRunner().invoke(
            configure, cli_options, catch_exceptions=False)
        self.assertTrue(user_2['email'] in result.output)
        self.assertTrue("is already present" in result.output)


class TestVerdiDataCommands(AiidaTestCase):

    cmd_to_nodeid_map = dict()
    cmd_to_nodeid_map_for_groups = dict()
    cmd_to_nodeid_map_for_nuser = dict()

    group_name = "trj_group"
    group_id = None

    @classmethod
    def create_trajectory_data(cls, cmd_to_nodeid_map,
                               cmd_to_nodeid_map_for_groups,
                               cmd_to_nodeid_map_for_nuser, group, new_user):

        from aiida.orm.data.array.trajectory import TrajectoryData
        from aiida.cmdline.commands.data import _Trajectory
        import numpy

        # Create the Trajectory data nodes
        tjn1 = TrajectoryData()

        # I create sample data
        stepids = numpy.array([60, 70])
        times = stepids * 0.01
        cells = numpy.array([[[2., 0., 0.], [0., 2., 0.], [0., 0., 2.]],
                             [[3., 0., 0.], [0., 3., 0.], [0., 0., 3.]]])
        symbols = numpy.array(['H', 'O', 'C'])
        positions = numpy.array(
            [[[0., 0., 0.], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]],
             [[0., 0., 0.], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]])
        velocities = numpy.array([[[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]],
                                  [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5],
                                   [-0.5, -0.5, -0.5]]])

        # I set the node
        tjn1.set_trajectory(
            stepids=stepids,
            cells=cells,
            symbols=symbols,
            positions=positions,
            times=times,
            velocities=velocities)
        tjn1.store()

        tjn2 = TrajectoryData()
        tjn2.set_trajectory(
            stepids=stepids,
            cells=cells,
            symbols=symbols,
            positions=positions,
            times=times,
            velocities=velocities)
        tjn2.store()

        # Keep track of the created objects
        cmd_to_nodeid_map[_Trajectory] = [tjn1.id, tjn2.id]

        # Add the second Trajectory data to the group
        group.add_nodes([tjn2])
        # Keep track of the id of the node that you added to the group
        cmd_to_nodeid_map_for_groups[_Trajectory] = tjn2.id

        # Create a trajectory data that belongs to another user
        tjn3 = TrajectoryData()
        tjn3.set_trajectory(
            stepids=stepids,
            cells=cells,
            symbols=symbols,
            positions=positions,
            times=times,
            velocities=velocities)
        tjn3.dbnode.user = new_user._dbuser
        tjn3.store()

        # Put it is to the right map
        cmd_to_nodeid_map_for_nuser[_Trajectory] = [tjn3.id]

    @classmethod
    def create_cif_data(cls, cmd_to_nodeid_map, cmd_to_nodeid_map_for_groups,
                        cmd_to_nodeid_map_for_nuser, group, new_user):

        from aiida.orm.data.cif import CifData
        from aiida.cmdline.commands.data import _Cif
        import tempfile

        # Create the CIF data nodes
        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                 data_9012064
                 _space_group_IT_number           166
                 _symmetry_space_group_name_H-M   'R -3 m :H'
                 _cell_angle_alpha                90
                 _cell_angle_beta                 90
                 _cell_angle_gamma                120
                 _cell_length_a                   4.395
                 _cell_length_b                   4.395
                 _cell_length_c                   30.440
                 _cod_database_code               9012064
                 loop_
                 _atom_site_label
                 _atom_site_fract_x
                 _atom_site_fract_y
                 _atom_site_fract_z
                 _atom_site_U_iso_or_equiv
                 Bi 0.00000 0.00000 0.40046 0.02330
                 Te1 0.00000 0.00000 0.00000 0.01748
                 Te2 0.00000 0.00000 0.79030 0.01912
             ''')
            f.flush()
            c1 = CifData(file=f.name)
            c1.store()
            c2 = CifData(file=f.name)
            c2.store()

            # Keep track of the created objects
            cmd_to_nodeid_map[_Cif] = [c1.id, c2.id]

            # Add the second CIF data to the group
            group.add_nodes([c2])
            # Keep track of the id of the node that you added to the group
            cmd_to_nodeid_map_for_groups[_Cif] = c2.id

            # Create a Cif node belonging to another user
            c3 = CifData(file=f.name)
            c3.dbnode.user = new_user._dbuser
            c3.store()

            # Put it is to the right map
            cmd_to_nodeid_map_for_nuser[_Cif] = [c3.id]

    @classmethod
    def sub_create_bands_data(cls, user=None):
        from aiida.orm.data.array.kpoints import KpointsData
        from aiida.orm import JobCalculation
        from aiida.orm.data.structure import StructureData
        from aiida.common.links import LinkType
        from aiida.orm.data.array.bands import BandsData
        import numpy

        s = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))
        s.append_atom(
            position=(0., 0., 0.),
            symbols=['Ba', 'Ti'],
            weights=(1., 0.),
            name='mytype')
        if user is not None:
            s.dbnode.user = user._dbuser
        s.store()

        c = JobCalculation(
            computer=cls.computer,
            resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            })
        if user is not None:
            c.dbnode.user = user._dbuser
        c.store()
        c.add_link_from(s, "S1", LinkType.INPUT)
        c._set_state(calc_states.RETRIEVING)

        # define a cell
        alat = 4.
        cell = numpy.array([
            [alat, 0., 0.],
            [0., alat, 0.],
            [0., 0., alat],
        ])

        k = KpointsData()
        k.set_cell(cell)
        k.set_kpoints_path()
        if user is not None:
            k.dbnode.user = user._dbuser
        k.store()

        b = BandsData()
        b.set_kpointsdata(k)
        input_bands = numpy.array(
            [numpy.ones(4) * i for i in range(k.get_kpoints().shape[0])])
        b.set_bands(input_bands, units='eV')
        if user is not None:
            b.dbnode.user = user._dbuser
        b.store()

        b.add_link_from(c, link_type=LinkType.CREATE)

        return b

    @classmethod
    def create_bands_data(cls, cmd_to_nodeid_map, cmd_to_nodeid_map_for_groups,
                          cmd_to_nodeid_map_for_nuser, group, new_user):
        from aiida.cmdline.commands.data import _Bands

        b1 = cls.sub_create_bands_data()
        b2 = cls.sub_create_bands_data()

        # Keep track of the created objects
        cmd_to_nodeid_map[_Bands] = [b1.id, b2.id]

        # Add the second Kpoint & Bands data to the group
        group.add_nodes([b2])
        # Keep track of the id of the node that you added to the group
        cmd_to_nodeid_map_for_groups[_Bands] = b2.id

        b3 = cls.sub_create_bands_data(user=new_user)
        # Put it is to the right map (of the different user)
        cmd_to_nodeid_map_for_nuser[_Bands] = [b3.id]

    @classmethod
    def create_structure_data(cls, cmd_to_nodeid_map,
                              cmd_to_nodeid_map_for_groups,
                              cmd_to_nodeid_map_for_nuser, group, new_user):
        from aiida.orm.data.structure import StructureData
        from aiida.cmdline.commands.data import _Structure

        s1 = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))
        s1.append_atom(
            position=(0., 0., 0.),
            symbols=['Ba', 'Ti'],
            weights=(1., 0.),
            name='mytype')
        s1.store()

        s2 = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))
        s2.append_atom(
            position=(0., 0., 0.),
            symbols=['Ba', 'Ti'],
            weights=(1., 0.),
            name='mytype')
        s2.store()

        # Keep track of the created objects
        cmd_to_nodeid_map[_Structure] = [s1.id, s2.id]

        # Add the second Kpoint & Bands data to the group
        group.add_nodes([s2])
        # Keep track of the id of the node that you added to the group
        cmd_to_nodeid_map_for_groups[_Structure] = s2.id

        # Create a StructureData node belonging to another user
        s3 = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))
        s3.append_atom(
            position=(0., 0., 0.),
            symbols=['Ba', 'Ti'],
            weights=(1., 0.),
            name='mytype')
        s3.dbnode.user = new_user._dbuser
        s3.store()

        # Put it is to the right map
        cmd_to_nodeid_map_for_nuser[_Structure] = [s3.id]

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create some data needed for the tests
        """
        super(TestVerdiDataCommands, cls).setUpClass()

        from aiida.orm.user import User
        from aiida.orm.group import Group

        # Create a secondary user
        new_email = "newuser@new.n"
        new_user = User(email=new_email)
        new_user.force_save()

        # Create a group to add specific data inside
        g1 = Group(name=cls.group_name)
        g1.store()
        cls.group_id = g1.id

        cls.create_bands_data(cls.cmd_to_nodeid_map,
                              cls.cmd_to_nodeid_map_for_groups,
                              cls.cmd_to_nodeid_map_for_nuser, g1, new_user)

        cls.create_structure_data(cls.cmd_to_nodeid_map,
                                  cls.cmd_to_nodeid_map_for_groups,
                                  cls.cmd_to_nodeid_map_for_nuser, g1, new_user)

        cls.create_cif_data(cls.cmd_to_nodeid_map,
                            cls.cmd_to_nodeid_map_for_groups,
                            cls.cmd_to_nodeid_map_for_nuser, g1, new_user)

        cls.create_trajectory_data(
            cls.cmd_to_nodeid_map, cls.cmd_to_nodeid_map_for_groups,
            cls.cmd_to_nodeid_map_for_nuser, g1, new_user)

    def test_trajectory_simple_listing(self):
        from aiida.cmdline.commands.data import _Bands
        from aiida.cmdline.commands.data import _Structure
        from aiida.cmdline.commands.data import _Cif
        from aiida.cmdline.commands.data import _Trajectory

        sub_cmds = [_Bands, _Structure, _Cif, _Trajectory]
        for sub_cmd in sub_cmds:
            with Capturing() as output:
                sub_cmd().list()

            out_str = ' '.join(output)

            for nid in self.cmd_to_nodeid_map[sub_cmd]:
                if str(nid) not in out_str:
                    self.fail(
                        "The data objects ({}) with ids {} and {} "
                        "were not found. ".format(
                            sub_cmd, str(self.cmd_to_nodeid_map[sub_cmd][0]),
                            str(self.cmd_to_nodeid_map[sub_cmd][1])) +
                        "The output was {}".format(out_str))

    def test_trajectory_all_user_listing(self):
        from aiida.cmdline.commands.data import _Bands
        from aiida.cmdline.commands.data import _Structure
        from aiida.cmdline.commands.data import _Cif
        from aiida.cmdline.commands.data import _Trajectory

        sub_cmds = [_Bands, _Structure, _Cif, _Trajectory]
        for sub_cmd in sub_cmds:
            args_to_test = [['-A'], ['--all-users']]
            for arg in args_to_test:
                curr_scmd = sub_cmd()
                with Capturing() as output:
                    curr_scmd.list(*arg)

                out_str = ' '.join(output)

                for nid in (self.cmd_to_nodeid_map[sub_cmd] +
                            self.cmd_to_nodeid_map_for_nuser[sub_cmd]):
                    if str(nid) not in out_str:
                        self.fail("The data objects ({}) with ids {} and {} "
                                  "were not found. ".format(
                                      sub_cmd,
                                      str(self.cmd_to_nodeid_map[sub_cmd][0]),
                                      str(self.cmd_to_nodeid_map[sub_cmd][1])) +
                                  "The output was {}".format(out_str))

    def test_trajectory_past_days_listing(self):
        from aiida.cmdline.commands.data import _Bands
        from aiida.cmdline.commands.data import _Structure
        from aiida.cmdline.commands.data import _Cif
        from aiida.cmdline.commands.data import _Trajectory

        sub_cmds = [_Bands, _Structure, _Cif, _Trajectory]
        for sub_cmd in sub_cmds:
            args_to_test = [['-p', '0'], ['--past-days', '0']]
            for arg in args_to_test:
                curr_scmd = sub_cmd()
                with Capturing() as output:
                    curr_scmd.list(*arg)
                out_str = ' '.join(output)

                # This should be an empty output
                for nid in self.cmd_to_nodeid_map[sub_cmd]:
                    if str(nid) in out_str:
                        self.fail("No data objects should be retrieved and "
                                  "some were retrieved. The (concatenation of "
                                  "the) output was: {}".format(out_str))

            args_to_test = [['-p', '1'], ['--past-days', '1']]
            for arg in args_to_test:
                curr_scmd = sub_cmd()
                with Capturing() as output:
                    curr_scmd.list(*arg)
                out_str = ' '.join(output)

                for nid in self.cmd_to_nodeid_map[sub_cmd]:
                    if str(nid) not in out_str:
                        self.fail("The data objects ({}) with ids {} and {} "
                                  "were not found. ".format(
                                      sub_cmd,
                                      str(self.cmd_to_nodeid_map[sub_cmd][0]),
                                      str(self.cmd_to_nodeid_map[sub_cmd][1])) +
                                  "The output was {}".format(out_str))

    def test_trajectory_group_listing(self):
        from aiida.cmdline.commands.data import _Bands
        from aiida.cmdline.commands.data import _Structure
        from aiida.cmdline.commands.data import _Cif
        from aiida.cmdline.commands.data import _Trajectory

        args_to_test = [['-g', self.group_name],
                        ['--group-name', self.group_name],
                        ['-G', str(self.group_id)],
                        ['--group-pk', str(self.group_id)]]

        sub_cmds = [_Bands, _Structure, _Cif, _Trajectory]
        for sub_cmd in sub_cmds:
            for arg in args_to_test:
                curr_scmd = sub_cmd()
                with Capturing() as output:
                    curr_scmd.list(*arg)
                out_str = ' '.join(output)

                if str(self.
                       cmd_to_nodeid_map_for_groups[sub_cmd]) not in out_str:
                    self.fail(
                        "The data object ({}) with id {} "
                        "was not found. ".format(
                            sub_cmd,
                            str(self.cmd_to_nodeid_map_for_groups[sub_cmd]) +
                            "The output was {}".format(out_str)))
