import click
from aiida.cmdline.utils import echo
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.params.options.multivalue import MultipleValueOption


_show_options = [
    arguments.NODES(),
    click.option('-f', '--format', 'format',
                type=click.Choice(['jmol', 'xcrysden', 'mpl_heatmap', 'mpl_pos']),
                default='jmol',
                help="Type of the visualization format/tool"),
    click.option('--step', type=click.INT,
                default=None,
                help="ID of the trajectory step. If none is supplied, all"
                " steps are explored."),
    click.option('-c', '--contour', type=click.FLOAT,
                cls=MultipleValueOption,
                default=None,
                help="Isovalues to plot"),
    click.option('--sampling-stepsize', type=click.INT,
                default=None,
                help="Sample positions in plot every sampling_stepsize"
                " timestep"),
    click.option('--stepsize', type=click.INT,
                default=None,
                help="The stepsize for the trajectory, set it higher"
                " to reduce number of points"),
    click.option('--mintime', type=click.INT,
                default=None,
                help="The time to plot from"),
    click.option('--maxtime', type=click.INT,
                default=None,
                help="The time to plot to"),
    click.option('-e', '--elements', type=click.STRING,
                cls=MultipleValueOption,
                default=None,
                help="Show only atoms of that species"),
    click.option('--indices', type=click.INT,
                cls=MultipleValueOption,
                default=None,
                help="Show only these indices"),
    click.option('--dont-block', 'block', is_flag=True,
                default=True,
                help="Don't block interpreter when showing plot."),
]

def show_options(func):
    for option in reversed(_show_options):
        func = option(func)

    return func

def _show_jmol(exec_name, trajectory_list, **kwargs):
    """
    Plugin for jmol
    """
    import tempfile, subprocess

    with tempfile.NamedTemporaryFile() as f:
        for trajectory in trajectory_list:
            f.write(trajectory._exportstring('cif', **kwargs)[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(
                exec_name))
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical ("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(
                    exec_name))
            else:
                raise


def _show_xcrysden(exec_name, object_list, **kwargs):
    """
    Plugin for xcrysden
    """
    import tempfile, subprocess

    if len(object_list) > 1:
        raise MultipleObjectsError("Visualization of multiple trajectories "
                                    "is not implemented")
    obj = object_list[0]

    with tempfile.NamedTemporaryFile(suffix='.xsf') as f:
        f.write(obj._exportstring('xsf', **kwargs)[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, '--xsf', f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(
                exec_name))
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(
                    exec_name))
            else:
                raise

def _show_mpl_pos(exec_name, trajectory_list, **kwargs):
    """
    Produces a matplotlib plot of the trajectory
    """
    for t in trajectory_list:
        t.show_mpl_pos(**kwargs)


def _show_mpl_heatmap(exec_name, trajectory_list, **kwargs):
    """
    Produces a matplotlib plot of the trajectory
    """
    for t in trajectory_list:
        t.show_mpl_heatmap(**kwargs)

def _show_ase(exec_name, structure_list):
    """
    Plugin to show the structure with the ASE visualizer
    """
    try:
        from ase.visualize import view
        for structure in structure_list:
            view(structure.get_ase())
    except ImportError:
        raise

def _show_vesta(exec_name, structure_list):
    """
    Plugin for VESTA
    This VESTA plugin was added by Yue-Wen FANG and Abel Carreras
    at Kyoto University in the group of Prof. Isao Tanaka's lab

    """
    import sys
    import tempfile, subprocess

    with tempfile.NamedTemporaryFile(suffix='.cif') as f:
        for structure in structure_list:
            f.write(structure._exportstring('cif')[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(
                exec_name))
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(exec_name))
            else:
                raise

def _show_vmd(exec_name, structure_list):
    """
    Plugin for vmd
    """
    import tempfile, subprocess

    if len(structure_list) > 1:
        raise MultipleObjectsError("Visualization of multiple objects "
                                    "is not implemented")
    structure = structure_list[0]

    with tempfile.NamedTemporaryFile(suffix='.xsf') as f:
        f.write(structure._exportstring('xsf')[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(
                exec_name))
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical ("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(
                    exec_name))
            else:
                raise
