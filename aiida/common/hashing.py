# -*- coding: utf-8 -*-
from passlib.context import CryptContext
import random
import hashlib
import time

"""
Here we define a single password hashing instance for the full AiiDA.
"""

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."

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

    # vary rounds parameter randomly when creating new hashes...
    all__vary_rounds=0.1,

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

