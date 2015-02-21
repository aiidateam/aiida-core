Developer data command line plugins
###################################

AiiDA can be extended by adding custom types of Data nodes and means of
manipulating them. One of the means of use and integration of AiiDA with
the variety of free and open-source software is the command line. In this
chapter the ways to extend the AiiDA command line interface are described.

To make a class/function loaded automatically while issuing ``verdi shell``,
one has to register it in ``default_modules_list`` in
``aiida.djsite.db.management.commands.customshell.py``.

Adding a ``verdi`` command
++++++++++++++++++++++++++

.. todo:: Describe here


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

* ``Listable``
* ``Visualizable``
* ``Importable``
* ``Exportable``,

which are inherited by ``_<Datatype>`` classes (multiple inheritance is
possible). Actions ``show``, ``import`` and ``export`` can be extended with
new format plugins simply by adding additional methods in ``_<Datatype>``
(these are automatically detected). Action ``list`` can be extended by
overriding default methods of the ``Listable``.

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

    class _Parameter(VerdiCommandWithSubcommands,Visualizable):
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

        def _show_json_date(self,exec_name,node_list):
            """
            Show contents of ParameterData nodes.
            """

If the default plugin is not defined and there are more than one plugin,
an exception will be raised upon issuing ``verdi data <datatype> <action>``
to be caught and explained for the user.

Implementing ``list``
---------------------

As listing of data nodes can be extended with filters, controllable using
command line parameters, the code of ``Listable`` is split into a few
separate methods, that can be individually overridden:

* ``list``:
    the main method, parsing the command line arguments and printing the
    data node information to the standard output;
* ``query``:
    takes the parsed command line arguments and performs a query on the
    database, returns table of unformatted strings, representing the hits;
* ``append_list_cmdline_arguments``
    informs the command line argument parser about additional, user-defined
    parameters, used to control the ``query`` function;
* ``get_column_names``
    returns the names of columns to be printed by ``list`` method.
