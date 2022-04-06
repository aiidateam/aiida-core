# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Abstracts JSON usage to ensure compatibility with Python2 and Python3.

Use this module prefentially over standard json to ensure compatibility.

.. deprecated:: This module is deprecated in v2.0.0 and should no longer be used. Python 2 support has long since been
    dropped and for Python 3, one should simply use the ``json`` module of the standard library directly.

"""
import codecs
import json

from aiida.common.warnings import warn_deprecation

warn_deprecation(
    'This module has been deprecated and should no longer be used. Use the `json` standard library instead.', version=3
)


def dump(data, handle, **kwargs):
    """Serialize ``data`` as a JSON formatted stream to ``handle``.

    We use ``ensure_ascii=False`` to write unicode characters specifically as this improves the readability of the json
    and reduces the file size.
    """
    try:
        if 'b' in handle.mode:
            handle = codecs.getwriter('utf-8')(handle)
    except AttributeError:
        pass

    return json.dump(data, handle, ensure_ascii=False, **kwargs)


def dumps(data, **kwargs):
    """Serialize ``data`` as a JSON formatted string.

    We use ``ensure_ascii=False`` to write unicode characters specifically as this improves the readability of the json
    and reduces the file size.
    """
    return json.dumps(data, ensure_ascii=False, **kwargs)


def load(handle, **kwargs):
    """Deserialize ``handle`` text or binary file containing a JSON document to a Python object.

    :raises ValueError: if no valid JSON object could be decoded.
    """
    if 'b' in handle.mode:
        handle = codecs.getreader('utf-8')(handle)

    try:
        return json.load(handle, **kwargs)
    except json.JSONDecodeError as exc:
        raise ValueError from exc


def loads(string, **kwargs):
    """Deserialize text or binary ``string`` containing a JSON document to a Python object.

    :raises ValueError: if no valid JSON object could be decoded.
    """
    if isinstance(string, bytes):
        string = string.decode('utf-8')

    try:
        return json.loads(string, **kwargs)
    except json.JSONDecodeError as exc:
        raise ValueError from exc
