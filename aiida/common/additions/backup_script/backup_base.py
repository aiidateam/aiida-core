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
import datetime
import shutil
import os
import logging

from abc import abstractmethod, ABCMeta

from dateutil.parser import parse
from aiida.utils import timezone as dtimezone
from pytz import timezone as ptimezone




class AbstractBackup(object):
    """
    This class handles the backup of the AiiDA repository that is referenced
    by the current AiiDA database. The backup will start from the
    given backup timestamp (*oldest_object_backedup*) or the date of the
    oldest node/workflow object found and it will periodically backup
    (in periods of *periodicity* days) until the ending date of the backup
    specified by *end_date_of_backup* or *days_to_backup*.
    """

    __metaclass__ = ABCMeta

    # Keys in the dictionary loaded by the JSON file
    OLDEST_OBJECT_BK_KEY = "oldest_object_backedup"
    BACKUP_DIR_KEY = "backup_dir"
    DAYS_TO_BACKUP_KEY = "days_to_backup"
    END_DATE_OF_BACKUP_KEY = "end_date_of_backup"
    PERIODICITY_KEY = "periodicity"
    BACKUP_LENGTH_THRESHOLD_KEY = "backup_length_threshold"

    # Backup parameters that will be populated by the JSON file

    # Where did the last backup stop
    _oldest_object_bk = None
    # The destination directory of the backup
    _backup_dir = None

    # How many days to backup
    _days_to_backup = None
    # Until what date we should backup
    _end_date_of_backup = None

    # How many consecutive days to backup in one round.
    _periodicity = None

    # The threshold (in hours) between the oldest object to be backed up
    # and the end of the backup. If the difference is bellow this threshold
    # the backup should not start.
    _backup_length_threshold = None

    # The end of the backup dates (or days) until the end are translated to
    # the following internal variable containing the end date
    _internal_end_date_of_backup = None

    _additional_back_time_mins = None

    _ignore_backup_dir_existence_check = False

    def __init__(self, backup_info_filepath, additional_back_time_mins):

        # The path to the JSON file with the backup information
        self._backup_info_filepath = backup_info_filepath

        self._additional_back_time_mins = additional_back_time_mins

        # Configuring the logging
        logging.basicConfig(
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

        # The logger of the backup script
        self._logger = logging.getLogger("aiida_backup")

    def _read_backup_info_from_file(self, backup_info_file_name):
        """
        This method reads the backup information from the given file and
        passes the dictionary to the method responsible for the initialization
        of the needed class variables.
        """
        backup_variables = None

        with open(backup_info_file_name, 'r') as backup_info_file:
            try:
                backup_variables = json.load(backup_info_file)
            except ValueError:
                self._logger.error("Could not parse file " +
                                   backup_info_file_name)
                raise BackupError("Could not parse file " +
                                  backup_info_file_name)

        self._read_backup_info_from_dict(backup_variables)

    def _read_backup_info_from_dict(self, backup_variables):
        """
        This method reads the backup information from the given dictionary and
        sets the needed class variables.
        """
        # Setting the oldest backup date. This will be used as start of
        # the new backup procedure.
        #
        # If the oldest backup date is not set, then find the oldest
        # creation timestamp and set it as the oldest backup date.
        if backup_variables.get(self.OLDEST_OBJECT_BK_KEY) is None:

            # qb = QueryBuilder()
            # qb.append(
            #     Node,
            # )
            # qb.order_by({Node: {'ctime': 'asc'}})
            # query_node_res = qb.first()

            query_node_res = self._query_first_node()
            query_workflow_res = self._query_first_workflow()

            if (not query_node_res) and (not query_workflow_res):
                self._logger.error("The oldest modification date "
                                   "was not found.")
                raise BackupError("The oldest modification date "
                                  "was not found.")

            oldest_timestamps = []
            if query_node_res:
                oldest_timestamps.append(query_node_res[0].ctime)
            if query_workflow_res:
                oldest_timestamps.append(query_workflow_res[0].ctime)

            self._oldest_object_bk = min(oldest_timestamps)
            self._logger.info("Setting the oldest modification date to the "
                              "creation date of the oldest object "
                              "({})".format(self._oldest_object_bk))

        # If the oldest backup date is not None then try to parse it
        else:
            try:
                self._oldest_object_bk = parse(
                    backup_variables.get(self.OLDEST_OBJECT_BK_KEY))
                if self._oldest_object_bk.tzinfo is None:
                    curr_timezone = str(dtimezone.get_current_timezone())
                    self._oldest_object_bk = ptimezone(
                        str(curr_timezone)).localize(self._oldest_object_bk)
                    self._logger.info("No timezone defined in the oldest "
                                      "modification date timestamp. Setting "
                                      "current timezone ({})."
                                      .format(curr_timezone))
            # If it is not parsable...
            except ValueError:
                self._logger.error(
                    "We did not manage to parse the start timestamp "
                    "of the last backup.")
                raise

        # Setting the backup directory & normalizing it
        self._backup_dir = os.path.normpath(
            backup_variables.get(self.BACKUP_DIR_KEY))
        if (not self._ignore_backup_dir_existence_check and
                not os.path.isdir(self._backup_dir)):
            self._logger.error("The given backup directory doesn't exist.")
            raise BackupError("The given backup directory doesn't exist.")

        # You can not set an end-of-backup date and end days from the backup
        # that you should stop.
        if (backup_variables.get(self.DAYS_TO_BACKUP_KEY) is not None and
                    backup_variables.get(
                        self.END_DATE_OF_BACKUP_KEY) is not None):
            self._logger.error("Only one end of backup date can be set.")
            raise BackupError("Only one backup end can be set (date or "
                              "days from backup start.")

        # Check if there is an end-of-backup date
        elif backup_variables.get(self.END_DATE_OF_BACKUP_KEY) is not None:
            try:
                self._end_date_of_backup = parse(backup_variables.get(
                    self.END_DATE_OF_BACKUP_KEY))

                if self._end_date_of_backup.tzinfo is None:
                    curr_timezone = str(dtimezone.get_current_timezone())
                    self._end_date_of_backup = \
                        ptimezone(str(curr_timezone)).localize(
                            self._end_date_of_backup)
                    self._logger.info("No timezone defined in the end date of "
                                      "backup timestamp. Setting current "
                                      "timezone ({}).".format(curr_timezone))

                self._internal_end_date_of_backup = self._end_date_of_backup
            except ValueError:
                self._logger.error("The end date of the backup could not be "
                                   "parsed correctly")
                raise

        # Check if there is defined a days to backup
        elif backup_variables.get(self.DAYS_TO_BACKUP_KEY) is not None:
            try:
                self._days_to_backup = int(
                    backup_variables.get(self.DAYS_TO_BACKUP_KEY))
                self._internal_end_date_of_backup = (
                    self._oldest_object_bk +
                    datetime.timedelta(days=self._days_to_backup))
            except ValueError:
                self._logger.error("The days to backup should be an integer")
                raise
        # If the backup end is not set, then the ending date remains open

        # Parse the backup periodicity.
        try:
            self._periodicity = int(backup_variables.get(
                self.PERIODICITY_KEY))
        except ValueError:
            self._logger.error("The backup _periodicity should be an integer")
            raise

        # Parse the backup length threshold
        try:
            hours_th = int(backup_variables.get(
                self.BACKUP_LENGTH_THRESHOLD_KEY))
            self._backup_length_threshold = datetime.timedelta(hours=hours_th)
        except ValueError:
            self._logger.error("The backup length threshold should be "
                               "an integer")
            raise

    def _dictionarize_backup_info(self):
        """
        This dictionarises the backup information and returns the dictionary.
        """
        backup_variables = {
            self.OLDEST_OBJECT_BK_KEY:
                str(self._oldest_object_bk),
            self.BACKUP_DIR_KEY: self._backup_dir,
            self.DAYS_TO_BACKUP_KEY: self._days_to_backup,
            self.END_DATE_OF_BACKUP_KEY:
                None if self._end_date_of_backup is None
                else str(self._end_date_of_backup),
            self.PERIODICITY_KEY: self._periodicity,
            self.BACKUP_LENGTH_THRESHOLD_KEY:
                int((self._backup_length_threshold.total_seconds() / 3600))
        }

        return backup_variables

    def _store_backup_info(self, backup_info_file_name):
        """
        This method writes the backup variables dictionary to a file with the
        given filename.
        """
        backup_variables = self._dictionarize_backup_info()
        backup_info_file = open(backup_info_file_name, 'w')
        json.dump(backup_variables, backup_info_file)
        backup_info_file.close()

    def _find_files_to_backup(self):
        """
        Query the database for nodes that were created after the
        the start of the last backup. Return a query set.
        """
        # Go a bit further back to avoid any rounding problems. Set the
        # smallest timestamp to be backed up.
        start_of_backup = (self._oldest_object_bk -
                           datetime.timedelta(
                               minutes=self._additional_back_time_mins))

        # Find the end of backup for this round using the given _periodicity.
        backup_end_for_this_round = (self._oldest_object_bk +
                                     datetime.timedelta(
                                         days=self._periodicity))

        # If the end of the backup is after the given end by the user,
        # adapt it accordingly
        if (self._internal_end_date_of_backup is not None and
                    backup_end_for_this_round > self._internal_end_date_of_backup):
            backup_end_for_this_round = self._internal_end_date_of_backup

        # If the end of the backup is after then current time,
        # adapt the end accordingly
        now_timestamp = datetime.datetime.now(dtimezone.get_current_timezone())
        if backup_end_for_this_round > now_timestamp:
            self._logger.info(
                "We can not backup until {}. ".format(
                    backup_end_for_this_round) +
                "We will backup until now ({}).".format(now_timestamp))
            backup_end_for_this_round = now_timestamp

        # Check if the backup length is below the backup length threshold
        if backup_end_for_this_round - start_of_backup < \
                self._backup_length_threshold:
            self._logger.info("Backup (timestamp) length is below "
                              "the given threshold. Backup finished")
            return -1, None

        # Construct the queries & query sets
        query_sets = self._get_query_sets(start_of_backup, backup_end_for_this_round)

        # Set the new start of the backup
        self._oldest_object_bk = backup_end_for_this_round

        # Check if threshold is 0
        if self._backup_length_threshold == datetime.timedelta(hours=0):
            return -2, query_sets

        return 0, query_sets

    def _get_repository_path(self):
        from aiida.backends import settings
        from aiida.common.setup import (get_config, get_profile_config,
                                        parse_repository_uri)
        from aiida.common.exceptions import ConfigurationError

        try:
            confs = get_config()
        except ConfigurationError:
            raise ConfigurationError(
                "Please run the AiiDA Installation, no config found")

        if settings.AIIDADB_PROFILE is None:
            raise ConfigurationError(
                "settings.AIIDADB_PROFILE not defined, did you load django"
                "through the AiiDA load_dbenv()?")

        profile_conf = get_profile_config(settings.AIIDADB_PROFILE, conf_dict=confs)

        REPOSITORY_URI = profile_conf.get('AIIDADB_REPOSITORY_URI', '')
        REPOSITORY_PROTOCOL, REPOSITORY_PATH = parse_repository_uri(REPOSITORY_URI)

        return REPOSITORY_PATH

    def _backup_needed_files(self, query_sets):
        REPOSITORY_PATH = self._get_repository_path()
        repository_path = os.path.normpath(REPOSITORY_PATH)

        parent_dir_set = set()
        copy_counter = 0

        dir_no_to_copy = 0

        for query_set in query_sets:
            dir_no_to_copy += self._get_query_set_length(query_set)

        self._logger.info("Start copying {} directories".format(dir_no_to_copy))

        last_progress_print = datetime.datetime.now()
        percent_progress = 0

        for query_set in query_sets:
            iterator = self._get_query_set_iterator(query_set)

            for item in iterator:
                source_dir = self._get_source_directory(item)

                # Get the relative directory without the / which
                # separates the repository_path from the relative_dir.
                relative_dir = source_dir[(len(repository_path) + 1):]
                destination_dir = os.path.join(self._backup_dir, relative_dir)

                # Remove the destination directory if it already exists
                if os.path.exists(destination_dir):
                    shutil.rmtree(destination_dir)

                # Copy the needed directory
                try:
                    shutil.copytree(source_dir, destination_dir, True, None)
                except EnvironmentError as e:
                    self._logger.warning(
                        "Problem copying directory {} ".format(source_dir) +
                        "to {}. ".format(destination_dir) +
                        "More information: {} (Error no: {})".format(
                            e.strerror,
                            e.errno))
                    # Raise envEr

                # Extract the needed parent directories
                AbstractBackup._extract_parent_dirs(relative_dir, parent_dir_set)
                copy_counter += 1

                if (self._logger.getEffectiveLevel() <= logging.INFO and
                            (datetime.datetime.now() -
                                 last_progress_print).seconds > 60):
                    last_progress_print = datetime.datetime.now()
                    percent_progress = (copy_counter * 100 / dir_no_to_copy)
                    self._logger.info(
                        "Copied {} ".format(copy_counter) +
                        "directories [{}]".format(item.__class__.__name__, ) +
                        " ({}/100)".format(percent_progress))

                if (self._logger.getEffectiveLevel() <= logging.INFO and
                            percent_progress < (
                                        copy_counter * 100 / dir_no_to_copy)):
                    percent_progress = (copy_counter * 100 / dir_no_to_copy)
                    last_progress_print = datetime.datetime.now()
                    self._logger.info(
                        "Copied {} ".format(copy_counter) +
                        "directories [{}]".format(item.__class__.__name__, ) +
                        " ({}/100)".format(percent_progress))

        self._logger.info("{} directories copied".format(copy_counter))

        self._logger.info("Start setting permissions")
        perm_counter = 0
        for tempRelPath in parent_dir_set:
            try:
                shutil.copystat(os.path.join(repository_path, tempRelPath),
                                os.path.join(self._backup_dir, tempRelPath))
            except OSError as e:
                self._logger.warning(
                    "Problem setting permissions to directory " +
                    "{}.".format(os.path.join(self._backup_dir,
                                              tempRelPath)))
                self._logger.warning(os.path.join(repository_path, tempRelPath))
                self._logger.warning("More information: " +
                                     "{} (Error no: {})".format(e.strerror,
                                                                e.errno))
            perm_counter += 1

        self._logger.info("Set correct permissions "
                          "to {} directories.".format(perm_counter))

        self._logger.info("End of backup")
        self._logger.info("Backed up objects with modification timestamp "
                          "less or equal to {}".format(
            self._oldest_object_bk))

    @staticmethod
    def _extract_parent_dirs(given_rel_dir, parent_dir_set):
        """
        This method extracts the parent directories of the givenDir
        and populates the parent_dir_set.
        """
        sub_paths = given_rel_dir.split("/")

        temp_path = ""
        for sub_path in sub_paths:
            temp_path += sub_path + "/"
            parent_dir_set.add(temp_path)

        return parent_dir_set

    def run(self):
        while True:
            self._read_backup_info_from_file(self._backup_info_filepath)
            item_sets_to_backup = self._find_files_to_backup()
            if item_sets_to_backup[0] == -1:
                break
            self._backup_needed_files(item_sets_to_backup[1])
            self._store_backup_info(self._backup_info_filepath)
            if item_sets_to_backup[0] == -2:
                self._logger.info("Threshold is 0. "
                                  "Backed up one round and exiting.")
                break

    @abstractmethod
    def _query_first_workflow(self):
        """
        Query first workflow
        """
        pass

    @abstractmethod
    def _query_first_node(self):
        """
        Query first node
        """
        pass

    @abstractmethod
    def _get_query_set_length(self, query_set):
        """
        Get query set length
        """
        pass

    @abstractmethod
    def _get_query_sets(self, start_of_backup, backup_end_for_this_round):
        """
        Get query set
        """
        pass

    @abstractmethod
    def _get_query_set_iterator(self, query_set):
        """
        Get query set iterator
        """
        pass

    @abstractmethod
    def _get_source_directory(self, item):
        """
        Get source directory of item
        :param self:
        :return:
        """
        pass



class BackupError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
