# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functions to delete nodes from the database, preserving provenance integrity."""
from typing import Callable, Iterable, Optional, Set, Tuple, Union
import warnings


def delete_nodes(
    pks: Iterable[int],
    verbosity: Optional[int] = None,
    dry_run: Union[bool, Callable[[Set[int]], bool]] = True,
    force: Optional[bool] = None,
    **traversal_rules: bool
) -> Tuple[Set[int], bool]:
    """Delete nodes given a list of "starting" PKs.

    .. deprecated:: 1.6.0
        This function has been moved and will be removed in `v2.0.0`.
        It should now be imported using `from aiida.tools import delete_nodes`

    """
    from aiida.common.warnings import AiidaDeprecationWarning
    from aiida.tools import delete_nodes as _delete

    warnings.warn(
        'This function has been moved and will be removed in `v2.0.0`.'
        'It should now be imported using `from aiida.tools import delete_nodes`', AiidaDeprecationWarning
    )  # pylint: disable=no-member

    return _delete(pks, verbosity, dry_run, force, **traversal_rules)
