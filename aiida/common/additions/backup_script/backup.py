import json
import datetime
import shutil
import os
import logging

from dateutil.parser import parse
from django.utils import timezone as dtimezone
from pytz import timezone as ptimezone
from sets import Set
 
from aiida.orm.node import Node
from aiida.orm.workflow import Workflow

from aiida.djsite.db.models import DbNode
from aiida.djsite.db.models import DbWorkflow

from aiida.common.folders import RepositoryFolder

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Spyros Zoupanos"

class Backup(object):

    # Keys in the dictionary loaded by the JSON file
    _oldest_object_backedup_key = "oldest_object_backedup"
    _backup_dir_key = "backup_dir"
    _days_to_backup_key = "days_to_backup"
    _end_date_of_backup_key = "end_date_of_backup"
    _periodicity_key = "periodicity"
    _backup_length_threshold_key = "backup_length_threshold"


    # Backup parameters that will be populated by the JSON file
    
    # Where did the last backup stop
    _oldest_object_backedup = None
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
    
    
    def __init__(self, backup_info_filepath, additional_back_time_mins):
        
        # The path to the JSON file with the backup information
        self._backup_info_filepath = backup_info_filepath

        self._additional_back_time_mins = additional_back_time_mins
        
        # Configuring the logging
        logging.basicConfig(level=logging.INFO,
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
                self._logger.error("Could not parse file " + backup_info_file_name)
                raise BackupError("Could not parse file " + backup_info_file_name)
        
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
        if backup_variables.get(self._oldest_object_backedup_key) == None:
            query_node_res = DbNode.objects.all().order_by('ctime')[:1]
            query_workflow_res = DbWorkflow.objects.all().order_by('ctime')[:1]

            if (not query_node_res) and (not query_workflow_res):
                self._logger.error("The oldest modification date was not found.")
                raise BackupError("The oldest modification date was not found.")
            
            oldest_timestamps = [] 
            if query_node_res:
                oldest_timestamps.append(query_node_res[0].ctime)
            if query_workflow_res:
                oldest_timestamps.append(query_workflow_res[0].ctime)

            self._oldest_object_backedup = min(oldest_timestamps)
            self._logger.info("Setting the oldest modification date to the "
                         "creation date of the oldest object "
                         "({})".format(self._oldest_object_backedup))   
        
        # If the oldest backup date is not None then try to parse it
        else:
            try:
                self._oldest_object_backedup = \
                    parse(backup_variables.get(self._oldest_object_backedup_key))
                if self._oldest_object_backedup.tzinfo is None:
                    curr_timezone = str(dtimezone.get_current_timezone())
                    self._oldest_object_backedup = \
                        ptimezone(str(curr_timezone)).localize(
                                         self._oldest_object_backedup)
                    self._logger.info("No timezone defined in the oldest "
                        "modification date timestamp. Setting current " +
                        "timezone ({}).".format(curr_timezone))
            # If it is not parsable...
            except ValueError:
                self._logger.error(
                              "We did not manage to parse the start timestamp "
                              "of the last backup.")
                raise
        
        # Setting the backup directory & normalizing it
        self._backup_dir = os.path.normpath(
                                backup_variables.get(self._backup_dir_key))
        if not os.path.isdir(self._backup_dir):
            self._logger.error("The given backup directory doesn't exist.")
            raise BackupError("Only one backup end can be set (date or days"
                              "from backup start.")
        
        # You can not set an end-of-backup date and end days from the backup
        # that you should stop.
        if backup_variables.get(self._days_to_backup_key) != None \
            and backup_variables.get(self._end_date_of_backup_key) != None:
            self._logger.error("Only one end of backup date can be set.")
            raise BackupError("Only one backup end can be set (date or days"
                              "from backup start.")
        
        # Check if there is an end-of-backup date
        elif backup_variables.get(self._end_date_of_backup_key) != None:
            try:
                self._end_date_of_backup = \
                        parse(backup_variables.get(self._end_date_of_backup_key))

                if self._end_date_of_backup.tzinfo is None:
                    curr_timezone = str(dtimezone.get_current_timezone())
                    self._end_date_of_backup = \
                        ptimezone(str(curr_timezone)).localize(
                                         self._end_date_of_backup)
                    self._logger.info("No timezone defined in the end "
                        "date of backup timestamp. Setting current " +
                        "timezone ({}).".format(curr_timezone))

                self._internal_end_date_of_backup = self._end_date_of_backup 
            except ValueError:
                self._logger.error("The end date of the backup could not be "
                                  "parsed correctly")
                raise
        
        # Check if there is defined a days to backup
        elif backup_variables.get(self._days_to_backup_key) != None:
            try:
                self._days_to_backup = \
                        int(backup_variables.get(self._days_to_backup_key))
                self._internal_end_date_of_backup = self._oldest_object_backedup \
                    + datetime.timedelta(days=self._days_to_backup)
            except ValueError:
                self._logger.error("The days to backup should be an integer")
                raise
        # If the backup end is not set, then the ending date remains open
        
        # Parse the backup periodicity.
        try:
            self._periodicity = int(backup_variables.get(self._periodicity_key))
        except ValueError:
            self._logger.error("The backup _periodicity should be an integer")
            raise
        
        # Parse the backup length.threshold
        try:
            hoursThres = int(backup_variables.get(
                                           self._backup_length_threshold_key))
            self._backup_length_threshold = datetime.timedelta(hours=hoursThres)
        except ValueError:
            self._logger.error("The backup length threshold should be an integer")
            raise


    def _dictionarize_backup_info(self):
        """
        This dictionarises the backup information and returns the dictionary.
        """
        backup_variables = {}
        backup_variables[self._oldest_object_backedup_key] = \
                                        str(self._oldest_object_backedup)
        backup_variables[self._backup_dir_key] = self._backup_dir
        backup_variables[self._days_to_backup_key] = self._days_to_backup
        backup_variables[self._end_date_of_backup_key] = \
            None if self._end_date_of_backup == None else str(self._end_date_of_backup)
        backup_variables[self._periodicity_key] = self._periodicity
        backup_variables[self._backup_length_threshold_key] = \
                int((self._backup_length_threshold.total_seconds() / 3600))
        
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
        start_of_backup = self._oldest_object_backedup - \
            datetime.timedelta(minutes=self._additional_back_time_mins)
        
        # Find the end of backup for this round using the given _periodicity.
        backup_end_for_this_round = self._oldest_object_backedup + \
                                    datetime.timedelta(days=self._periodicity)
        
        # If the end of the backup is after the given end by the user,
        # adapt it accordingly
        if self._internal_end_date_of_backup != None and \
            backup_end_for_this_round > self._internal_end_date_of_backup:
            backup_end_for_this_round = self._internal_end_date_of_backup
        
        # If the end of the backup is after then current time, 
        # adapt the end accordingly
        now_timestamp = datetime.datetime.now(dtimezone.get_current_timezone())
        if backup_end_for_this_round > now_timestamp:
            backup_end_for_this_round = now_timestamp
            self._logger.info(
                "We can not backup until {}. ".format(backup_end_for_this_round) +
                "We will backup until now ({}).".format(now_timestamp))
             
        # Check if the backup length is below the backup length threshold
        if backup_end_for_this_round - start_of_backup < \
                    self._backup_length_threshold:
            self._logger.info("Backup (timestamp) length is below "
                        "the given threshold. Backup finished")
            return None

        # Construct the queries & query sets     
        querySets = []
        querySets.append(DbNode.objects.filter(mtime__gte=start_of_backup,
                                    mtime__lte=backup_end_for_this_round))
        querySets.append(DbWorkflow.objects.filter(mtime__gte=start_of_backup,
                                    mtime__lte=backup_end_for_this_round))
        
        # Set the new start of the backup
        self._oldest_object_backedup = backup_end_for_this_round
        
        return querySets
    

    def _backup_needed_files(self, query_sets):
        from aiida.djsite.settings.settings import REPOSITORY_PATH
        
        parent_dir_set = Set()
        copy_counter = 0
        
        dir_no_to_copy = 0
        for query_set in query_sets:
            dir_no_to_copy += query_set.count()

        self._logger.info("Start copying {} directories".format(dir_no_to_copy))
        
        last_progress_print = datetime.datetime.now()
        percent_progress = 0
        
        for query_set in query_sets:
            for item in query_set.iterator():
                source_dir = None
                if type(item) == DbWorkflow:
                    source_dir = RepositoryFolder(
                                    section=Workflow._section_name,
                                    uuid=item.uuid).abspath
                elif type(item) == DbNode:
                    source_dir = RepositoryFolder(
                                    section=Node._section_name,
                                    uuid=item.uuid).abspath
                else:
                    #raise exception
                    self._logger.error(
                        "Unexpected item type to backup: {}".format(type(item)))
                    raise BackupError(
                        "Unexpected item type to backup: {}".format(type(item)))
                    
                relative_dir = source_dir[len(REPOSITORY_PATH):]
                destination_dir = os.path.join(self._backup_dir, relative_dir)
                
                # Remove the destination directory if it already exists
                if os.path.exists(destination_dir):
                    shutil.rmtree(destination_dir)
                
                # Copy the needed directory
                try:
                    shutil.copytree(source_dir, destination_dir, True, None)
                except EnvironmentError as envEr:
                    self._logger.warning(
                        "Problem copying directory {}".format(source_dir) +
                        "More information: {} (Error no: {})".format(
                                                             envEr.strerror,
                                                             envEr.errno))
                    #raise envEr

                # Extract the needed parent directories
                self._extract_parent_dirs(relative_dir, parent_dir_set)
                copy_counter += 1
                
                if self._logger.getEffectiveLevel() <= logging.INFO and \
                    (datetime.datetime.now() - last_progress_print).seconds > 60 :
                    last_progress_print = datetime.datetime.now()
                    percent_progress = (copy_counter*100/dir_no_to_copy)
                    self._logger.info(
                         "Copied {} ".format(copy_counter) +
                         "directories [{}]".format(item.__class__.__name__,) +
                         " ({}/100)".format(percent_progress))
                
                if self._logger.getEffectiveLevel() <= logging.INFO and \
                    percent_progress < (copy_counter*100/dir_no_to_copy):
                    percent_progress = (copy_counter*100/dir_no_to_copy)
                    last_progress_print = datetime.datetime.now()
                    self._logger.info(
                         "Copied {} ".format(copy_counter) +
                         "directories [{}]".format(item.__class__.__name__,) +
                         " ({}/100)".format(percent_progress))

        self._logger.info("{} directories copied".format(copy_counter))
        
        self._logger.info("Start setting permissions")
        perm_counter = 0
        for tempRelPath in parent_dir_set:
            try:
                shutil.copystat(REPOSITORY_PATH + tempRelPath,
                                self._backup_dir + tempRelPath)
            except OSError as osEr:
                self._logger.warning("Problem setting permissions to directory "
                                 + self._backup_dir + tempRelPath)
                self._logger.warning("More information:" +  
                                    " {} (Error no: {})".format(osEr.strerror,
                                                                osEr.errno))
                #raise osEr
            perm_counter += 1
        
        self._logger.info("Set correct permissions" + 
                         "to {} directories.".format(perm_counter))
       
        self._logger.info("End of backup")
        self._logger.info("Backed up objects with modification timestamp " +
                     "less or equal to {}".format(self._oldest_object_backedup))


    def _extract_parent_dirs(self, given_rel_dir, parent_dir_set):
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
            itemSetsToBackup = self._find_files_to_backup()
            if itemSetsToBackup == None:
                break
            self._backup_needed_files(itemSetsToBackup)
            self._store_backup_info(self._backup_info_filepath)


class BackupError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


#if __name__ == '__main__':
#    Backup(_backup_info_filepath="/home/szoupanos/workspace/BackupScript/src/backupInfo.json",
#           _oldest_object_backedup_key="_oldest_object_backedup", 
#           "_backup_dir", "_days_to_backup",
#           "_end_date_of_backup", "_periodicity", "_backup_length_threshold", 2).run()

