# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import shutil
import tempfile
import subprocess
from os.path import join, dirname
import xml.etree.ElementTree as ET

import pytest

@pytest.fixture
def reference_result():
    def inner(name):
        return join(dirname(__file__), 'reference_results', name)
    return inner

@pytest.fixture
def build_dir():
    # Python 2 doesn't have tempfile.TemporaryDirectory
    dirname = tempfile.mkdtemp()
    try:
        yield dirname
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(dirname)


@pytest.fixture
def build_sphinx(build_dir):
    def inner(source_dir, builder='xml'):
        doctree_dir = join(build_dir, 'doctrees')
        out_dir = join(build_dir, builder)

        subprocess.check_call([
            sys.executable, '-m', 'sphinx', '-b', builder, '-d', doctree_dir,
            source_dir, out_dir
        ])

        return out_dir

    return inner


@pytest.fixture
def xml_equal():
    def inner(test_file, reference_file):
        if not os.path.isfile(reference_file):
            shutil.copyfile(test_file, reference_file)
            raise ValueError('Reference file does not exist!')
        assert _flatten_xml(test_file) == _flatten_xml(reference_file)
    return inner


def _flatten_xml(filename):
    return [
        (
            el.tag,
            {k: v for k, v in el.attrib.items() if k not in ['source']},
            el.text
        )
        for el in ET.parse(filename).iter()
    ]
