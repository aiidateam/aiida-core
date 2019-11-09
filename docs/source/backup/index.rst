.. _backup:

AiiDA stores:

 * the profile configuration in the ``config.json`` file located in the ``.aiida`` folder. Typically located at ``~/.aiida`` (see also :ref:`configure_aiida`).

 * files associated with nodes in the repository folder (one per profile). Typically located in the ``.aiida`` folder.

 * queryable metadata in the PostgreSQL database (one per profile).

All three components are required for the operation of AiiDA and should be backed up.

.. _repository_backup:

Repository backup (``.aiida`` folder)
++++++++++++++++++++++++++++++++++++++

For **small repositories** back up the ``.aiida`` folder either by making a full copy or using tools for incremental backups like ``rsync``.

For **large repositories** with more than 100k nodes, even incremental backups can take a significant amount of time.
AiiDA provides a helper script that takes advantage of the AiiDA database in order to figure out which files have been added since your last backup.
The instructions below explain how to use it:


 1. Configure your backup using ``verdi -p PROFILENAME devel configure-backup`` where ``PROFILENAME`` is the name of the AiiDA profile that should be backed up.
    | This will ask for information on:

      * The "backup folder", where the backup *configuration file* will be placed.
        This defaults to a folder named ``backup_PROFILENAME`` in your ``.aiida`` directory.

      * The "destination folder", where the files of the backup will be stored.
        This defaults to a subfolder of the backup folder but we **strongly suggest to back up to a different drive** (see note below).

    The configuration step creates two files in the "backup folder": a ``backup_info.json`` configuration file (can also be edited manually) and a ``start_backup.py`` script.

    .. note::

        Using the same disk for your backup forgoes protection against the most common cause of data loss: disk failure.
        One simple option is to use a destination folder mounted over ssh.

        On Ubuntu, install ``sshfs`` using ``sudo apt-get install sshfs``.
        Imagine you run your calculations on `server_1` and would like to back up regularly to `server_2`.
        Mount a `server_2` directory on `server_1` using the following command on `server_1`:

        .. code-block:: shell

            sshfs -o idmap=user -o rw backup_user@server_2:/home/backup_user/backup_destination_dir/ /home/aiida_user/remote_backup_dir/

        Use ``gnome-session-properties`` in the terminal to add this line to the actions performed at start-up.
        Do **not** add it to your shell's startup file (e.g. ``.bashrc``) or your computer will complain that the mount point is not empty whenever you open a new terminal.


 2. Run the ``start_backup.py`` script in the "backup folder" to start the backup.

    This will back up all data added after the ``oldest_object_backedup`` date.
    It will only carry out a new backup every ``periodicity`` days, until a certain end date if specified (using ``end_date_of_backup`` or ``days_to_backup``), see :ref:`backup_configuration_options` below.

    | Once you've checked that it works, make sure to run the script periodically (e.g. using a daily cron job, see note below).

    .. note::

        On Ubuntu, you can set up a cron job using::

            sudo crontab -u USERNAME -e

        It will open an editor, where you can add a line of the form::

            00 03 * * * /home/USERNAME/.aiida/backup/start_backup.py 2>&1 | mail -s "Incremental backup of the repository" USER_EMAIL@domain.net

        or (if you need to backup a different profile than the default one)::

            00 03 * * * verdi -p PROFILENAME run /home/USERNAME/.aiida/backup/start_backup.py 2>&1 | mail -s "Incremental backup of the repository" USER_EMAIL@domain.net

        This will launch the backup of the database every day at 3 AM (03:00), and send the output (or any error message) to the email address specified at the end (provided the ``mail`` command -- from ``mailutils`` -- is configured appropriately).


Finally, if you have a separate automatic backup of your home directory set up, do not forget to exclude the repository folder.

.. _backup_configuration_options:


Configuration options
---------------------

The configuration options in the ``backup_info.json`` are:

* | ``periodicity`` (in `days`):
  | The backup runs periodically for a number of days defined in the periodicity variable.
    The purpose of this variable is to limit the backup to run only on a few number of days and therefore to limit the number of files that are backed up at every round.
  | E.g. ``"periodicity": 2``.
  | Example: If you have files in the AiiDA repositories created in the past 30 days, and periodicity is 15, the first run will backup the files of the first 15 days; a second run of the script will backup the next 15 days, completing the backup (if it is run within the same day).
    Further runs will only backup newer files, if they are created.

* | ``oldest_object_backedup`` (`timestamp` or ``null``):
  | This is the timestamp of the oldest object that was backed up.
    If you are not aware of this value or if it is the first time you start a backup for this repository, then set this value to ``null``.
    Then the script will search the creation date of the oldest Node object in the database and start the backup from that date.
  | E.g. ``"oldest_object_backedup": "2015-07-20 11:13:08.145804+02:00"``

* | ``end_date_of_backup`` (`timestamp` or ``null``):
  | If set, the backup script will backup files that have a modification date up until the value specified by this variable.
    If not set, the ending of the backup will be set by the ``days_to_backup`` variable, which specifies how many days to backup from the start of the backup.
    If none of these variables are set (``end_date_of_backup`` and ``days_to_backup``), then the end date of backup is set to the current date.
  | E.g. ``"end_date_of_backup": null`` or ``"end_date_of_backup": "2015-07-20 11:13:08.145804+02:00"``.

* | ``days_to_backup`` (in `days` or ``null``):
  | If set, you specify how many days you will backup from the starting date of your backup.
    If it is set to ``null`` and also ``end_date_of_backup`` is set to ``null``, then the end date of the backup is set to the current date.
    You can not set ``days_to_backup`` & ``end_date_of_backup`` at the same time (it will lead to an error).
  | E.g. ``"days_to_backup": null`` or ``"days_to_backup": 5``.

* | ``backup_length_threshold`` (in `hours`):
  | The backup script runs in rounds and on every round it will backup a number of days that are controlled primarily by ``periodicity`` and also by ``end_date_of_backup`` / ``days_to_backup``, for the last backup round.
    The ``backup_length_threshold`` specifies the *lowest acceptable* round length.
    This is important for the end of the backup.
  | E.g. ``backup_length_threshold: 1``

* | ``backup_dir`` (absolute path):
  | The destination directory of the backup.
  | E.g. ``"backup_dir": "/home/USERNAME/.aiida/backup/backup_dest"``.


.. _backup_postgresql:

Database backup
+++++++++++++++

PostgreSQL typically spreads database information over multiple files that, if backed up directly, are not guaranteed to restore the database.
We therefore strongly recommend to periodically dump the database contents to a file (which you can then back up using your method of choice).

The instructions below show how to achieve this under Ubuntu 12.04 and 18.04.
In the following, we assume your database is called ``aiidadb``, and the database user and owner is ``aiida``.
You'll find this information in the output of ``verdi profile show``.

In order to dump your database, use a bash script similar to :download:`backup_postgresql.sh <backup_postgresql.sh>`:

.. _backup_script:

.. literalinclude:: backup_postgresql.sh
   :language: shell

.. note::
    In order to avoid having to enter your database password each time you use the script, you can create a file :download:`.pgpass <pgpass>` in your home directory:

    .. literalinclude:: pgpass

    where ``YOUR_DATABASE_PASSWORD`` is the password you set up for the database.

    This file needs read and write permissions: ``chmod u=rw ~/.pgpass``.


In order to automatically dump the database to a file ``~/.aiida/${AIIDADB}-backup.psql.gz`` once per day, you can add a cron job:

Add the following script :download:`backup-aiidadb-USERNAME <backup-aiidadb-USERNAME>` to the folder ``/etc/cron.daily/``:

.. literalinclude:: backup-aiidadb-USERNAME
   :language: shell

and replace all instances of ``USERNAME`` with your UNIX user name.

Remember to give the script execute permissions::

  sudo chmod +x /etc/cron.daily/backup-aiidadb-USERNAME

Finally make sure your database folder (``/home/USERNAME/.aiida/``) containing this dump file and the ``repository`` directory, is properly backed up by your backup software (under Ubuntu, 12.04: Backup -> check the "Folders" tab, 18.04: Backups -> check the "Folder to save" tab).

.. _restore_postgresql:

Restore backup
++++++++++++++

In order to restore a backup, you will need to:

 1. | Restore the repository folder.
    | If you used the :ref:`backup script <backup_script>`, this involves extracting the corresponding zip file (should be created in ``~/.aiida/``).

 2. | Create an empty database following the instructions described in :ref:`database` skipping the ``verdi setup`` phase.
    | The database should have the same name and database username as the original one (i.e. if you are restoring on the original postgresql cluster, you may have to either rename or delete the original database).

 3. As the ``postgres`` user, ``cd`` to the folder containing the database dump (``aiidadb-backup.psql``) and load it::

      psql -h localhost -U aiida -d aiidadb -f aiidadb-backup.psql


    After supplying your database password, the database should be restored.

    .. note::

        On Ubuntu, type ``sudo su - postgres`` to become the postgres UNIX user.



