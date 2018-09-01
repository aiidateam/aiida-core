# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import sys

from six.moves import cStringIO as StringIO


class Capturing(object):
    """
    This class captures stdout and returns it
    (as a list, split by lines).

    Note: if you raise a SystemExit, you have to catch it outside.
    E.g., in our tests, this works::

        import sys
        with self.assertRaises(SystemExit):
            with Capturing() as output:
                sys.exit()

    But out of the testing environment, the code instead just exits.

    To use it, access the obj.stdout_lines, or just iterate over the object

    :param capture_stderr: if True, also captures sys.stderr. To access the
        lines, use obj.stderr_lines. If False, obj.stderr_lines is None.
    """

    def __init__(self, capture_stderr=False):
        self.stdout_lines = list()
        super(Capturing, self).__init__()

        self._capture_stderr = capture_stderr
        if self._capture_stderr:
            self.stderr_lines = list()
        else:
            self.stderr_lines = None

    def __enter__(self):
        self._stdout = sys.stdout
        self._stringioout = StringIO()
        sys.stdout = self._stringioout
        if self._capture_stderr:
            self._stderr = sys.stderr
            self._stringioerr = StringIO()
            sys.stderr = self._stringioerr
        return self

    def __exit__(self, *args):
        self.stdout_lines.extend(self._stringioout.getvalue().splitlines())
        sys.stdout = self._stdout
        del self._stringioout  # free up some memory
        if self._capture_stderr:
            self.stderr_lines.extend(self._stringioerr.getvalue().splitlines())
            sys.stderr = self._stderr
            del self._stringioerr  # free up some memory

    def __str__(self):
        return str(self.stdout_lines)

    def __iter__(self):
        return iter(self.stdout_lines)
