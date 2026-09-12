.. _reference:api:public:

Overview of public API
----------------------

The top-level package of the ``aiida-core`` distribution is called ``aiida``.
It contains various sub-packages that we refer to as "second-level packages".

.. admonition:: Rule
    :class: tip title-icon-lightbulb

    **Any resource that can be imported directly from the top level or from a second-level package is part of the public python API** and intended for external use.
    Resources at deeper nesting level are considered internal and are not intended for use outside ``aiida-core``.

    For example:

    .. code-block:: python

        from aiida import load_profile  # OK, top-level import
        from aiida.orm import QueryBuilder  # OK, second-level import
        from aiida.tools.importexport import Archive # NOT PUBLIC API

.. warning::

    The interface and implementation of resources that are *not* considered part of the public API can change between minor AiiDA releases, and can even be moved or fully removed, without a deprecation period whatsoever.
    Be aware that scripts or AiiDA plugins that rely on such resources, can therefore break unexpectedly in between minor AiiDA releases.

Below we provide a list of the resources per second-level package that are exposed in this way.
If a module is mentioned, then all the resources defined in its ``__all__`` are included

``aiida.cmdline``
.................

.. autoattribute:: aiida.cmdline.__all__

Since some ``click`` argument and option decorators clash, these may be imported at a lower level:

.. autoattribute:: aiida.cmdline.params.arguments.__all__

.. autoattribute:: aiida.cmdline.params.options.__all__


``aiida.common``
................

.. autoattribute:: aiida.common.__all__


``aiida.engine``
................

.. autoattribute:: aiida.engine.__all__

``aiida.manage``
................

.. autoattribute:: aiida.manage.__all__

``aiida.orm``
.............

.. autoattribute:: aiida.orm.__all__

``aiida.parsers``
.................

.. autoattribute:: aiida.parsers.__all__


``aiida.plugins``
.................

.. autoattribute:: aiida.plugins.__all__


``aiida.schedulers``
....................

.. autoattribute:: aiida.schedulers.__all__


``aiida.tools``
...............

.. autoattribute:: aiida.tools.__all__


``aiida.transports``
....................

.. autoattribute:: aiida.transports.__all__
