Sphinx cheatsheet
+++++++++++++++++

A brief overview of some of the main functions of Sphinx
as used in the aiida documentation. View :ref:`this-page` to see
how this page was formatted. This is only a brief outline for more
please see `the Sphinx documentation <http://sphinx-doc.org/contents.html>`_


Main Titles and Subtitles
-------------------------

This is an example of a main title.

subtitles are made like this
============================

This is an example of a subtitle.

Formatting
----------

Basic Paragraph Formatting
==========================

Words can be written in *italics* or in **bold**. Text describing a specific
``computer_thing`` can be formatted as well.


Paragraph and Indentation
=========================

Much like in regular python, the indentation plays a strong role in the formatting.

For example all of this sentence will
appear on the same line.

While this sentence will appear
 differently because there is an indent.

Terminal and Code Formatting
============================

Something to be run in command line can be formatted like this::

 >> Some command

As can be seen above, while snippets of python on code can be done like this::

 import module
 print('hello world')

Notes
=====
.. note:: Notes can be added like this.

Bullet Points and Lists
=======================

* Bullet points can be added
* Just like this
  * With sub-bullets like this

#. While numerical bullets
#. Can be added
#. Like this


Links, Code Display, Cross References
-------------------------------------
External Links
==============
Can be done like here for `AiiDA <www.aiida.net/>`_

Code Download
=============

Code can be downloaded like this.

Download: :download:`this example script <devel_tutorial/sum_executable.py>`

Code Display
============

Can be done like this. This entire document can be seen unformated below using this method.

.. literalinclude:: devel_tutorial/sum_executable.py

.. _self-reference:

Math
====

Math formulas can be added as follows :math:`<g_i|`, see
`the Sphinx documentation on math <http://sphinx-doc.org/latest/ext/math.html#module-sphinx.ext.mathbase>`_


Cross Reference Docs
====================

Here is an example of a reference to the :ref:`structure_tutorial` which is on *another page*

Here is an example of a reference to something on the same page, :ref:`self-reference`

.. note:: References within the same document need a reference label, see `.. _self-reference:`
          used in this section for an example. *Hidden in formatted page, can only be seen in the
          input text.*

Cross Reference Classes and Methods
===================================

Any class can be referenced for example :py:class:`~aiida.orm.data.structure.StructureData` references the
StructureData data class.

Similarily any method can be referenced for example :py:meth:`~aiida.orm.data.structure.StructureData.append_atom`
shows the StructureData class' append atom method.


Table of Contents Docs and Code
-------------------------------

Table of Contents for Docs
==========================
An example of the table of contents syntax for the :ref:`git-cheatsheet` can be seen here
note that these are especially important in the global structure of the
document, as found in index.rst files.

.. toctree::
   :maxdepth: 2

   git_cheatsheet

.. note:: The `maxdepth` parameter can be used to change how deep the title indexing goes. See :ref:`this-page`.


Table of Contents for Code
==========================

Table of contents, that cross reference code, can be done very similarly to how
it is done for documents. For example the parser docs can be indexed like this

.. toctree::
   :maxdepth: 1

   aiida.orm <../orm/dev>
   ../parsers/dev


Automodules Example
====================

.. toctree::
   :maxdepth: 2

.. automodule:: aiida.common.datastructures
   :members:
   :noindex:

.. note:: A `:noindex:` directive was added to avoid duplicate object
          description for this example. Do not put the keyword in a real
          documentation.

How To Format Docstrings
------------------------

Much of the work will be done automatically by Sphinx, just format the docstrings with the same syntax used here,
a few extra examples of use would include::

    :param parameters: some notes on input parameters

    :return returned: some note on what is returned

    :raise Errors: Notes on warnings raised



Changing The Docs
-----------------

If you are creating a new .rst file, make sure to add it in
the relevant index.rst tree. This can be done by:

* Modifying relevant doc strings or .rst files (be sure to modify them in the /doc/source/ folder and not /doc/build)

* Making sure that all relevant .rst files are added
  to the relevant index.rst file

* Running `make html` in /aiida/docs/ folder

* Be sure to check for any warnings and correct if possible

.. _this-page:

This Page
=========

.. literalinclude:: sphinx_cheatsheet.rst
