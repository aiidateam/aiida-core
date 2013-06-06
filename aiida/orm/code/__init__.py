from aiida.orm import Node

class Code(Node):
    """
    A code entity.
    It can either be 'local', or 'remote'.

    Local code:
        it is a collection of files/dirs (added using the add_path() method), where one
        file is flagged as executable (using the set_local_executable() method).
    Remote code:
        it is a pair (remotecomputer, remotepath_of_executable) set using the
        set_remote_computer_exec() method.

    For both codes, one can set some code to be executed right before or right after
    the execution of the code, using the set_preexec_code() and set_postexec_code()
    methods (e.g., the set_preexec_code() can be used to load specific modules required
    for the code to be run).
    """
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
            remote_computer_exec: a list or tuple of length 2 with (computer, remote_exec_path)
                as accepted by the set_remote_computer_exec() method.
        """
        import os
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
            self.add_path(f,os.path.split(f)[1])

        # By default I set a local code
        self._set_local()

        local_executable = kwargs.pop('local_executable', None)
        if local_executable is not None:
            self.set_local_executable(local_executable)
        
        remote_computer_exec = kwargs.pop('remote_computer_exec', None)
        if remote_computer_exec is not None:
            if local_executable is not None:
                raise ValueError("You cannot specify both local_executable and "
                                 "remote_computer_exec")
            if (not isinstance(remote_computer_exec,(list,tuple))
                or len(remote_computer_exec) != 2):
                raise ValueError("remote_computer_exec must be a list or tuple "
                                 "of length 2, with machine and executable "
                                 "name")
            self.set_remote_computer_exec(*remote_computer_exec)

        if kwargs:
            raise ValueError("Invalid parameters found in the __init__: {}".format(kwargs.keys()))

    def validate(self):
        from aiida.common.exceptions import ValidationError
        
        super(Code,self).validate()

        if self.is_local():
            if not self.get_local_executable():
                raise ValidationError("You have to set which file is the local executable "
                                      "using the set_exec_filename() method")
                # c[1] is True if the element is a file
            if self.get_local_executable() not in self.get_path_list():
                raise ValidationError("The local executable '{}' is not in the list of "
                                      "files of this code".format(self.get_local_executable()))
        else:
            if self.get_path_list():
                raise ValidationError("The code is remote but it has files inside")
            if not self.get_remote_computer():
                raise ValidationError("You did not specify a remote computer")
            if not self.get_remote_exec_path():
                raise ValidationError("You did not specify a remote executable")
            
        
    def add_link_from(self,src,label=None):
        raise ValueError("A code node cannot have any input nodes")

    def can_link_as_output(self,dest):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        
        An output of a code can only be a calculation
        """
        from aiida.orm import Calculation
        
        if not isinstance(dest, Calculation):
            raise ValueError("The output of a code node can only be a calculation")

        return super(Code, self).can_link_as_output(dest)

    def set_prepend_text(self,code):
        """
        Pass a string of code that will be put in the scheduler script before the
        execution of the code.
        """
        self.set_attr('prepend_text', unicode(code))

    def get_prepend_text(self):
        """
        Return the code that will be put in the scheduler script before the
        execution, or an empty string if no pre-exec code was defined.
        """
        return self.get_attr('prepend_text',u"")

    def set_append_text(self,code):
        """
        Pass a string of code that will be put in the scheduler script after the
        execution of the code.
        """
        self.set_attr('append_text', unicode(code))

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
        self.set_attr('local_executable',exec_name)

    def get_local_executable(self):
        return self.get_attr('local_executable', u"")

    def set_remote_computer_exec(self,computer,remote_exec_path):
        """
        Set the code as remote, and pass the computer on which it resides
        and the absolute path on that computer.
        
        Args:
            computer: a aiida.orm.Computer or an
                aiida.djsite.db.models.DbComputer object.
            remote_exec_path: the absolute path of the main executable on the
                computer.
        """
        import os
        from aiida.orm import Computer
        from aiida.djsite.db.models import DbComputer
        
        if not os.path.isabs(remote_exec_path):
            raise ValueError("exec_path must be an absolute path (on the remote machine)")

        remote_dbcomputer = computer
        if isinstance(remote_dbcomputer, Computer):
            remote_dbcomputer = remote_dbcomputer.dbcomputer
        if not(isinstance(remote_dbcomputer, DbComputer)):
            raise TypeError("computer must be either a Computer or DbComputer object")

        self._set_remote()

        self.dbnode.computer = remote_dbcomputer
        self.set_attr('remote_exec_path', remote_exec_path)

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
        self.set_attr('is_local', True)
        self.dbnode.computer = None
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

