# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import hashlib
import numbers
import random
import time
import uuid
from datetime import datetime

from passlib.context import CryptContext

try: # Python3
    from functools import singledispatch
    from collections import abc
except ImportError: # Python2
    from singledispatch import singledispatch
    import collections as abc

import numpy as np

from .folders import Folder

"""
Here we define a single password hashing instance for the full AiiDA.
"""


# The prefix of the hashed using pbkdf2_sha256 algorithm in Django
HASHING_PREFIX_DJANGO = "pbkdf2_sha256"
# The prefix of the hashed using pbkdf2_sha256 algorithm in Passlib
HASHING_PREFIX_PBKDF2_SHA256 = "$pbkdf2-sha256"

# This will never be a valid encoded hash
UNUSABLE_PASSWORD_PREFIX = '!'
# Number of random chars to add after UNUSABLE_PASSWORD_PREFIX
UNUSABLE_PASSWORD_SUFFIX_LENGTH = 40

HASHING_KEY="HashingKey"

pwd_context = CryptContext(
    # The list of hashes that we support
    schemes=["pbkdf2_sha256", "des_crypt"],
    # The default hashing mechanism
    default="pbkdf2_sha256",

    # We set the number of rounds that should be used...
    pbkdf2_sha256__default_rounds=8000,
    )


def create_unusable_pass():
    return UNUSABLE_PASSWORD_PREFIX + get_random_string(
        UNUSABLE_PASSWORD_SUFFIX_LENGTH)


def is_password_usable(enc_pass):
    if enc_pass is None or enc_pass.startswith(UNUSABLE_PASSWORD_PREFIX):
        return False

    if pwd_context.identify(enc_pass) is not None:
        return True

    # Backward compatibility for old Django hashing
    if enc_pass.startswith(HASHING_PREFIX_DJANGO):
        enc_pass = enc_pass.replace(HASHING_PREFIX_DJANGO,
                                    HASHING_PREFIX_PBKDF2_SHA256, 1)
        if pwd_context.identify(enc_pass) is not None:
            return True

    return False

###################################################################
# THE FOLLOWING WAS TAKEN FROM DJANGO BUT IT CAN BE EASILY REPLACED
###################################################################

# Use the system PRNG if possible
try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    import warnings
    warnings.warn('A secure pseudo-random number generator is not available '
                  'on your system. Falling back to Mersenne Twister.')
    using_sysrandom = False


def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Returns a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    if not using_sysrandom:
        # This is ugly, and a hack, but it makes things better than
        # the alternative of predictability. This re-seeds the PRNG
        # using a value that is hard for an attacker to predict, every
        # time a random string is required. This may change the
        # properties of the chosen random sequence slightly, but this
        # is better than absolute predictability.
        random.seed(
            hashlib.sha256(
                ("%s%s%s" % (
                    random.getstate(),
                    time.time(),
                    HASHING_KEY)).encode('utf-8')
            ).digest())
    return ''.join(random.choice(allowed_chars) for i in range(length))



def make_hash_with_type(type_chr, string_to_hash):
    """
    Convention: type_chr should be a single char, lower case
      for simple datatypes, upper case for composite datatypes
      We don't check anything for speed efficiency
    """
    return hashlib.sha224("{}{}".format(type_chr, string_to_hash)).hexdigest()

@singledispatch
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
    hashing iteratively.
    Uses python's sorted function to sort unsorted sets and dictionaries
    and hashlib.sha224 to hash the value.
    We make an example with two dictionaries that should produce the
    same hash because only the order of the keys is different::

        aa = {
            '3':4,
            3:4,
            'a':{
                '1':'hello', 2:'goodbye', 1:'here'
            },
            'b':4,
            'c': set([2, '5','a', 'b', 5])
        }
        bb = {
            'c': set([2, 'b', 5, 'a', '5']),
            'b':4, 'a':{2:'goodbye', 1:'here', '1':'hello'},
            '3':4, 3:4
        }

        print str(aa) == str(bb)
        print aa == bb
        print
        print hashlib.sha224(str(aa)).hexdigest()
        print hashlib.sha224(str(bb)).hexdigest()
        print hashlib.sha224(str(aa)).hexdigest(
            ) == hashlib.sha224(str(bb)).hexdigest()
        print
        print make_hash(aa)
        print make_hash(bb)
        print make_hash(aa) == make_hash(bb)

    produces the output::

        False
        True

        0f6f0cc1e3256f6486e998e934d07cb192ea78d3ce75595267b4c665
        86877298dfb629201055e8bc410b5a2157ce65cf246677c54316723a
        False

        696cdf26b46d7abc5d6fdfb2244829dad9dd2b0100afd1e2f20a8002
        696cdf26b46d7abc5d6fdfb2244829dad9dd2b0100afd1e2f20a8002
        True

    We can conclude that using simple hashfunctions operating on
    the string of dictionary do not suffice if we want to check for equality
    of dictionaries using hashes.
    """
    raise ValueError("Value of type {} cannot be hashed".format(
        type(object_to_hash))
    )

@make_hash.register(abc.Sequence)
def _(sequence, **kwargs):
    hashes = tuple([
        make_hash(x, **kwargs) for x in sequence
    ])
    return make_hash_with_type('L', ",".join(hashes))

@make_hash.register(abc.Set)
def _(object_to_hash, **kwargs):
    hashes = tuple([
            make_hash(x, **kwargs)
            for x
            in sorted(object_to_hash)
        ])
    return make_hash_with_type('S', ",".join(hashes))

@make_hash.register(abc.Mapping)
def _(mapping, **kwargs):
    hashed_dictionary = {
        k: make_hash(v, **kwargs)
        for k,v
        in mapping.items()
    }
    return make_hash_with_type(
        'D',
        make_hash(sorted(hashed_dictionary.items()), **kwargs)
    )

@make_hash.register(numbers.Real)
def _(object_to_hash, **kwargs):
    return make_hash_with_type(
            'f',
            truncate_float64(object_to_hash).tobytes()
        )

@make_hash.register(numbers.Complex)
def _(object_to_hash, **kwargs):
    return make_hash_with_type(
        'c',
        ','.join([
            make_hash(object_to_hash.real, **kwargs),
            make_hash(object_to_hash.imag, **kwargs)
        ])
    )

@make_hash.register(numbers.Integral)
def _(object_to_hash, **kwargs):
    return make_hash_with_type('i', str(object_to_hash))

@make_hash.register(basestring)
def _(object_to_hash, **kwargs):
    return make_hash_with_type('s', object_to_hash)

@make_hash.register(bool)
def _(object_to_hash, **kwargs):
    return make_hash_with_type('b', str(object_to_hash))

@make_hash.register(type(None))
def _(object_to_hash, **kwargs):
    return make_hash_with_type('n', str(object_to_hash))

@make_hash.register(datetime)
def _(object_to_hash, **kwargs):
    return make_hash_with_type('d', str(object_to_hash))

@make_hash.register(uuid.UUID)
def _(object_to_hash, **kwargs):
    return make_hash_with_type('u', str(object_to_hash))


@make_hash.register(Folder)
def _(folder, **kwargs):
    # make sure file is closed after being read
    def _read_file(folder, name):
        with folder.open(name) as f:
            return f.read()

    ignored_folder_content = kwargs.get('ignored_folder_content', [])

    return make_hash_with_type(
        'pd',
        make_hash([
            (
                name,
                folder.get_subfolder(name) if folder.isdir(name) else
                make_hash_with_type('pf', _read_file(folder, name))
            )
            for name in sorted(folder.get_content_list())
            if name not in ignored_folder_content
        ], **kwargs)
    )

@make_hash.register(np.ndarray)
def _(object_to_hash, **kwargs):
    if object_to_hash.dtype == np.float64:
        return make_hash_with_type(
            'af',
            make_hash(truncate_array64(object_to_hash).tobytes(), **kwargs)
        )
    elif object_to_hash.dtype == np.complex128:
        return make_hash_with_type(
            'ac',
            make_hash([
                object_to_hash.real,
                object_to_hash.imag
            ], **kwargs)
        )
    else:
        return make_hash_with_type(
            'ao',
            make_hash(object_to_hash.tobytes(), **kwargs)
        )

def truncate_float64(x, num_bits=4):
    mask = ~(2**num_bits - 1)
    int_repr = np.float64(x).view(np.int64)
    masked_int = int_repr & mask
    truncated_x = masked_int.view(np.float64)
    return truncated_x

def truncate_array64(x, num_bits=4):
    mask = ~(2**num_bits - 1)
    int_array = np.array(x, dtype=np.float64).view(np.int64)
    masked_array = int_array & mask
    return masked_array.view(np.float64)
