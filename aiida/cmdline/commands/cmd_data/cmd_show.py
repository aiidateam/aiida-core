# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to manage showfunctionality to all data types.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import click

from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.exceptions import MultipleObjectsError

SHOW_OPTIONS = [
    options.TRAJECTORY_INDEX(),
    options.WITH_ELEMENTS(),
    click.option('-c', '--contour', type=click.FLOAT, cls=MultipleValueOption, default=None, help="Isovalues to plot"),
    click.option(
        '--sampling-stepsize',
        type=click.INT,
        default=None,
        help="Sample positions in plot every sampling_stepsize timestep"),
    click.option(
        '--stepsize',
        type=click.INT,
        default=None,
        help="The stepsize for the trajectory, set it higher to reduce number of points"),
    click.option('--mintime', type=click.INT, default=None, help="The time to plot from"),
    click.option('--maxtime', type=click.INT, default=None, help="The time to plot to"),
    click.option('--indices', type=click.INT, cls=MultipleValueOption, default=None, help="Show only these indices"),
    click.option(
        '--dont-block', 'block', is_flag=True, default=True, help="Don't block interpreter when showing plot."),
]


def show_options(func):
    for option in reversed(SHOW_OPTIONS):
        func = option(func)

    return func


def _show_jmol(exec_name, trajectory_list, **kwargs):
    """
    Plugin for jmol
    """
    import tempfile
    import subprocess

    # pylint: disable=protected-access
    with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
        for trajectory in trajectory_list:
            tmpf.write(trajectory._exportcontent('cif', **kwargs)[0])
        tmpf.flush()

        try:
            subprocess.check_output([exec_name, tmpf.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(exec_name))
        except OSError as err:
            if err.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                                   "or try with an absolute path.".format(exec_name))
            else:
                raise


def _show_xcrysden(exec_name, object_list, **kwargs):
    """
    Plugin for xcrysden
    """
    import tempfile
    import subprocess

    if len(object_list) > 1:
        raise MultipleObjectsError("Visualization of multiple trajectories is not implemented")
    obj = object_list[0]

    # pylint: disable=protected-access
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.xsf') as tmpf:
        tmpf.write(obj._exportcontent('xsf', **kwargs)[0])
        tmpf.flush()

        try:
            subprocess.check_output([exec_name, '--xsf', tmpf.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(exec_name))
        except OSError as err:
            if err.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                                   "or try with an absolute path.".format(exec_name))
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
    import tempfile
    import subprocess

    # pylint: disable=protected-access
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.cif') as tmpf:
        for structure in structure_list:
            tmpf.write(structure._exportcontent('cif')[0])
        tmpf.flush()

        try:
            subprocess.check_output([exec_name, tmpf.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(exec_name))
        except OSError as err:
            if err.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                                   "or try with an absolute path.".format(exec_name))
            else:
                raise


def _show_vmd(exec_name, structure_list):
    """
    Plugin for vmd
    """
    import tempfile
    import subprocess

    if len(structure_list) > 1:
        raise MultipleObjectsError("Visualization of multiple objects is not implemented")
    structure = structure_list[0]

    # pylint: disable=protected-access
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.xsf') as tmpf:
        tmpf.write(structure._exportcontent('xsf')[0])
        tmpf.flush()

        try:
            subprocess.check_output([exec_name, tmpf.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(exec_name))
        except OSError as err:
            if err.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                                   "or try with an absolute path.".format(exec_name))
            else:
                raise


def _show_xmgrace(exec_name, list_bands):
    """
    Plugin for showing the bands with the XMGrace plotting software.
    """
    import sys
    import subprocess
    import tempfile
    from aiida.orm.nodes.data.array.bands import max_num_agr_colors

    list_files = []
    current_band_number = 0
    for iband, bnds in enumerate(list_bands):
        # extract number of bands
        nbnds = bnds.get_bands().shape[1]
        # pylint: disable=protected-access
        text, _ = bnds._exportcontent(
            'agr', setnumber_offset=current_band_number, color_number=(iband + 1 % max_num_agr_colors))
        # write a tempfile
        tempf = tempfile.NamedTemporaryFile('w+', suffix='.agr')
        tempf.write(text)
        tempf.flush()
        list_files.append(tempf)
        # update the number of bands already plotted
        current_band_number += nbnds

    try:
        subprocess.check_output([exec_name] + [f.name for f in list_files])
    except subprocess.CalledProcessError:
        print("Note: the call to {} ended with an error.".format(exec_name))
    except OSError as err:
        if err.errno == 2:
            print("No executable '{}' found. Add to the path," " or try with an absolute path.".format(exec_name))
            sys.exit(1)
        else:
            raise
    finally:
        for fhandle in list_files:
            fhandle.close()
