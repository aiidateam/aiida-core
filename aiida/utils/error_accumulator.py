# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
class ErrorAccumulator(object):
    """
    Allows to run a number of functions and collect all the errors they raise

    This allows to validate multiple things and tell the user about all the
    errors encountered at once. Works best if the individual functions do not depend on each other.

    Does not allow to trace the stack of each error, therefore do not use for debugging, but for
    semantical checking with user friendly error messages.
    """

    def __init__(self, *error_cls):
        self.error_cls = error_cls
        self.errors = {k: [] for k in self.error_cls}

    def run(self, function, *args, **kwargs):
        try:
            function(*args, **kwargs)
        except self.error_cls as err:
            self.errors[err.__class__].append(err)

    def success(self):
        return bool(not any(self.errors.values()))

    def result(self, raise_error=Exception):
        if raise_error:
            self.raise_errors(raise_error)
        return self.success(), self.errors

    def raise_errors(self, raise_cls):
        if not self.success():
            raise raise_cls('The following errors were encountered: {}'.format(self.errors))

