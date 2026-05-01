###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for ``aiida.cmdline.utils.daemon`` formatter helpers."""

import pytest

from aiida.cmdline.utils.daemon import (
    format_package_state_change_lines,
    format_package_version_info,
)


@pytest.mark.parametrize(
    ('version_info', 'expected'),
    [
        pytest.param({'version': '2.8.0.post0'}, '2.8.0.post0', id='plain'),
        pytest.param(
            {'version': '2.8.0.post0', 'editable_path': None},
            '2.8.0.post0',
            id='editable-none-treated-as-absent',
        ),
    ],
)
def test_format_package_version_info_no_path(version_info, expected):
    """``format_package_version_info`` with no editable path returns the bare version."""
    assert format_package_version_info(version_info) == expected


def test_format_package_version_info_with_editable_path(tmp_path):
    """``format_package_version_info`` formats as ``'<version> @ <path>'``."""
    info = {'version': '2.8.0.post0', 'editable_path': str(tmp_path)}
    expected = f'2.8.0.post0 @ {tmp_path}'
    assert format_package_version_info(info) == expected


@pytest.mark.parametrize(
    ('daemon', 'current', 'expected'),
    [
        pytest.param({}, {}, [], id='both-empty'),
        pytest.param(
            {'aiida-core': {'version': '2.8.0'}},
            {'aiida-core': {'version': '2.8.0'}},
            [],
            id='unchanged',
        ),
        pytest.param(
            {},
            {'aiida-plugin': {'version': '1.2.3'}},
            ['Added packages: aiida-plugin (1.2.3)'],
            id='added',
        ),
        pytest.param(
            {'aiida-plugin': {'version': '1.2.3'}},
            {},
            ['Removed packages: aiida-plugin (1.2.3)'],
            id='removed',
        ),
        pytest.param(
            {'aiida-core': {'version': '2.8.0'}},
            {'aiida-core': {'version': '2.8.1'}},
            ['Changed packages: aiida-core (2.8.0 -> 2.8.1)'],
            id='changed-version',
        ),
        pytest.param(
            {'a': {'version': '1'}, 'b': {'version': '2'}},
            {'a': {'version': '1.1'}, 'c': {'version': '3'}},
            [
                'Changed packages: a (1 -> 1.1)',
                'Added packages: c (3)',
                'Removed packages: b (2)',
            ],
            id='mixed-section-order',
        ),
        pytest.param(
            {},
            {'b-pkg': {'version': '1'}, 'a-pkg': {'version': '2'}},
            ['Added packages: a-pkg (2), b-pkg (1)'],
            id='multiple-added-alphabetical',
        ),
    ],
)
def test_format_package_state_change_lines(daemon, current, expected):
    """Pin the categorisation, ordering, and formatting contract."""
    assert format_package_state_change_lines(daemon, current) == expected


def test_format_package_state_change_lines_editable_path_changed(tmp_path):
    """A change in editable path alone (same version) is reported as Changed."""
    old = tmp_path / 'old'
    new = tmp_path / 'new'
    daemon = {'aiida-core': {'version': '2.8.0', 'editable_path': str(old)}}
    current = {'aiida-core': {'version': '2.8.0', 'editable_path': str(new)}}
    expected = [f'Changed packages: aiida-core (2.8.0 @ {old} -> 2.8.0 @ {new})']
    assert format_package_state_change_lines(daemon, current) == expected


def test_format_package_state_change_lines_editable_path_appears(tmp_path):
    """Package gaining an editable path shows up as Changed."""
    daemon = {'aiida-core': {'version': '2.8.0'}}
    current = {'aiida-core': {'version': '2.8.0', 'editable_path': str(tmp_path)}}
    expected = [f'Changed packages: aiida-core (2.8.0 -> 2.8.0 @ {tmp_path})']
    assert format_package_state_change_lines(daemon, current) == expected


def test_format_package_state_change_lines_editable_path_disappears(tmp_path):
    """Package losing its editable path shows up as Changed."""
    daemon = {'aiida-core': {'version': '2.8.0', 'editable_path': str(tmp_path)}}
    current = {'aiida-core': {'version': '2.8.0'}}
    expected = [f'Changed packages: aiida-core (2.8.0 @ {tmp_path} -> 2.8.0)']
    assert format_package_state_change_lines(daemon, current) == expected
