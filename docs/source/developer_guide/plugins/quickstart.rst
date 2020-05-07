==========
Quickstart
==========

You have a code and would like to use it from AiiDA?
You need a special data type, parser, scheduler, ... that is not available?
Then you'll need to write an **AiiDA plugin**.

Let's get started with creating a new plugin packacge ``aiida-mycode``.

 0. At least once, :ref:`install an existing aiida plugin package <plugins>` to make sure this works.

 1. Check on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_
    that your desired plugin name is still available

 #. Use the `AiiDA plugin cutter <https://github.com/aiidateam/aiida-plugin-cutter>`_ to jumpstart your plugin package::

        pip install cookiecutter
        cookiecutter https://github.com/aiidateam/aiida-plugin-cutter.git
        # follow instructions ...
        cd aiida-mycode

 #. Install your new plugin package::

        workon <name_of_your_virtualenv> # if you have one
        pip install -e .
        reentry scan -r aiida

That's it - now you can ``import aiida_mycode`` and start developing your plugin

A few things to keep in mind:
 * Be sure to update the `setup.json`_, in particular the license and version number
 * :ref:`Get your plugin package listed <plugins.get_listed>` as soon as possible to reserve your plugin name and to inform others of your ongoing development

.. _setup.json: https://github.com/aiidateam/aiida-plugin-template/blob/master/setup.json
.. _registry: https://github.com/aiidateam/aiida-registry
