##########################
Workflow's Guide For AiiDA
##########################

.. todo: Write a more detailed guide.

Creating new workflows
++++++++++++++++++++++

New user specific workflows should be put in ``aiida/workflows/user``. If the
workflow is general enough to be of interest for the community, the best is to
create a git repository (e.g. on `GitHub <https://github.com>`_) and clone
the content of the repository in a subfolder of ``aiida/workflows/user``, e.g.
in ``aiida/workflows/user/epfl_theos`` for workflows from the group THEOS at EPFL.

Put ``__init__.py`` files in all subdirectories of ``aiida/workflows/user``
to be able to import any workflows. Also, it may be a good
idea to create a specific workflow factory to load easily workflows of the subdirectory.
To do so place in your ``__init__.py`` file in the main workflow directory 
(e.g. in ``aiida/workflows/user/epfl_theos/__init__.py`` in the example above):

.. code-block:: python

	from aiida.orm.workflow import Workflow
	
	def TheosWorkflowFactory(module):
	    """
	    Return a suitable Workflow subclass for the workflows defined here.
	    """
	    from aiida.common.pluginloader import BaseFactory
	
	    return BaseFactory(module, Workflow, "aiida.workflows.user.epfl_theos")
	
In this example, a workflow located in e.g. ``aiida/workflows/user/epfl_theos/quantumespresso/pw.py``
can be loaded simply by typing::
	
	TheosWorkflowFactory('quantumespresso.pw')
	
.. note:: The class name of the workflow should be compliant with the ``BaseFactory``
	syntax. In the above example, it should be called ``PwWorkflow`` otherwise
	the workflow factory won't work.

You can also customize your verdi shell by adding this function to the modules
to be loaded automatically -- see :doc:`here<../verdi/properties>` for more information.
