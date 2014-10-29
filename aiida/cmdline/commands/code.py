# -*- coding: utf-8 -*-
"""
This allows to setup and configure a code from command line.

TODO: think if we want to allow to change path and prepend/append text.
"""
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

def cmdline_fill(attributes, store, print_header=True):
    import inspect
    import readline
    from aiida.common.exceptions import ValidationError
    
    if print_header:
        print "At any prompt, type ? to get some help."
        print "---------------------------------------"

    for internal_name, name, desc, multiline in (
      attributes):

        getter_name = '_get_{}_string'.format(internal_name)
        try:
            getter = dict(inspect.getmembers(
               store))[getter_name]
        except KeyError:
            print >> sys.stderr, ("Internal error! "
                "No {} getter defined in Computer".format(getter_name))
            sys.exit(1)
        previous_value = getter()
            
        setter_name = '_set_{}_string'.format(internal_name)
        try:
            setter = dict(inspect.getmembers(
               store))[setter_name]
        except KeyError:
            print >> sys.stderr, ("Internal error! "
                "No {} setter defined in Computer".format(setter_name))
            sys.exit(1)
        
        valid_input = False
        while not valid_input:
            if multiline:
                newlines = []
                print "=> {}: ".format(name)
                print "   # This is a multiline input, press CTRL+D on a"
                print "   # empty line when you finish"

                try:
                    for l in previous_value.splitlines():                        
                        while True: 
                            readline.set_startup_hook(lambda:
                                readline.insert_text(l))
                            input_txt = raw_input()
                            if input_txt.strip() == '?':
                                print ["  > {}".format(descl) for descl
                                       in "HELP: {}".format(desc).split('\n')]
                                continue
                            else:
                                newlines.append(input_txt)
                                break
                    
                    # Reset the hook (no default text printed)
                    readline.set_startup_hook()
                    
                    print "   # ------------------------------------------"
                    print "   # End of old input. You can keep adding     "
                    print "   # lines, or press CTRL+D to store this value"
                    print "   # ------------------------------------------"
                    
                    while True: 
                        input_txt = raw_input()
                        if input_txt.strip() == '?':
                            print "\n".join(["  > {}".format(descl) for descl
                                   in "HELP: {}".format(desc).split('\n')])
                            continue
                        else:
                            newlines.append(input_txt)
                except EOFError:
                    #Ctrl+D pressed: end of input.
                    pass
                
                input_txt = "\n".join(newlines)
                
            else: # No multiline
                readline.set_startup_hook(lambda: readline.insert_text(
                    previous_value))
                input_txt = raw_input("=> {}: ".format(name))
                if input_txt.strip() == '?':
                    print "HELP:", desc
                    continue

            try:
                setter(input_txt)
                valid_input = True
            except ValidationError as e:
                print >> sys.stderr, "Invalid input: {}".format(e.message)
                print >> sys.stderr, "Enter '?' for help".format(e.message)


class CodeInputValidationClass(object):
    """
    A class with information for the validation of input text of Codes
    """
    # It is a list of tuples. Each tuple has three elements:
    # 1. an internal name (used to find the 
    #    _set_internalname_string, and get_internalname_string methods)
    # 2. a short human-readable name
    # 3. A long human-readable description
    # 4. True if it is a multi-line input, False otherwise  
    # IMPORTANT!
    # for each entry, remember to define the 
    # _set_internalname_string and get_internalname_string methods.
    # Moreover, the _set_internalname_string method should also immediately
    # validate the value. 
    _conf_attributes_relabel = [
        ("label",
         "Label",
         "A label to refer to this code",
         False,
        ),
        ("description",
         "Description",
         "A human-readable description of this code",
         False,
        ),                        
        ]
    _conf_attributes_start = [
        ("label",
         "Label",
         "A label to refer to this code",
         False,
        ),
        ("description",
         "Description",
         "A human-readable description of this code",
         False,
        ),                        
        ("is_local",
         "Local",
         "True or False; if True, then you have to provide a folder with "
         "files that will be stored in AiiDA and copied to the remote "
         "computers for every calculation submission. If True, the code "
         "is just a link to a remote computer and an absolute path there",
         False,
        ),
        ("input_plugin",
         "Default input plugin",
         "A string of the default input plugin to be used with this code "
         "that is recognized by the CalculationFactory. Use the "
         "'verdi calculation plugins' command to get the list of existing"
         "plugins",
         False,
        ),                              
        ]
    _conf_attributes_local = [
        ("folder_with_code",
         "Folder with the code",
         "The folder on your local computer in which there are the files to be "
         "stored in the AiiDA repository and then copied over for every "
         "submitted calculation",
         False,
         ),
        ("local_rel_path",
         "Relative path of the executable",
         "The relative path of the executable file inside the folder entered "
         "in the previous step",
         False,
         ),
        ]
    _conf_attributes_remote = [
        ("computer",
         "Remote computer name",
         "The computer name as on which the code resides, as stored in the "
         "AiiDA database",
         False,
         ),
        ("remote_abs_path",
         "Remote absolute path",
         "The (full) absolute path on the remote machine",
         False,
         ),
        ]
    _conf_attributes_end = [ 
        ("prepend_text",
         "Text to prepend to each command execution\n"
         "FOR INSTANCE, MODULES TO BE LOADED FOR THIS CODE",
         "This is a multiline string, whose content will be prepended inside\n"
         "the submission script before the real execution of the job. It is\n"
         "your responsibility to write proper bash code!",
         True,
         ),
         ("append_text",
         "Text to append to each command execution",
         "This is a multiline string, whose content will be appended inside\n"
         "the submission script after the real execution of the job. It is\n"
         "your responsibility to write proper bash code!",
         True,
         ),
        ]
    
    label = ""
    
    def _get_label_string(self):
        return self.label

    def _set_label_string(self,string):
        """
        Set the label starting from a string.
        """
        self._label_validator(string)
        self.label = string
        
    def _label_validator(self,label):
        """
        Validates the label.
        """
        from aiida.common.exceptions import ValidationError
    
        if not label.strip():
            raise ValidationError("No label specified")

    description = ""
    
    def _get_description_string(self):
        return self.description

    def _set_description_string(self,string):
        """
        Set the description starting from a string.
        """
        self._description_validator(string)
        self.description = string
        
    def _description_validator(self,folder_with_code):
        """
        Validates the folder_with_code.
        """
        pass

    folder_with_code = ""
    
    def _get_folder_with_code_string(self):
        return self.folder_with_code

    def _set_folder_with_code_string(self,string):
        """
        Set the folder_with_code starting from a string.
        """
        self._folder_with_code_validator(string)
        self.folder_with_code = string
        
    def _folder_with_code_validator(self,folder_with_code):
        """
        Validates the folder_with_code.
        """
        import os.path
        from aiida.common.exceptions import ValidationError
        
        if not os.path.isdir(folder_with_code):
            raise ValidationError("'{}' is not a valid directory".format(
                 folder_with_code))

    local_rel_path = ""
    
    def _get_local_rel_path_string(self):
        return self.local_rel_path

    def _set_local_rel_path_string(self,string):
        """
        Set the local_rel_path starting from a string.
        """
        self._local_rel_path_validator(string)
        self.local_rel_path = string
        
    def _local_rel_path_validator(self,local_rel_path):
        """
        Validates the local_rel_path.
        """
        import os.path
        from aiida.common.exceptions import ValidationError
        
        if not os.path.isfile(os.path.join(self.folder_with_code,
                                           local_rel_path)):
            raise ValidationError("'{}' is not a valid file within '{}'".format(
                 local_rel_path, self.folder_with_code))
            
    computer = None
    
    def _get_computer_string(self):
        if self.computer is None:
            return ""
        else:
            return self.computer.name

    def _set_computer_string(self,string):
        """
        Set the computer starting from a string.
        """
        from aiida.orm import Computer as AiidaOrmComputer
        from aiida.common.exceptions import ValidationError, NotExistent
        load_dbenv()
        
        try:
            computer = AiidaOrmComputer.get(string)
        except NotExistent:
            raise ValidationError("Computer with name '{}' not found in "
                                  "DB".format(string))
        
        self._computer_validator(computer)
        self.computer = computer

    def _computer_validator(self,computer):
        """
        Validates the computer.
        """
        from aiida.common.exceptions import ValidationError
        from aiida.orm import Computer as AiidaOrmComputer
            
        if not isinstance(computer, AiidaOrmComputer):
            raise ValidationError("The computer is not a valid Computer instance")  

    remote_abs_path = ""
    
    def _get_remote_abs_path_string(self):
        return self.remote_abs_path

    def _set_remote_abs_path_string(self,string):
        """
        Set the remote_abs_path starting from a string.
        """
        self._remote_abs_path_validator(string)
        self.remote_abs_path = string
        
    def _remote_abs_path_validator(self,remote_abs_path):
        """
        Validates the remote_abs_path.
        """
        from aiida.common.exceptions import ValidationError
        import os.path
    
        if not os.path.isabs(remote_abs_path):
            raise ValidationError("This is not a valid absolute path")
        if not os.path.split(remote_abs_path)[1]:
            raise ValidationError("This is a folder, not an executable")       

    is_local = False
    
    def _get_is_local_string(self):
        return "True" if self.is_local else "False"

    def _set_is_local_string(self,string):
        """
        Set the is_local starting from a string.
        """
        from aiida.common.exceptions import ValidationError
    
        upper_string = string.upper()
        if upper_string in ['YES', 'Y', 'T', 'TRUE']:
            is_local = True
        elif upper_string in ['NO', 'N', 'F', 'FALSE']:
            is_local = False
        else:
            raise ValidationError("Invalid value '{}' for the is_local variable, must "
                                  "be a boolean".format(string))
            
        self._is_local_validator(is_local)        
        self.is_local = is_local
        
    def _is_local_validator(self,is_local):
        """
        Validates the is_local.
        """
        from aiida.common.exceptions import ValidationError

        if not isinstance(is_local,bool):
            raise ValidationError("Invalid value '{}' for the is_local variable, must "
                                  "be a boolean".format(str(is_local)))

    input_plugin = None

    def _get_input_plugin_string(self):
        """
        Return the input plugin string
        """
        return self.input_plugin

    def _set_input_plugin_string(self,string):
        """
        Set the input_plugin starting from a string.
        """
        input_plugin = string.strip()
        
        if input_plugin.lower == "none":
            input_plugin = None
        
        self._input_plugin_validator(input_plugin)        
        self.input_plugin = input_plugin
        
    def _input_plugin_validator(self,input_plugin):
        """
        Validates the input_plugin, checking it is in the list of existing
        plugins.
        """
        from aiida.common.exceptions import ValidationError
        from aiida.orm import Calculation
        from aiida.common.pluginloader import existing_plugins

        if input_plugin is None:
            return

        if input_plugin not in existing_plugins(Calculation,
                                                'aiida.orm.calculation'):
            raise ValidationError("Invalid value '{}' for the input_plugin "
                "variable, it is not among the existing plugins".format(
                str(input_plugin)))

    prepend_text = ""
    
    def _get_prepend_text_string(self):
        return self.prepend_text

    def _set_prepend_text_string(self,string):
        """
        Set the prepend_text starting from a string.
        """
        self._prepend_text_validator(string)
        self.prepend_text = string
        
    def _prepend_text_validator(self,prepend_text):
        """
        Validates the prepend_text.
        """
        pass
    
    append_text = ""
    
    def _get_append_text_string(self):
        return self.append_text

    def _set_append_text_string(self,string):
        """
        Set the append_text starting from a string.
        """
        self._append_text_validator(string)
        self.append_text = string
        
    def _append_text_validator(self,append_text):
        """
        Validates the append_text.
        """
        pass
    
    def create_code(self):
        """
        Create a code with the information contained in this class,
        BUT DOES NOT STORE IT.
        """
        import os.path
        from aiida.orm import Code as AiidaOrmCode
        
        if self.is_local:
            file_list = [os.path.realpath(os.path.join(self.folder_with_code,f))
                         for f in os.listdir(self.folder_with_code)]
            code = AiidaOrmCode(local_executable=self.local_rel_path,
                                files=file_list)
        else:
            code = AiidaOrmCode(remote_computer_exec = (self.computer,
                                                self.remote_abs_path))

        code.label = self.label
        code.description = self.description
        code.set_input_plugin_name(self.input_plugin)
        code.set_prepend_text(self.prepend_text)    
        code.set_append_text(self.append_text)    
        
        return code

#     def load_from_code(self, code):
#         from aiida.orm import Code as AiidaOrmCode
# 
#         if not isinstance(code, AiidaOrmCode):
#             raise ValueError("code is not a valid Code instance")
#         
#         self.label = code.label
#         self.description = code.description
#         # Add here also the input_plugin stuff
#         self.is_local = code.is_local()
#         if self.is_local:
#             raise NotImplementedError
#         else:
#             self.computer = code.get_remote_computer()
#             self.remote_abs_path = code.get_remote_exec_path()
#         self.prepend_text = code.get_prepend_text()
#         self.append_text = code.get_append_text()

    def ask(self):
        cmdline_fill(self._conf_attributes_start,
                      store = self)
        if self.is_local:
            cmdline_fill(self._conf_attributes_local,
                         store = self, print_header = False)
        else:
            cmdline_fill(self._conf_attributes_remote,
                         store = self, print_header = False)
        cmdline_fill(self._conf_attributes_end,
                     store = self, print_header = False)
            
            


class Code(VerdiCommandWithSubcommands):
    """
    Setup and manage codes to be used

    This command allows to list, add, modify, configure codes.
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'list': (self.code_list, self.complete_none),
            'show' : (self.code_show, self.complete_code_names_and_pks),
            'setup': (self.code_setup, self.complete_code_pks),
            'relabel': (self.code_relabel, self.complete_code_pks),
            'update': (self.code_update, self.complete_code_pks),
            'delete': (self.code_delete, self.complete_code_pks),
            }

    def complete_code_names(self, subargs_idx, subargs):
        code_names = [c[1] for c in self.get_code_pks_and_labels()]
        return "\n".join(code_names)

    def complete_code_pks(self, subargs_idx, subargs):
        code_pks = [str(c[0]) for c in self.get_code_pks_and_labels()]
        return "\n".join(code_pks)

    def complete_code_names_and_pks(self, subargs_idx, subargs):
        return "\n".join([self.complete_code_names(subargs_idx, subargs),
                          self.complete_code_pks(subargs_idx, subargs)])

    def code_list(self, *args):
        """
        List available codes
        """
        if args:
            print >> sys.stderr, "No arguments allowed to the 'list' command."
            sys.exit(1)
        
        existing_codes = self.get_code_pks_and_labels()
        
        print "# List of configured codes:"
        print "# (use 'verdi code show CODEID' to see the details)"
        if existing_codes:
            print "\n".join("* Id {}: '{}'".format(pk, label)
                            for pk, label in existing_codes)
        else:
            print "# No codes configured yet. Use 'verdi code setup'"
        

    def get_code_pks_and_labels(self):
        """
        Retrieve the list of codes in the DB.
        """
        from aiida.orm import Code as AiidaOrmCode

        load_dbenv()
        return sorted([(c.pk, c.label) for c in AiidaOrmCode.query()])


    def get_code(self, code_id):
        """
        Get a Computer object with given identifier, that can either be
        the numeric ID (pk), or the label (if unique).
        
        .. note:: If an string that can be converted to an integer is given,
            the numeric ID is verified first (therefore, is a code A with a
            label equal to the ID of another code B is present, code A cannot
            be referenced by label).
        """    
        from aiida.orm import Code as AiidaOrmCode
        from aiida.common.exceptions import NotExistent, MultipleObjectsError
        
        load_dbenv()
        try:
            code_int = int(code_id)
            try:
                return AiidaOrmCode.get_subclass_from_pk(code_int)
            except NotExistent:
                raise ValueError() # Jump to the following section
                                   # to check if a code with the given
                                   # label exists.
            except MultipleObjectsError:
                print >> sys.stderr, (
                    "More than one code in the DB with pk='{}'!"
                    "".format(code_id))
                sys.exit(1)
        except ValueError:
            # Before dying, try to see if the user passed a (unique) label.
            codes = AiidaOrmCode.query(label=code_id)
            if len(codes) == 0:
                print >> sys.stderr, "'{}' is not a valid code ID or label.".format(code_id)
                sys.exit(1)
            if len(codes) > 1:
                print >> sys.stderr, (
                    "There are multiple codes with label '{}', having IDs:"
                    "".format(code_id))
                print >> sys.stderr, (
                    ", ".join(sorted([str(c.pk) for c in codes])) + ".")
                print >> sys.stderr, (
                    "Relabel them (using their ID), or refer to them "
                    "with their ID.")
                sys.exit(1)
            if len(codes) == 1:
                return codes[0]


    def code_show(self, *args):
        """
        Show information on a given code
        """
        load_dbenv()
        if len(args) != 1:
            print >> sys.stderr, ("after 'code show' there should be one "
                                  "argument only, being the code id.")
            sys.exit(1)

        code = self.get_code(args[0])
        print code.full_text_info
        
    def code_setup(self, *args):
        from aiida.common.exceptions import ValidationError

        load_dbenv()
          
        if len(args) != 0:
            print >> sys.stderr, ("after 'code setup' there cannot be any "
                                  "argument")
            sys.exit(1)


        set_params = CodeInputValidationClass()
        
        set_params.ask()
        
        code = set_params.create_code()
        
        try:
            code.store()
        except ValidationError as e:
            print "Unable to store the computer: {}. Exiting...".format(e.message)
            sys.exit(1)
                
        print "Code '{}' successfully stored in DB.".format(code.label)
        print "pk={}, uuid={}".format(code.pk, code.uuid)
      
    def code_relabel(self, *args):
        if len(args) != 1:
            print >> sys.stderr, ("after 'code relabel' there should be one "
                                  "argument only, being the code id.")
            sys.exit(1)

        code = self.get_code(args[0])
        
        set_params = CodeInputValidationClass()
        set_params.label = code.label
        set_params.description = code.description
        
        cmdline_fill(set_params._conf_attributes_relabel,
                      store = set_params)
        
        code.label = set_params.label
        code.description = set_params.description

    def code_update(self, *args):
        import os,datetime
        from aiida.djsite.utils import get_automatic_user
        from aiida.common.exceptions import ModificationNotAllowed
        if len(args) != 1:
            print >> sys.stderr, ("after 'code relabel' there should be one "
                                  "argument only, being the code id.")
            sys.exit(1)

        code = self.get_code(args[0])

        if code.has_children:
            print "***********************************"
            print "|                                 |"
            print "|            WARNING!             |"
            print "| Consider to create another code |"
            print "| You risk of losing the history  |"
            print "|                                 |"
            print "***********************************"
        
        # load existing stuff
        set_params = CodeInputValidationClass()
        set_params.label = code.label
        set_params.description = code.description
        set_params.input_plugin = code.get_input_plugin_name()
        
        
        was_local_before = code.is_local()
        set_params.is_local = code.is_local()
        
        if code.is_local():
            set_params.local_rel_path = code.get_local_executable()
            # I don't have saved the folder with code, so I will just have the list of files
            #file_list = [ code._get_folder_pathsubfolder.get_abs_path(i)
            #    for i in code.get_folder_list() ]
        else:
            set_params.computer = code.computer
            set_params.remote_abs_path = code.get_remote_exec_path()
        
        set_params.prepend_text = code.get_prepend_text()
        set_params.append_text = code.get_append_text()
        
        # ask for the new values
        set_params.ask()
        
        # prepare a comment containing the previous version of the code
        now = datetime.datetime.now()
        new_comment = []
        new_comment.append("Code modified on {}".format(now))
        new_comment.append("Old configuration was:")
        new_comment.append("label: {}".format(code.label))
        new_comment.append("description: {}".format(code.description))
        new_comment.append("input_plugin_name: {}".format(code.get_input_plugin_name()))
        new_comment.append("is_local: {}".format(code.is_local()))
        if was_local_before:
            new_comment.append("local_executable: {}".format(code.get_local_executable()))
        else:
            new_comment.append("computer: {}".format(code.computer))
            new_comment.append("remote_exec_path: {}".format(code.get_remote_exec_path()))
        new_comment.append("prepend_text: {}".format(code.get_prepend_text()))
        new_comment.append("append_text: {}".format(code.get_append_text()))
        comment = "\n".join(new_comment)
        
        if set_params.is_local:
            print "WARNING: => Folder with the code, and" 
            print "         => Relative path of the executable, "
            print "         will be ignored! It is not possible to replace "
            print "         the scripts, you have to create a new code for that."
        else:
            if was_local_before:
                # some old files will be left in the repository, and I cannot delete them
                print >> sys.stderr, ("It is not possible to change a "
                                      "code from local to remote.\n"
                                      "Modification cancelled.")
                sys.exit(1)
            print "WARNING: => computer, and"
            print "         => remote absolute path,"
            print "         will be ignored! It is not possible to replace them"
            print "         you have to create a new code for that."

#            print set_params.computer
#            code.computer = set_params.computer
#            code.set_remote_computer_exec( (set_params.computer,set_params.remote_abs_path ) )
        
        code.label = set_params.label
        code.description = set_params.description
        code.set_input_plugin_name(set_params.input_plugin)
        code.set_prepend_text(set_params.prepend_text)    
        code.set_append_text(set_params.append_text)    
        
        # store comment, to track history
        code.add_comment(comment,user=get_automatic_user())
        
    def code_delete(self, *args):
        """
        Delete a code
        
        Does not delete the code if there are calculations that are using it
        (i.e., if there are output links)
        """
        from aiida.common.exceptions import InvalidOperation
        from aiida.orm.code import delete_code
        
        if len(args) != 1:
            print >> sys.stderr, ("after 'code delete' there should be one "
                                  "argument only, being the code id.")
            sys.exit(1)
        
        code = self.get_code(args[0])
        pk = code.pk       
        try:
            delete_code(code)
        except InvalidOperation as e:
            print >> sys.stderr, e.message       
            sys.exit(1)
         
        print "Code '{}' deleted.".format(pk)
