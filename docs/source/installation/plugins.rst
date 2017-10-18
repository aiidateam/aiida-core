.. _plugins:

==================
Installing plugins
==================

The plugins available for AiiDA are listed on the
`AiiDA homepage <http://www.aiida.net/plugins/>`_

For a plugin ``aiida-plugin-template`` hosted on 
`PyPI <https://pypi.python.org/>`_, simply do::

    pip install aiida-plugin-template
    reentry scan -r aiida   # notify aiida of new entry points

In case there is no PyPI package available, you can install 
the plugin from the python source, e.g.::

    git clone https://github.com/aiidateam/aiida-plugin-template
    pip install aiida-plugin-template
    reentry scan -r aiida

