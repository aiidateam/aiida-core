###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""Version scripts of the storage migration chain."""

from importlib import import_module
from pathlib import Path

for _path in Path(__file__).parent.glob('*.py'):
    if _path.name != '__init__.py':
        # Import under the canonical module name so coverage can attribute the executed lines; see tests/conftest.py.
        import_module(f'{__name__}.{_path.stem}')
