# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cell-var-from-loop
"""Convenience classes to help building the input dictionaries for Processes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from collections import Mapping

from aiida.engine.processes.ports import PortNamespace

__all__ = ('ProcessBuilder', 'CalcJobBuilder', 'ProcessBuilderNamespace')


class ProcessBuilderNamespace(Mapping):
    """
    Input namespace for the ProcessBuilder. Dynamically generates the getters and setters
    for the input ports of a given PortNamespace
    """

    def __init__(self, port_namespace):
        """
        Dynamically construct the get and set properties for the ports of the given port namespace

        For each port in the given port namespace a get and set property will be constructed dynamically
        and added to the ProcessBuilderNamespace. The docstring for these properties will be defined
        by calling str() on the Port, which should return the description of the Port.

        :param port_namespace: the inputs PortNamespace for which to construct the builder
        """
        # pylint: disable=super-init-not-called
        self._port_namespace = port_namespace
        self._valid_fields = []
        self._data = {}

        for name, port in port_namespace.items():

            self._valid_fields.append(name)

            if isinstance(port, PortNamespace):
                self._data[name] = ProcessBuilderNamespace(port)

                def fgetter(self, name=name):
                    return self._data.get(name)
            elif port.has_default():

                def fgetter(self, name=name, default=port.default):
                    return self._data.get(name, default)
            else:

                def fgetter(self, name=name):
                    return self._data.get(name, None)

            def fsetter(self, value):
                self._data[name] = value

            fgetter.__doc__ = str(port)
            getter = property(fgetter)
            getter.setter(fsetter)
            setattr(self.__class__, name, getter)

    def __setattr__(self, attr, value):
        """
        Any attributes without a leading underscore being set correspond to inputs and should hence
        be validated with respect to the corresponding input port from the process spec
        """
        if attr.startswith('_'):
            object.__setattr__(self, attr, value)
        else:
            try:
                port = self._port_namespace[attr]
            except KeyError:
                raise AttributeError('Unknown builder parameter: {}'.format(attr))

            value = port.serialize(value)
            validation_error = port.validate(value)
            if validation_error:
                raise ValueError('invalid attribute value {}'.format(validation_error.message))

            self._data[attr] = value

    def __repr__(self):
        return self._data.__repr__()

    def __dir__(self):
        return sorted(set(self._valid_fields + [key for key, _ in self.__dict__.items() if key.startswith('_')]))

    def __iter__(self):
        for key in self._data:
            yield key

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        return self._data[item]


class ProcessBuilder(ProcessBuilderNamespace):
    """A process builder that helps setting up the inputs for creating a new process."""

    def __init__(self, process_class):
        self._process_class = process_class
        self._process_spec = self._process_class.spec()
        super(ProcessBuilder, self).__init__(port_namespace=self._process_spec.inputs)

    @property
    def process_class(self):
        return self._process_class


class CalcJobBuilder(ProcessBuilder):
    """A process builder specific to CalcJob implementations that provides also the `submit_test` functionality."""

    def __dir__(self):
        return super(CalcJobBuilder, self).__dir__() + ['submit_test']

    def submit_test(self, folder=None, subfolder_name=None):
        """
        Run a test submission by creating the files that would be generated for the real calculation in a local folder,
        without actually storing the calculation nor the input nodes. This functionality therefore also does not
        require any of the inputs nodes to be stored yet.

        :param folder: a Folder object, within which to create the calculation files. By default a folder
            will be created in the current working directory
        :param subfolder_name: the name of the subfolder to use within the directory of the ``folder`` object. By
            default a unique string will be generated based on the current datetime with the format ``yymmdd-``
            followed by an auto incrementing index
        """
        import os
        import errno
        from tempfile import NamedTemporaryFile

        from aiida.common import timezone
        from aiida.transports.plugins.local import LocalTransport
        from aiida.orm import Computer
        from aiida.common.folders import Folder
        from aiida.common.exceptions import NotExistent
        from aiida.orm import load_node, Code

        inputs = {'metadata': {'store_provenance': False}}
        inputs.update(**self)
        process = self.process_class(inputs=inputs)

        if folder is None:
            folder = Folder(os.path.abspath('submit_test'))

        # In case it is not created yet
        folder.create()

        if subfolder_name is None:
            subfolder_basename = timezone.localtime(timezone.now()).strftime(
                '%Y%m%d')
        else:
            subfolder_basename = subfolder_name

        ## Find a new subfolder.
        ## I do not user tempfile.mkdtemp, because it puts random characters
        # at the end of the directory name, therefore making difficult to
        # understand the order in which directories where stored
        counter = 0
        while True:
            counter += 1
            subfolder_path = os.path.join(folder.abspath,
                                          "{}-{:05d}".format(subfolder_basename,
                                                             counter))
            # This check just tried to avoid to try to create the folder
            # (hoping that a test of existence is faster than a
            # test and failure in directory creation)
            # But it could be removed
            if os.path.exists(subfolder_path):
                continue

            try:
                # Directory found, and created
                os.mkdir(subfolder_path)
                break
            except OSError as e:
                if e.errno == errno.EEXIST:
                    # The directory has been created in the meantime,
                    # retry with a new one...
                    continue
                # Some other error: raise, so we avoid infinite loops
                # e.g. if we are in a folder in which we do not have write
                # permissions
                raise

        subfolder = folder.get_subfolder(
            os.path.relpath(subfolder_path, folder.abspath),
            reset_limit=True)

        # I use the local transport where possible, to be as similar
        # as possible to a real submission
        transport = LocalTransport()
        with transport:
            transport.chdir(subfolder.abspath)

            calc_info, script_filename = process.presubmit(subfolder)

            # code = process.node.get_code()
            codes_info = calc_info.codes_info
            input_codes = [load_node(_.code_uuid, sub_classes=(Code,)) for _ in codes_info]

            for code in input_codes:
                if code.is_local():
                    # Note: this will possibly overwrite files
                    for f in code.get_folder_list():
                        transport.put(code.get_abs_path(f), f)
                    transport.chmod(code.get_local_executable(), 0o755)  # rwxr-xr-x

            local_copy_list = calc_info.local_copy_list
            remote_copy_list = calc_info.remote_copy_list
            remote_symlink_list = calc_info.remote_symlink_list

            if local_copy_list is not None:
                for uuid, filename, target in local_copy_list:

                    try:
                        data_node = load_node(uuid=uuid)
                    except exceptions.NotExistent:
                        logger.warning('failed to load Node<{}> specified in the `local_copy_list`'.format(uuid))

                    with NamedTemporaryFile(mode='w+') as handle:
                        handle.write(data_node.get_object_content(filename))
                        handle.flush()
                        transport.put(handle.name, target)

            if remote_copy_list:
                with open(os.path.join(subfolder.abspath,
                                       '_aiida_remote_copy_list.txt'),
                          'w') as f:
                    for (remote_computer_uuid, remote_abs_path,
                         dest_rel_path) in remote_copy_list:
                        try:
                            remote_computer = Computer(
                                uuid=remote_computer_uuid)
                        except NotExistent:
                            remote_computer = "[unknown]"
                        f.write("* I WOULD REMOTELY COPY "
                                "FILES/DIRS FROM COMPUTER {} (UUID {}) "
                                "FROM {} TO {}\n".format(remote_computer.name,
                                                         remote_computer_uuid,
                                                         remote_abs_path,
                                                         dest_rel_path))

            if remote_symlink_list:
                with open(os.path.join(subfolder.abspath,
                                       '_aiida_remote_symlink_list.txt'),
                          'w') as f:
                    for (remote_computer_uuid, remote_abs_path,
                         dest_rel_path) in remote_symlink_list:
                        try:
                            remote_computer = Computer(
                                uuid=remote_computer_uuid)
                        except NotExistent:
                            remote_computer = "[unknown]"
                        f.write("* I WOULD PUT SYMBOLIC LINKS FOR "
                                "FILES/DIRS FROM COMPUTER {} (UUID {}) "
                                "FROM {} TO {}\n".format(remote_computer.name,
                                                         remote_computer_uuid,
                                                         remote_abs_path,
                                                         dest_rel_path))
        return subfolder, script_filename
