Backup script of the AiiDA repository
=====================================

This script backs up the AiiDA repository that is referenced by the current AiiDA database. The script will start from the "oldest_object_backedup" date or the date of the oldest node/workflow object found and it will periodically backup (in periods of "periodicity" days) until the ending date of the backup specified by "end_date_of_backup" or "days_to_backup"

To start the backup, please, run the start_backup.py script.

For more information on the backup variables that have to be set in the JSON file, please consult the documentation below.


Variables to set up in the JSON file
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


