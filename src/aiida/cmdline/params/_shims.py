###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Various horrible hacks around click internals"""

from __future__ import annotations

import functools
import typing as t

C = t.TypeVar('C', bound=t.Callable[..., t.Any])


# Compatibility between click 8.1 and 8.2
# https://github.com/pallets/click/pull/2929
def shim_add_ctx(f: C) -> C:
    """Add a click.Context 'ctx' argument to a decorated function if missing"""

    @functools.wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        if 'ctx' not in kwargs:
            # DH modification
            # kwargs["ctx"] = click.get_current_context(silent=True)
            kwargs['ctx'] = None
        return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
