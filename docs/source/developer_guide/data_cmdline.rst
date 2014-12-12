Developer data command line plugins
###################################

AiiDA can be extended by adding custom types of Data nodes and means of
manipulating them. One of the means of use and integration of AiiDA with
the variety of free and open-source software is the command line. In this
chapter the ways to extend the AiiDA command line interface are described.

Framework for ``verdi data``
++++++++++++++++++++++++++++

Code for each of the ``verdi data <datatype> <action> <plugin>`` commands
is placed in ``_Datatype`` class inside ``aiida.cmdline.commands.data.py``.
Standard actions, such as

* ``list``
* ``show``
* ``export``

are implemented in corresponding classes:

* ``Listable``
* ``Visualisable``
* ``Exportable``,

which are inherited by ``_Datatype`` classes (multiple inheritance is
possible). Actions ``show`` and ``export`` can be extended simply by adding
additional methods in ``_Datatype`` (these automatically detected). Action
``list`` can be extended by overriding default methods of the ``Listable``.

Adding plugins for ``show``, ``export`` and like
------------------------------------------------

A plugin to show or export the data node can be added by inserting a method
to ``_Datatype`` class. Each new method is automatically detected,
provided it starts with ``_plugin_`` (for ``show``) and ``_export_`` (for
``export``). Node for each of such method is passed using a parameter.

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
