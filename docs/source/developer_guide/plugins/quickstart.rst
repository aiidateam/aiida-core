==========
Quickstart
==========

You have a code and would like to use it from AiiDA?
You need a special data type, parser, scheduler, ... that is not available?
Then you'll need to write an **AiiDA plugin**.

Let's get started with creating a new plugin ``aiida-mycode``.

 0. At least once, :ref:`install an existing aiida plugin <plugins>` to make sure this works.

 1. Check on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_
    that the plugin name is still available

 #. Download the AiiDA plugin template::

        wget https://github.com/aiidateam/aiida-plugin-template/archive/master.zip
        unzip master.zip
        cd aiida-plugin-template

 #. Replace the name ``aiida-plugin-template`` by ``aiida-mycode``::

        mv aiida_plugin_template aiida_mycode
        sed -i .bak 's/aiida_plugin_template/aiida_mycode/g' README.md setup.json examples/*.py
        sed -i .bak 's/aiida-plugin-template/aiida-mycode/g' README.md setup.json
        sed -i .bak 's/template\./mycode./g' setup.json
 #. Install your new plugin::

        workon <name_of_your_virtualenv> # if you have one
        pip install -e .
        reentry scan -r aiida

That's it - now you can ``import aiida-mycode`` and start developing your plugin


A few notes:
 * Be sure to update the `setup.json`_, in particular the license and version number
 * :ref:`Get your plugin listed <plugins.get_listed>` as soon as possible to reserve your plugin name and to inform others of your ongoing development

.. _setup.json: https://github.com/aiidateam/aiida-plugin-template/blob/master/setup.json
.. _registry: https://github.com/aiidateam/aiida-registry
