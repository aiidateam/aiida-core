###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This allows to manage showfunctionality to all data types."""

import pathlib

from aiida.cmdline.utils import echo
from aiida.common.exceptions import MultipleObjectsError


def has_executable(exec_name):
    """:return: True if executable can be found in PATH, False otherwise."""
    import shutil

    return shutil.which(exec_name) is not None


def _show_jmol(exec_name, trajectory_list, **_kwargs):
    """Plugin for jmol"""
    import subprocess
    import tempfile

    if not has_executable(exec_name):
        echo.echo_critical(f"No executable '{exec_name}' found. Add to the path, or try with an absolute path.")

    with tempfile.NamedTemporaryFile(mode='w+b') as handle:
        for trajectory in trajectory_list:
            handle.write(trajectory._exportcontent('cif')[0])
        handle.flush()

        try:
            subprocess.check_output([exec_name, handle.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_error(f'the call to {exec_name} ended with an error.')


def _show_xcrysden(exec_name, trajectory_list, **_kwargs):
    """Plugin for xcrysden"""
    import subprocess
    import tempfile

    if len(trajectory_list) > 1:
        raise MultipleObjectsError('Visualization of multiple trajectories is not implemented')
    obj = trajectory_list[0]

    if not has_executable(exec_name):
        echo.echo_critical(f"No executable '{exec_name}' found.")

    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.xsf') as tmpf:
        tmpf.write(obj._exportcontent('xsf')[0])
        tmpf.flush()

        try:
            subprocess.check_output([exec_name, '--xsf', tmpf.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_error(f'the call to {exec_name} ended with an error.')


def _show_mpl_pos(exec_name, trajectory_list, **kwargs):
    """Produces a matplotlib plot of the trajectory"""
    for traj in trajectory_list:
        traj.show_mpl_pos(**kwargs)


def _show_mpl_heatmap(exec_name, trajectory_list, **kwargs):
    """Produces a matplotlib plot of the trajectory"""
    for traj in trajectory_list:
        traj.show_mpl_heatmap(**kwargs)


def _show_ase(exec_name, structure_list):
    """Plugin to show the structure with the ASE visualizer"""
    try:
        from ase.visualize import view

        for structure in structure_list:
            view(structure.get_ase())
    except ImportError:
        raise


def _show_vesta(exec_name, structure_list):
    """Plugin for VESTA
    This VESTA plugin was added by Yue-Wen FANG and Abel Carreras
    at Kyoto University in the group of Prof. Isao Tanaka's lab

    """
    import subprocess
    import tempfile

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
    """Plugin for vmd"""
    import subprocess
    import tempfile

    if len(structure_list) > 1:
        raise MultipleObjectsError('Visualization of multiple objects is not implemented')
    structure = structure_list[0]

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
    """Plugin for showing the bands with the XMGrace plotting software."""
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
            text, _ = bnds._exportcontent(
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
