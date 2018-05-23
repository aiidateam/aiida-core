# -*- coding: utf-8 -*-
from __future__ import absolute_import 
import click


def command():
    """
    Wrapped decorator for click's command decorator, which makes sure
    that the database environment is loaded
    """
    from aiida.cmdline.utils.decorators import with_dbenv

    @click.command
    @with_dbenv()
    def inner():
        func(*args, **kwargs)

    return inner
