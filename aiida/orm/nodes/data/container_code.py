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

from .data import Data
from .code import Code

__all__ = ('ContainerCode',)


class ContainerCode(Code):
    """
    A container code entity.
    """

    # pylint: disable=too-many-public-methods

    def __init__(self, 
                computer=None, 
                cmdline_tmpl=None,
                image=None,
                container_exec_path=None,
                input_plugin_name=None, **kwargs):
        super().__init__(**kwargs)

        # do some check of parameters
        
        self.set_container_exec(computer, cmdline_tmpl, image, container_exec_path)

        if input_plugin_name:
            self.set_input_plugin_name(input_plugin_name)


    def _validate(self):
        pass

    def set_container_exec(self, computer, cmdline_tmpl, image, container_exec_path):
        """
        Set the code as container
        """
        from aiida import orm
        from aiida.common.lang import type_check

        if not os.path.isabs(container_exec_path):
            raise ValueError('executable path must be an absolute path (on the remote machine)')

        type_check(computer, orm.Computer)
        self.computer = computer
        
        container_cmdline_params = cmdline_tmpl.format(image=image)
        
        self.set_attribute('container_cmdline_params', container_cmdline_params)
        self.set_attribute('image', image)
        self.set_attribute('container_exec_path', container_exec_path)

    def get_container_exec_path(self):
        return self.get_attribute('container_exec_path', '')

    def get_remote_computer(self):
        return self.computer
    
    def get_image(self):
        """Get image name"""
        return self.get_attribute('image', '')
    
    def container_cmd_params(self):
        return self.get_attribute('container_cmdline_params', '')

