Run scripts and open an interactive shell with AiiDA
====================================================

How to run a script
+++++++++++++++++++
In order to run a script that interacts with the database, you need
to select the proper settings for the database.

To simplify the procedure, we provide an utility command, ``load_dbenv``.
As the first two lines of your script, write::
  
  from aiida import load_dbenv
  load_dbenv()

From there on, you can import without problems any module and interact with
the database (submit calculations, perform queries, ...).



.. _verdi_shell_description:

verdi shell
+++++++++++
If you want to work in interactive mode (rather than writing a script and
then execute it), we strongly suggest that you use the ``verdi shell`` command.

This command will run an IPython shell, if ipython is installed in the system
(it also supports bpython), which has many nice features, including TAB 
completion and much more.

Moreover, it will automatically execute the ``load_dbenv`` command, and
automatically several modules/classes.

.. note:: It is possible to customize the shell by adding modules to be loaded 
	automatically, thanks to the ``verdi devel setproperty verdishell.modules``
	command.
	See :doc:`here<../verdi/properties>` for more information.




