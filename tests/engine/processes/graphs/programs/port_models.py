###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Port models declarations shared by the graph behavior suites."""

from pathlib import Path

from aiida.engine.processes.port_model import PortModel


class Settings(PortModel):
    """Explicit namespace with a required field, for missing-input tests."""

    count: int = 2
    nullable: int | None


class Configuration(PortModel):
    """Top-level namespace carrying settings and a label."""

    settings: Settings
    label: str = 'test'


class DefaultedSettings(PortModel):
    """A namespace usable without any inputs, for default coverage."""

    count: int = 2


class UnsupportedPortModel(PortModel):
    """A namespace with an unpersistable field, for declaration rejection."""

    log_path: Path
