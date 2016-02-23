# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
import json
import aiida

from shutil import copyfile, rmtree

from aiida.common.additions.migration import Migration

import aiida.common.setup as setup

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Spyros Zoupanos"


class MigrationTest(unittest.TestCase):

    _temp_dir_path_name = None
    _aiida_main_config_dir_rel_path = ".aiida"

    _conf_files_rel_path = "test_migration_files"
    _original_files_rel_path = "original"
    _final_files_rel_path = "final"

    _aiida_conf_dir_replace_str = "{AIIDA_CONF_DIR}"
    _aiida_dir_replace_str = "{AIIDA_DIR}"

    def setUp(self):
        pass

    def tearDown(self):
        pass

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
        temp_daemon_subfolder = os.path.join(
            temp_aiida_subfolder, setup.DAEMON_SUBDIR)
        os.makedirs(temp_daemon_subfolder)

        # Copy the daemon conf file to the corresponding temp directory
        source_daemon_conf = os.path.join(given_conf_dir, setup.DAEMON_CONF_FILE)
        dest_daemon_conf = os.path.join(
            temp_daemon_subfolder, setup.DAEMON_CONF_FILE)
        copyfile(source_daemon_conf, dest_daemon_conf)

        return temp_aiida_subfolder

    def perform_migration(self, aiida_folder_full_path):
        setup.AIIDA_CONFIG_FOLDER = aiida_folder_full_path
        mobj = Migration()
        mobj.perform_migration()

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
        json_res = json_files_equivalent(tmp_config_json_path, cor_config_json_path)
        print("json_res {}".format(json_res))

        # The path of the generated aiida_daemon.conf
        tmp_daemon_conf_path = os.path.join(
            aiida_folder_full_path, setup.DAEMON_SUBDIR,
            setup.DAEMON_CONF_FILE)
        # The path to the correct aiida_daemon.conf
        cor_daemon_conf_path = os.path.join(
            correct_files_dir, setup.DAEMON_CONF_FILE)
        self.config_text_files_equal(tmp_daemon_conf_path, cor_daemon_conf_path, aiida_folder_full_path)




    def test_migration(self):
        # Find all the needed directories that contain configuration files
        curr_file_dir = os.path.dirname(os.path.realpath(__file__))
        # print("================> {}".format(curr_file_dir))
        dir_with_conf_files = os.path.join(curr_file_dir,
                                           self._conf_files_rel_path)
        # print("================> {}".format(dir_with_conf_files))
        dirs_with_confs = os.listdir(dir_with_conf_files)
        for d in dirs_with_confs:
            # Get the first directory that contains the configuration files
            curr_dir_with_conf_files = os.path.join(dir_with_conf_files, d)
            curr_conf_orig_dir = os.path.join(
                curr_dir_with_conf_files, self._original_files_rel_path)
            temp_aiida_folder = self.prepare_the_temp_aiida_folder(curr_conf_orig_dir)

            for c in os.walk(temp_aiida_folder):
                print("llllllll=> {}".format(c))

            self.perform_migration(temp_aiida_folder)
            self.check_miration_res(
                temp_aiida_folder, os.path.join(
                    curr_dir_with_conf_files, self._final_files_rel_path))

            return

            # Delete the temporary folder
            rmtree(temp_aiida_folder)
        pass


    def config_text_files_equal(self, generated_conf_path, original_conf_path, aiida_conf_dir):
        #{AIIDA_DIR}
        # print("Comparing files {} {}".format(input_file1_filename, input_file2_filename))
        aiida_dir = os.path.split(os.path.abspath(aiida.__file__))[0]
        from itertools import izip
        with open(generated_conf_path, 'r') as generated_conf, open(original_conf_path, 'r') as original_conf:
            for g_line, o_line in izip(generated_conf, original_conf):
                if g_line != o_line.replace(self._aiida_conf_dir_replace_str, aiida_conf_dir).replace(self._aiida_dir_replace_str, aiida_dir):
                    print("===========> lines not equal")
                    print("g_lin: {}".format(g_line))
                    print("o_li1: {}".format(o_line))
                    print("o_li2: {}".format(o_line.replace(self._aiida_conf_dir_replace_str, aiida_conf_dir)))
                    print os.path.split(os.path.abspath(aiida.__file__))[0]
            # generated_conf_data = generated_conf.readlines()
            # original_conf_data = original_conf.readlines()
            # print generated_conf_data
            # print original_conf_data



            # data = f.readlines()
            # same = set(generated_conf).intersection(file2)

        # print("same: {}". format(same))


def json_files_equivalent(input_file1_filename, input_file2_filename):
    """
    Checks that two json files are equivalent (contain the same key/value pairs
    irrespective of their order.
    :param input_file1_filename: The first json file.
    :param input_file2_filename: The second json file.
    :return: True if the two files are equivalent, false otherwise.
    """
    with open(input_file1_filename) as input_file1:
        with open(input_file2_filename) as input_file2:
            json1 = json.load(input_file1)
            json2 = json.load(input_file2)
            if ordered(json1) == ordered(json2):
                return True
            else:
                return False

def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def read_file_and_return_string(filename):
    return_str = ""
    with open(filename, "rt") as f:
        for line in f:
            return_str += line
    return return_str

if __name__ == "__main__":
    unittest.main()