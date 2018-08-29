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
This allows to setup and configure a code from command line.
"""
from __future__ import absolute_import
import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options, arguments, types
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv, deprecated_command
from aiida.cmdline.utils.multi_line_input import ensure_scripts
from aiida.control.code import CodeBuilder


@verdi.group('code')
def verdi_code():
    """Setup and manage codes."""
    pass


def is_on_computer(ctx):
    return bool(ctx.params.get('on_computer'))


def is_not_on_computer(ctx):
    return bool(not is_on_computer(ctx))


@verdi_code.command('setup')
@options.LABEL(prompt='Label', cls=InteractiveOption, help='A label to refer to this code')
@options.DESCRIPTION(prompt='Description', cls=InteractiveOption, help='A human-readable description of this code')
@options.INPUT_PLUGIN(prompt='Default calculation input plugin', cls=InteractiveOption)
@click.option(
    '--on-computer/--store-in-db',
    is_eager=False,
    default=True,
    prompt='Installed on target computer?',
    cls=InteractiveOption)
@options.COMPUTER(
    prompt='Computer',
    cls=InteractiveOption,
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    help='Name of the computer, on which the code resides')
@click.option(
    '--remote-abs-path',
    prompt='Remote absolute path',
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    type=types.AbsolutePathParamType(dir_okay=False),
    cls=InteractiveOption,
    help=('[if --on-computer]: the absolute path to the executable on the remote machine'))
@click.option(
    '--code-folder',
    prompt='Local directory containing the code',
    type=click.Path(file_okay=False, exists=True, readable=True),
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    cls=InteractiveOption,
    help=('[if --store-in-db]: directory the executable and all other files necessary for running it'))
@click.option(
    '--code-rel-path',
    prompt='Relative path of executable inside directory',
    type=click.Path(dir_okay=False),
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    cls=InteractiveOption,
    help=('[if --store-in-db]: relative path of the executable ' + \
          'inside the code-folder'))
@options.PREPEND_TEXT()
@options.APPEND_TEXT()
@options.NON_INTERACTIVE()
@with_dbenv()
def setup_code(non_interactive, **kwargs):
    """Add a Code."""
    from aiida.common.exceptions import ValidationError

    if not non_interactive:
        pre, post = ensure_scripts(kwargs.pop('prepend_text', ''), kwargs.pop('append_text', ''), kwargs)
        kwargs['prepend_text'] = pre
        kwargs['append_text'] = post

    if kwargs.pop('on_computer'):
        kwargs['code_type'] = CodeBuilder.CodeType.ON_COMPUTER
    else:
        kwargs['code_type'] = CodeBuilder.CodeType.STORE_AND_UPLOAD
    code_builder = CodeBuilder(**kwargs)
    code = code_builder.new()

    try:
        code.store()
        code.reveal()  # newly setup code shall not be hidden
    except ValidationError as err:
        echo.echo_critical('unable to store the code: {}. Exiting...'.format(err))

    echo.echo_success('code "{}" stored in DB.'.format(code.label))
    echo.echo_info('pk: {}, uuid: {}'.format(code.pk, code.uuid))


@verdi_code.command()
@arguments.CODE()
@click.option('-v', '--verbose', is_flag=True, help='show additional verbose information')
@with_dbenv()
def show(code, verbose):
    """
    Display information about a Code object identified by CODE_ID which can be the pk or label
    """
    click.echo(tabulate.tabulate(code.full_text_info(verbose)))


@verdi_code.command()
@arguments.CODES()
@with_dbenv()
def delete(codes):
    """
    Delete codes.

    Does not delete codes that are used by calculations
    (i.e., if there are output links)
    """
    from aiida.common.exceptions import InvalidOperation
    from aiida.orm.code import delete_code

    for code in codes:
        try:
            delete_code(code)
        except InvalidOperation as exc:
            echo.echo_critical(str(exc))

        echo.echo_success("Code '{}' deleted.".format(code.pk))


@verdi_code.command()
@arguments.CODES()
@with_dbenv()
def hide(codes):
    """
    Hide one or more codes from the verdi show command
    """
    for code in codes:
        code.hide()
        echo.echo_success("Code '{}' hidden.".format(code.pk))


@verdi_code.command()
@arguments.CODES()
@with_dbenv()
def reveal(codes):
    """
    Reveal one or more hidden codes to the verdi show command
    """
    for code in codes:
        code.reveal()
        echo.echo_success("Code '{}' revealed.".format(code.pk))


@verdi_code.command()
@arguments.CODE()
@with_dbenv()
@deprecated_command("Updating codes breaks data provenance. Use 'duplicate' instead.")
# pylint: disable=unused-argument
def update(code):
    """
    Update an existing code.
    """
    pass


@verdi_code.command()
@arguments.CODE('old_label')
@arguments.LABEL('new_label')
@with_dbenv()
def relabel(old_label, new_label):
    """
    Relabel a code.
    """
    # Note: old_label actually holds a code but we need to
    # specify it that way for the click help message
    code = old_label
    old_label = code.full_label
    code.relabel(new_label)

    echo.echo_success("Relabeled code with ID={} from '{}' to '{}'".format(code.pk, old_label, code.full_label))


@verdi_code.command()
@arguments.CODE('OLD_LABEL')
@arguments.LABEL('NEW_LABEL')
@with_dbenv()
@click.pass_context
@deprecated_command("This command may be removed in a future release. Use 'relabel' instead.")
# pylint: disable=unused-argument
def rename(ctx, old_label, new_label):
    """
    Rename a code (change its label).
    """
    ctx.forward(relabel)


@verdi_code.command('list')
@options.COMPUTER(help="Filter codes by computer")
@options.INPUT_PLUGIN(help="Filter codes by calculation input plugin.")
@options.ALL(help="Include hidden codes.")
@options.ALL_USERS(help="Include codes from all users.")
@click.option('-o', '--show-owner', 'show_owner', is_flag=True, default=False, help='Show owners of codes.')
@with_dbenv()
def code_list(computer, input_plugin, all_entries, all_users, show_owner):
    """List the codes in the database."""
    from aiida.orm.backend import construct_backend
    backend = construct_backend()

    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.code import Code  # pylint: disable=redefined-outer-name
    from aiida.orm.computer import Computer
    from aiida.orm.user import User

    qb_user_filters = dict()
    if not all_users:
        user = backend.users.get_automatic_user()
        qb_user_filters['email'] = user.email

    qb_computer_filters = dict()
    if computer is not None:
        qb_computer_filters['name'] = computer.name

    qb_code_filters = dict()
    if input_plugin is not None:
        qb_code_filters['attributes.input_plugin'] = input_plugin.name

    # If not all_entries, hide codes with HIDDEN_KEY extra set to True
    if not all_entries:
        qb_code_filters['or'] = [{
            'extras': {
                '!has_key': Code.HIDDEN_KEY
            }
        }, {
            'extras.{}'.format(Code.HIDDEN_KEY): {
                '==': False
            }
        }]

    echo.echo("# List of configured codes:")
    echo.echo("# (use 'verdi code show CODEID' to see the details)")

    # pylint: disable=invalid-name
    if computer is not None:
        qb = QueryBuilder()
        qb.append(Code, tag="code", filters=qb_code_filters, project=["id", "label"])
        # We have a user assigned to the code so we can ask for the
        # presence of a user even if there is no user filter
        qb.append(User, creator_of="code", project=["email"], filters=qb_user_filters)
        # We also add the filter on computer. This will automatically
        # return codes that have a computer (and of course satisfy the
        # other filters). The codes that have a computer attached are the
        # remote codes.
        qb.append(Computer, computer_of="code", project=["name"], filters=qb_computer_filters)
        qb.order_by({Code: {'id': 'asc'}})
        print_list_res(qb, show_owner)

    # If there is no filter on computers
    else:
        # Print all codes that have a computer assigned to them
        # (these are the remote codes)
        qb = QueryBuilder()
        qb.append(Code, tag="code", filters=qb_code_filters, project=["id", "label"])
        # We have a user assigned to the code so we can ask for the
        # presence of a user even if there is no user filter
        qb.append(User, creator_of="code", project=["email"], filters=qb_user_filters)
        qb.append(Computer, computer_of="code", project=["name"])
        qb.order_by({Code: {'id': 'asc'}})
        print_list_res(qb, show_owner)

        # Now print all the local codes. To get the local codes we ask
        # the dbcomputer_id variable to be None.
        qb = QueryBuilder()
        comp_non_existence = {"dbcomputer_id": {"==": None}}
        if not qb_code_filters:
            qb_code_filters = comp_non_existence
        else:
            new_qb_code_filters = {"and": [qb_code_filters, comp_non_existence]}
            qb_code_filters = new_qb_code_filters
        qb.append(Code, tag="code", filters=qb_code_filters, project=["id", "label"])
        # We have a user assigned to the code so we can ask for the
        # presence of a user even if there is no user filter
        qb.append(User, creator_of="code", project=["email"], filters=qb_user_filters)
        qb.order_by({Code: {'id': 'asc'}})
        print_list_res(qb, show_owner)


def print_list_res(qb_query, show_owner):
    """Print list of codes."""
    # pylint: disable=invalid-name
    if qb_query.count() > 0:
        for tuple_ in qb_query.all():
            if len(tuple_) == 3:
                (pk, label, useremail) = tuple_
                computername = None
            elif len(tuple_) == 4:
                (pk, label, useremail, computername) = tuple_
            else:
                echo.echo_warning("Wrong tuple size")
                return

            if show_owner:
                owner_string = " ({})".format(useremail)
            else:
                owner_string = ""
            if computername is None:
                computernamestring = ""
            else:
                computernamestring = "@{}".format(computername)
            echo.echo("* pk {} - {}{}{}".format(pk, label, computernamestring, owner_string))
    else:
        echo.echo("# No codes found matching the specified criteria.")
