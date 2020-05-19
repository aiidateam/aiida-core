.. _how-to:codes:

*************************
How to run external codes
*************************


.. _how-to:codes:plugin:

Interfacing external codes
==========================

`#3986`_

In order to work with an external simulation code in AiiDA, you need a calculation input plugin (subclassing the :py:class:`~aiida.engine.CalcJob` class) and an output parser plugin (subclassing the :py:class:`~aiida.parsers.Parser` class):

Before starting to write a plugin, check on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_ whether a plugin for your code is already available.

Design guidelines
------------------

 * | **Start simple.**
   | Make use of existing classes like :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...
   | Write only what is necessary to pass information from and to AiiDA.
 * | **Don't break data provenance.**
   | Store *at least* what is needed for full reproducibility.
 * | **Parse what you want to query for.**
   | Make a list of which information to:

     #. parse into the database for querying (:py:class:`~aiida.orm.nodes.data.dict.Dict`, ...)
     #. store in the file repository for safe-keeping (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...)
     #. leave on the computer where the calculation ran (:py:class:`~aiida.orm.nodes.data.remote.RemoteData`, ...)

 * | **Expose the full functionality.**
   | Standardization is good but don't artificially limit the power of a code you are wrapping - or your users will get frustrated.
   | If the code can do it, there should be *some* way to do it with your plugin.

 * | **Don't rely on AiiDA internals.**
   | AiiDA's :ref:`public python API<python_api_public_list>` includes anything that you can import via ``from aiida.module import thing``.
   | Functionality at deeper nesting levels is not considered part of the public API and may change between minor AiiDA releases, breaking your plugin.


.. _how-to:codes:run:

Running external codes
======================

`#3987`_


.. _how-to:codes:caching:

Using caching to save computational resources
=============================================

`#3988`_


.. _how-to:codes:scheduler:

Adding support for a custom scheduler
=====================================

`#3989`_


.. _how-to:codes:transport:

Adding support for a custom transport
=====================================

`#3990`_


.. _#3986: https://github.com/aiidateam/aiida-core/issues/3986
.. _#3987: https://github.com/aiidateam/aiida-core/issues/3987
.. _#3988: https://github.com/aiidateam/aiida-core/issues/3988
.. _#3989: https://github.com/aiidateam/aiida-core/issues/3989
.. _#3990: https://github.com/aiidateam/aiida-core/issues/3990
