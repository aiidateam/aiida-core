Sphinx cheatsheet
#################

A collection of some Sphinx features used in the aiida documentation.

Terminal and Code Formatting
============================

Something to be run in command line can be formatted like this::

  Some command


Code formatting, but now with python syntax highlighting::

   import module
   print('hello world')

Notes
=====
.. note:: Notes can be added like this.


Links, Code Display, Cross References
-------------------------------------

Code Download
=============

Code can be downloaded like this.

Download: :download:`this example script <../devel_tutorial/sum_executable.py>`

Code Display
============

Can be done like this. This entire document can be seen unformatted below using this method.

.. literalinclude:: ../devel_tutorial/sum_executable.py

.. _self-reference:

Math
====

Math formulas can be added as follows :math:`<g_i|`, see
`the Sphinx documentation on math <http://sphinx-doc.org/latest/ext/math.html#module-sphinx.ext.mathbase>`_


Cross Reference Docs
====================

Here is an example of a reference to the :ref:`structure_tutorial` which is on *another page*

Here is an example of a :ref:`self-reference` to something on the same page

.. note:: References within the same document need a reference label, see `.. _self-reference:`
          used in this section for an example.

Cross Reference Classes and Methods
===================================

Reference to the :py:class:`aiida.orm.nodes.data.structure.StructureData` class, showing the full path.

Reference to the :py:class:`~aiida.orm.nodes.data.structure.StructureData` class (with preceding tilde), showing only the class name.

.. note:: Always point to the actual definition of a class, e.g. ``aiida.backends.querybuild.querybuilder_base.AbstractQueryBuilder``, **not** an alias like ``aiida.orm.QueryBuilder`` (or sphinx will complain).

Reference to the :py:meth:`~aiida.orm.nodes.data.structure.StructureData.append_atom`
method.

.. note:: In the docstring of a class, you can 
  `refer to a method of the same class <http://www.sphinx-doc.org/en/stable/domains.html>`_ 
  using ``py:meth:`.name_of_method```.


Table of Contents for Code
==========================

Table of contents, that cross reference code, can be done very similarly to how
it is done for documents. For example the parser docs can be indexed like this

.. toctree::
   :maxdepth: 1

   aiida.orm <../../apidoc/aiida.orm>


Automodules Example
====================

.. toctree::
   :maxdepth: 2

.. automodule:: aiida.common.warnings
   :members:
   :noindex:

.. note:: A `:noindex:` directive was added to avoid duplicate object
          description for this example.

How To Format Docstrings
------------------------

Much of the work will be done automatically by Sphinx, just format the docstrings with the same syntax used here,
a few extra examples of use would include::

    :param parameter: some notes on input parameter
    :type parameter: str

    :return returned: some note on what is returned
    :rtype: str

    :raise Errors: Notes on warnings raised


.. _this-page:

This Page
=========

.. literalinclude:: sphinx_cheatsheet.rst
