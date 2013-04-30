from aida.orm import Node

def _get_machine_name_from_computer(computer):
    from aida.djsite.db.models import Computer
    if isinstance(computer,basestring):
        machinename = computer
    elif isinstance(computer, Computer):
        machinename = computer.hostname
    else:
        raise ValueError("pass either a string with a computer name, or a "
                         "django Computer object")
    return machinename

class Code(Node):
    """
    A code entity.
    It can either be 'local', or 'remote'.

    Local code:
        it is a collection of files (added using the add_file() method), where one
        file is flagged as executable (using the set_local_executable() method).
    Remote code:
        it is a pair (remotecomputer, remotepath_of_executable) set using the
        set_remote_machine_exec() method.

    For both codes, one can set some code to be executed right before or right after
    the execution of the code, using the set_preexec_code() and set_postexec_code()
    methods (e.g., the set_preexec_code() can be used to load specific modules required
    for the code to be run).
    """
    _plugin_type_string = "code"
    _updatable_attributes = tuple() 
    
    def __init__(self,**kwargs):
        """
        Initialize a Code node.
 
        Args:
            uuid: an existing entry is loaded from the DB. No further parameters can be
                specified
            local_executable: a filename of the file that should be set as local executable
            files: a list of files to be added to this Code node; pass absolute paths here, and
                files will be copied within this node. This can be used also if you specify
            remote_machine_exec: a list or tuple of length 2 with (machinename, remote_executable)
                as accepted by the set_remote_machine_exec() method.
        """
        import os
        self._logger = super(Code,self).logger.getChild('code')
        super(Code,self).__init__(**kwargs)

        uuid = kwargs.pop('uuid',None)
        if uuid is not None:
            # if I am loading an existing code: stop here
            return

        # Files
        files = kwargs.pop('files', [])
        if isinstance(files, basestring):
            files=[files]
        for f in files:
            self.add_file(f,os.path.split(f)[1])

        # By default I set a local code
        self._set_local()

        local_executable = kwargs.pop('local_executable', None)
        if local_executable is not None:
            self.set_local_executable(local_executable)
        
        remote_machine_exec = kwargs.pop('remote_machine_exec', None)
        if remote_machine_exec is not None:
            if local_executable is not None:
                raise ValueError("You cannot specify both local_executable and "
                                 "remote_machine_exec")
            if (not isinstance(remote_machine_exec,(list,tuple))
                or len(remote_machine_exec) != 2):
                raise ValueError("remote_machine_exec must be a list or tuple "
                                 "of length 2, with machine and executable "
                                 "name")
            self.set_remote_machine_exec(*remote_machine_exec)

        input_plugin = kwargs.pop('input_plugin', None)
        self.set_input_plugin(input_plugin)

        output_plugin = kwargs.pop('output_plugin', None)
        self.set_output_plugin(output_plugin)

        if kwargs:
            raise ValueError("Invalid parameters found in the __init__: {}".format(kwargs.keys()))

    def validate(self):
        from aida.common.exceptions import ValidationError
        
        super(Code,self).validate()

        if self.is_local():
            if not self.get_local_executable():
                raise ValidationError("You have to set which file is the local executable "
                                      "using the set_exec_filename() method")
            if self.get_local_executable() not in self.get_file_list():
                raise ValidationError("The local executable '{}' is not in the list of "
                                      "files of this code".format(self.get_local_executable()))
        else:
            if self.get_file_list():
                raise ValidationError("The code is remote but it has files inside")
            if not self.get_remote_machine():
                raise ValidationError("You did not specify a remote machine")
            if not self.get_remote_executable():
                raise ValidationError("You did not specify a remote executable")
            
        
    def add_link_from(self,src,*args,**kwargs):
        raise ValueError("A code node cannot have any input nodes")

    def set_preexec_code(self,code):
        """
        Pass a string of code that will be put in the scheduler script before the
        execution of the code.
        """
        self.set_attr('preexec_code', unicode(code))

    def get_preexec_code(self):
        """
        Return the preexec_code, or an empty string if no pre-exec code was defined.
        """
        return self.get_attr('preexec_code',u"")

    def set_postexec_code(self,code):
        """
        Pass a string of code that will be put in the scheduler script before the
        execution of the code.
        """
        self.set_attr('postexec_code', unicode(code))

    def get_postexec_code(self):
        """
        Return the postexec_code, or an empty string if no post-exec code was defined.
        """
        return self.get_attr('postexec_code',u"")

    def set_input_plugin(self, input_plugin):
        """
        Set a string for the input plugin

        TODO: check that the plugin referenced by th string input_plugin actually exists
        """
        if input_plugin is None:
            raise ValueError("You need to specify an input plugin")
        self.set_attr('input_plugin', input_plugin)
        
    def get_input_plugin(self):
        """
        Return the input plugin
        """
        return self.get_attr('input_plugin')

    def set_output_plugin(self, output_plugin):
        """
        Set a string for the output plugin
        Can be none if no output plugin is available/needed

        TODO: check that the plugin referenced by th string input_plugin actually exists
        """
        self.set_attr('output_plugin', output_plugin)
        
    def get_output_plugin(self, output_plugin):
        """
        Return the output plugin
        """
        return self.get_attr('output_plugin',None)


    def set_local_executable(self,exec_name):
        """
        Set the filename of the local executable.
        Implicitly set the code as local.
        """
        self._set_local()
        self.set_attr('local_executable',exec_name)

    def get_local_executable(self):
        return self.get_attr('local_executable', u"")

    def set_remote_machine_exec(self,machine,exec_path):
        """
        Set the code as remote, and pass the machine on which it resides and the absolute
        path on that machine.
        """
        import os
        if not os.path.isabs(exec_path):
            raise ValueError("exec_path must be an absolute path (on the remote machine)")

        machinename = _get_machine_name_from_computer(machine)

        self._set_remote()

        self.set_attr('remote_machine',unicode(machinename).lower().strip())
        self.set_attr('remote_exec_path', exec_path)

    def get_remote_executable(self):
        return self.get_attr('remote_exec_path', u"")

    def get_remote_machine(self):
        return self.get_attr('remote_machine', None)

    def _set_local(self):
        """
        Set the code as a 'local' code, meaning that all the files belonging to the code
        will be copied to the cluster, and the file set with set_exec_filename will be
        run.

        It also deletes the flags related to the local case (if any)
        """
        self.set_attr('is_local', True)
        try:
            self.del_attr('remote_machine')
        except AttributeError:
            pass
        try:
            self.del_attr('remote_exec_path')
        except AttributeError:
            pass

    def _set_remote(self):
        """
        Set the code as a 'remote' code, meaning that the code itself has no files attached,
        but only a location on a remote computer (with an absolute path of the executable on
        the remote computer).

        It also deletes the flags related to the local case (if any)
        """
        self.set_attr('is_local', False)
        try:
            self.del_attr('local_executable')
        except AttributeError:
            pass

    def is_local(self):
        """
        Return True if the code is 'local', False if it is 'remote' (see also documentation
        of the set_local and set_remote functions).
        """
        return self.get_attr('is_local')

    def can_run_on(self, computer):
        """
        Return True if this code can run on the given computer, False otherwise.

        Local codes can run on any machine; remote codes can run only on the machine
        on which they reside.

        TODO: add filters to mask the remote machines on which a local code can run.
        """
        machinename = _get_machine_name_from_computer(computer)
        
        if self.is_local():
            return True
        else:
            return (
                unicode(machinename).lower().strip() ==
                self.get_remote_machine()
                )
        
    def get_execname(self):
        """
        Return the executable string to be put in the script.
        For local codes, it is ./LOCAL_EXECUTABLE_NAME
        For remote codes, it is the absolute path to the executable.
        """
        if self.is_local():
            return u"./{}".format(self.get_local_executable())
        else:
            return get_remote_executable()

