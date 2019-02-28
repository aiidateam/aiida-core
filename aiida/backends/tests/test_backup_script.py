# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import datetime
import importlib
import shutil
import sys
import tempfile

from dateutil.parser import parse

from aiida.backends.utils import is_dbenv_loaded, load_dbenv, BACKEND_SQLA, BACKEND_DJANGO
from aiida.backends.settings import BACKEND
from aiida.backends.testbase import AiidaTestCase
from aiida.common import utils
from aiida.manage.backup import backup_setup
from aiida.manage.backup import backup_utils
from aiida.orm import Data
from aiida.common import json


if not is_dbenv_loaded():
    load_dbenv()


class TestBackupScriptUnit(AiidaTestCase):


    _json_test_input_1 = '{"backup_length_threshold": 2, "periodicity": 2,' + \
        ' "oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": null, "days_to_backup": null, "backup_dir": ' +\
        '"/scratch/aiida_user/backupScriptDest"}'

    _json_test_input_2 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": null, "days_to_backup": null, "backup_dir": ' +\
        '"/scratch/aiida_user/backupScriptDest"}'

    _json_test_input_3 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": null, "days_to_backup": 2, "backup_dir": ' + \
        '"/scratch/aiida_user/backupScriptDest"}'

    _json_test_input_4 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": "2014-07-22 14:54:53.688484+00:00", ' + \
        '"days_to_backup": null, "backup_dir": ' + \
        '"/scratch/aiida_user/backupScriptDest"}'

    _json_test_input_5 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": "2014-07-22 14:54:53.688484+00:00", ' + \
        '"days_to_backup": 2, "backup_dir": "/scratch/aiida_user/backup"}'

    _json_test_input_6 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484", ' + \
        '"end_date_of_backup": "2014-07-22 14:54:53.688484", ' + \
        '"days_to_backup": null, ' \
        '"backup_dir": "/scratch/./aiida_user////backup//"}'

    def setUp(self):
        super(TestBackupScriptUnit, self).setUp()
        if not is_dbenv_loaded():
            load_dbenv()

        if BACKEND == BACKEND_SQLA:
            from aiida.manage.backup.backup_sqlalchemy import Backup
        elif BACKEND == BACKEND_DJANGO:
            from aiida.manage.backup.backup_django import Backup
        else:
            self.skipTest("Unknown backend")

        self._backup_setup_inst = Backup("", 2)

    def tearDown(self):
        super(TestBackupScriptUnit, self).tearDown()
        self._backup_setup_inst = None

    def test_loading_basic_params_from_file(self):
        """
        This method tests the correct loading of the basic _backup_setup_inst
        parameters from a JSON string.
        """
        backup_variables = json.loads(self._json_test_input_1)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

        self.assertEqual(
            self._backup_setup_inst._oldest_object_bk,
            parse("2014-07-18 13:54:53.688484+00:00"),
            "Last _backup_setup_inst start date is not parsed correctly")

        # The destination directory of the _backup_setup_inst
        self.assertEqual(
            self._backup_setup_inst._backup_dir,
            "/scratch/aiida_user/backupScriptDest",
            "_backup_setup_inst destination directory not parsed correctly")

        self.assertEqual(
            self._backup_setup_inst._backup_length_threshold,
            datetime.timedelta(hours=2),
            "_backup_length_threshold not parsed correctly")

        self.assertEqual(
            self._backup_setup_inst._periodicity,
            2,
            "_periodicity not parsed correctly")

    def test_loading_backup_time_params_from_file_1(self):
        """
        This method tests that the _backup_setup_inst limits are correctly
        loaded from the JSON string and are correctly set.

        In the parsed JSON string, no _backup_setup_inst end limits are set
        """
        backup_variables = json.loads(self._json_test_input_2)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

        self.assertEqual(
            self._backup_setup_inst._days_to_backup,
            None,
            "_days_to_backup should be None/null but it is not")

        self.assertEqual(
            self._backup_setup_inst._end_date_of_backup,
            None,
            "_end_date_of_backup should be None/null but it is not")

        self.assertEqual(
            self._backup_setup_inst._internal_end_date_of_backup,
            None,
            "_internal_end_date_of_backup should be None/null but it is not")

    def test_loading_backup_time_params_from_file_2(self):
        """
        This method tests that the _backup_setup_inst limits are correctly
        loaded from the JSON string and are correctly set.

        In the parsed JSON string, only the daysToBackup limit is set.
        """
        backup_variables = json.loads(self._json_test_input_3)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

        self.assertEqual(
            self._backup_setup_inst._days_to_backup,
            2,
            "_days_to_backup should be 2 but it is not")

        self.assertEqual(
            self._backup_setup_inst._end_date_of_backup,
            None,
            "_end_date_of_backup should be None/null but it is not")

        self.assertEqual(
            self._backup_setup_inst._internal_end_date_of_backup,
            parse("2014-07-20 13:54:53.688484+00:00"),
            "_internal_end_date_of_backup is not the expected one")

    def test_loading_backup_time_params_from_file_3(self):
        """
        This method tests that the _backup_setup_inst limits are correctly
        loaded from the JSON string and are correctly set.

        In the parsed JSON string, only the endDateOfBackup limit is set.
        """
        backup_variables = json.loads(self._json_test_input_4)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

        self.assertEqual(
            self._backup_setup_inst._days_to_backup,
            None,
            "_days_to_backup should be None/null but it is not")

        self.assertEqual(
            self._backup_setup_inst._end_date_of_backup,
            parse("2014-07-22 14:54:53.688484+00:00"),
            "_end_date_of_backup should be None/null but it is not")

        self.assertEqual(
            self._backup_setup_inst._internal_end_date_of_backup,
            parse("2014-07-22 14:54:53.688484+00:00"),
            "_internal_end_date_of_backup is not the expected one")

    def test_loading_backup_time_params_from_file_4(self):
        """
        This method tests that the _backup_setup_inst limits are correctly
        loaded from the JSON string and are correctly set.

        In the parsed JSON string, the endDateOfBackup & daysToBackuplimit
        are set which should lead to an exception.
        """
        from aiida.manage.backup.backup_base import BackupError

        backup_variables = json.loads(self._json_test_input_5)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        # An exception should be raised because endDateOfBackup
        # & daysToBackuplimit have been defined in the same time.
        with self.assertRaises(BackupError):
            self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

    def check_full_deserialization_serialization(self, input_string, backup_inst):
        input_variables = json.loads(input_string)
        backup_inst._ignore_backup_dir_existence_check = True
        backup_inst._read_backup_info_from_dict(input_variables)
        target_variables = backup_inst._dictionarize_backup_info()

        self.assertEqual(input_variables, target_variables,
                      "The test string {} did not succeed".format(
                          input_string) +
                      " the serialization deserialization test.\n" +
                      "Input variables: {}\n".format(input_variables) +
                      "Output variables: {}\n".format(target_variables))

    def test_full_deserialization_serialization_1(self):
        """
        This method tests the correct deserialization / serialization of the
        variables that should be stored in a file.
        """
        input_string = self._json_test_input_1
        backup_inst = self._backup_setup_inst

        self.check_full_deserialization_serialization(input_string, backup_inst)

    def test_full_deserialization_serialization_2(self):
        """
        This method tests the correct deserialization / serialization of the
        variables that should be stored in a file.
        """
        input_string = self._json_test_input_2
        backup_inst = self._backup_setup_inst

        self.check_full_deserialization_serialization(input_string, backup_inst)

    def test_full_deserialization_serialization_3(self):
        """
        This method tests the correct deserialization / serialization of the
        variables that should be stored in a file.
        """
        input_string = self._json_test_input_3
        backup_inst = self._backup_setup_inst

        self.check_full_deserialization_serialization(input_string, backup_inst)

    def test_full_deserialization_serialization_4(self):
        """
        This method tests the correct deserialization / serialization of the
        variables that should be stored in a file.
        """
        input_string = self._json_test_input_4
        backup_inst = self._backup_setup_inst

        self.check_full_deserialization_serialization(input_string, backup_inst)

    def test_timezone_addition_and_dir_correction(self):
        """
        This method tests if the timezone is added correctly to timestamps
        that don't have a timezone. Moreover, it checks if the given directory
        paths are normalized as expected.
        """

        backup_variables = json.loads(self._json_test_input_6)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

        self.assertIsNotNone(
            self._backup_setup_inst._oldest_object_bk.tzinfo,
            "Timezone info should not be none (timestamp: {})."
            .format(self._backup_setup_inst._oldest_object_bk))

        self.assertIsNotNone(
            self._backup_setup_inst._end_date_of_backup.tzinfo,
            "Timezone info should not be none (timestamp: {})."
            .format(self._backup_setup_inst._end_date_of_backup))

        self.assertIsNotNone(
            self._backup_setup_inst._internal_end_date_of_backup.tzinfo,
            "Timezone info should not be none (timestamp: {})."
            .format(self._backup_setup_inst._internal_end_date_of_backup))

        # The destination directory of the _backup_setup_inst
        self.assertEqual(
            self._backup_setup_inst._backup_dir,
            "/scratch/aiida_user/backup",
            "_backup_setup_inst destination directory is "
            "not normalized as expected.")


class TestBackupScriptIntegration(AiidaTestCase):

    _aiida_rel_path = ".aiida"
    _backup_rel_path = "backup"
    _repo_rel_path = "repository"

    _bs_instance = backup_setup.BackupSetup()

    def test_integration(self):
        from aiida.common.utils import Capturing

        # Fill in the repository with data
        self.fill_repo()
        try:
            # Create a temp folder where the backup files will be placed
            # and the backup will be stored
            temp_folder = tempfile.mkdtemp()

            # Capture the sysout of the following command
            with Capturing():
                # Create the backup scripts
                backup_full_path = self.create_backup_scripts(temp_folder)

            # Put the backup folder in the path
            sys.path.append(backup_full_path)

            # Import the backup script - this action will also run it
            # It is assumed that the backup script ends with .py
            importlib.import_module(self._bs_instance._script_filename[:-3])

            # Check the backup
            from aiida import settings
            from filecmp import dircmp
            import os
            from aiida.common.utils import are_dir_trees_equal
            source_dir = os.path.join(settings.REPOSITORY_PATH,
                                      self._repo_rel_path)
            dest_dir = os.path.join(backup_full_path,
                                    self._bs_instance._file_backup_folder_rel,
                                    self._repo_rel_path)
            res, msg = are_dir_trees_equal(source_dir, dest_dir)
            self.assertTrue(res, "The backed-up repository has differences to the original one. " + str(msg)
                             + ". If the test fails, report it in issue #2134.")
        finally:
            shutil.rmtree(temp_folder, ignore_errors=True)

    def fill_repo(self):
        from aiida.orm import CalcJobNode, Data
        from aiida.plugins import CalculationFactory, DataFactory

        extra_name = self.__class__.__name__ + "/test_with_subclasses"
        resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 1}

        Dict = DataFactory('dict')

        a1 = CalcJobNode(computer=self.computer)
        a1.set_option('resources', resources)
        a1.store()
        # To query only these nodes later
        a1.set_extra(extra_name, True)
        a3 = Data().store()
        a3.set_extra(extra_name, True)
        a4 = Dict(dict={'a': 'b'}).store()
        a4.set_extra(extra_name, True)
        a5 = Data().store()
        a5.set_extra(extra_name, True)
        # I don't set the extras, just to be sure that the filtering works
        # The filtering is needed because other tests will put stuff int he DB
        a6 = CalcJobNode(computer=self.computer)
        a6.set_option('resources', resources)
        a6.store()
        a7 = Data()
        a7.store()

    def create_backup_scripts(self, tmp_folder):
        backup_full_path = "{}/{}/{}/".format(tmp_folder, self._aiida_rel_path,
                                              self._backup_rel_path)
        # The predefined answers for the setup script
        ac = utils.ArrayCounter()
        answers = [backup_full_path,   # the backup folder path
                   "",                  # should the folder be created?
                   "",                  # destination folder of the backup
                   "",                  # should the folder be created?
                   "n",                 # print config explanation?
                   "",                  # configure the backup conf file now?
                   "", # start date of backup?
                   "",                  # is it correct?
                   "",                  # days to backup?
                   "",                  # is it correct?
                   "", # end date of backup
                   "",                  # is it correct?
                   "1",                 # periodicity
                   "",                  # is it correct?
                   "0",                 # threshold?
                   ""]                  # is it correct?
        backup_utils.input = lambda _: answers[ac.array_counter()]

        # Run the setup script
        self._bs_instance.run()

        return backup_full_path
