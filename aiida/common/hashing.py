# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common password and hash generation functions."""
from collections import OrderedDict, abc
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import singledispatch
import hashlib
from itertools import chain
import numbers
from operator import itemgetter
import secrets
import string
import typing
import uuid

from aiida.common.constants import AIIDA_FLOAT_PRECISION
from aiida.common.exceptions import HashingError
from aiida.common.utils import DatetimePrecision

from .folders import Folder


def get_random_string(length: int = 12) -> str:
    """Return a securely generated random string.

    The default length of 12 with the all ASCII letters and digits returns a 71-bit value:

        log_2((26+26+10)^12) =~ 71 bits

    :param length: The number of characters to use for the string.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))


BLAKE2B_OPTIONS = {
    'fanout': 0,  # unlimited fanout/depth mode
    'depth': 2,  # has fixed depth of 2
    'digest_size': 32,  # we do not need a cryptographically relevant digest
    'inner_size': 64,  # ... but still use 64 as the inner size
}


def chunked_file_hash(
    handle: typing.BinaryIO, hash_cls: typing.Any, chunksize: int = 524288, **kwargs: typing.Any
) -> str:
    """Return the hash for the given file handle

    Will read the file in chunks, which should be opened in 'rb' mode.

    :param handle: a file handle, opened in 'rb' mode.
    :param hash_cls: a class implementing hashlib._Hash
    :param chunksize: number of bytes to chunk the file read in
    :param kwargs: arguments to pass to the hasher initialisation
    :return: the hash hexdigest (the hash key)
    """
    hasher = hash_cls(**kwargs)
    while True:
        chunk = handle.read(chunksize)
        hasher.update(chunk)

        if not chunk:
            # Empty returned value: EOF
            break

    return hasher.hexdigest()


def make_hash(object_to_hash, **kwargs):
    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable or nonhashable types (including lists, tuples, sets, and
    dictionaries).

    :param object_to_hash: the object to hash

    :returns: a unique hash

    There are a lot of modules providing functionalities to create unique
    hashes for hashable values.
    However, getting hashes for nonhashable items like sets or dictionaries is
    not easily doable because order is not fixed.
    This leads to the peril of getting different hashes for the same
    dictionary.

    This function avoids this by recursing through nonhashable items and
    hashing iteratively. Uses python's sorted function to sort unsorted
    sets and dictionaries by sorting the hashed keys.
    """
    hashes = _make_hash(object_to_hash, **kwargs)  # pylint: disable=assignment-from-no-return

    # use the Unlimited fanout hashing protocol outlined in
    #   https://blake2.net/blake2_20130129.pdf
    final_hash = hashlib.blake2b(node_depth=1, last_node=True, **BLAKE2B_OPTIONS)

    for sub in hashes:
        final_hash.update(sub)

    # add an empty last leaf node
    final_hash.update(hashlib.blake2b(node_depth=0, last_node=True, **BLAKE2B_OPTIONS).digest())

    return final_hash.hexdigest()


@singledispatch
def _make_hash(object_to_hash, **_):
    """
    Implementation of the ``make_hash`` function. The hash is created as a
    28 byte integer, and only later converted to a string.
    """
    raise HashingError(f'Value of type {type(object_to_hash)} cannot be hashed')


def _single_digest(obj_type, obj_bytes=b''):
    return hashlib.blake2b(obj_bytes, person=obj_type.encode('ascii'), node_depth=0, **BLAKE2B_OPTIONS).digest()


_END_DIGEST = _single_digest(')')


@_make_hash.register(bytes)
def _(bytes_obj, **kwargs):
    """Hash arbitrary byte strings."""
    return [_single_digest('str', bytes_obj)]


@_make_hash.register(str)
def _(val, **kwargs):
    """Convert strings explicitly to bytes."""
    return [_single_digest('str', val.encode('utf-8'))]


@_make_hash.register(abc.Sequence)
def _(sequence_obj, **kwargs):
    # unpack the list and use the elements
    return [_single_digest('list(')] + list(chain.from_iterable(_make_hash(i, **kwargs) for i in sequence_obj)
                                            ) + [_END_DIGEST]


@_make_hash.register(abc.Set)
def _(set_obj, **kwargs):
    # turn the set objects into a list of hashes which are always sortable,
    # then return a flattened list of the hashes
    return [_single_digest('set(')] + list(chain.from_iterable(sorted(_make_hash(i, **kwargs) for i in set_obj))
                                           ) + [_END_DIGEST]


@_make_hash.register(abc.Mapping)
def _(mapping, **kwargs):
    """Hashing arbitrary mapping containers (dict, OrderedDict) by first sorting by hashed keys"""

    def hashed_key_mapping():
        for key, value in mapping.items():
            yield (_make_hash(key, **kwargs), value)

    return [_single_digest('dict(')] + list(
        chain.from_iterable(
            (k_digest + _make_hash(val, **kwargs)) for k_digest, val in sorted(hashed_key_mapping(), key=itemgetter(0))
        )
    ) + [_END_DIGEST]


@_make_hash.register(OrderedDict)
def _(mapping, **kwargs):
    """
    Hashing of OrderedDicts

    :param odict_as_unordered: hash OrderedDicts as normal dicts (mostly for testing)
    """

    if kwargs.get('odict_as_unordered', False):
        return _make_hash.registry[abc.Mapping](mapping)

    return ([_single_digest('odict(')] + list(
        chain.from_iterable((_make_hash(key, **kwargs) + _make_hash(val, **kwargs)) for key, val in mapping.items())
    ) + [_END_DIGEST])


@_make_hash.register(numbers.Real)
def _(val, **kwargs):
    """
    Before hashing a float, convert to a string (via rounding) and with a fixed number of digits after the comma.
    Note that the `_single_digest` requires a bytes object so we need to encode the utf-8 string first
    """
    return [_single_digest('float', float_to_text(val, sig=AIIDA_FLOAT_PRECISION).encode('utf-8'))]


@_make_hash.register(Decimal)
def _(val, **kwargs):
    """
    While a decimal can be converted exactly to a string which captures all characteristics of the underlying
    implementation, we also need compatibility with "equal" representations as int or float. Hence we are checking
    for the exponent (which is negative if there is a fractional component, 0 otherwise) and get the same hash
    as for a corresponding float or int.
    """
    if val.as_tuple().exponent < 0:
        return [_single_digest('float', float_to_text(val, sig=AIIDA_FLOAT_PRECISION).encode('utf-8'))]
    return [_single_digest('int', f'{val}'.encode('utf-8'))]


@_make_hash.register(numbers.Complex)
def _(val, **kwargs):
    """
    In case of a complex number, use the same encoding of two floats and join them with a special symbol (a ! here).
    """
    return [
        _single_digest(
            'complex', '{}!{}'.format(
                float_to_text(val.real, sig=AIIDA_FLOAT_PRECISION), float_to_text(val.imag, sig=AIIDA_FLOAT_PRECISION)
            ).encode('utf-8')
        )
    ]


@_make_hash.register(numbers.Integral)
def _(val, **kwargs):
    """get the hash of the little-endian signed long long representation of the integer"""
    return [_single_digest('int', f'{val}'.encode('utf-8'))]


@_make_hash.register(bool)
def _(val, **kwargs):
    return [_single_digest('bool', b'\x01' if val else b'\x00')]


@_make_hash.register(type(None))
def _(val, **kwargs):
    return [_single_digest('none')]


@_make_hash.register(datetime)
def _(val, **kwargs):
    """hashes the little-endian rep of the float <epoch-seconds>.<subseconds>"""
    # see also https://stackoverflow.com/a/8778548 for an excellent elaboration
    if val.tzinfo is None or val.utcoffset() is None:
        val = val.replace(tzinfo=timezone.utc)

    timestamp = val.timestamp()
    return [_single_digest('datetime', float_to_text(timestamp, sig=AIIDA_FLOAT_PRECISION).encode('utf-8'))]


@_make_hash.register(date)
def _(val, **kwargs):
    """Hashes the string representation in ISO format of the `datetime.date` object."""
    return [_single_digest('date', val.isoformat().encode('utf-8'))]


@_make_hash.register(uuid.UUID)
def _(val, **kwargs):
    return [_single_digest('uuid', val.bytes)]


@_make_hash.register(DatetimePrecision)
def _(datetime_precision, **kwargs):
    """ Hashes for DatetimePrecision object
    """
    return [_single_digest('dt_prec')] + list(
        chain.from_iterable(_make_hash(i, **kwargs) for i in [datetime_precision.dtobj, datetime_precision.precision])
    ) + [_END_DIGEST]


@_make_hash.register(Folder)
def _(folder, **kwargs):
    """
    Hash the content of a Folder object. The name of the folder itself is actually ignored
    :param ignored_folder_content: list of filenames to be ignored for the hashing
    """

    ignored_folder_content = kwargs.get('ignored_folder_content', [])

    def folder_digests(subfolder):
        """traverses the given folder and yields digests for the contained objects"""
        for name, isfile in sorted(subfolder.get_content_list(only_paths=False), key=itemgetter(0)):
            if name in ignored_folder_content:
                continue

            if isfile:
                yield _single_digest('fname', name.encode('utf-8'))
                with subfolder.open(name, mode='rb') as fhandle:
                    yield _single_digest('fcontent', fhandle.read())
            else:
                yield _single_digest('dir(', name.encode('utf-8'))
                for digest in folder_digests(subfolder.get_subfolder(name)):
                    yield digest
                yield _END_DIGEST

    return [_single_digest('folder')] + list(folder_digests(folder))


def float_to_text(value, sig):
    """
    Convert float to text string for computing hash.
    Preseve up to N significant number given by sig.

    :param value: the float value to convert
    :param sig: choose how many digits after the comma should be output
    """
    if value == 0:
        value = 0.  # Identify value of -0. and overwrite with 0.
    fmt = f'{{:.{sig}g}}'
    return fmt.format(value)
