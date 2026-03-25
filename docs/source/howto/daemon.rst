
.. _how-to:manage-daemon:

How to manage the daemon
------------------------

The AiiDA daemon process runs in the background and takes care of processing your submitted calculations and workflows, checking their status, retrieving their results once they are finished and storing them in the AiiDA database.

The AiiDA daemon is controlled using three simple commands:

* ``verdi daemon start``: start the daemon
* ``verdi daemon status``: check the status of the daemon
* ``verdi daemon stop``: stop the daemon

For a practical debugging walkthrough with common failure scenarios, see also
`Debugging AiiDA Daemon (a practical guide) <https://aiida.net/news/posts/2025-02-21-how-to-debug-aiida-daemon.html>`__.
