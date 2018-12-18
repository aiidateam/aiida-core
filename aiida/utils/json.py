# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Abstracts JSON usage to ensure compatibility with Python2 and Python3.

Use this module prefentially over standard json to ensure compatibility.
Also note the conventions for using io.open for dump and dumps.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import simplejson


def dump(data, fhandle, **kwargs):
    """
    Write JSON encoded 'data' to a file-like object, fhandle
    In Py2/3, use io.open(filename, 'wb') to write.
    The utf8write object is used to ensure that the resulting serialised data is
    encoding as UTF8.
    Any strings with non-ASCII characters need to be unicode strings.
    We use ensure_ascii=False to write unicode characters specifically
    as this improves the readability of the json and reduces the file size.
    """
    import codecs
    utf8writer = codecs.getwriter('utf8')
    simplejson.dump(data, utf8writer(fhandle), ensure_ascii=False, encoding='utf8', **kwargs)


def dumps(data, **kwargs):
    """
    Write JSON encoded 'data' to a string.
    simplejson is useful here as it always returns unicode if ensure_ascii=False is used,
    unlike the standard library json, rather than being dependant on the input.
    We use also ensure_ascii=False to write unicode characters specifically
    as this improves the readability of the json and reduces the file size.
    When writing to file, use io.open(filename, 'w', encoding='utf8')
    """
    return simplejson.dumps(data, ensure_ascii=False, encoding='utf8', **kwargs)


def load(fhandle, **kwargs):
    """
    Deserialise a JSON file.

    For Py2/Py3 compatibility, io.open(filename, 'r', encoding='utf8') should be used.

    :raises ValueError: if no valid JSON object could be decoded
    """
    try:
        return simplejson.load(fhandle, encoding='utf8', **kwargs)
    except simplejson.errors.JSONDecodeError:
        raise ValueError


def loads(json_string, **kwargs):
    """
    Deserialise a JSON string.

    :raises ValueError: if no valid JSON object could be decoded
    """
    try:
        return simplejson.loads(json_string, encoding='utf8', **kwargs)
    except simplejson.errors.JSONDecodeError:
        raise ValueError
