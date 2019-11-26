.. _disable_repo_indexing:

Exclude file repository from index
----------------------------------

Many Linux distributions include the ``locate`` command to quickly find files and folders,
and run a daily cron job ``updatedb.mlocate`` to create the corresponding index.
A large file repository can take a long time to index, up to the point where the hard drive is constantly indexing.

In order to exclude the repository folder from indexing, add its path to the ``PRUNEPATH`` variable in the ``/etc/updatedb.conf`` configuration file
(use ``sudo``).
