# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to manage showfunctionality to all data types.
"""
import pathlib

import click

from aiida.cmdline.params import options
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.utils import echo
from aiida.common.exceptions import MultipleObjectsError

SHOW_OPTIONS = [
    options.TRAJECTORY_INDEX(),
    options.WITH_ELEMENTS(),
    click.option('-c', '--contour', type=click.FLOAT, cls=MultipleValueOption, default=None, help='Isovalues to plot'),
    click.option(
        '--sampling-stepsize',
        type=click.INT,
        default=None,
        help='Sample positions in plot every sampling_stepsize timestep'
    ),
    click.option(
        '--stepsize',
        type=click.INT,
        default=None,
        help='The stepsize for the trajectory, set it higher to reduce number of points'
    ),
    click.option('--mintime', type=click.INT, default=None, help='The time to plot from'),
    click.option('--maxtime', type=click.INT, default=None, help='The time to plot to'),
    click.option('--indices', type=click.INT, cls=MultipleValueOption, default=None, help='Show only these indices'),
    click.option(
        '--dont-block', 'block', is_flag=True, default=True, help="Don't block interpreter when showing plot."
    ),
]


def show_options(func):
    for option in reversed(SHOW_OPTIONS):
        func = option(func)

    return func


def _show_jmol(exec_name, trajectory_list, **kwargs):
    """
    Plugin for jmol
    """
    import subprocess
    import tempfile

    # pylint: disable=protected-access
    with tempfile.NamedTemporaryFile(mode='w+b') as handle:
        for trajectory in trajectory_list:
            handle.write(trajectory._exportcontent('cif', **kwargs)[0])
        handle.flush()

        try:
            subprocess.check_output([exec_name, handle.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_error(f'the call to {exec_name} ended with an error.')
        except OSError as err:
            if err.errno == 2:
                echo.echo_critical(f"No executable '{exec_name}' found. Add to the path, or try with an absolute path.")
            else:
                raise


def _show_xcrysden(exec_name, object_list, **kwargs):
    """
    Plugin for xcrysden
    """
    import subprocess
    import tempfile

    if len(object_list) > 1:
        raise MultipleObjectsError('Visualization of multiple trajectories is not implemented')
    obj = object_list[0]

    # pylint: disable=protected-access
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.xsf') as tmpf:
        tmpf.write(obj._exportcontent('xsf', **kwargs)[0])
        tmpf.flush()

        try:
            subprocess.check_output([exec_name, '--xsf', tmpf.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_error(f'the call to {exec_name} ended with an error.')
        except OSError as err:
            if err.errno == 2:
                echo.echo_critical(f"No executable '{exec_name}' found. Add to the path, or try with an absolute path.")
            else:
                raise


# pylint: disable=unused-argument
def _show_mpl_pos(exec_name, trajectory_list, **kwargs):
    """
    Produces a matplotlib plot of the trajectory
    """
    for traj in trajectory_list:
        traj.show_mpl_pos(**kwargs)


# pylint: disable=unused-argument
def _show_mpl_heatmap(exec_name, trajectory_list, **kwargs):
    """
    Produces a matplotlib plot of the trajectory
    """
    for traj in trajectory_list:
        traj.show_mpl_heatmap(**kwargs)


# pylint: disable=unused-argument
def _show_ase(exec_name, structure_list):
    """
    Plugin to show the structure with the ASE visualizer
    """
    try:
        from ase.visualize import view
        for structure in structure_list:
            view(structure.get_ase())
    except ImportError:  # pylint: disable=try-except-raise
        raise


def _show_vesta(exec_name, structure_list):
    """
    Plugin for VESTA
    This VESTA plugin was added by Yue-Wen FANG and Abel Carreras
    at Kyoto University in the group of Prof. Isao Tanaka's lab

    """
    import subprocess
    import tempfile

    # pylint: disable=protected-access
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.cif') as tmpf:
        for structure in structure_list:
            tmpf.write(structure._exportcontent('cif')[0])
        tmpf.flush()

        try:
            subprocess.check_output([exec_name, tmpf.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_error(f'the call to {exec_name} ended with an error.')
        except OSError as err:
            if err.errno == 2:
                echo.echo_critical(f"No executable '{exec_name}' found. Add to the path, or try with an absolute path.")
            else:
                raise


def _show_vmd(exec_name, structure_list):
    """
    Plugin for vmd
    """
    import subprocess
    import tempfile

    if len(structure_list) > 1:
        raise MultipleObjectsError('Visualization of multiple objects is not implemented')
    structure = structure_list[0]

    # pylint: disable=protected-access
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.xsf') as tmpf:
        tmpf.write(structure._exportcontent('xsf')[0])
        tmpf.flush()

        try:
            subprocess.check_output([exec_name, tmpf.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_error(f'the call to {exec_name} ended with an error.')
        except OSError as err:
            if err.errno == 2:
                echo.echo_critical(f"No executable '{exec_name}' found. Add to the path, or try with an absolute path.")
            else:
                raise


def _show_xmgrace(exec_name, list_bands):
    """
    Plugin for showing the bands with the XMGrace plotting software.
    """
    import subprocess
    import sys
    import tempfile

    from aiida.orm.nodes.data.array.bands import MAX_NUM_AGR_COLORS

    list_files = []
    current_band_number = 0

    with tempfile.TemporaryDirectory() as tmpdir:

        dirpath = pathlib.Path(tmpdir)

        for iband, bnds in enumerate(list_bands):
            # extract number of bands
            nbnds = bnds.get_bands().shape[1]
            text, _ = bnds._exportcontent(  # pylint: disable=protected-access
                'agr', setnumber_offset=current_band_number, color_number=(iband + 1 % MAX_NUM_AGR_COLORS)
            )
            # write a tempfile
            filepath = dirpath / f'{iband}.agr'
            filepath.write_bytes(text)
            list_files.append(str(filepath))
            # update the number of bands already plotted
            current_band_number += nbnds

        try:
            subprocess.check_output([exec_name] + [str(filepath) for filepath in list_files])
        except subprocess.CalledProcessError:
            print(f'Note: the call to {exec_name} ended with an error.')
        except OSError as err:
            if err.errno == 2:
                print(f"No executable '{exec_name}' found. Add to the path, or try with an absolute path.")
                sys.exit(1)
            else:
                raise
