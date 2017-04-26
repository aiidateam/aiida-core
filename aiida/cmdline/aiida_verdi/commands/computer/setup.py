# -*- coding: utf8 -*-
"""
verdi computer setup command
"""
import click
import sys

from aiida_verdi.verdic_utils import load_dbenv_if_not_loaded
from aiida_verdi import options
from aiida_verdi.utils.interactive import InteractiveOption
from aiida_verdi.utils.aiidadb import comp_not_exists
from aiida_verdi.param_types.plugin import PluginParam
from aiida_verdi.utils.aiidadb import aiida_dbenv


@aiida_dbenv
def scheduler_accepts_ppm(ctx):
    from aiida.scheduler import SchedulerFactory
    sched = SchedulerFactory(ctx.params['scheduler'])
    jrcls = sched._job_resource_class
    return jrcls.accepts_default_mpiprocs_per_machine()


@click.command()
@options.label(prompt='Label', cls=InteractiveOption, callback=comp_not_exists, help='The name for this Computer')
@options.description(prompt='Description', cls=InteractiveOption)
@click.option('--hostname', prompt='Fully-qualified hostname', cls=InteractiveOption, help='The fully qualified host name of this computer')
@click.option('--enabled/--disabled', default=True, prompt='Enabled', cls=InteractiveOption, help=('if disabled, calculations associated with this computer' 'will not be submitted'))
@click.option('--transport', prompt='Transport type', cls=InteractiveOption, type=PluginParam(category='transports'), help='Transport to be used')
@click.option('--scheduler', prompt='Scheduler type', cls=InteractiveOption, type=PluginParam(category='schedulers'), help='Scheduler to be used')
@click.option('--workdir', prompt='AiiDA work directory', cls=InteractiveOption, type=click.Path(), help='Absolute path on the computer. AiiDA will run all calculations under that directory (typically on the scratch file system). {username} will be replaced by your username on the remote computer')
@click.option('--mpirun', prompt='mpirun command', cls=InteractiveOption, help='The mpirun command to be used on the computer to run MPI programs. {tot_num_mpiprocs} will be replaced by the total number of cpus. See the scheduler docs for more replacement fields.')
@click.option('--ppm', '--default-mpiprocs-per-machine', 'ppm', required_fn=scheduler_accepts_ppm, prompt='Default number of CPUs per machine, only necessary for some schedulers', cls=InteractiveOption, type=int, empty_ok=True, help='Default number of CPUs per machine (node) to be used if nothing else specified. Leave empty if you do not want to provide a default value')
@options.prepend_text()
@options.append_text()
@options.non_interactive()
@options.dry_run()
def setup(dry_run=None, non_interactive=None, **kwargs):
    """
    add compute resources
    """
    from aiida.common.exceptions import ValidationError
    from aiida_verdi.utils.aiidadb import create_computer
    load_dbenv_if_not_loaded()

    pre = kwargs['prepend_text'] or ''
    post = kwargs['append_text'] or ''
    if (not non_interactive) and ((not pre) or (not post)):
        '''let the user edit the pre and post execution scripts'''
        from aiida_verdi.utils.mlinput import edit_pre_post
        pre, post = edit_pre_post(pre, post, kwargs)
        kwargs['prepend_text'] = pre
        kwargs['append_text'] = post

    computer = create_computer(**kwargs)
    click.echo('Creating new computer with name "{}"'.format(kwargs['label']))
    if not dry_run:
        try:
            computer.store()
            click.echo('Computer "{}" successfully stored.'.format(kwargs['label']))
            click.echo('pk: {}, uuid: {}'.format(computer.pk, computer.uuid))
            click.echo('Note: before using it with AiiDA, configure it using the command')
            click.echo('  verdi computer configure {}'.format(computer.name))
            click.echo('(Note: machine dependent transport parameters cannot be set via ')
            click.echo('the command-line interface at the moment)')
        except ValidationError as e:
            raise click.ClickException('Unable to store computer: {}. Exiting...'.format(e.message))
    else:
        click.echo('Computer "{}" successfully created.'.format(kwargs['label']))
        click.echo(computer.full_text_info)
        click.echo('recieved --dry-run, the computer will not be stored')
