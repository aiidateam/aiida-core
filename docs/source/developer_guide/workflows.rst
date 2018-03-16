##########################
Workflow's Guide For AiiDA
##########################

.. todo: Write a more detailed guide.

Creating new workflows
++++++++++++++++++++++

New user specific workflows should be importable by python.
The simplest thing is to put them in ``aiida/workflows/user``. 
A better option, if the workflow is general enough to be of interest for the community, is to
create a new AiiDA plugin containing the workflow and install it
(you can check :ref:`the documentation on how to make new plugin repositories<plugin_development>`).

In the first case, put ``__init__.py`` files in all subdirectories of ``aiida/workflows/user`` to be able to import any workflows.

You can also customize your verdi shell by adding this function to the modules
to be loaded automatically -- see :doc:`here<../verdi/properties>` for more information.
