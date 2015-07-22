import os
import sys
import logging
import shutil
import datetime
import json
import stat

# Import needed for Django initialization
from aiida.djsite.utils import load_dbenv

from aiida.common.setup import AIIDA_CONFIG_FOLDER
load_dbenv()
from backup import Backup
from dateutil.parser import parse
from os.path import expanduser
from __builtin__ import int


class BackupSetup(object):
    
    def __init__(self):
        # The backup directory names
        self._conf_backup_folder_rel = "backup"
        self._file_backup_folder_rel = "backup_dest"
        
        # The backup configuration file (& template) names
        self._backup_info_filename = "backup_info.json"
        self._backup_info_tmpl_filename = "backup_info.json.tmpl"

        # The name of the sctipt that initiates the backup
        self._script_filename = "start_backup.py"

        # Configuring the logging
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

        # The logger of the backup script
        self._logger = logging.getLogger("aiida_backup_setup")

    
    def query_yes_no(self, question, default="yes"):
        """Ask a yes/no question via raw_input() and return their answer.
    
        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).
    
        The "answer" return value is True for "yes" or False for "no".
        """
        valid = {"yes": True, "y": True, "ye": True,
                 "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)
    
        while True:
            sys.stdout.write(question + prompt)
            choice = raw_input().lower()
            if default is not None and choice == "":
                if default == "":
                    return None
                else:
                    return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")


    def query_string(self, question, default):
        if default is None or not default:
            prompt = ""
        else:
            prompt = " [{}]".format(default)
        
        while True:
            sys.stdout.write(question + prompt)
            reply = raw_input()
            if default is not None and reply == "":
                if default == "":
                    return None
                else:
                    return default
            elif reply != "":
                return reply
            else:
                sys.stdout.write("Please provide a non empty answer.\n")


    def ask_backup_question(self, question, reply_type, allow_none_as_answer):
        final_answer =  None
        
        while True:
            answer = self.query_string(question, "")
            
            # If the reply is empty
            if not answer:
                if not allow_none_as_answer:
                    continue
            # Otherwise, try to parse it    
            else:
                try:
                    if reply_type == int:
                        final_answer = int(answer)
                    elif reply_type == datetime.datetime:
                        final_answer = parse(answer)
                    else:
                        raise ValueError
                # If it is not parsable...
                except ValueError:
                    sys.stdout.write("The given value could not be parsed. " +
                        "Type expected: {}\n".format(reply_type))
                    # If the timestamp could not have been parsed, ask again the
                    # same question.
                    continue
            
            if self.query_yes_no("{} was parsed. Is it correct?"
                                 .format(final_answer), default="yes"):
                break
        return final_answer


    def construct_backup_variables(self, file_backup_folder_abs):
        backup_variables = {}

        # Setting the oldest backup timestamp
        oldest_object_backedup = \
            self.ask_backup_question("Please provide the oldest backup " +
                            "timestamp (e.g. 2014-07-18 13:54:53.688484+00:00). ", 
                            datetime.datetime, True)
        if oldest_object_backedup == None:
            backup_variables[Backup._oldest_object_backedup_key] = None
        else:
            backup_variables[Backup._oldest_object_backedup_key] = \
                str(oldest_object_backedup)
        
        # Setting the backup directory
        backup_variables[Backup._backup_dir_key] = file_backup_folder_abs
        
        # Setting the days_to_backup
        backup_variables[Backup._days_to_backup_key] = \
        self.ask_backup_question("Please provide the number of days to backup.", 
                            int, True)
        
        # Setting the end date
        end_date_of_backup_key = \
        self.ask_backup_question("Please provide the end date of the backup " +
                            "(e.g. 2014-07-18 13:54:53.688484+00:00).", 
                            datetime.datetime, True)
        if end_date_of_backup_key == None:
            backup_variables[Backup._end_date_of_backup_key] = None
        else:
            backup_variables[Backup._end_date_of_backup_key] = \
                str(end_date_of_backup_key)
                
        # Setting the backup periodicity
        backup_variables[Backup._periodicity_key] = \
        self.ask_backup_question("Please periodicity (in days).", 
                            int, False)
        
        # Setting the backup threshold
        backup_variables[Backup._backup_length_threshold_key] = \
        self.ask_backup_question("Please provide the backup threshold (in hours).", 
                            int, False)
        
        return backup_variables


    def create_dir(self, question, dir_path):
        final_path = self.query_string(question, dir_path)
        
        if not os.path.exists(final_path):
            if self.query_yes_no("The path {} doesn't exist. Should it be "
                              "created?".format(final_path), "yes"):
                try:
                    os.makedirs(final_path)
                except OSError:
                    self._logger.error("Error creating the path "
                                       "{}.".format(final_path))
                    raise
        return final_path


    def print_info(self):
        info_str = \
"""Variables to set up in the JSON file
------------------------------------

- backup_length_threshold (in hours):

If the backup script reaches a point that it has to backup for a period which is smaller that the given threshold, it will stop. The starting point of each backup period is given by the variables that will be set below (oldest_object_backedup, periodicity, end_date_of_backup and days_to_backup).

e.g. "backup_length_threshold": 1


- periodicity (in days):

The backup runs periodicly for a number of days defined in the periodiciry variable. The purpose of this variable is to limit the backup to run only on a few number of days and therefore to limit the number of files that are backed up no every round.

e.g. "periodicity": 2


-oldest_object_backedup (timestamp or null):

This is the timestamp of the oldest object that was backed up. If you are not aware of this value or if it is the first time that you start a backup up for this repository, then set this value to null. Then the script will search the creation date of the oldest workflow or node object in the database and it will start the backup from that date.

e.g. "oldest_object_backedup": "2015-07-20 11:13:08.145804+02:00"


- end_date_of_backup

If set, the backup script will backup files that have a modification date until the given end date of backup. If not set, the ending of the backup will be set by the following variable (days_to_backup) which specifies how many days to backup from the start of the backup. If none of these variables are set (end_date_of_backup & days_to_backup) then the end date of backup is set to the current date.

e.g. "end_date_of_backup": null or "end_date_of_backup": "2015-07-20 11:13:08.145804+02:00"


- days_to_backup

If set, you specify how many days from the starting date of your backup, you will backup. If it set to null and also end_date_of_backup is set to null then the end date of the backup is set to the current date. You can not set days_to_backup & end_date_of_backup in the same time (it will lead to an error).

e.g. "days_to_backup": null or "days_to_backup": 5


- backup_dir

The destination directory of the backup.

e.g. "backup_dir": "/scratch/spyros/backupScriptDestGio/"
"""
        sys.stdout.write(info_str)


    def run(self):
        
        conf_backup_folder_abs = self.create_dir("Please provide the backup "
                               "folder by providing the full path."
                               , os.path.join(
                                  expanduser(AIIDA_CONFIG_FOLDER), 
                                  self._conf_backup_folder_rel))

        file_backup_folder_abs = self.create_dir("Please provide the destination "
                               "folder of the backup (normally in the previously "
                               "provided backup folder)."
                               , os.path.join(
                                  conf_backup_folder_abs, 
                                  self._file_backup_folder_rel))
        
        # The template backup configuration file
        template_conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     self._backup_info_tmpl_filename)
        # Copy the configuration file to the backup folder
        try:
            shutil.copy(template_conf_path, conf_backup_folder_abs)
        except Exception:
            self._logger.error("Error copying the file {} ".format(template_conf_path) +
                               "to the directory {}.".format(conf_backup_folder_abs))
            raise
        
        if self.query_yes_no("A sample configuration file was copied to " + 
                             "{}. Would you like to ".format(conf_backup_folder_abs) +
                             "see the configuration parameters " +
                             "explanation?", default="yes") == True:
            self.print_info()


        # Construct the path to the backup configuration file
        final_conf_filepath = os.path.join(conf_backup_folder_abs,
                                               self._backup_info_filename)

        # If the backup parameters are configured now
        if self.query_yes_no("Would you like to configure the backup " +
                             "configuration file now?", default="yes") == True:

            # Ask questions to properly setup the backup variables
            backup_variables = self.construct_backup_variables(file_backup_folder_abs)

            with open(final_conf_filepath, 'w') as backup_info_file:
                json.dump(backup_variables, backup_info_file)
        # If the backup parameters are configured manually
        else:
            sys.stdout.write(
             "Please rename the file {} ".format(self._backup_info_tmpl_filename) +
             "found in {} to ".format(conf_backup_folder_abs) +
             "{} and ".format(self._backup_info_filename) +
             "change the backup parameters accordingly.\n")

        # The contents of the startup script
        script_content = \
"""#!/usr/bin/env runaiida
import logging

from aiida.common.additions.backup_script.backup import Backup

# Create the backup instance
backup_inst = Backup(backup_info_filepath="{}", additional_back_time_mins = 2)

# Define the backup logging level
backup_inst._logger.setLevel(logging.INFO)

# Start the backup
backup_inst.run()
""".format(final_conf_filepath)

        # Script full path
        script_path = os.path.join(conf_backup_folder_abs, self._script_filename)

        # Write the contents to the script
        with open(script_path ,'w') as script_file:
            script_file.write(script_content)

        # Set the right permissions
        try:
            st = os.stat(script_path)
            os.chmod(script_path, st.st_mode | stat.S_IEXEC)
        except OSError:
            self._logger.error("Problem setting the right permissions to the " +
                               "script {}.".format(script_path))
            raise

if __name__ == '__main__':
    print os.path.dirname(os.path.abspath(__file__))
    print os.path.abspath("backup_info.json.tmpl")
    BackupSetup().run()
    
    