# -*- coding: utf-8 -*-
from aiida.orm import Node

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class Code(Node):
    """
    A code entity.
    It can either be 'local', or 'remote'.

    * Local code: it is a collection of files/dirs (added using the add_path() method), where one \
    file is flagged as executable (using the set_local_executable() method).

    * Remote code: it is a pair (remotecomputer, remotepath_of_executable) set using the \
    set_remote_computer_exec() method.

    For both codes, one can set some code to be executed right before or right after
    the execution of the code, using the set_preexec_code() and set_postexec_code()
    methods (e.g., the set_preexec_code() can be used to load specific modules required
    for the code to be run).
    """
    _updatable_attributes = ('input_plugin','append_text', 'prepend_text') 

    _set_incompatibilities = [('remote_computer_exec','local_executable')]
    
    def set_files(self, files):
        """
        Given a list of filenames (or a single filename string),
        add it to the path (all at level zero, i.e. without folders).
        Therefore, be careful for files with the same name!

        :todo: decide whether to check if the Code must be a local executable
             to be able to call this function.
        """
        import os
        if isinstance(files, basestring):
            files=[files]
        for f in files:
            self.add_path(f,os.path.split(f)[1])

    def __str__(self):
        local_str = "Local" if self.is_local() else "Remote"
        computer_str = "repository" if self.is_local() else self.computer.name
        
        return "{} code '{}' on {}, pk={}, uuid={}".format(local_str, self.label,
                                           computer_str, self.pk, self.uuid)

    @classmethod
    def get(cls,label,computername=None,useremail=None):
        """
        Get a code from its label. 

        :param label: the code label
        :param computername: filter only codes on computers with this name
        :param useremail: filter only codes belonging to a user with this 
          email

        :raise NotExistent: if no matches are found
        :raise MultipleObjectsError: if multiple matches are found. In this case
          you may want to pass the additional parameters to filter the codes,
          or relabel the codes.
        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError
        from django.db.models import Q
        
        q_obj = Q(label=label)
        if computername is not None:
            q_obj &= Q(dbcomputer__name=computername)
        if useremail is not None:
            q_obj &= Q(user__email=useremail)
        queryresults = cls.query(q_obj)

        valid_codes = list(queryresults)
        if len(valid_codes) == 1:
            return valid_codes[0]
        else:
            otherstr = ""
            if computername is not None:
                otherstr += " on computer '{}'".format(computername)
            if useremail is not None:
                otherstr += " of user '{}'".format(useremail)
            if len(valid_codes) == 0:
                errstr = "No code in the DB with name '{}'{}".format(label,otherstr)
                raise NotExistent(errstr)
            elif len(valid_codes) > 1:
                errstr = ("More than one code in the DB with name "
                          "'{}'{}, please rename at least one of "
                          "them".format(label,otherstr))
                raise MultipleObjectsError

    @classmethod
    def get_from_string(cls, code_string):
        """
        Get a Computer object with given identifier string, that can either be
        the numeric ID (pk), or the label (if unique); the label can either
        be simply the label, or in the format label@machinename. See the note
        below for details on the string detection algorithm.

        .. note:: If a string that can be converted to an integer is given,
          the numeric ID is verified first (therefore, is a code A with a 
          label equal to the ID of another code B is present, code A cannot 
          be referenced by label). Similarly, the (leftmost) '@' symbol is
          always used to split code and computername. Therefore do not use
          '@' in the code name if you want to use this function
          ('@' in the computer name are instead valid).

        :param code_string: the code string identifying the code to load

        :raise NotExistent: if no code identified by the given string is found
        :raise MultipleObjectsError: if the string cannot identify uniquely
            a code
        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        try:
            code_int = int(code_string)
            try:
                return cls.get_subclass_from_pk(code_int)
            except NotExistent:
                raise ValueError() # Jump to the following section
                                   # to check if a code with the given
                                   # label exists.                              
            except MultipleObjectsError:
                raise MultipleObjectsError("More than one code in the DB "
                                           "with pk='{}'!".format(code_string))
        except ValueError:
            # Before dying, try to see if the user passed a (unique) label.
            # split with the leftmost '@' symbol (i.e. code names cannot
            # contain '@' symbols, computer names can)
            codename, sep, computername = code_string.partition('@')
            if sep:
                codes = cls.query(label=codename, dbcomputer__name=computername)
            else:
                codes = cls.query(label=codename)

            if len(codes) == 0:
                raise NotExistent("'{}' is not a valid code "
                                  "ID or label.".format(code_string))
            elif len(codes) > 1:
                retstr = ("There are multiple codes with label '{}', having IDs: "
                    "".format(code_string))
                retstr += ", ".join(sorted([str(c.pk) for c in codes])) + ".\n"
                retstr += ("Relabel them (using their ID), or refer to them "
                           "with their ID.")
                raise MultipleObjectsError(retstr)
            else:
                return codes[0]

    @classmethod
    def list_for_plugin(cls,plugin,labels=True):
        """
        Return a list of valid code strings for a given plugin.
        
        :param plugin: The string of the plugin.
        :param labels: if True, return a list of code names, otherwise
          return the code PKs (integers).
        :return: a list of string, with the code names if labels is True,
          otherwise a list of integers with the code PKs.
        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError
        
        valid_codes = list(cls.query(
            dbattributes__key="input_plugin",
            dbattributes__tval=plugin))

        if labels:
            return [c.label for c in valid_codes]
        else:
            return [c.pk for c in valid_codes]

    def _validate(self):
        from aiida.common.exceptions import ValidationError
        
        super(Code,self)._validate()

        if self.is_local() is None:
            raise ValidationError("You did not set whether the code is local "
                                  "or remote")            

        if self.is_local():
            if not self.get_local_executable():
                raise ValidationError("You have to set which file is the local executable "
                                      "using the set_exec_filename() method")
                # c[1] is True if the element is a file
            if self.get_local_executable() not in self.get_folder_list():
                raise ValidationError("The local executable '{}' is not in the list of "
                                      "files of this code".format(self.get_local_executable()))
        else:
            if self.get_folder_list():
                raise ValidationError("The code is remote but it has files inside")
            if not self.get_remote_computer():
                raise ValidationError("You did not specify a remote computer")
            if not self.get_remote_exec_path():
                raise ValidationError("You did not specify a remote executable")
            
        
    def _add_link_from(self,src,label=None):
        raise ValueError("A code node cannot have any input nodes")

    def _can_link_as_output(self,dest):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        
        An output of a code can only be a calculation
        """
        from aiida.orm import Calculation
        
        if not isinstance(dest, Calculation):
            raise ValueError("The output of a code node can only be a calculation")

        return super(Code, self)._can_link_as_output(dest)

    def set_prepend_text(self,code):
        """
        Pass a string of code that will be put in the scheduler script before the
        execution of the code.
        """
        self._set_attr('prepend_text', unicode(code))

    def get_prepend_text(self):
        """
        Return the code that will be put in the scheduler script before the
        execution, or an empty string if no pre-exec code was defined.
        """
        return self.get_attr('prepend_text',u"")

    def set_input_plugin_name(self, input_plugin):
        """
        Set the name of the default input plugin, to be used for the automatic
        generation of a new calculation.
        """
        if input_plugin is None:
            self._set_attr('input_plugin', None)
        else:
            self._set_attr('input_plugin', unicode(input_plugin))
        
    def get_input_plugin_name(self):
        """
        Return the name of the default input plugin (or None if no input plugin
        was set.
        """
        return self.get_attr('input_plugin', None)

    def set_append_text(self,code):
        """
        Pass a string of code that will be put in the scheduler script after the
        execution of the code.
        """
        self._set_attr('append_text', unicode(code))

    def get_append_text(self):
        """
        Return the postexec_code, or an empty string if no post-exec code was defined.
        """
        return self.get_attr('append_text',u"")

    def set_local_executable(self,exec_name):
        """
        Set the filename of the local executable.
        Implicitly set the code as local.
        """
        self._set_local()
        self._set_attr('local_executable',exec_name)

    def get_local_executable(self):
        return self.get_attr('local_executable', u"")

    def set_remote_computer_exec(self,remote_computer_exec):
        """
        Set the code as remote, and pass the computer on which it resides
        and the absolute path on that computer.
        
        Args:
            remote_computer_exec: a tuple (computer, remote_exec_path), where
              computer is a aiida.orm.Computer or an
              aiida.djsite.db.models.DbComputer object, and
              remote_exec_path is the absolute path of the main executable on
              remote computer.
        """
        import os
        from aiida.orm import Computer
        from aiida.djsite.db.models import DbComputer
        
        if (not isinstance(remote_computer_exec,(list,tuple))
            or len(remote_computer_exec) != 2):
            raise ValueError("remote_computer_exec must be a list or tuple "
                             "of length 2, with machine and executable "
                             "name")
        
        computer,remote_exec_path = tuple(remote_computer_exec)
        
        if not os.path.isabs(remote_exec_path):
            raise ValueError("exec_path must be an absolute path (on the remote machine)")

        remote_dbcomputer = computer
        if isinstance(remote_dbcomputer, Computer):
            remote_dbcomputer = remote_dbcomputer.dbcomputer
        if not(isinstance(remote_dbcomputer, DbComputer)):
            raise TypeError("computer must be either a Computer or DbComputer object")

        self._set_remote()

        self.dbnode.dbcomputer = remote_dbcomputer
        self._set_attr('remote_exec_path', remote_exec_path)

    def get_remote_exec_path(self):
        if self.is_local():
            raise ValueError("The code is local")
        return self.get_attr('remote_exec_path', "")

    def get_remote_computer(self):
        from aiida.orm import Computer

        if self.is_local():
            raise ValueError("The code is local")
        
        return self.computer

    def _set_local(self):
        """
        Set the code as a 'local' code, meaning that all the files belonging to the code
        will be copied to the cluster, and the file set with set_exec_filename will be
        run.

        It also deletes the flags related to the local case (if any)
        """
        self._set_attr('is_local', True)
        self.dbnode.dbcomputer = None
        try:
            self._del_attr('remote_exec_path')
        except AttributeError:
            pass

    def _set_remote(self):
        """
        Set the code as a 'remote' code, meaning that the code itself has no files attached,
        but only a location on a remote computer (with an absolute path of the executable on
        the remote computer).

        It also deletes the flags related to the local case (if any)
        """
        self._set_attr('is_local', False)
        try:
            self._del_attr('local_executable')
        except AttributeError:
            pass

    def is_local(self):
        """
        Return True if the code is 'local', False if it is 'remote' (see also documentation
        of the set_local and set_remote functions).
        """
        return self.get_attr('is_local', None)

    def can_run_on(self, computer):
        """
        Return True if this code can run on the given computer, False otherwise.

        Local codes can run on any machine; remote codes can run only on the machine
        on which they reside.

        TODO: add filters to mask the remote machines on which a local code can run.
        """
        from aiida.orm import Computer
        from aiida.djsite.db.models import DbComputer
                
        if self.is_local():
            return True
        else:
            dbcomputer = computer
            if isinstance(dbcomputer, Computer):
                dbcomputer = dbcomputer.dbcomputer
            if not isinstance(dbcomputer, DbComputer):
                raise ValueError("computer must be either a Computer or DbComputer object")
            dbcomputer = DbComputer.get_dbcomputer(computer)
            return (dbcomputer.pk ==
                self.get_remote_computer().dbcomputer.pk)
        
    def get_execname(self):
        """
        Return the executable string to be put in the script.
        For local codes, it is ./LOCAL_EXECUTABLE_NAME
        For remote codes, it is the absolute path to the executable.
        """
        if self.is_local():
            return u"./{}".format(self.get_local_executable())
        else:
            return self.get_remote_exec_path()

    def new_calc(self, *args, **kwargs):
        """
        Create and return a new Calculation object (unstored) with the correct
        plugin subclass, as otained by the self.get_input_plugin_name() method.
        
        Parameters are passed to the calculation __init__ method.
        
        :note: it also directly creates the link to this code (that will of
            course be cached, since the new node is not stored yet).
        
        :raise MissingPluginError: if the specified plugin does not exist.
        :raise ValueError: if no plugin was specified.        
        """
        from aiida.orm import CalculationFactory
        from aiida.common.exceptions import MissingPluginError
        
        plugin_name = self.get_input_plugin_name()
        if plugin_name is None:
            raise ValueError("You did not specify an input plugin "
                             "for this code")
        
        try:
            C = CalculationFactory(plugin_name)
            
        except MissingPluginError:
            raise MissingPluginError("The input_plugin name for this code is "
                                     "'{}', but it is not an existing plugin"
                                     "name".format(plugin_name))

        # For remote codes, automatically set the computer,
        # unless explicitly set by the user
        if not self.is_local():
            if 'computer' not in kwargs:
                kwargs['computer'] = self.get_remote_computer()
        
        new_calc = C(*args, **kwargs)
        # I link to the code
        new_calc.use_code(self)
        return new_calc

    @property
    def full_text_info(self):
        """
        Return a (multiline) string with a human-readable detailed information
        on this computer.
        """
        
        ret_lines = []
        ret_lines.append(" * PK:             {}".format(self.pk))
        ret_lines.append(" * UUID:           {}".format(self.uuid))
        ret_lines.append(" * Label:          {}".format(self.label))
        ret_lines.append(" * Description:    {}".format(self.description))
        ret_lines.append(" * Default plugin: {}".format(
            self.get_input_plugin_name()))
        ret_lines.append(" * Used by:        {} calculations".format(
             self.dbnode.outputs.count()))
        if self.is_local():
            ret_lines.append(" * Type:           {}".format("local"))
            ret_lines.append(" * Exec name:      {}".format(self.get_execname()))
            ret_lines.append(" * List of files/folders:")
            for fname in self._get_folder_pathsubfolder.get_content_list():
                ret_lines.append("   * [{}] {}".format(" dir" if
                    self._get_folder_pathsubfolder.isdir(fname) else "file", fname))
        else:
            ret_lines.append(" * Type:           {}".format("remote"))
            ret_lines.append(" * Remote machine: {}".format(
                self.get_remote_computer().name))
            ret_lines.append(" * Remote absolute path: ")
            ret_lines.append("   " + self.get_remote_exec_path())
        
        ret_lines.append(" * prepend text:")
        if self.get_prepend_text().strip():
            for l in self.get_prepend_text().split('\n'):
                ret_lines.append("   {}".format(l))
        else:
            ret_lines.append("   # No prepend text.")
        ret_lines.append(" * append text:")
        if self.get_append_text().strip():
            for l in self.get_append_text().split('\n'):
                ret_lines.append("   {}".format(l))
        else:
            ret_lines.append("   # No append text.")

        return "\n".join(ret_lines)
    
def delete_code(code):
    """
    Delete a code from the DB. 
    Check before that there are no output nodes. 
    
    NOTE! Not thread safe... Do not use with many users accessing the DB
    at the same time.
    
    Implemented as a function on purpose, otherwise complicated logic would be
    needed to set the internal state of the object after calling 
    computer.delete(). 
    """
    from django.db import transaction
    from aiida.common.exceptions import InvalidOperation
    if not isinstance(code, Code):
        raise TypeError("code must be an instance of "
                        "aiida.orm.computer.Code")

    existing_outputs = code.get_outputs()

    if len(existing_outputs) != 0:    
        raise InvalidOperation("Unable to delete the requested code because it "
                               "has {} output links".format(
                                len(existing_outputs)))
    else:
        repo_folder = code._repository_folder
        with transaction.commit_on_success():
            code.dbnode.delete()
            repo_folder.erase()

