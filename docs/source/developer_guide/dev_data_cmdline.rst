Developer data command line plugins-test
########################################

AiiDA can be extended by adding custom types of Data nodes and means of manipulating them. One of the means of use and integration of AiiDA with the variety of free and open-source software is the command line. In this section we will discuss about the ways to extend  AiiDA command line interface.


Framework for ``verdi data``
++++++++++++++++++++++++++++

Code for each of the ``verdi data <datatype> <action> [--format <plugin>]``
commands is placed in ``_<Datatype>`` class inside
``aiida.cmdline.commands.data.py``. Standard actions, such as

* ``list``
* ``show``
* ``import``
* ``export``

are implemented in corresponding classes:

* :py:class:`~aiida.cmdline.commands.data.Listable`
* :py:class:`~aiida.cmdline.commands.data.Visualizable`
* :py:class:`~aiida.cmdline.commands.data.Importable`
* :py:class:`~aiida.cmdline.commands.data.Exportable`,

which are inherited by ``_<Datatype>`` classes (multiple inheritance is
possible). Actions ``show``, ``import`` and ``export`` can be extended with
new format plugins simply by adding additional methods in ``_<Datatype>``
(these are automatically detected). Action ``list`` can be extended by
overriding default methods of the
:py:class:`~aiida.cmdline.commands.data.Listable`.

To make a class/function loaded automatically while issuing ``verdi shell``,
one has to register it in ``default_modules_list`` in
``aiida.djsite.db.management.commands.customshell.py``.


Adding plugins for ``show``, ``import``, ``export`` and like
------------------------------------------------------------

A plugin to show, import or export the data node can be added by inserting
a method to ``_<Datatype>`` class. Each new method is automatically detected,
provided it starts with ``_<action>_`` (that means ``_show_`` for ``show``,
``_import_`` for ``import`` and ``_export_`` for ``export``). Node for each
of such method is passed using a parameter.

.. note:: plugins for ``show`` are passed a list of nodes, while plugins for
    ``import`` and ``export`` are passed a single node.

As the ``--format`` option is optional, the default plugin can be specified
by setting the value for ``_default_<action>_plugin`` in the inheriting class,
for example::

    class _Parameter(VerdiCommandWithSubcommands, Visualizable):
        """
        View and manipulate Parameter data classes.
        """

        def __init__(self):
            """
            A dictionary with valid commands and functions to be called.
            """
            from aiida.orm.data.parameter import ParameterData
            self.dataclass = ParameterData
            self._default_show_format = 'json_date'
            self.valid_subcommands = {
                'show': (self.show, self.complete_visualizers),
                }

        def _show_json_date(self, exec_name, node_list):
            """
            Show contents of ParameterData nodes.
            """

If the default plugin is not defined and there are more than one plugin,
an exception will be raised upon issuing ``verdi data <datatype> <action>``
to be caught and explained for the user.

Plugin-specific command line options
====================================

Plugin-specific command line options can be appended in plugin-specific
methods ``_<action>_<plugin>_parameters(self,parser)``. All these methods
are called before parsing command line arguments, and are passed an
``argparse.ArgumentParser`` instance, to which command line argument
descriptions can be appended using ``parser.add_argument()``. For example::

    def _show_jmol_parameters(self, parser):
        """
        Describe command line parameters.
        """
        parser.add_argument('--step',
                            help="ID of the trajectory step. If none is "
                                 "supplied, all steps are exported.",
                            type=int, action='store')

.. note:: as all ``_<action>_<plugin>_parameters(self,parser)`` methods are
    called, it requires some attention in order not to make conflicting
    command line argument names!
.. note:: it's a good practice to set ``default=None`` for all command line
    arguments, since ``None``-valued arguments are excluded before passing
    the parsed argument dictionary to a desired plugin.

Implementing ``list``
---------------------

As listing of data nodes can be extended with filters, controllable using
command line parameters, the code of
:py:class:`~aiida.cmdline.commands.data.Listable` is split into a few
separate methods, that can be individually overridden:

* :py:class:`~aiida.cmdline.commands.data.Listable.list`:
    the main method, parsing the command line arguments and printing the
    data node information to the standard output;
* :py:class:`~aiida.cmdline.commands.data.Listable.query`:
    takes the parsed command line arguments and performs a query on the
    database, returns table of unformatted strings, representing the hits;
* :py:class:`~aiida.cmdline.commands.data.Listable.append_list_cmdline_arguments`:
    informs the command line argument parser about additional, user-defined
    parameters, used to control the
    :py:class:`~aiida.cmdline.commands.data.Listable.query` function;
* :py:class:`~aiida.cmdline.commands.data.Listable.get_column_names`:
    returns the names of columns to be printed by
    :py:class:`~aiida.cmdline.commands.data.Listable.list` method.


Adding a ``verdi`` command
++++++++++++++++++++++++++

Here we will add a new verdi command for the FloatData datatype we created and used in ``Developer code plugin tutorial`` and ``Developer workflow tutorial`` exercises.  

The new command will be::

    >> verdi data float show <pk>

To create the above verdi command, we will write ``_Float`` class inherited from ``VerdiCommandWithSubcommands`` and ``Visualizable`` classes in ``aiida.cmdline.commands.data.py`` file as shown below. The ``Visualizable`` is added in base class list to inherit its ``show()`` method.

.. code-block:: python

	class _Float(VerdiCommandWithSubcommands, Visualizable):
	    """
	    View and manipulate Float data classes.
	    """

	    def __init__(self):
		"""
		A dictionary with valid commands and functions to be called.
		"""
		from aiida.orm.data.float import FloatData

		self.dataclass = FloatData
		self.valid_subcommands = {
		    'show': (self.show, self.complete_none),
		}
		self._default_show_format = 'json_date'


The features used in ``init`` method are:

``self.dataclass`` = It is the data type for which the command is written. In this example it is ``FloatData``.

``self.valid_subcommands`` = It is the dictionary of valid keys and the functions to be called. Each key will be the command for the defined data type. For ``FloatData`` we added ``show`` as command and ``self.show()`` as method from base cass to be called on. The ``self.show()`` method creates a list of all methods defined with prefix ``_show_`` and not with postfix as ``_parameters`` in current class and provides as subcommands for the show command for given data type.

``self._default_show_format`` = It is the default format to be displayed for the ``show'`` command when no subcommand is passed as an argument. For FloatData, we will show data in ``json`` format by default. To display node in ``json``, we will add the format called ``json_date`` and the method called ``_show_json_date()`` in ``_Float`` class. Please note that the method name should follow the convention of ``_show_ + format_name``.


The ``_show_json_date()`` method will be:

.. code-block:: python

	def _show_json_date(self, exec_name, node_list):
	    """
	    Show contents of FloatData nodes.
	    """
	    from aiida.cmdline import print_dictionary

	    for node in node_list:
	        the_dict = node.get_dict()
	        print_dictionary(the_dict, 'json+date')

In this method we have passed the executable name and the list of nodes. To print FloatData in json format we are using the ``print_dictionary`` routine from AiiDA .

Once the ``_Float`` class is added, make sure to add entry in ``self.routed_subcommands`` dictionary in the ``__init__`` method of the ``Data`` class in ``aiida.cmdline.commands.data.py`` file as shown below.

.. code-block:: python

	class Data(VerdiCommandRouter):
	    """
	    Setup and manage data specific types
	    
	    There is a list of subcommands for managing specific types of data.
	    For instance, 'data upf' manages pseudopotentials in the UPF format.
	    """

	    def __init__(self):
		"""
		A dictionary with valid commands and functions to be called.
		"""
		## Add here the classes to be supported.
		self.routed_subcommands = {
		    .
		    .
		    # other entries

		    'float': _Float,
		}



The new verdi command ``float``, is now ready!

Try experimenting by adding other formats for ``show`` command or by adding other commands like ``list``, ``import`` and ``export`` for FloatData data type.












