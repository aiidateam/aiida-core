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

    type_check(iterable, Iterable, allow_none=True)
    type_check(total, int, allow_none=True)
    type_check(leave, bool, allow_none=True)

    if PROGRESS_BAR is None:
        if iterable is not None and total is not None:
            if len(iterable) == total:
                kwargs['iterable'] = iterable
            else:
                raise ProgressBarError('You can not set both "iterable" and "total" for the progress bar.')
        elif iterable is None and total is None:
            kwargs['total'] = 1
        elif iterable is not None:
            kwargs['iterable'] = iterable
        elif total is not None:
            kwargs['total'] = total

        if ('iterable' not in kwargs and 'total' not in kwargs) or ('iterable' in kwargs and 'total' in kwargs):
            raise ProgressBarError('Internal logic error in get_progress_bar')

        PROGRESS_BAR = tqdm(bar_format=BAR_FORMAT, leave=leave, **kwargs)
    else:
        if iterable is not None and total is not None:
            if len(iterable) == total:
                kwargs['iterable'] = iterable
            else:
                raise ProgressBarError('You can not set both "iterable" and "total" for the progress bar.')
        elif iterable is None and total is None:
            pass
        elif iterable is not None:
            # Create a new progress bar
            # We leave it up to the caller/creator to properly have set leave before we close the current progress bar
            if leave is None:
                leave = PROGRESS_BAR.leave if PROGRESS_BAR.leave is not None else False
            close_progress_bar()
            PROGRESS_BAR = tqdm(iterable=iterable, bar_format=BAR_FORMAT, leave=leave, **kwargs)
        elif total is not None:
            # Create a new progress bar
            # We leave it up to the caller/creator to properly have set leave before we close the current progress bar
            if leave is None:
                leave = PROGRESS_BAR.leave if PROGRESS_BAR.leave is not None else False
            close_progress_bar()
            PROGRESS_BAR = tqdm(total=total, bar_format=BAR_FORMAT, leave=leave, **kwargs)

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
