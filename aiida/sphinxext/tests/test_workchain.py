# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the AiiDA workchain Sphinx directive."""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from os.path import join, dirname

import six
import pytest

WORKCHAIN = join(dirname(__file__), 'workchain_source')


def test_workchain_build(build_sphinx, xml_equal, reference_result):
    out_dir = build_sphinx(WORKCHAIN)
    index_file = join(out_dir, 'index.xml')
    if six.PY2:
        xml_equal(index_file, reference_result('workchain.py2.xml'))
    else:
        xml_equal(index_file, reference_result('workchain.py3.xml'))
