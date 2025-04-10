###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""Defines common type aliases for consistent path handling"""

from pathlib import Path, PurePath, PurePosixPath
from typing import Union

PathType = Union[str, Path, PurePath, PurePosixPath]