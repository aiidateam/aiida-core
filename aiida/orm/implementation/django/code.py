# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from django.db import transaction

from aiida.common.exceptions import InvalidOperation
from aiida.common.utils import type_check


def delete_code(code):
    """
    Delete a code from the DB.

    Check before that there are no output nodes.

    NOTE! Not thread safe... Do not use with many users accessing the DB
    at the same time.

    Implemented as a function on purpose, otherwise complicated logic would be
    needed to set the internal state of the object after calling
    computer.delete().
    """
    from aiida.orm.data.code import Code

    type_check(code, Code)

    existing_outputs = code.get_outputs()

    if len(existing_outputs) != 0:
        raise InvalidOperation('Unable to delete {} because it has {} output links'.format(
            code.full_label, len(existing_outputs)))
    else:
        repo_folder = code._repository_folder
        with transaction.atomic():
            code.dbnode.delete()
            repo_folder.erase()
