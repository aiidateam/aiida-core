# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import json
import os
import tempfile
import unittest
from shutil import copyfile, rmtree

import aiida
import aiida.common.setup as setup
from aiida.common.additions.old_migrations.migration_05dj_to_06dj import (
    Migration)



class MigrationTest(unittest.TestCase):
    """
    This class tests that migration script for the transition to the new\
    configuration files works correctly.
    """

    # The temporary directory for the tests
    _temp_dir_path_name = None
    # The relative directory that the AiIDA conf files will be stored.
    _aiida_main_config_dir_rel_path = ".aiida"

    # The relative directory where the various test configurations should be
    # found
    _conf_files_rel_path = "test_migration_files"
    # The relative directory (under _conf_files_rel_path) where the original
    # configuration files (corresponding to files before the migration) should
    # be found
    _original_files_rel_path = "original"
    # The relative directory (under _conf_files_rel_path) where the final
    # configuration files (corresponding to files after the migration) should
    # be found
    _final_files_rel_path = "final"

    # Replace strings inside the original configuration files:
    # To be replaced by AiiDA conf folder
    _aiida_conf_dir_replace_str = "{AIIDA_CONF_DIR}"
    # To be replaced by the AiiDA fodler
    _aiida_dir_replace_str = "{AIIDA_DIR}"
    # To be replaced by the linux user under which AiiDA runs
    _aiida_linux_user = "{AIIDA_LINUX_USR}"

    def prepare_the_temp_aiida_folder(self, given_conf_dir):
        """
        This method creates an .aiida folder in a temporary directory
        and returns the absolute path to that folder.
        :param given_conf_dir: The directory that the needed configuration
        files can be found.
        :return: The created temp folder with the needed files.
        """
        # Construct a temporary folder to place the files
        temp_folder = tempfile.mkdtemp()

        # Create an .aiida subfolder
        temp_aiida_subfolder = os.path.join(
            temp_folder, self._aiida_main_config_dir_rel_path)
        os.makedirs(temp_aiida_subfolder)

        # Copy the main AiiDA configuration file to the temp folder
        source_aiida_conf = os.path.join(
            given_conf_dir, setup.CONFIG_FNAME)
        dest_aiida_conf = os.path.join(
            temp_aiida_subfolder, setup.CONFIG_FNAME)
        copyfile(source_aiida_conf, dest_aiida_conf)

        # Create the daemon directory
        # There is no need to place a daemon conf file in created directory
        temp_daemon_subfolder = os.path.join(
            temp_aiida_subfolder, setup.DAEMON_SUBDIR)
        os.makedirs(temp_daemon_subfolder)

        return temp_aiida_subfolder

    def perform_migration(self, aiida_folder_abs_path):
        """
        This method performs the migration to the new configuration format.
        :param aiida_folder_abs_path: The absolute path to the AiiDA
        configuration folder.
        """
        orig_val = setup.AIIDA_CONFIG_FOLDER
        try:
            setup.AIIDA_CONFIG_FOLDER = aiida_folder_abs_path
            Migration().perform_migration()
        finally:
            setup.AIIDA_CONFIG_FOLDER = orig_val

    def check_miration_res(self, aiida_folder_full_path, correct_files_dir):
        """
        This method checks that the migration result is correct. More
        specifically it checks that the generated config.json &
        aiida_daemon.conf are the expected ones.
        :param aiida_folder_full_path:
        :param correct_files_dir:
        :return:
        """
        # The path of the generated config.json
        tmp_config_json_path = os.path.join(
            aiida_folder_full_path, setup.CONFIG_FNAME)
        # The path to the correct config.json
        cor_config_json_path = os.path.join(
            correct_files_dir, setup.CONFIG_FNAME)
        # Compare the two json files
        json_res = json_files_equivalent(tmp_config_json_path,
                                         cor_config_json_path)
        # If the files are not equivalent, report it
        self.assertTrue(json_res[0], json_res[1])

        # The path of the generated aiida_daemon.conf
        tmp_daemon_conf_path = os.path.join(
            aiida_folder_full_path, setup.DAEMON_SUBDIR,
            setup.DAEMON_CONF_FILE)
        # The path to the correct aiida_daemon.conf
        cor_daemon_conf_path = os.path.join(
            correct_files_dir, setup.DAEMON_CONF_FILE)
        conf_txt_res = self.config_text_files_equal(
            tmp_daemon_conf_path, cor_daemon_conf_path, aiida_folder_full_path)
        # If the files are not the same, report it
        self.assertTrue(conf_txt_res[0], conf_txt_res[1])

    def test_migration(self):
        """
        This method tests creates a temporary .aiida folder with the needed
        configuration files, performs the migration and then checks the
        migration final result if it is correct. It does this for all the
        available test configurations.
        """
        # Find all the needed directories that contain configuration files
        curr_file_dir = os.path.dirname(os.path.realpath(__file__))
        dir_with_conf_subdirs = os.path.join(curr_file_dir,
                                           self._conf_files_rel_path)
        subdirs_with_confs = os.listdir(dir_with_conf_subdirs)
        # For every available testing directory (with configuration files)
        for d in subdirs_with_confs:
            # Get the first directory that contains the configuration files
            curr_dir_with_conf_files = os.path.join(dir_with_conf_subdirs, d)
            curr_conf_orig_dir = os.path.join(
                curr_dir_with_conf_files, self._original_files_rel_path)
            try:
                # Create a temporary .aiida folder that will be migrated
                temp_aiida_folder = self.prepare_the_temp_aiida_folder(
                    curr_conf_orig_dir)
                # Perform the migration
                self.perform_migration(temp_aiida_folder)
                # Check that the migration is correct
                self.check_miration_res(
                    temp_aiida_folder, os.path.join(
                        curr_dir_with_conf_files, self._final_files_rel_path))
            finally:
                # Delete the temporary folder
                rmtree(temp_aiida_folder)

    def config_text_files_equal(self, generated_conf_path, original_conf_path,
                                aiida_conf_dir):
        """
        This method checks two text configuration files (line by line) if they
        are equal. It also performs the necessary string replacements before
        the checks.
        :param generated_conf_path: The path to the generated configuration
        file.
        :param original_conf_path: The path to the original configuration file.
        :param aiida_conf_dir: The path to AiiDA configuration folder created
        for the test.
        :param linux_user: The user under whose account the AiiDA runs..
        :return: True or False with the corresponding message (if needed).
        """
        aiida_dir = os.path.split(os.path.abspath(aiida.__file__))[0]
        from itertools import izip
        import getpass
        with open(generated_conf_path, 'r') as generated_conf, open(
                original_conf_path, 'r') as original_conf:
            for g_line, o_line in izip(generated_conf, original_conf):
                o_line_mod = o_line.replace(
                    self._aiida_conf_dir_replace_str,
                    aiida_conf_dir).replace(
                    self._aiida_dir_replace_str,
                    aiida_dir).replace(
                    self._aiida_linux_user, getpass.getuser())
                if g_line != o_line_mod:
                    messg = ("The following lines are not equal: \n({file1}): "
                             "{line1} \n({file2}): {line2}"
                             .format(file1=generated_conf_path,
                                     file2=original_conf_path,
                                     line1=g_line, line2=o_line_mod))
                    return False, messg
        return True, ""


def json_files_equivalent(input_file1_filename, input_file2_filename):
    """
    Checks that two json files are equivalent (contain the same key/value pairs
    irrespective of their order.
    :param input_file1_filename: The first json file.
    :param input_file2_filename: The second json file.
    :return: True or False with the corresponding message (if needed).
    """
    with open(input_file1_filename) as input_file1:
        with open(input_file2_filename) as input_file2:
            json1 = json.load(input_file1)
            json2 = json.load(input_file2)
            if ordered(json1) == ordered(json2):
                return True, ""
            else:
                return (False,
                        "The following configuration files are different "
                        "{file1} {file2}. \n({file1}): {contents1}\n\n"
                        "({file2}): {contents2}"
                        .format(file1=input_file1_filename,
                                file2=input_file2_filename,
                                contents1=json1, contents2=json2))


def ordered(obj):
    """
    Sorts recursively a (JSON) object.
    :param obj: The object to be sorted.
    :return: A sorted version of the object.
    """
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


if __name__ == "__main__":
    unittest.main()
