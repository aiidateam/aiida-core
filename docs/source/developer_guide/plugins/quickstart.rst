==========
Quickstart
==========

You have a code and would like to use it from AiiDA?
You need a special data type, parser, scheduler, ... that is not available?
Then you'll need to write an **AiiDA plugin**.

Let's get started with creating a new plugin ``aiida-compute``.

 0. At least once, :ref:`install an existing aiida plugin <plugins>` to make sure this works.

 1. Check on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_
    that the plugin name is still available

 #. Download the AiiDA plugin template::

        wget https://github.com/aiidateam/aiida-plugin-template/archive/master.zip
        unzip master.zip
        cd aiida-plugin-template

 #. Replace the name ``aiida-plugin-template`` by ``aiida-compute``::

        mv aiida_plugin_template aiida_compute
        sed -i .bak 's/aiida_plugin_template/aiida_compute/g' README.md setup.json examples/*.py
        sed -i .bak 's/aiida-plugin-template/aiida-compute/g' README.md setup.json
        sed -i .bak 's/template\./compute./g' setup.json
 #. Install your new plugin::

        workon <name_of_your_virtualenv> # if you have one
        pip install -e .
        reentry scan -r aiida

That's it - now you can ``import aiida-compute`` and start developing your plugin
