# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click
from click_plugins import with_plugins

from aiida.common.pluginloader import entry_point_list


@click.group()
@click.option('--profile', '-p')
def verdi(profile):
    pass


@verdi.group()
def work():
    pass


@verdi.group()
def user():
    pass


@verdi.group()
def data():
    pass


@data.group('plug')
def data_plug():
    pass
