.. _move_postgresql:

Moving the database
-------------------

This section describes how to move the physical location of the database files from one location to another (e.g. if you run out of disk space).

 1. Stop the AiiDA daemon and :ref:`back up your database <backup_postgresql>`.

 2. Find the data directory of your postgres installation (something like ``/var/lib/postgresql/9.6/main``, ``/scratch/postgres/9.6/main``, ...).

    The best way is to become the postgres UNIX user and enter the postgres shell::

      psql
      SHOW data_directory;
      \q


    If you are unable to enter the postgres shell, try looking for the ``data_directory`` variable in a file ``/etc/postgresql/9.6/main/postgresql.conf`` or similar.

 3. Stop the postgres database service::

        service postgresql stop

 4. Copy all files and folders from the postgres ``data_directory`` to the new location::

      cp -a SOURCE_DIRECTORY DESTINATION_DIRECTORY


    .. note::
        Flag ``-a`` will create a directory within ``DESTINATION_DIRECTORY``, e.g.::

            cp -a OLD_DIR/main/ NEW_DIR/

        creates ``NEW_DIR/main``.
        It will also keep the file permissions (necessary).

    The file permissions of the new and old directory need to be identical (including subdirectories).
    In particular, the owner and group should be both ``postgres`` (except for symbolic links in ``server.crt`` and ``server.key`` that may or may not be present).

    .. note::

        If the permissions of these links need to be changed, use the ``-h`` option of ``chown`` to avoid changing the permissions of the destination of the links.
        In case you have changed the permission of the links destination by mistake, they should typically be (beware that this might depend on your actual distribution!)::

            -rw-r--r-- 1 root root 989 Mar  1  2012 /etc/ssl/certs/ssl-cert-snakeoil.pem
            -rw-r----- 1 root ssl-cert 1704 Mar  1  2012 /etc/ssl/private/ssl-cert-snakeoil.key

 5. Point the ``data_directory`` variable in your postgres configuration file (e.g. ``/etc/postgresql/9.6/main/postgresql.conf``) to the new directory.

 6. Restart the database daemon::

        service postgresql start


Finally, check that the data directory has indeed changed::

  psql
  SHOW data_directory;
  \q

and try a simple AiiDA query with the new database.

If everything went fine, you can delete the old database location.
