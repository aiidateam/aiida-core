.. _reference:backup-script-config-options:

**********************************************
Repository backup script configuration options
**********************************************

We describe below the configuration options for the repository backup script that is provided with AiiDA (whose use is described :ref:`in this howto <how-to:installation:backup:repository>`).

Here are the flags that can be set in the ``backup_info.json`` file and their meaning:

* ``periodicity`` (in `days`): The backup runs periodically for a number of days defined in the periodicity variable.
  The purpose of this variable is to limit the backup to run only on a few number of days and therefore to limit the number of files that are backed up at every round.
  E.g. ``"periodicity": 2``.

  Example: If you have files in the AiiDA repositories created in the past 30 days, and periodicity is 15, the first run will backup the files of the first 15 days; a second run of the script will backup the next 15 days, completing the backup (if it is run within the same day).
  Further runs will only backup newer files, if they are created.

* ``oldest_object_backedup`` (`timestamp` or ``null``): This is the timestamp of the oldest object that was backed up.
  If you are not aware of this value or if it is the first time you start a backup for this repository, then set this value to ``null``.
  Then the script will search the creation date of the oldest Node object in the database and start the backup from that date.
  E.g. ``"oldest_object_backedup": "2015-07-20 11:13:08.145804+02:00"``

* ``end_date_of_backup`` (`timestamp` or ``null``): If set, the backup script will backup files that have a modification date up until the value specified by this variable.
  If not set, the ending of the backup will be set by the ``days_to_backup`` variable, which specifies how many days to backup from the start of the backup.
  If none of these variables are set (``end_date_of_backup`` and ``days_to_backup``), then the end date of backup is set to the current date.
  E.g. ``"end_date_of_backup": null`` or ``"end_date_of_backup": "2015-07-20 11:13:08.145804+02:00"``.

* ``days_to_backup`` (in `days` or ``null``): If set, you specify how many days you will backup from the starting date of your backup.
  If it is set to ``null`` and also ``end_date_of_backup`` is set to ``null``, then the end date of the backup is set to the current date.
  You can not set ``days_to_backup`` & ``end_date_of_backup`` at the same time (it will lead to an error).
  E.g. ``"days_to_backup": null`` or ``"days_to_backup": 5``.

* ``backup_length_threshold`` (in `hours`): The backup script runs in rounds and on every round it will backup a number of days that are controlled primarily by ``periodicity`` and also by ``end_date_of_backup`` / ``days_to_backup``, for the last backup round.
  The ``backup_length_threshold`` specifies the *lowest acceptable* round length.
  This is important for the end of the backup.
  E.g. ``backup_length_threshold: 1``

* ``backup_dir`` (absolute path): The destination directory of the backup.
  E.g. ``"backup_dir": "/home/USERNAME/.aiida/backup/backup_dest"``.
