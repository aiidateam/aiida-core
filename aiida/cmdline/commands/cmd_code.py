# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi code` command."""
from collections import defaultdict
from functools import partial

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.groups.dynamic import DynamicEntryPointCommandGroup
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.params.options.commands import code as options_code
from aiida.cmdline.utils import echo, echo_tabulate
from aiida.cmdline.utils.decorators import deprecated_command, with_dbenv
from aiida.common import exceptions


@verdi.group('code')
def verdi_code():
    """Setup and manage codes."""


def create_code(ctx: click.Context, cls, non_interactive: bool, **kwargs):  # pylint: disable=unused-argument
    """Create a new `Code` instance."""
    try:
        instance = cls(**kwargs)
    except (TypeError, ValueError) as exception:
        echo.echo_critical(f'Failed to create instance `{cls}`: {exception}')

    try:
        instance.store()
    except exceptions.ValidationError as exception:
        echo.echo_critical(f'Failed to store instance of `{cls}`: {exception}')

    echo.echo_success(f'Created {cls.__name__}<{instance.pk}>')


@verdi_code.group(
    'create',
    cls=DynamicEntryPointCommandGroup,
    command=create_code,
    entry_point_group='aiida.data',
    entry_point_name_filter=r'core\.code\..*'
)
def code_create():
    """Create a new code."""


def get_default(key, ctx):
    """
    Get the default argument using a user instance property
    :param value: The name of the property to use
    :param ctx: The click context (which will be used to get the user)
    :return: The default value, or None
    """
    try:
        value = getattr(ctx.code_builder, key)
        if value == '':
            value = None
    except KeyError:
        value = None

    return value


def get_computer_name(ctx):
    return getattr(ctx.code_builder, 'computer').label


def get_on_computer(ctx):
    return not getattr(ctx.code_builder, 'is_local')()


# pylint: disable=unused-argument
def set_code_builder(ctx, param, value):
    """Set the code spec for defaults of following options."""
    from aiida.orm.utils.builders.code import CodeBuilder
    ctx.code_builder = CodeBuilder.from_code(value)
    return value


# Defining the ``COMPUTER`` option first guarantees that the user is prompted for the computer first. This is necessary
# because the ``LABEL`` option has a callback that relies on the computer being already set. Execution order is
# guaranteed only for the interactive case, however. For the non-interactive case, the callback is called explicitly
# once more in the command body to cover the case when the label is specified before the computer.
@verdi_code.command('setup')
@options_code.ON_COMPUTER()
@options_code.COMPUTER()
@options_code.LABEL()
@options_code.DESCRIPTION()
@options_code.INPUT_PLUGIN()
@options_code.REMOTE_ABS_PATH()
@options_code.FOLDER()
@options_code.REL_PATH()
@options_code.USE_DOUBLE_QUOTES()
@options_code.PREPEND_TEXT()
@options_code.APPEND_TEXT()
@options.NON_INTERACTIVE()
@options.CONFIG_FILE()
@click.pass_context
@with_dbenv()
@deprecated_command('This command will be removed soon, use `verdi code create` instead.')
def setup_code(ctx, non_interactive, **kwargs):
    """Setup a new code."""
    from aiida.orm.utils.builders.code import CodeBuilder

    options_code.validate_label_uniqueness(ctx, None, kwargs['label'])

    if kwargs.pop('on_computer'):
        kwargs['code_type'] = CodeBuilder.CodeType.ON_COMPUTER
    else:
        kwargs['code_type'] = CodeBuilder.CodeType.STORE_AND_UPLOAD

    # Convert entry point to its name
    if kwargs['input_plugin']:
        kwargs['input_plugin'] = kwargs['input_plugin'].name

    code_builder = CodeBuilder(**kwargs)

    try:
        code = code_builder.new()
    except ValueError as exception:
        echo.echo_critical(f'invalid inputs: {exception}')

    try:
        code.store()
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical(f'Unable to store the Code: {exception}')

    echo.echo_success(f'Code<{code.pk}> {code.full_label} created')


@verdi_code.command('test')
@arguments.CODE(callback=set_code_builder)
@with_dbenv()
def code_test(code):
    """Run tests for the given code to check whether it is usable.

    For remote codes the following checks are performed:

     * Whether the remote executable exists.

    """
    from aiida.orm import InstalledCode

    if isinstance(code, InstalledCode):
        try:
            code.validate_filepath_executable()
        except exceptions.ValidationError as exception:
            echo.echo_critical(f'validation failed: {exception}')

    echo.echo_success('all tests succeeded.')


# Defining the ``COMPUTER`` option first guarantees that the user is prompted for the computer first. This is necessary
# because the ``LABEL`` option has a callback that relies on the computer being already set. Execution order is
# guaranteed only for the interactive case, however. For the non-interactive case, the callback is called explicitly
# once more in the command body to cover the case when the label is specified before the computer.
@verdi_code.command('duplicate')
@arguments.CODE(callback=set_code_builder)
@options_code.ON_COMPUTER(contextual_default=get_on_computer)
@options_code.COMPUTER(contextual_default=get_computer_name)
@options_code.LABEL(contextual_default=partial(get_default, 'label'))
@options_code.DESCRIPTION(contextual_default=partial(get_default, 'description'))
@options_code.INPUT_PLUGIN(contextual_default=partial(get_default, 'input_plugin'))
@options_code.REMOTE_ABS_PATH(contextual_default=partial(get_default, 'remote_abs_path'))
@options_code.FOLDER(contextual_default=partial(get_default, 'code_folder'))
@options_code.REL_PATH(contextual_default=partial(get_default, 'code_rel_path'))
@options_code.PREPEND_TEXT(contextual_default=partial(get_default, 'prepend_text'))
@options_code.APPEND_TEXT(contextual_default=partial(get_default, 'append_text'))
@options.NON_INTERACTIVE()
@click.option('--hide-original', is_flag=True, default=False, help='Hide the code being copied.')
@click.pass_context
@with_dbenv()
def code_duplicate(ctx, code, non_interactive, **kwargs):
    """Duplicate a code allowing to change some parameters."""
    from aiida.common.exceptions import ValidationError
    from aiida.orm.utils.builders.code import CodeBuilder

    options_code.validate_label_uniqueness(ctx, None, kwargs['label'])

    if kwargs.pop('on_computer'):
        kwargs['code_type'] = CodeBuilder.CodeType.ON_COMPUTER
    else:
        kwargs['code_type'] = CodeBuilder.CodeType.STORE_AND_UPLOAD

    if kwargs.pop('hide_original'):
        code.is_hidden = True

    # Convert entry point to its name
    if kwargs['input_plugin']:
        kwargs['input_plugin'] = kwargs['input_plugin'].name

    code_builder = ctx.code_builder
    for key, value in kwargs.items():
        setattr(code_builder, key, value)
    new_code = code_builder.new()

    try:
        new_code.store()
        new_code.is_hidden = False
    except ValidationError as exception:
        echo.echo_critical(f'Unable to store the Code: {exception}')

    echo.echo_success(f'Code<{new_code.pk}> {new_code.full_label} created')


@verdi_code.command()
@arguments.CODE()
@with_dbenv()
def show(code):
    """Display detailed information for a code."""
    from aiida.cmdline import is_verbose

    table = []
    table.append(['PK', code.pk])
    table.append(['UUID', code.uuid])
    table.append(['Type', code.entry_point.name])
    for key in code.get_cli_options().keys():
        try:
            table.append([key.capitalize().replace('_', ' '), getattr(code, key)])
        except AttributeError:
            continue
    if is_verbose():
        table.append(['Calculations', len(code.base.links.get_outgoing().all())])

    echo_tabulate(table)


@verdi_code.command()
@arguments.CODE()
@arguments.OUTPUT_FILE(type=click.Path(exists=False))
@with_dbenv()
def export(code, output_file):
    """Export code to a yaml file."""
    import yaml

    code_data = {}

    for key in code.get_cli_options().keys():
        if key == 'computer':
            value = getattr(code, key).label
        else:
            value = getattr(code, key)

        # If the attribute is not set, for example ``with_mpi`` do not export it, because the YAML won't be valid for
        # use in ``verdi code create`` since ``None`` is not a valid value on the CLI.
        if value is not None:
            code_data[key] = str(value)

    with open(output_file, 'w', encoding='utf-8') as yfhandle:
        yaml.dump(code_data, yfhandle)


@verdi_code.command()
@arguments.CODES()
@options.DRY_RUN()
@options.FORCE()
@with_dbenv()
def delete(codes, dry_run, force):
    """Delete a code.

    Note that codes are part of the data provenance, and deleting a code will delete all calculations using it.
    """
    from aiida.tools import delete_nodes

    node_pks_to_delete = [code.pk for code in codes]

    def _dry_run_callback(pks):
        if not pks or force:
            return False
        echo.echo_warning(f'YOU ARE ABOUT TO DELETE {len(pks)} NODES! THIS CANNOT BE UNDONE!')
        return not click.confirm('Shall I continue?', abort=True)

    was_deleted = delete_nodes(node_pks_to_delete, dry_run=dry_run or _dry_run_callback)

    if was_deleted:
        echo.echo_success('Finished deletion.')


@verdi_code.command()
@arguments.CODES()
@with_dbenv()
def hide(codes):
    """Hide one or more codes from `verdi code list`."""
    for code in codes:
        code.is_hidden = True
        echo.echo_success(f'Code<{code.pk}> {code.full_label} hidden')


@verdi_code.command()
@arguments.CODES()
@with_dbenv()
def reveal(codes):
    """Reveal one or more hidden codes in `verdi code list`."""
    for code in codes:
        code.is_hidden = False
        echo.echo_success(f'Code<{code.pk}> {code.full_label} revealed')


@verdi_code.command()
@arguments.CODE()
@arguments.LABEL()
@with_dbenv()
def relabel(code, label):
    """Relabel a code."""
    old_label = code.full_label

    try:
        code.label = label
    except (TypeError, ValueError) as exception:
        echo.echo_critical(f'invalid code label: {exception}')
    else:
        echo.echo_success(f'Code<{code.pk}> relabeled from {old_label} to {code.full_label}')


VALID_PROJECTIONS = {
    'full_label': [('code', 'label'), ('computer', 'label')],
    'entry_point': [('code', 'node_type')],
    'pk': [('code', 'id')],
    'uuid': [('code', 'uuid')],
    'label': [('code', 'label')],
    'default_calc_job_plugin': [('code', 'attributes.input_plugin')],
    'computer': [('computer', 'label')],
    'user': [('user', 'email')],
}


@verdi_code.command('list')
@options.COMPUTER(help='Filter codes by computer.')
@click.option(
    '-d',
    '--default-calc-job-plugin',
    type=types.PluginParamType(group='calculations', load=False),
    help='Filter codes by their optional default calculation job plugin.'
)
@options.ALL(help='Include hidden codes.')
@options.ALL_USERS(help='Include codes from all users.')
@options.PROJECT(type=click.Choice(VALID_PROJECTIONS.keys()), default=['full_label', 'pk', 'entry_point'])
@options.RAW()
@click.option('-o', '--show-owner', 'show_owner', is_flag=True, default=False, help='Show owners of codes.')
@with_dbenv()
def code_list(computer, default_calc_job_plugin, all_entries, all_users, raw, show_owner, project):
    # pylint: disable=too-many-branches,too-many-locals
    """List the available codes."""
    from aiida import orm
    from aiida.orm.utils.node import load_node_class

    if show_owner:
        echo.echo_deprecated(
            'the `-o/--show-owner` option is deprecated. To show the user use the `-P/--project` option instead, e.g., '
            '`verdi code list -P full_label user`.'
        )
        if 'user' not in project:
            project = project + ('user',)

    filters = defaultdict(dict)
    projections = defaultdict(list)

    for key in project:
        for entity, projection in VALID_PROJECTIONS[key]:
            if projection not in projections[entity]:
                projections[entity].append(projection)

    if not all_entries:
        filters['code'][f'extras.{orm.Code.HIDDEN_KEY}'] = {'!==': True}

    if not all_users:
        filters['user']['email'] = orm.User.collection.get_default().email

    if computer is not None:
        filters['computer']['uuid'] = computer.uuid

    if default_calc_job_plugin is not None:
        filters['code']['attributes.input_plugin'] = default_calc_job_plugin.name

    query = orm.QueryBuilder()
    query.append(orm.Code, tag='code', project=projections.get('code', None), filters=filters.get('code', None))
    query.append(
        orm.Computer,
        tag='computer',
        with_node='code',
        project=projections.get('computer', None),
        filters=filters.get('computer', None)
    )
    query.append(
        orm.User,
        tag='user',
        with_node='code',
        project=projections.get('user', None),
        filters=filters.get('user', None)
    )
    query.order_by({'code': {'id': 'asc'}})

    if not query.count():
        echo.echo_report('No codes found matching the specified criteria.')
        return

    table = []
    headers = [projection.replace('_', ' ').capitalize() for projection in project] if not raw else []
    table_format = 'plain' if raw else None

    for result in query.iterdict():
        row = []
        for key in project:
            if key == 'entry_point':
                node_type = result['code']['node_type']
                entry_point = load_node_class(node_type).entry_point
                row.append(entry_point.name)
            else:
                row.append('@'.join(str(result[entity][projection]) for entity, projection in VALID_PROJECTIONS[key]))
        table.append(row)

    echo_tabulate(table, headers=headers, tablefmt=table_format)

    if not raw:
        echo.echo_report('\nUse `verdi code show IDENTIFIER` to see details for a code', prefix=False)
