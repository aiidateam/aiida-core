# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Class to backup an AiiDA instance profile."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import datetime
import io
import logging
import os
import shutil
import stat
import sys

from aiida.backends.profile import BACKEND_DJANGO
from aiida.backends.profile import BACKEND_SQLA
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.common import json
from aiida.manage.backup.backup_base import AbstractBackup, BackupError
from aiida.manage.configuration.settings import AIIDA_CONFIG_FOLDER

from . import backup_utils as utils

if not is_dbenv_loaded():
    load_dbenv()

from aiida.backends.settings import BACKEND, AIIDADB_PROFILE  # pylint: disable=wrong-import-order,wrong-import-position


class BackupSetup(object):  # pylint: disable=useless-object-inheritance
    """
    This class setups the main backup script related information & files like::

        - the backup parameter file. It also allows the user to set it up by answering questions.
        - the backup folders.
        - the script that initiates the backup.
    """

    def __init__(self):
        # The backup directory names
        self._conf_backup_folder_rel = "backup_{}".format(AIIDADB_PROFILE)
        self._file_backup_folder_rel = "backup_dest"

        # The backup configuration file (& template) names
        self._backup_info_filename = "backup_info.json"
        self._backup_info_tmpl_filename = "backup_info.json.tmpl"

        # The name of the script that initiates the backup
        self._script_filename = "start_backup.py"

        # Configuring the logging
        logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

        # The logger of the backup script
        self._logger = logging.getLogger("aiida_backup_setup")

    @staticmethod
    def construct_backup_variables(file_backup_folder_abs):
        """Construct backup variables."""
        backup_variables = {}

        # Setting the oldest backup timestamp
        oldest_object_bk = utils.ask_question(
            "Please provide the oldest backup timestamp "
            "(e.g. 2014-07-18 13:54:53.688484+00:00). ", datetime.datetime, True)

        if oldest_object_bk is None:
            backup_variables[AbstractBackup.OLDEST_OBJECT_BK_KEY] = None
        else:
            backup_variables[AbstractBackup.OLDEST_OBJECT_BK_KEY] = str(oldest_object_bk)

        # Setting the backup directory
        backup_variables[AbstractBackup.BACKUP_DIR_KEY] = file_backup_folder_abs

        # Setting the days_to_backup
        backup_variables[AbstractBackup.DAYS_TO_BACKUP_KEY] = utils.ask_question(
            "Please provide the number of days to backup.", int, True)

        # Setting the end date
        end_date_of_backup_key = utils.ask_question(
            "Please provide the end date of the backup " + "(e.g. 2014-07-18 13:54:53.688484+00:00).",
            datetime.datetime, True)
        if end_date_of_backup_key is None:
            backup_variables[AbstractBackup.END_DATE_OF_BACKUP_KEY] = None
        else:
            backup_variables[AbstractBackup.END_DATE_OF_BACKUP_KEY] = str(end_date_of_backup_key)

        # Setting the backup periodicity
        backup_variables[AbstractBackup.PERIODICITY_KEY] = utils.ask_question("Please periodicity (in days).", int,
                                                                              False)

        # Setting the backup threshold
        backup_variables[AbstractBackup.BACKUP_LENGTH_THRESHOLD_KEY] = utils.ask_question(
            "Please provide the backup threshold (in hours).", int, False)

        return backup_variables

    def create_dir(self, question, dir_path):
        """Create the directories for the backup folder and return its path."""
        final_path = utils.query_string(question, dir_path)

        if not os.path.exists(final_path):
            if utils.query_yes_no("The path {} doesn't exist. Should it be created?".format(final_path), "yes"):
                try:
                    os.makedirs(final_path)
                except OSError:
                    self._logger.error("Error creating the path %s.", final_path)
                    raise
        return final_path

    @staticmethod
    def print_info():
        """Write a string with information to stdout."""
        info_str = \
"""Variables to set up in the JSON file
------------------------------------

 * ``periodicity`` (in days): The backup runs periodically for a number of days
   defined in the periodicity variable. The purpose of this variable is to limit
   the backup to run only on a few number of days and therefore to limit the
   number of files that are backed up at every round. e.g. ``"periodicity": 2``
   Example: if you have files in the AiiDA repositories created in the past 30
   days, and periodicity is 15, the first run will backup the files of the first
   15 days; a second run of the script will backup the next 15 days, completing
   the backup (if it is run within the same day). Further runs will only backup
   newer files, if they are created.

 * ``oldest_object_backedup`` (timestamp or null): This is the timestamp of the
   oldest object that was backed up. If you are not aware of this value or if it
   is the first time that you start a backup up for this repository, then set
   this value to ``null``. Then the script will search the creation date of the
   oldest node object in the database and it will start
   the backup from that date. E.g. ``"oldest_object_backedup":
   "2015-07-20 11:13:08.145804+02:00"``

 * ``end_date_of_backup``: If set, the backup script will backup files that
   have a modification date until the value specified by this variable. If not
   set, the ending of the backup will be set by the following variable
   (``days_to_backup``) which specifies how many days to backup from the start
   of the backup. If none of these variables are set (``end_date_of_backup``
   and ``days_to_backup``), then the end date of backup is set to the current
   date. E.g. ``"end_date_of_backup": null`` or ``"end_date_of_backup":
   "2015-07-20 11:13:08.145804+02:00"``


 * ``days_to_backup``: If set, you specify how many days you will backup from
   the starting date of your backup. If it set to ``null`` and also
   ``end_date_of_backup`` is set to ``null``, then the end date of the backup
   is set to the current date. You can not set ``days_to_backup``
   & ``end_date_of_backup`` at the same time (it will lead to an error).
   E.g. ``"days_to_backup": null`` or ``"days_to_backup": 5``

 * ``backup_length_threshold`` (in hours): The backup script runs in rounds and
   on every round it backs-up a number of days that are controlled primarily by
   ``periodicity`` and also by ``end_date_of_backup`` / ``days_to_backup``,
   for the last backup round. The ``backup_length_threshold`` specifies the
   lowest acceptable round length. This is important for the end of the backup.

 * ``backup_dir``: The destination directory of the backup. e.g.
   ``"backup_dir": "/scratch/aiida_user/backup_script_dest"``
"""
        sys.stdout.write(info_str)

    def run(self):
        """Run the backup."""
        conf_backup_folder_abs = self.create_dir(
            "Please provide the backup folder by providing the full path.",
            os.path.join(os.path.expanduser(AIIDA_CONFIG_FOLDER), self._conf_backup_folder_rel))

        file_backup_folder_abs = self.create_dir(
            "Please provide the destination folder of the backup (normally in "
            "the previously provided backup folder).", os.path.join(conf_backup_folder_abs,
                                                                    self._file_backup_folder_rel))

        # The template backup configuration file
        template_conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._backup_info_tmpl_filename)

        # Copy the sample configuration file to the backup folder
        try:
            shutil.copy(template_conf_path, conf_backup_folder_abs)
        except Exception:
            self._logger.error("Error copying the file %s to the directory %s", template_conf_path,
                               conf_backup_folder_abs)
            raise

        if utils.query_yes_no(
                "A sample configuration file was copied to {}. "
                "Would you like to ".format(conf_backup_folder_abs) + "see the configuration parameters explanation?",
                default="yes"):
            self.print_info()

        # Construct the path to the backup configuration file
        final_conf_filepath = os.path.join(conf_backup_folder_abs, self._backup_info_filename)

        # If the backup parameters are configured now
        if utils.query_yes_no("Would you like to configure the backup " + "configuration file now?", default="yes"):

            # Ask questions to properly setup the backup variables
            backup_variables = self.construct_backup_variables(file_backup_folder_abs)

            with io.open(final_conf_filepath, 'wb') as backup_info_file:
                json.dump(backup_variables, backup_info_file)
        # If the backup parameters are configured manually
        else:
            sys.stdout.write("Please rename the file {} ".format(self._backup_info_tmpl_filename) +
                             "found in {} to ".format(conf_backup_folder_abs) +
                             "{} and ".format(self._backup_info_filename) +
                             "change the backup parameters accordingly.\n")
            sys.stdout.write("Please adapt the startup script accordingly to point to the " +
                             "correct backup configuration file. For the moment, it points " +
                             "to {}\n".format(os.path.join(conf_backup_folder_abs, self._backup_info_filename)))

        # The contents of the startup script
        if BACKEND == BACKEND_DJANGO:
            backup_import = ("from aiida.manage.backup.backup_django import Backup")
        elif BACKEND == BACKEND_SQLA:
            backup_import = ("from aiida.manage.backup.backup_sqlalchemy import Backup")
        else:
            raise BackupError("Following backend is unknown: {}".format(BACKEND))

        script_content = \
u"""#!/usr/bin/env python
import logging
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv(profile="{}")

{}

# Create the backup instance
backup_inst = Backup(backup_info_filepath="{}", additional_back_time_mins = 2)

# Define the backup logging level
backup_inst._logger.setLevel(logging.INFO)

# Start the backup
backup_inst.run()
""".format(AIIDADB_PROFILE, backup_import, final_conf_filepath)

        # Script full path
        script_path = os.path.join(conf_backup_folder_abs, self._script_filename)

        # Write the contents to the script
        with io.open(script_path, 'w', encoding='utf8') as script_file:
            script_file.write(script_content)

        # Set the right permissions
        try:
            statistics = os.stat(script_path)
            os.chmod(script_path, statistics.st_mode | stat.S_IEXEC)
        except OSError:
            self._logger.error("Problem setting the right permissions to the script %s.", script_path)
            raise

        sys.stdout.write("Backup setup completed.")


if __name__ == '__main__':
    BackupSetup().run()
