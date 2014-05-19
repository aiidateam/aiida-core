Run scripts and open an interactive shell with AiiDA
====================================================

How to run a script
+++++++++++++++++++
In order to run a script that interacts with the database, you need
to select the proper settings for the database, otherwise you will
get an ``ImproperlyConfigured`` exception from Django.

To simplify the procedure, we provide an utility command, ``load_django``.
As the first two lines of your script, write::
  
  from aiida.common.utils import load_django
  load_django()

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

Moreover, it will automatically execute the ``load_django`` command, and
automatically import the following modules/classes::
  
  from aiida.orm import (Node, Calculation, Code, Data,
      Computer, Group, DataFactory, CalculationFactory)
  from aiida.djsite.db import models

so that you do not need to perform these useful imports every time you
start the shell.




