##########################
Workflow's Guide For AiiDA
##########################

.. todo: Write a more detailed guide.

Creating new workflows
++++++++++++++++++++++

New user specific workflows should be importable by python.
The simplest thing is to put them in ``aiida/workflows/user``. 
A better option, if the workflow is general enough to be of 
interest for the community, is to
create a new AiiDA plugin containing the workflow and install it
(you can check :ref:`the documentation on how to make new plugin repositories<plugin_development>`).

In the first case, put ``__init__.py`` files in all subdirectories 
of ``aiida/workflows/user``
to be able to import any workflows. Also, it may be a good
idea to create a specific workflow factory to load easily workflows of the subdirectory.
To do so place in your ``__init__.py`` file in the main workflow directory 
(e.g. in ``aiida/workflows/user/myname/__init__.py`` in the example above):

.. code-block:: python

	from aiida.orm.workflow import Workflow
	
	def MynameWorkflowFactory(module):
	    """
	    Return a suitable Workflow subclass for the workflows defined here.
	    """
	    from aiida.plugins.factory import BaseFactory
	
	    return BaseFactory(module, Workflow, "aiida.workflows.user.myname")
	
In this example, a workflow located in e.g. ``aiida/workflows/user/myname/foldername/plugin.py``
can be loaded simply by typing::
	
	MynameWorkflowFactory('foldername.plugin')
	
.. note:: The class name of the workflow should be compliant with the ``BaseFactory``
	syntax. In the above example, it should be called ``PluginWorkflow`` otherwise
	the workflow factory won't work.

You can also customize your verdi shell by adding this function to the modules
to be loaded automatically -- see :doc:`here<../verdi/properties>` for more information.
