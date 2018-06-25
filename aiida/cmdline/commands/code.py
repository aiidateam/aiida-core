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
import click
import tabulate

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, verdi_code
from aiida.cmdline.params import options, arguments
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.utils.multi_line_input import edit_pre_post
from aiida.control.code import CodeBuilder

#def cmdline_fill(attributes, store, print_header=True):
#    import inspect
#    import readline
#    from aiida.common.exceptions import ValidationError
#
#    if print_header:
#        print "At any prompt, type ? to get some help."
#        print "---------------------------------------"
#
#    for internal_name, name, desc, multiline in (attributes):
#
#        getter_name = '_get_{}_string'.format(internal_name)
#        try:
#            getter = dict(inspect.getmembers(store))[getter_name]
#        except KeyError:
#            print >> sys.stderr, ("Internal error! " "No {} getter defined in Computer".format(getter_name))
#            sys.exit(1)
#        previous_value = getter()
#
#        setter_name = '_set_{}_string'.format(internal_name)
#        try:
#            setter = dict(inspect.getmembers(store))[setter_name]
#        except KeyError:
#            print >> sys.stderr, ("Internal error! " "No {} setter defined in Computer".format(setter_name))
#            sys.exit(1)
#
#        valid_input = False
#        while not valid_input:
#            if multiline:
#                newlines = []
#                print "=> {}: ".format(name)
#                print "   # This is a multiline input, press CTRL+D on a"
#                print "   # empty line when you finish"
#
#                try:
#                    for l in previous_value.splitlines():
#                        while True:
#                            readline.set_startup_hook(lambda: readline.insert_text(l))
#                            input_txt = raw_input()
#                            if input_txt.strip() == '?':
#                                print ["  > {}".format(descl) for descl in "HELP: {}".format(desc).split('\n')]
#                                continue
#                            else:
#                                newlines.append(input_txt)
#                                break
#
#                    # Reset the hook (no default text printed)
#                    readline.set_startup_hook()
#
#                    print "   # ------------------------------------------"
#                    print "   # End of old input. You can keep adding     "
#                    print "   # lines, or press CTRL+D to store this value"
#                    print "   # ------------------------------------------"
#
#                    while True:
#                        input_txt = raw_input()
#                        if input_txt.strip() == '?':
#                            print "\n".join(["  > {}".format(descl) for descl in "HELP: {}".format(desc).split('\n')])
#                            continue
#                        else:
#                            newlines.append(input_txt)
#                except EOFError:
#                    # Ctrl+D pressed: end of input.
#                    pass
#
#                input_txt = "\n".join(newlines)
#
#            else:  # No multiline
#                readline.set_startup_hook(lambda: readline.insert_text(previous_value))
#                input_txt = raw_input("=> {}: ".format(name))
#                if input_txt.strip() == '?':
#                    print "HELP:", desc
#                    continue
#
#            try:
#                setter(input_txt)
#                valid_input = True
#            except ValidationError as e:
#                print >> sys.stderr, "Invalid input: {}".format(e.message)
#                print >> sys.stderr, "Enter '?' for help".format(e.message)

#class CodeInputValidationClass(object):
#    """
#    A class with information for the validation of input text of Codes
#    """
#    # It is a list of tuples. Each tuple has three elements:
#    # 1. an internal name (used to find the
#    # _set_internalname_string, and get_internalname_string methods)
#    # 2. a short human-readable name
#    # 3. A long human-readable description
#    # 4. True if it is a multi-line input, False otherwise
#    # IMPORTANT!
#    # for each entry, remember to define the
#    # _set_internalname_string and get_internalname_string methods.
#    # Moreover, the _set_internalname_string method should also immediately
#    # validate the value.
#
#    #pylint: disable=no-self-use
#    _conf_attributes_relabel = [
#        (
#            "label",
#            "Label",
#            "A label to refer to this code",
#            False,
#        ),
#        (
#            "description",
#            "Description",
#            "A human-readable description of this code",
#            False,
#        ),
#    ]
#    _conf_attributes_start = [
#        (
#            "label",
#            "Label",
#            "A label to refer to this code",
#            False,
#        ),
#        (
#            "description",
#            "Description",
#            "A human-readable description of this code",
#            False,
#        ),
#        (
#            "is_local",
#            "Local",
#            "True or False; if True, then you have to provide a folder with "
#            "files that will be stored in AiiDA and copied to the remote "
#            "computers for every calculation submission. If True, the code "
#            "is just a link to a remote computer and an absolute path there",
#            False,
#        ),
#        (
#            "input_plugin",
#            "Default input plugin",
#            "A string of the default input plugin to be used with this code "
#            "that is recognized by the CalculationFactory. Use the "
#            "'verdi calculation plugins' command to get the list of existing"
#            "plugins",
#            False,
#        ),
#    ]
#    _conf_attributes_local = [
#        (
#            "folder_with_code",
#            "Folder with the code",
#            "The folder on your local computer in which there are the files to be "
#            "stored in the AiiDA repository and then copied over for every "
#            "submitted calculation",
#            False,
#        ),
#        (
#            "local_rel_path",
#            "Relative path of the executable",
#            "The relative path of the executable file inside the folder entered "
#            "in the previous step",
#            False,
#        ),
#    ]
#    _conf_attributes_remote = [
#        (
#            "computer",
#            "Remote computer name",
#            "The computer name as on which the code resides, as stored in the "
#            "AiiDA database",
#            False,
#        ),
#        (
#            "remote_abs_path",
#            "Remote absolute path",
#            "The (full) absolute path on the remote machine",
#            False,
#        ),
#    ]
#    _conf_attributes_end = [
#        (
#            "prepend_text",
#            "Text to prepend to each command execution\n"
#            "FOR INSTANCE, MODULES TO BE LOADED FOR THIS CODE",
#            "This is a multiline string, whose content will be prepended inside\n"
#            "the submission script before the real execution of the job. It is\n"
#            "your responsibility to write proper bash code!",
#            True,
#        ),
#        (
#            "append_text",
#            "Text to append to each command execution",
#            "This is a multiline string, whose content will be appended inside\n"
#            "the submission script after the real execution of the job. It is\n"
#            "your responsibility to write proper bash code!",
#            True,
#        ),
#    ]
#
#    label = ""
#
#    def _get_label_string(self):
#        return self.label
#
#    def _set_label_string(self, string):
#        """
#        Set the label starting from a string.
#        """
#        self._label_validator(string)
#        self.label = string
#
#    def _label_validator(self, label):
#        """
#        Validates the label.
#        """
#        from aiida.common.exceptions import ValidationError
#
#        if not label.strip():
#            raise ValidationError("No label specified")
#
#        if "@" in label:
#            raise ValidationError("Can not use '@' in label")
#
#    description = ""
#
#    def _get_description_string(self):
#        return self.description
#
#    def _set_description_string(self, string):
#        """
#        Set the description starting from a string.
#        """
#        self._description_validator(string)
#        self.description = string
#
#    def _description_validator(self, folder_with_code):
#        """
#        Validates the folder_with_code.
#        """
#        pass
#
#    folder_with_code = ""
#
#    def _get_folder_with_code_string(self):
#        return self.folder_with_code
#
#    def _set_folder_with_code_string(self, string):
#        """
#        Set the folder_with_code starting from a string.
#        """
#        self._folder_with_code_validator(string)
#        self.folder_with_code = string
#
#    def _folder_with_code_validator(self, folder_with_code):
#        """
#        Validates the folder_with_code.
#        """
#        import os.path
#        from aiida.common.exceptions import ValidationError
#
#        if not os.path.isdir(folder_with_code):
#            raise ValidationError("'{}' is not a valid directory".format(folder_with_code))
#
#    local_rel_path = ""
#
#    def _get_local_rel_path_string(self):
#        return self.local_rel_path
#
#    def _set_local_rel_path_string(self, string):
#        """
#        Set the local_rel_path starting from a string.
#        """
#        self._local_rel_path_validator(string)
#        self.local_rel_path = string
#
#    def _local_rel_path_validator(self, local_rel_path):
#        """
#        Validates the local_rel_path.
#        """
#        import os.path
#        from aiida.common.exceptions import ValidationError
#
#        if not os.path.isfile(os.path.join(self.folder_with_code, local_rel_path)):
#            raise ValidationError("'{}' is not a valid file within '{}'".format(local_rel_path, self.folder_with_code))
#
#    computer = None
#
#    def _get_computer_string(self):
#        if self.computer is None:
#            return ""
#        else:
#            return self.computer.name
#
#    def _set_computer_string(self, string):
#        """
#        Set the computer starting from a string.
#        """
#        from aiida.common.exceptions import ValidationError, NotExistent
#        from aiida.orm import Computer as AiidaOrmComputer
#
#        try:
#            computer = AiidaOrmComputer.get(string)
#        except NotExistent:
#            raise ValidationError("Computer with name '{}' not found in " "DB".format(string))
#
#        self._computer_validator(computer)
#        self.computer = computer
#
#    def _computer_validator(self, computer):
#        """
#        Validates the computer.
#        """
#        from aiida.common.exceptions import ValidationError
#        from aiida.orm import Computer as AiidaOrmComputer
#
#        if not isinstance(computer, AiidaOrmComputer):
#            raise ValidationError("The computer is not a valid Computer instance")
#
#    remote_abs_path = ""
#
#    def _get_remote_abs_path_string(self):
#        return self.remote_abs_path
#
#    def _set_remote_abs_path_string(self, string):
#        """
#        Set the remote_abs_path starting from a string.
#        """
#        self._remote_abs_path_validator(string)
#        self.remote_abs_path = string
#
#    def _remote_abs_path_validator(self, remote_abs_path):
#        """
#        Validates the remote_abs_path.
#        """
#        from aiida.common.exceptions import ValidationError
#        import os.path
#
#        if not os.path.isabs(remote_abs_path):
#            raise ValidationError("This is not a valid absolute path")
#        if not os.path.split(remote_abs_path)[1]:
#            raise ValidationError("This is a folder, not an executable")
#
#    is_local = False
#
#    def _get_is_local_string(self):
#        return "True" if self.is_local else "False"
#
#    def _set_is_local_string(self, string):
#        """
#        Set the is_local starting from a string.
#        """
#        from aiida.common.exceptions import ValidationError
#
#        upper_string = string.upper()
#        if upper_string in ['YES', 'Y', 'T', 'TRUE']:
#            is_local = True
#        elif upper_string in ['NO', 'N', 'F', 'FALSE']:
#            is_local = False
#        else:
#            raise ValidationError("Invalid value '{}' for the is_local variable, must " "be a boolean".format(string))
#
#        self._is_local_validator(is_local)
#        self.is_local = is_local
#
#    def _is_local_validator(self, is_local):
#        """
#        Validates the is_local.
#        """
#        from aiida.common.exceptions import ValidationError
#
#        if not isinstance(is_local, bool):
#            raise ValidationError("Invalid value '{}' for the is_local variable, must "
#                                  "be a boolean".format(str(is_local)))
#
#    input_plugin = None
#
#    def _get_input_plugin_string(self):
#        """
#        Return the input plugin string
#        """
#        return self.input_plugin
#
#    def _set_input_plugin_string(self, string):
#        """
#        Set the input_plugin starting from a string.
#        """
#        input_plugin = string.strip()
#
#        if input_plugin.lower == "none":
#            input_plugin = None
#
#        self._input_plugin_validator(input_plugin)
#        self.input_plugin = input_plugin
#
#    def _input_plugin_validator(self, input_plugin):
#        """
#        Validates the input_plugin, checking it is in the list of existing plugins.
#        """
#        from aiida.common.exceptions import ValidationError
#        from aiida.plugins.entry_point import get_entry_point_names
#
#        if input_plugin is None:
#            return
#
#        if input_plugin not in get_entry_point_names('aiida.calculations'):
#            raise ValidationError("Invalid value '{}' for the input_plugin "
#                                  "variable, it is not among the existing plugins".format(str(input_plugin)))
#
#    prepend_text = ""
#
#    def create_code(self):
#        """
#        Create a code with the information contained in this class,
#        BUT DOES NOT STORE IT.
#        """
#        import os.path
#        from aiida.orm import Code as AiidaOrmCode
#
#        if self.is_local:
#            file_list = [
#                os.path.realpath(os.path.join(self.folder_with_code, f)) for f in os.listdir(self.folder_with_code)
#            ]
#            code = AiidaOrmCode(local_executable=self.local_rel_path, files=file_list)
#        else:
#            code = AiidaOrmCode(remote_computer_exec=(self.computer, self.remote_abs_path))
#
#        code.label = self.label
#        code.description = self.description
#        code.set_input_plugin_name(self.input_plugin)
#        code.set_prepend_text(self.prepend_text)
#        code.set_append_text(self.append_text)
#
#        return code
#
#    #     def load_from_code(self, code):
#    #         from aiida.orm import Code as AiidaOrmCode
#    #
#    #         if not isinstance(code, AiidaOrmCode):
#    #             raise ValueError("code is not a valid Code instance")
#    #
#    #         self.label = code.label
#    #         self.description = code.description
#    #         # Add here also the input_plugin stuff
#    #         self.is_local = code.is_local()
#    #         if self.is_local:
#    #             raise NotImplementedError
#    #         else:
#    #             self.computer = code.get_remote_computer()
#    #             self.remote_abs_path = code.get_remote_exec_path()
#    #         self.prepend_text = code.get_prepend_text()
#    #         self.append_text = code.get_append_text()
#
#    def set_and_validate_from_code(self, kwargs):
#        """
#        This method is used by the Code Orm, for the utility to setup a new code
#        from the verdi shell
#        """
#        from aiida.common.exceptions import ValidationError
#
#        # convert to string so I can use all the functionalities of the command line
#        kwargs = {k: str(v) for k, v in kwargs.iteritems()}
#
#        start_var = [_[0] for _ in self._conf_attributes_start]
#        local_var = [_[0] for _ in self._conf_attributes_local]
#        remote_var = [_[0] for _ in self._conf_attributes_remote]
#        end_var = [_[0] for _ in self._conf_attributes_end]
#
#        def internal_launch(self, x, kwargs):
#            default_values = {k: getattr(self, '_get_{}_string'.format(k))() for k in x}
#            setup_keys = [[k, kwargs.pop(k, default_values[k])] for k in x]
#            #            for k,v in setup_keys:
#            #                setattr(self,k,v)
#            [getattr(self, '_set_{}_string'.format(k))(v) for k, v in setup_keys]
#
#            return kwargs
#
#        kwargs = internal_launch(self, start_var, kwargs)
#
#        if self.is_local:
#            kwargs = internal_launch(self, local_var, kwargs)
#        else:
#            print 'called remote', remote_var
#            kwargs = internal_launch(self, remote_var, kwargs)
#
#        kwargs = internal_launch(self, end_var, kwargs)
#
#        print kwargs
#
#        if kwargs:
#            raise ValidationError("Some parameters were not " "recognized: {}".format(kwargs))
#        return self.create_code()
#
#    def ask(self):
#        cmdline_fill(self._conf_attributes_start, store=self)
#        if self.is_local:
#            cmdline_fill(self._conf_attributes_local, store=self, print_header=False)
#        else:
#            cmdline_fill(self._conf_attributes_remote, store=self, print_header=False)
#        cmdline_fill(self._conf_attributes_end, store=self, print_header=False)


class Code(VerdiCommandWithSubcommands):
    """
    Setup and manage codes.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        super(Code, self).__init__()
        self.valid_subcommands = {
            'list': (self.cli, self.complete_none),
            'show': (self.cli, self.complete_none),
            'setup': (self.cli, self.complete_none),
            'rename': (self.cli, self.complete_none),
            'relabel': (self.cli, self.complete_none),
            'update': (self.cli, self.complete_none),
            'delete': (self.cli, self.complete_none),
            'hide': (self.cli, self.complete_none),
            'reveal': (self.cli, self.complete_none),
        }

    def cli(self, *args):  # pylint: disable=unused-argument,no-self-use
        verdi.main()

    # pylint: disable=fixme
    #TODO: This may be partly used in verdi code duplicate
    #@classmethod
    #def code_update(self, *args):
    #    import datetime
    #    from aiida.orm.backend import construct_backend

    #    backend = construct_backend()

    #    if len(args) != 1:
    #        print >> sys.stderr, ("after 'code update' there should be one "
    #                              "argument only, being the code id.")
    #        sys.exit(1)

    #    code = self.get_code(args[0])

    #    if code.has_children:
    #        print "***********************************"
    #        print "|                                 |"
    #        print "|            WARNING!             |"
    #        print "| Consider to create another code |"
    #        print "| You risk of losing the history  |"
    #        print "|                                 |"
    #        print "***********************************"

    #    # load existing stuff
    #    set_params = CodeInputValidationClass()
    #    set_params.label = code.label
    #    set_params.description = code.description
    #    set_params.input_plugin = code.get_input_plugin_name()

    #    was_local_before = code.is_local()
    #    set_params.is_local = code.is_local()

    #    if code.is_local():
    #        set_params.local_rel_path = code.get_local_executable()
    #        # I don't have saved the folder with code, so I will just have the list of files
    #        # file_list = [ code._get_folder_pathsubfolder.get_abs_path(i)
    #        #    for i in code.get_folder_list() ]
    #    else:
    #        set_params.computer = code.get_computer()
    #        set_params.remote_abs_path = code.get_remote_exec_path()

    #    set_params.prepend_text = code.get_prepend_text()
    #    set_params.append_text = code.get_append_text()

    #    # ask for the new values
    #    set_params.ask()

    #    # prepare a comment containing the previous version of the code
    #    now = datetime.datetime.now()
    #    new_comment = []
    #    new_comment.append("Code modified on {}".format(now))
    #    new_comment.append("Old configuration was:")
    #    new_comment.append("label: {}".format(code.label))
    #    new_comment.append("description: {}".format(code.description))
    #    new_comment.append("input_plugin_name: {}".format(code.get_input_plugin_name()))
    #    new_comment.append("is_local: {}".format(code.is_local()))
    #    if was_local_before:
    #        new_comment.append("local_executable: {}".format(code.get_local_executable()))
    #    else:
    #        new_comment.append("computer: {}".format(code.get_computer()))
    #        new_comment.append("remote_exec_path: {}".format(code.get_remote_exec_path()))
    #    new_comment.append("prepend_text: {}".format(code.get_prepend_text()))
    #    new_comment.append("append_text: {}".format(code.get_append_text()))
    #    comment = "\n".join(new_comment)

    #    if set_params.is_local:
    #        print "WARNING: => Folder with the code, and"
    #        print "         => Relative path of the executable, "
    #        print "         will be ignored! It is not possible to replace "
    #        print "         the scripts, you have to create a new code for that."
    #    else:
    #        if was_local_before:
    #            # some old files will be left in the repository, and I cannot delete them
    #            print >> sys.stderr, ("It is not possible to change a "
    #                                  "code from local to remote.\n"
    #                                  "Modification cancelled.")
    #            sys.exit(1)
    #        print "WARNING: => computer"
    #        print "         will be ignored! It is not possible to replace it"
    #        print "         you have to create a new code for that."

    #    code.label = set_params.label
    #    code.description = set_params.description
    #    code.set_input_plugin_name(set_params.input_plugin)
    #    code.set_prepend_text(set_params.prepend_text)
    #    code.set_append_text(set_params.append_text)

    #    if not was_local_before:
    #        if set_params.remote_abs_path != code.get_remote_exec_path():
    #            print "Are you sure about changing the path of the code?"
    #            print "This operation may imply loss of provenance."
    #            print "[Enter] to continue, [Ctrl + C] to exit"
    #            raw_input()

    #            from aiida.backends.djsite.db.models import DbAttribute

    #            DbAttribute.set_value_for_node(code.dbnode, 'remote_exec_path', set_params.remote_abs_path)

    #    # store comment, to track history
    #    code.add_comment(comment, user=backend.users.get_automatic_user())


def is_on_computer(ctx):
    return bool(ctx.params.get('on_computer'))


def is_not_on_computer(ctx):
    return bool(not is_on_computer(ctx))


def ensure_scripts(pre, post, summary):
    if (not pre) or (not post):
        return edit_pre_post(pre, post, summary)
    return pre, post


@verdi_code.command('setup')
@options.LABEL(prompt='Label', cls=InteractiveOption)
@options.DESCRIPTION(prompt='Description', cls=InteractiveOption)
@click.option(
    '--on-computer/--store-upload',
    is_eager=False,
    default=True,
    prompt='Installed on remote Computer?',
    cls=InteractiveOption)
@options.INPUT_PLUGIN(prompt='Default input plugin', cls=InteractiveOption)
@options.COMPUTER(prompt='Remote computer', cls=InteractiveOption, required_fn=is_on_computer, prompt_fn=is_on_computer)
@click.option(
    '--remote-abs-path',
    prompt='Remote path',
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    type=click.Path(file_okay=True),
    cls=InteractiveOption,
    help=('[if --on-computer]: the (full) absolute path on the remote machine'))
@click.option(
    '--code-folder',
    prompt='Folder containing the code',
    type=click.Path(file_okay=False, exists=True, readable=True),
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    cls=InteractiveOption,
    help=(
        '[if --store-upload]: folder containing the executable and all other files necessary for execution of the code')
)
@click.option(
    '--code-rel-path',
    prompt='Relative path of the executable',
    type=click.Path(dir_okay=False),
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    cls=InteractiveOption,
    help=('[if --store-upload]: the relative path of the executable file ' + \
          'inside the folder entered in the previous step or in --code-folder'))
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
        # pylint: disable=protected-access
        code._reveal()  # newly setup code shall not be hidden
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
            echo.echo_critical(exc.message)

        echo.echo_success("Code '{}' deleted.".format(code.pk))


@verdi_code.command()
@arguments.CODES()
@with_dbenv()
def hide(codes):
    """
    Hide one or more codes from the verdi show command
    """
    for code in codes:
        # pylint: disable=protected-access
        code._hide()
        echo.echo_success("Code '{}' hidden.".format(code.pk))


@verdi_code.command()
@arguments.CODES()
@with_dbenv()
def reveal(codes):
    """
    Reveal one or more hidden codes to the verdi show command
    """
    for code in codes:
        # pylint: disable=protected-access
        code._reveal()
        echo.echo_success("Code '{}' revealed.".format(code.pk))


@verdi_code.command()
@arguments.CODE()
@with_dbenv()
# pylint: disable=unused-argument
def update(code):
    """
    Update an existing code.

    Warning: This function is deprecated, since updating existing codes breaks data proevenance.
    Use 'duplicate' instead.
    """
    echo.echo_deprecated("Please use 'duplicate' instead.", exit=True)


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
    old_label = code.get_label(full=True)
    code.relabel(new_label)

    echo.echo_success("Relabeled code with ID={} from '{}' to '{}'".format(
        code.pk, old_label, code.get_label(full=True)))


@verdi_code.command()
@arguments.CODE('OLD_LABEL')
@arguments.LABEL('NEW_LABEL')
@with_dbenv()
@click.pass_context
# pylint: disable=unused-argument
def rename(ctx, old_label, new_label):
    """
    Rename a code (change its label).
    """
    echo.echo_deprecated("Use 'relabel' instead")
    ctx.forward(relabel)


@verdi_code.command('list')
@options.COMPUTER(help="Filter codes by computer")
@options.INPUT_PLUGIN(help="Filter codes by calculation input plugin.")
@options.ALL(help="Include hidden codes.")
@options.ALL_USERS(help="Include codes from all users.")
@click.option('-o', '--show-owner', 'show_owner', is_flag=True, default=False, help='Show owners of codes.')
@with_dbenv()
# pylint: disable=redefined-builtin
def code_list(computer, input_plugin, all, all_users, show_owner):
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

    # If not all, hide codes with HIDDEN_KEY extra set to True
    if not all:
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
    if qb_query.count > 0:
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
