from aiida.common.exceptions import (
    ConfigurationError, DbContentError, InvalidOperation,
    MissingPluginError)


class Computer(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything only on store().
    After the call to store(), in general attributes cannot be changed, except for those
    listed in the self._updatable_attributes tuple (empty for this class, can be
    extended in a subclass).

    Only after storing (or upon loading from uuid) metadata can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in the 'type' field.
    """
    import logging
    from aiida.transport import Transport
    from aiida.scheduler import Scheduler
    
    _logger = logging.getLogger(__name__)
    
    # This is the list of attributes to be automatically configured
    
    # It is a list of tuples. Each tuple has three elements:
    # 1. an internal name (used to find the 
    #    _set_internalname_string, and get_internalname_string methods)
    # 2. a short human-readable name
    # 3. A long human-readable description 
    # IMPORTANT!
    # for each entry, remember to define the 
    # _set_internalname_string and get_internalname_string methods.
    # Moreover, the _set_internalname_string method should also immediately
    # validate the value. 
    _conf_attributes = [
        ("hostname",
         "Hostname",
         "The fully qualified host-name of this computer",
        ),
        ("transport_type",
         "Transport type",
         "The name of the transport to be used. Valid names are: {}".format(
            ",".join(Transport.get_valid_transports())),
         ),
        ("scheduler_type",
         "Scheduler type",
         "The name of the scheduler to be used. Valid names are: {}".format(
            ",".join(Scheduler.get_valid_schedulers())),
         ),
        ("workdir",
         "AiiDA work directory",
         "The absolute path of the directory on the computer where AiiDA will\n"
         "run the calculation (typically, the scratch of the computer). You\n"
         "can use the {username} replacement, that will be replaced by your\n"
         "username on the remote computer",
         ),
        ] 
        
    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying with Django.
        Be careful, though, not to pass it to a wrong field! This only returns the
        local DB principal key value.
        """
        return self.pk

    @property
    def uuid(self):
        """
        Return the UUID in the DB.
        """
        return self._dbcomputer.uuid
    
    @property
    def pk(self):
        """
        Return the principal key in the DB.
        """
        return self._dbcomputer.pk
    
    def __init__(self,**kwargs):
        from aiida.djsite.db.models import DbComputer

        if 'dbcomputer' in kwargs:
            dbcomputer = kwargs.pop('dbcomputer')            
            if not(isinstance(dbcomputer, DbComputer)):
                raise TypeError("dbcomputer must be of type DbComputer")
            self._dbcomputer = dbcomputer

            if kwargs:
                raise ValueError("If you pass a dbcomputer parameter, "
                                 "you cannot pass any further parameter")
        else:
            self._dbcomputer = DbComputer()

            name = kwargs.pop('name', None)
            if name is not None:
                self.set_name(name)

            hostname = kwargs.pop('hostname', None)
            if hostname is not None:
                self.set_hostname(hostname)

            workdir = kwargs.pop('workdir', None)
            if workdir is not None:
                self.set_workdir(workdir)

            prepend_text = kwargs.pop('prepend_text', None)
            if prepend_text is not None:
                self.set_prepend_text(prepend_text)

            append_text = kwargs.pop('append_text', None)
            if append_text is not None:
                self.set_append_text(append_text)

            mpirun_command = kwargs.pop('mpirun_command', None)
            if mpirun_command is not None:
                self.set_mpirun_command(mpirun_command)

            transport_params = kwargs.pop('transport_params', None)
            if transport_params is not None:
                self.set_transport_params(transport_params)

            transport_type = kwargs.pop('transport_type', None)
            if transport_type is not None:
                self.set_transport_type(transport_type)

            scheduler_type = kwargs.pop('scheduler_type', None)
            if scheduler_type is not None:
                self.set_scheduler_type(scheduler_type)

            if kwargs:
                raise ValueError("Unrecognized parameters: {}".format(kwargs.keys()))

    @classmethod
    def list_names(cls):
        """
        Return a list with all the names of the computers in the DB.
        """
        from aiida.djsite.db.models import DbComputer
        return list(DbComputer.objects.filter().values_list('name',flat=True))

    @property
    def full_text_info(self):
        """
        Return a (multiline) string with a human-readable detailed information
        on this computer.
        """
        ret_lines = []
        ret_lines.append("Computer name:     {}".format(self.get_name()))
        ret_lines.append(" * PK:             {}".format(self.pk))
        ret_lines.append(" * UUID:           {}".format(self.uuid))
        ret_lines.append(" * Hostname:       {}".format(self.hostname))
        ret_lines.append(" * Transport type: {}".format(self.get_transport_type()))
        ret_lines.append(" * Scheduler type: {}".format(self.get_scheduler_type()))
        ret_lines.append(" * Work directory: {}".format(self.get_workdir()))
        ret_lines.append(" * mpirun command: {}".format(" ".join(
            self.get_mpirun_command())))
        ret_lines.append(" * prepend text:")
        if self.get_prepend_text().strip():
            for l in self.get_prepend_text().split('\n'):
                ret_lines.append("   {}".format(l))
        else:
            ret_lines.append("   # No prepend text.")
        ret_lines.append(" * append text:")
        if self.get_prepend_text().strip():
            for l in self.get_append_text().split('\n'):
                ret_lines.append("   {}".format(l))
        else:
            ret_lines.append("   # No append text.")

        return "\n".join(ret_lines)

    @property
    def to_be_stored(self):
        return (self._dbcomputer.pk is None)

    @classmethod
    def get(cls,computer):
        """
        Return a computer from its name (or from another Computer or DbComputer instance)
        """
        from aiida.djsite.db.models import DbComputer
        return cls(dbcomputer=DbComputer.get_dbcomputer(computer))

    @property
    def logger(self):
        return self._logger

    @classmethod
    def _name_validator(cls,name):
        """
        Validates the name.
        """
        from aiida.common.exceptions import ValidationError
    
        if not name.strip():
            raise ValidationError("No name specified")

    def _get_hostname_string(self):
        return self.get_hostname()

    def _set_hostname_string(self,string):
        """
        Set the hostname starting from a string.
        """
        self._hostname_validator(string)
        self.set_hostname(string)
        
    @classmethod
    def _hostname_validator(cls,hostname):
        """
        Validates the hostname.
        """
        from aiida.common.exceptions import ValidationError
    
        if not hostname.strip():
            raise ValidationError("No hostname specified")

    def _get_transport_type_string(self):
        return self.get_transport_type()

    def _set_transport_type_string(self,string):
        """
        Set the transport_type starting from a string.
        """
        self._transport_type_validator(string)
        self.set_transport_type(string)

    @classmethod
    def _transport_type_validator(cls, transport_type):
        """
        Validates the transport string.
        """
        from aiida.common.exceptions import ValidationError
        from aiida.transport import Transport
        
        if transport_type not in Transport.get_valid_transports():
            raise ValidationError("The specified transport is not a valid one")

    def _get_scheduler_type_string(self):
        return self.get_scheduler_type()

    def _set_scheduler_type_string(self,string):
        """
        Set the scheduler_type starting from a string.
        """
        self._scheduler_type_validator(string)
        self.set_scheduler_type(string)

    @classmethod
    def _scheduler_type_validator(cls, scheduler_type):
        """
        Validates the transport string.
        """
        from aiida.common.exceptions import ValidationError
        from aiida.scheduler import Scheduler
        
        if scheduler_type not in Scheduler.get_valid_schedulers():
            raise ValidationError("The specified scheduler is not a valid one")

    def _get_workdir_string(self):
        return self.get_workdir()

    def _set_workdir_string(self,string):
        """
        Set the workdir starting from a string.
        """
        self._workdir_validator(string)
        self.set_workdir(string)

    @classmethod
    def _workdir_validator(cls, workdir):
        """
        Validates the transport string.
        """
        from aiida.common.exceptions import ValidationError
        import os

        if not workdir.strip():
            raise ValidationError("No workdir specified")
        
        try:
            convertedwd = workdir.format(username="test")
        except KeyError as e:
            raise ValidationError("In workdir there is an unknown replacement field '{}'".format(
                e.message))
        
        if not os.path.isabs(convertedwd):
            raise ValidationError("The workdir must be an absolute path")
    
    def validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr and similar methods
        that automatically read either from the DB or from the internal attribute cache.

        For the base class, this is always valid. Subclasses will reimplement this.
        In the subclass, always call the super().validate() method first!
        """
        from aiida.common.exceptions import ValidationError
        
        if not self.get_name().strip():
            raise ValidationError("No name specified")

        self._hostname_validator(self.get_hostname())

        self._transport_type_validator(self.get_transport_type())

        self._scheduler_type_validator(self.get_scheduler_type())

        self._workdir_validator(self.get_workdir())

        try:
            self.get_transport_params()
        except DbContentError:
            raise ValidationError("Error in the DB content of the transport_params")

        mpirun_command = self.get_mpirun_command()
        if not isinstance(mpirun_command,(tuple,list)) or not(
            all(isinstance(i,basestring) for i in mpirun_command)):
                raise ValidationError("the mpirun_command must be a list of strings")
        try:
            for arg in mpirun_command:
                arg.format(num_machines=12,num_cpus_per_machine=2,tot_num_cpus=24)
        except KeyError as e:
            raise ValidationError("In workdir there is an unknown replacement field '{}'".format(
                e.message))

    def copy(self):
        """
        Return a copy of the current object to work with, not stored yet.
        """
        from aiida.djsite.db.models import DbComputer
        if self.to_be_stored:
            raise InvalidOperation("You can copy a computer only after having stored it")
        newdbcomputer = DbComputer.objects.get(pk=self.dbcomputer.pk)
        newdbcomputer.pk = None

        newobject = self.__class__(newdbcomputer)

        return newobject

    @property
    def dbcomputer(self):
        return self._dbcomputer

    def store(self):
        """
        Store the computer in the DB.
        
        Differently from Nodes, a computer can be re-stored if its properties
        are to be changed (e.g. a new mpirun command, etc.) 
        """
        from django.db import IntegrityError, transaction
        
#        if self.to_be_stored:

        # As a first thing, I check if the data is valid
        self.validate()
        try:
            # transactions are needed here for Postgresql:
            # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
            sid = transaction.savepoint()
            self.dbcomputer.save()
            transaction.savepoint_commit(sid)
        except IntegrityError:
            transaction.savepoint_rollback(sid)
            raise ValueError("Integrity error, probably the hostname already exists in the DB")

        #self.logger.error("Trying to store an already saved computer")
        #raise ModificationNotAllowed("The computer was already stored")

        # This is useful because in this way I can do
        # c = Computer().store()
        return self

    @property
    def hostname(self):
        return self.dbcomputer.hostname
        
    def _get_metadata(self):
        import json
        return json.loads(self.dbcomputer.metadata)

    def _set_metadata(self,metadata_dict):
        import json
#        if not self.to_be_stored:
#            raise ModificationNotAllowed("Cannot set a property after having stored the entry")
        self.dbcomputer.metadata = json.dumps(metadata_dict)

    def _set_property(self,k,v):
        olddata = self._get_metadata()
        olddata[k] = v
        self._set_metadata(olddata)

    def _get_property(self,k,*args):
        if len(args) > 1:
            raise TypeError("_get_property expected at most 2 arguments")
        olddata = self._get_metadata()
        try:
            return olddata[k]
        except KeyError:
            if len(args) == 0:
                raise AttributeError("'{}' property not found".format(k))
            elif len(args) == 1:
                return args[0]

    def get_prepend_text(self):
        return self._get_property("prepend_text", "")

    def set_prepend_text(self,val):
        self._set_property("prepend_text", unicode(val))

    def get_append_text(self):
        return self._get_property("append_text", "")

    def set_append_text(self,val):
        self._set_property("append_text", unicode(val))

    def get_mpirun_command(self):
        return self._get_property("mpirun_command", [])

    def set_mpirun_command(self,val):
        if not isinstance(val,(tuple,list)) or not(
            all(isinstance(i,basestring) for i in val)):
                raise TypeError("the mpirun_command must be a list of strings")
        self._set_property("mpirun_command", val)

    def get_transport_params(self):
        import json
        try:
            return json.loads(self.dbcomputer.transport_params)
        except ValueError:
            raise DbContentError(
                "Error while reading transport_params for computer {}".format(
                    self.hostname))

    def set_transport_params(self,val):
        import json

#        if self.to_be_stored:
        try:
            self.dbcomputer.transport_params = json.dumps(val)
        except ValueError:
            raise ValueError("The set of transport_params are not JSON-able")
#        else:
#            raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_workdir(self):
        return self.dbcomputer.workdir

    def set_workdir(self,val):
        #if self.to_be_stored:
        self.dbcomputer.workdir = val
        #else:
        #    raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_name(self):
        return self.dbcomputer.name

    def set_name(self,val):
        #if self.to_be_stored:
            self.dbcomputer.name = val

    def get_hostname(self):
        return self.dbcomputer.hostname

    def set_hostname(self,val):
        #if self.to_be_stored:
            self.dbcomputer.hostname = val
        #else:
        #    raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_scheduler_type(self):
        return self.dbcomputer.scheduler_type

    def set_scheduler_type(self,val):
        #if self.to_be_stored:
            self.dbcomputer.scheduler_type = val
        #else:
        #    raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_transport_type(self):
        return self.dbcomputer.transport_type

    def set_transport_type(self,val):
        #if self.to_be_stored:
            self.dbcomputer.transport_type = val
        #else:
        #    raise ModificationNotAllowed("Cannot set a property after having stored the entry")
        
    def get_scheduler(self):
        from aiida.scheduler import SchedulerFactory

        try:
            ThisPlugin = SchedulerFactory(self.get_scheduler_type())
            # I call the init without any parameter
            return ThisPlugin()
        except MissingPluginError as e:
            raise ConfigurationError('No scheduler found for {} [type {}], message: {}'.format(
                self.hostname, self.get_scheduler_type(), e.message))


