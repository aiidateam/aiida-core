# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement,too-many-branches
"""Have a single tqdm progress bar instance that should be handled using the functions in this module"""
from typing import Iterable

from tqdm import tqdm

from aiida.common.lang import type_check

from aiida.tools.importexport.common.config import BAR_FORMAT
from aiida.tools.importexport.common.exceptions import ProgressBarError

__all__ = ('get_progress_bar', 'close_progress_bar')

PROGRESS_BAR = None


def get_progress_bar(iterable=None, total=None, leave=None, **kwargs):
    """Set up, cache and return cached tqdm progress bar"""
    global PROGRESS_BAR

    leave_default = False

    type_check(iterable, Iterable, allow_none=True)
    type_check(total, int, allow_none=True)
    type_check(leave, bool, allow_none=True)

    # iterable and total are mutually exclusive
    if iterable is not None and total is not None:
        if len(iterable) == total:
            kwargs['iterable'] = iterable
        else:
            raise ProgressBarError('You can not set both "iterable" and "total" for the progress bar.')
    elif iterable is None and total is None:
        if PROGRESS_BAR is None:
            kwargs['total'] = 1
        # Else pass: we guess the desired outcome is to retrieve the current progress bar
    elif iterable is not None:
        kwargs['iterable'] = iterable
    elif total is not None:
        kwargs['total'] = total

    if PROGRESS_BAR is None:
        leave = leave if leave is not None else leave_default
        PROGRESS_BAR = tqdm(bar_format=BAR_FORMAT, leave=leave, **kwargs)
    elif 'iterable' in kwargs or 'total' in kwargs:
        # Create a new progress bar
        # We leave it up to the caller/creator to properly have set leave before we close the current progress bar
        if leave is None:
            leave = PROGRESS_BAR.leave if PROGRESS_BAR.leave is not None else leave_default
        for attribute in ('desc', 'disable'):
            if getattr(PROGRESS_BAR, attribute, None) is not None:
                kwargs[attribute] = getattr(PROGRESS_BAR, attribute)
        close_progress_bar()
        PROGRESS_BAR = tqdm(bar_format=BAR_FORMAT, leave=leave, **kwargs)
    else:
        for attribute, value in kwargs.items():
            try:
                setattr(PROGRESS_BAR, attribute, value)
            except AttributeError:
                raise ProgressBarError(
                    'The given attribute {} either can not be set or does not exist for the progress bar.'.
                    format(attribute)
                )

    return PROGRESS_BAR


def close_progress_bar(leave=None):
    """Close instantiated progress bar"""
    global PROGRESS_BAR

    type_check(leave, bool, allow_none=True)

    if PROGRESS_BAR is not None:
        if leave is not None:
            PROGRESS_BAR.leave = leave
        PROGRESS_BAR.close()

    PROGRESS_BAR = None
