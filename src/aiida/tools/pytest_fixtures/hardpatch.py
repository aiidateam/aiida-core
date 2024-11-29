"""Fixtures that allows you to "hardpatch" the source code.

These are useful, only if an external party is instantiating from source.
Otherwise, pytest-monkeypatching is the way to go.

When should I use these fixtures?
when patching the source code is your goal.
For instance, you might wish to patch a particular function that
should be reflected in the behavior of the daemon when submitting a job to it.
Because the daemon is instantiated as a distinct process and not routed from your process interpreter,
pytest-monkeypatching in your tests will not function in these situations.


This is where these fixtures come in handy. They allow you to inject directly to the source code.
Everything is reverted back to normal after the test is done.

Note: There might be other approaches that are more efficient:
- One could use importlib to set hooks in sys.meta_path.
- Or perhaps modifying sitecustomize.py in PYTHONPATH

I have not tested these approaches, but they might be worth exploring.

In the meantime, this is a simple solution that works.
And should remain backward compatible as the interface is designed to be simple.

"""

from __future__ import annotations

import atexit
import importlib
import inspect
import os
import typing as t

import pytest

from aiida.engine.daemon.client import DaemonNotRunningException

if t.TYPE_CHECKING:
    pass


@pytest.fixture(scope='function')
def inject_patch(started_daemon_client):
    """Fixture to inject a patch to the source code.

    It can be used this way:


    def test_my_code(inject_patch):

        def mock_open(self):
            raise Exception('Mock open exception')

        inject_patch.patch('aiida.transports.plugins.local.LocalTransport.open', mock_open)

        # Your test code here

        # to restore the original source code and remove the patch, (only if you need!)
        # inject_patch.restore()

        # More tests here
    """

    inj = InjectTool(started_daemon_client)
    yield inj
    inj.restore()


class InjectTool:
    def __init__(self, daemon_client):
        """This class is used to inject a patch to the source code."""

        self._BACKUP_NAME = '__backup__'
        self.patched_files = []
        self.daemon_client = daemon_client
        atexit.register(self.restore, notfound_ok=True)

    def patch(self, original_func: str, mock_func, restart_daemon=True):
        """This function patches a function with a mock function

        :param original_func: (str) the original function to be patched
        :param mock_func: (function) the mock function
        :param restart_daemon: (bool) if True, the daemon will be restarted after the patch is applied
            default is True
        """

        # Import original function
        module_name, function_name = original_func.rsplit('.', 1)
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            source_file = inspect.getfile(func)
        except ModuleNotFoundError as e:
            # if the module is not found, it could be a class, try to import it's parent module
            module_name, parent_module = module_name.rsplit('.', 1)
            module = importlib.import_module(module_name)
            # verify if the class is found
            if not hasattr(module, parent_module):
                raise e
            source_file = inspect.getfile(module)

        # Prepare the mock function
        mock_def = inspect.getsource(mock_func)
        def_style = 'async def' if 'async def' in mock_def else 'def'
        mock_def = mock_def.replace(f'{def_style} {mock_func.__name__}', f'{def_style} {function_name}')
        mock_indent = len(mock_def.split(f'{def_style}')[0])
        mock_def = mock_def.replace('\n' + ' ' * mock_indent, '\n')[mock_indent:]

        with open(source_file, 'r') as f:
            source_code = f.read()

            # Make a backup of the original source code
            backup_file = source_file + self._BACKUP_NAME
            if not os.path.exists(backup_file):
                with open(backup_file, 'w') as f_backup:
                    f_backup.write(source_code)

            f.seek(0)

            new_source_code = ''
            inserted = False
            def_completed = False
            while True:
                line = f.readline()
                if not line:
                    break

                if f'{def_style} {function_name}' in line:
                    indent_on_def = len(line.split(f'{def_style}')[0])
                    insert_string = ' ' * indent_on_def + mock_def.replace('\n', '\n' + ' ' * indent_on_def) + '\n'
                    new_source_code += insert_string
                    inserted = True
                    if line.strip().endswith(':'):
                        def_completed = True
                    continue

                elif inserted:
                    if not def_completed:
                        if line.strip().endswith(':'):
                            def_completed = True
                        continue

                    indent_ = len(line) - len(line.lstrip())
                    if indent_ > indent_on_def or line == '\n':
                        continue
                    else:
                        new_source_code += line + f.read()
                        break

                new_source_code += line

            if not inserted:
                raise ValueError(f'Function {function_name} not found in {source_file}')

        with open(source_file, 'w') as f:
            f.write(new_source_code)
            self.patched_files.append(source_file)

        if restart_daemon:
            self.daemon_client.restart_daemon()

    def restore(self, notfound_ok=False, restart_daemon=True):
        """This function unpatches the source code

        :param notfound_ok: (bool) if True, it will not raise an error if the backup file is not found.
            default is False
        :param restart_daemon: (bool) if True, the daemon will be restarted after the patch is removed
            default is True
        """

        for source_file in self.patched_files:
            backup_file = source_file + self._BACKUP_NAME

            try:
                with open(backup_file, 'r') as f:
                    source_code = f.read()
            except FileNotFoundError as e:
                if notfound_ok:
                    continue
                else:
                    raise e

            with open(source_file, 'w') as f:
                f.write(source_code)

            os.remove(backup_file)

        self.patched_files = []

        if restart_daemon:
            try:
                self.daemon_client.restart_daemon()
            except DaemonNotRunningException:
                pass
