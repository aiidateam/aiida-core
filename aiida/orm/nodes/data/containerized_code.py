# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin represeting a containter executable code to be wrapped and called through a `CalcJob` plugin."""
import os

from aiida.common import exceptions
from aiida.common.log import override_log_level

from .code import Code
from .data import Data

__all__ = ('ContainerizedCode',)


class ContainerizedCode(Code):
    """
    A container code entity.
    """

    # pylint: disable=too-many-public-methods

    def __init__(
        self, computer=None, engine_command=None, image=None, container_exec_path=None, input_plugin_name=None, **kwargs
    ):
        super().__init__(**kwargs)

        # do some check of parameters

        self.set_container_exec(computer, engine_command, image, container_exec_path)

        if input_plugin_name:
            self.set_input_plugin_name(input_plugin_name)

    def _validate(self):
        pass

    def set_container_exec(self, computer, engine_command, image, container_exec_path):
        """
        Set the code as container
        """
        from aiida import orm
        from aiida.common.lang import type_check

        if not os.path.isabs(container_exec_path):
            raise ValueError('executable path must be an absolute path (on the remote machine)')

        type_check(computer, orm.Computer)
        self.computer = computer

        container_engine_command = engine_command.format(image=image)

        self.set_attribute('container_engine_command', container_engine_command)
        self.set_attribute('image', image)
        self.set_attribute('container_exec_path', container_exec_path)

    def get_container_exec_path(self):
        return self.get_attribute('container_exec_path', None)

    def get_image(self):
        """Get image name"""
        return self.get_attribute('image', '')

    def get_container_engine_command(self):
        return self.get_attribute('container_engine_command', '')
