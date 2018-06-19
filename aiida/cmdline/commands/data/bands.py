# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys
import click
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.commands.data.list import _list
from aiida.cmdline.commands import verdi, verdi_data
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.exceptions import DanglingLinkError
from aiida.orm.data.array.bands import BandsData
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.common.utils import Prettifier

if not is_dbenv_loaded():
    load_dbenv()

def show_xmgrace(exec_name, list_bands):
    """
    Plugin for show the bands with the XMGrace plotting software.
    """
    import tempfile, subprocess, numpy
    from aiida.orm.data.array.bands import max_num_agr_colors

    list_files = []
    current_band_number = 0
    for iband, bands in enumerate(list_bands):
        # extract number of bands
        nbnds = bands.get_bands().shape[1]
        text, _ = bands._exportstring('agr', setnumber_offset=current_band_number,
                                        color_number=numpy.mod(iband + 1, max_num_agr_colors))
        # write a tempfile
        f = tempfile.NamedTemporaryFile(suffix='.agr')
        f.write(text)
        f.flush()
        list_files.append(f)
        # update the number of bands already plotted
        current_band_number += nbnds

    try:
        subprocess.check_output([exec_name] + [f.name for f in list_files])
        _ = [f.close() for f in list_files]
    except subprocess.CalledProcessError:
        print "Note: the call to {} ended with an error.".format(
            exec_name)
        _ = [f.close() for f in list_files]
    except OSError as e:
        _ = [f.close() for f in list_files]
        if e.errno == 2:
            print ("No executable '{}' found. Add to the path, "
                    "or try with an absolute path.".format(
                exec_name))
            sys.exit(1)
        else:
            raise


@verdi_data.group('bands')
@click.pass_context
def bands(ctx):
    """
    Manipulation on the bands
    """
    pass


@bands.command('show')
@arguments.NODES()
@click.option('-f', '--format', 'format',
              type=click.Choice(['xmgrace', 'gnuplot']),
              default='xmgrace',
              help="Filter the families only to those containing "
              "a pseudo for each of the specified elements")
def show(nodes, format):
    """
    Visualize bands object
    """
    default_database = None
    from aiida.orm import load_node
    for n in nodes:
        try:
            if not isinstance(n, BandsData):
                echo.echo_critical("Node {} is of class {} instead "
                                   "of {}".format(n, type(n), BandsData))
        except AttributeError:
            pass
    
    show_xmgrace(format, n_list)


@bands.command('list')
@click.option('-e', '--elements', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Print all bandsdatas from structures "
              "containing desired elements")
@click.option('-eo', '--elements-only', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Print all bandsdatas from structures "
              "containing only the selected elements")
@click.option('-f', '--formulamode',
              type=click.Choice(['hill', 'hill_compact', 'reduce', 'group', 'count', 'count_compact']),
              default='hill',
              help="Formula printing mode (if None, does not print the formula)")
@click.option('-p', '--past-days', type=click.INT,
              default=None,
              help="Add a filter to show only bandsdatas"
              " created in the past N days")
@options.GROUPS()
@click.option('-A', '--all-users', is_flag=True, default=False,
              help="show groups for all users, rather than only for the"
              "current user")
def list_bands(elements, elements_only, formulamode, past_days, groups, all_users):
    """
    List stored BandData objects
    """
    project = ['ID', 'Ctime', 'Label', 'Formula']
    _list(BandsData, project, elements, elements_only, formulamode, past_days, groups, all_users)



@bands.command('export')
@click.option('-y', '--format',
              type=click.Choice(['xmgrace', 'gnuplot'])
              help="Type of the exported file.")
@click.option('--y-min-lim', type=click.FLOAT,
              default=None,
              help='The minimum value for the y axis.'
              ' Default: minimum of all bands')
@click.option('--y-max-lim', type=click.FLOAT,
              default=None,
              help='The maximum value for the y axis.'
              ' Default: maximum of all bands')
@click.option('-o', '--output', type=click.STRING,
              default=None,
              help="If present, store the output directly on a file "
              "with the given name. It is essential to use this option "
              "if more than one file needs to be created.")
@options.FORCE(help="If passed, overwrite files without checking.")
@click.option('--prettify-format', default=None,
                type=click.Choice(Prettifier.get_prettifiers()),
                help='The style of labels for the prettifier')
@arguments.NODE()
def export(prettify_format, y_min_lim, y_max_lim, output, force, node):
    """
    Export bands
    """
    print 1


