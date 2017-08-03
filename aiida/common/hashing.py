# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from passlib.context import CryptContext
import random
import hashlib
import time
from datetime import datetime

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

def make_hash(object_to_hash, float_precision=12):
    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable or nonhashable types (including lists, tuples, sets, and
    dictionaries).

    :param object_to_hash: the object to hash
    :param int float_precision: the precision when converting floats to strings

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
    import numpy as np

    if isinstance(object_to_hash, (tuple, list)):
        hashes = tuple([
                make_hash(_, float_precision=float_precision)
                for _
                in object_to_hash
            ])
        # We treat lists and tuples as if they are the same thing,
        # but I think this is OK
        return make_hash_with_type('L', "".join(hashes))

    elif isinstance(object_to_hash, set):
        hashes = tuple([
                make_hash(_, float_precision=float_precision)
                for _
                in sorted(object_to_hash)
            ])
        return make_hash_with_type('S', "".join(hashes))

    elif isinstance(object_to_hash, dict):
        hashed_dictionary = {
            k: make_hash(v, float_precision=float_precision)
            for k,v
            in object_to_hash.items()
        }
        return make_hash_with_type(
            'D', make_hash(sorted(
                    hashed_dictionary.items()), float_precision=float_precision
                )
            )

    elif isinstance(object_to_hash, float):
        return make_hash_with_type(
                'f','{:.{precision}f}'.format(
                        object_to_hash, precision=float_precision
                )
            )
    # If is numpy:
    elif type(object_to_hash).__module__ == np.__name__:
        return make_hash_with_type('N', str(object_to_hash))

    elif isinstance(object_to_hash, basestring):
        return make_hash_with_type('s', object_to_hash)

    elif isinstance(object_to_hash, bool): # bool must come before int
        # I prefer to be sure of what I hash instead of using 'str'
        return make_hash_with_type('b', "True" if object_to_hash else "False")

    elif object_to_hash is None:
        return make_hash_with_type('n', "None")

    elif isinstance(object_to_hash, int):
        return make_hash_with_type('i', str(object_to_hash))
    elif isinstance(object_to_hash, long):
        return make_hash_with_type('l', str(object_to_hash))

    elif isinstance(object_to_hash, datetime):
        return make_hash_with_type('d', str(object_to_hash))
    # Possibly add more types here, as needed
    else:
        raise ValueError("Value of type {} cannot be hashed".format(
                type(object_to_hash)))
