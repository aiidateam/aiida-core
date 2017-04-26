# -*- coding: utf8 -*-
"""
verdi code setup
"""
import click

from aiida_verdi import options
from aiida_verdi.verdic_utils import create_code
from aiida_verdi.utils.interactive import InteractiveOption


@click.command()
@options.label(prompt='Label', cls=InteractiveOption, help='The name for this code')
@options.description(prompt='Description', cls=InteractiveOption, help='A human-readable description of this code')
@click.option('--installed/--upload', is_eager=False, default=True, prompt='Preinstalled?', cls=InteractiveOption, help=('installed: the executable is installed on the remote computer. ' 'upload: the executable has to be copied onto the computer before execution.'))
@options.input_plugin(prompt='Default input plugin', cls=InteractiveOption)
@click.option('--code-folder', prompt='Folder containing the code', type=click.Path(file_okay=False, exists=True, readable=True), required_fn=lambda c: not c.params.get('installed'), cls=InteractiveOption, help=('[if --upload]: folder containing the executable and ' 'all other files necessary for execution of the code'))
@click.option('--code-rel-path', prompt='Relative path of the executable', type=click.Path(dir_okay=False), required_fn=lambda c: not c.params.get('installed'), cls=InteractiveOption, help=('[if --upload]: The relative path of the executable file inside ' 'the folder entered in the previous step or in --code-folder'))
@options.computer(prompt='Remote computer', cls=InteractiveOption, required_fn=lambda c: c.params.get('installed'), help=('[if --installed]: The name of the computer on which the ' 'code resides as stored in the AiiDA database'))
@options.remote_abs_path(prompt='Remote path', required_fn=lambda c: c.params.get('installed'), cls=InteractiveOption, help=('[if --installed]: The (full) absolute path on the remote ' 'machine'))
@options.prepend_text()
@options.append_text()
@options.non_interactive()
@options.dry_run()
@options.debug()
def setup(non_interactive, dry_run, **kwargs):
    """create and store a code on the commandline"""
    import sys
    from aiida.common.exceptions import ValidationError

    pre = kwargs['prepend_text'] or ''
    post = kwargs['append_text'] or ''
    if (not non_interactive) and ((not pre) or (not post)):
        '''let the user edit the pre and post execution scripts'''
        from aiida_verdi.utils.mlinput import edit_pre_post
        pre, post = edit_pre_post(pre, post, kwargs)
        kwargs['prepend_text'] = pre
        kwargs['append_text'] = post

    '''actually create the code'''
    the_code = create_code(**kwargs)

    '''Enforcing the code to be not hidden.'''
    the_code._reveal()

    '''store or display'''
    if not dry_run:
        '''store'''
        try:
            the_code.store()
        except ValidationError as e:
            print "Unable to store the code: {}. Exiting...".format(e.message)
            sys.exit(1)

        click.echo("Code '{}' successfully stored in DB.".format(the_code.label))
        click.echo("pk: {}, uuid: {}".format(the_code.pk, the_code.uuid))
    else:
        '''dry-run, so only display'''
        click.echo('The following code was created:')
        click.echo(the_code.full_text_info)
        click.echo('Recieved --dry-run, therefore not storing the code')
