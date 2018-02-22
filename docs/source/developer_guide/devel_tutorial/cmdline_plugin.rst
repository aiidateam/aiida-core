.. note: ``verdi data`` subcommands are currently the only commands that can be added in plugins.

.. _DeveloperCmdlinePluginTutorial:

Tutorial: Commandline plugin - Data subcommand
==============================================

.. toctree::
   :maxdepth: 2

If your plugin provides :doc:`custom data types <code_plugin_float_sum>`, you might want to provide commandline commands to handle them: Create them from files (example: pseudopotentials), provide export to file formats, visualize them, etc.

With commandline plugins you have the possibility to make you command accessible from the ``verdi`` commandline. Your cli plugin will be treated as a subcommand of ``verdi data``.

Exercise: command to export FloatData to file
---------------------------------------------

Plugin structure::

   aiida-yourplugin/
      aiida_yourplugin/
         __init__.py
         data/
            __init__.py
            float.py
      setup.py
      setup.json

The file ``float.py`` can be taken from :doc:`the datatype tutorial <code_plugin_float_sum>` or replaced by your own custom data type.

File excerpt ``setup.json``::

   {
      ...
      "entry_points": {
         "aiida.data": {
            "yourplugin.float = aiida_yourplugin.data.float:FloatData"
         },
         ...
      }
      ...
   }

We will assume your plugin provides a ``FloatData`` data class. Let's provide a command that exports it to some file format.

First, we create a new subpackage (this is optional but helps structure our plugin), containing an empty module in which we will work. New plugin structure::

   aiida-yourplugin/
      aiida_yourplugin/
         __init__.py
         data/
            __init__.py
            float.py
         cmdline/
            __init__.py
            float_cmd.py  <-- new empty module
      setup.py
      setup.json

Inside that module we will first create an empty command-group (it will do nothing but subcommands can be added to it later). which can be called from the commandline using ``verdi data yourplugin-float``. Command groups are explained in the `Click documentation <click_docs>`_.

File ``float_cmd.py``::
   
   import click  # This we will use in a later step

   from aiida.cmdline.commands import data_cmd
   from aiida.cmdline.dbenv_lazyloading import load_dbenv_if_not_loaded  # Will be used in a later step

   @data_cmd.group('yourplugin-float'):
   def float_cmd():
      """Commandline interface for working with FloatData"""

This so far does nothing and will not yet be recognized by AiiDA. We will now expose it through an entry point for AiiDA to find.
Changes to file ``setup.json``::

   {
      ...
      "entry_points": {
         "aiida.data": {
            "yourplugin.float = aiida_yourplugin.data.float:FloatData"
         },
         "aiida.cmdline.data": {                                              <-- NEW
            "yourplugin-float = aiida_yourplugin.cmdline.float_cmd:float_cmd" <-- NEW
         }                                                                    <-- NEW
         ...
      }
      ...
   }

Now we only have to reinstall our plugin (``pip install -e <path/to/aiida-yourplugin>``) and the command should be recognized. We can test it by running::

   verdi data yourplugin-float --help

It should print some basic usage information containing the docstring we gave to the ``float_cmd()`` function.

The last step is now implementing ``verdi data yourplugin-float export`` command that exports our FloatData instance to a file.

Append to file ``float_cmd.py``::

   @float_cmd.command()
   @click.option('--outfile', '-o', type=click.Path(dir_okay=False), help='write output to this file (by default print to stout).'
   @click.argument('pk', type=int)
   def export(outfile, pk):
      """Export a FloatData node, identified by PK to plain text format"""
      load_dbenv_if_not_loaded()  # Important to load the dbenv in the last moment
      from aiida.orm import load_node
      float_node = load_node(pk)  # Exercise left to the user: check if it is a FloatData
      file_content = str(float_node.value)
      if outfile:
         with open(outfile, 'w') as out_file_obj:
            out_file_obj.write(file_content)
      else:
         click.echo(file_content)

A subcommand to a group can be defined using the following pattern::

   @float_cmd.command()
   def export(...):
      ...

Where the subcommand will now automatically have the name of the function. If you want it to have a different name, simply pass it as an argument to the ``<group>.command('<subcmd name>')`` decorator.

::
   
   def export(...):
      """..."""
      load_dbenv_if_not_loaded()  # Important to load the dbenv in the last moment

As is mentioned in the comment, it is important to load the dbenv as late as possible. Particularly it should never be done at import time (on module level) but only inside whichever function requires it. This ensures that command completion does not get slowed down while importing your command.

Last but by no means least, it is important to test our plugin command, this example will use the builtin unittest framework but it is just as well possible to use pytest.

New structure::

   aiida-yourplugin/
      aiida_yourplugin/
         __init__.py
         data/
            __init__.py
            float.py
         cmdline/
            __init__.py
            float_cmd.py
            test_float_cmd.py <-- new empty module
      setup.py
      setup.json

Example test in ``test_float_cmd.py``::

   import os

   from click.testing import CliRunner
   from aiida.utils.fixtures import PluginTestCase

   from aiida_yourplugin.cmdline.float_cmd import float_cmd

   TestFloadCmd(PluginTestCase):
      """Test correctness of the verdi data yourplugin-float export command"""

        BACKEND = os.environ.get('TEST_BACKEND')
        # load the backend to be tested from the environment variable
        # on bash, simply prepend the test command with TEST_BACKEND='django' or TEST_BACKEND='sqlalchemy'
        # or set the TEST_BACKEND in your CI configuration

      def setUp(self):
         from aiida.orm import DataFactory
         self.float_node = DataFactory('yourplugin.float')()
         self.float_node.value = 1.2
         self.runner = CliRunner()

      def test_export(self):
         self.float_node.store()
         result = self.runner.invoke(float_cmd, ['export', str(self.float_node.pk)])
         self.assertEqual(result.output, str(self.float_node.value))

This test can now be run using ``TEST_BACKEND=django python -m unittest discover`` from your top level project directory ``aiida-yourplugin``.

As a further exercise, try adding a ``--format`` option to choose between plain text and, say json.

Understanding commandline plugins
---------------------------------

The discovery of plugins via entry points follows exactly the same mechanisms as all other plugin types.

The possibility of plugging cli commands into each other is a feature of ``click`` a python library that greatly simplifies the task. You can find in-depth documentation here: `Click 6.0 docs <click_docs>`_.

.. _click_docs: http://click.pocoo.org/6/
