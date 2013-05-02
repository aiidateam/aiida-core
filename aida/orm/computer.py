import aida.common
from aida.common.exceptions import (
    ConfigurationError, InvalidOperation, MissingPluginError, ModificationNotAllowed)

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
    _logger = aida.common.aidalogger.getChild('computer')
        
    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying with Django.
        Be careful, though, not to pass it to a wrong field! This only returns the
        local DB principal key value.
        """
        return self._dbcomputer.pk
    
    def __init__(self,**kwargs):
        from aida.djsite.db.models import DbComputer

        dbcomputer = kwargs.pop('dbcomputer', None)
        if dbcomputer is not None:
            if not(isinstance(dbcomputer, DbComputer)):
                raise TypeError("dbcomputer must be of type DbComputer")
            self._dbcomputer = dbcomputer

            if kwargs:
               raise ValueError("If you pass a dbcomputer parameter, you cannot pass any further parameter")
        else:
            self._dbcomputer = DbComputer()

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

    @property
    def to_be_stored(self):
        return (self._dbcomputer.pk is None)

    @classmethod
    def get(cls,computer):
        """
        Return a computer from hostname (or from another Computer or DbComputer instance)
        """
        from aida.djsite.db.models import DbComputer
        return cls(dbcomputer=DbComputer.get_dbcomputer(computer))

    @property
    def logger(self):
        return self._logger

    def validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr and similar methods
        that automatically read either from the DB or from the internal attribute cache.

        For the base class, this is always valid. Subclasses will reimplement this.
        In the subclass, always call the super().validate() method first!
        """
        from aida.common.exceptions import ValidationError
        
        if not self.get_hostname().strip():
            raise ValidationError("No hostname specified")
        if not self.get_transport_type().strip():
            raise ValidationError("No transport_type specified")
        if not self.get_scheduler_type().strip():
            raise ValidationError("No scheduler_type specified")
        if not self.get_workdir().strip():
            raise ValidationError("No workdir specified")
        try:
            self.get_workdir().format(username="test")
        except KeyError as e:
            raise ValidationError("In workdir there is an unknown replacement field '{}'".format(
                e.message))
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
                arg.format(num_nodes=12,num_cpus_per_node=2,tot_num_cpus=24)
        except KeyError as e:
            raise ValidationError("In workdir there is an unknown replacement field '{}'".format(
                e.message))

    def copy(self):
        """
        Return a copy of the current object to work with, not stored yet.
        """
        from aida.djsite.db.models import DbComputer
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
        Can be called only once. 
        """
        from django.db import IntegrityError
        
        if self.to_be_stored:

            # As a first thing, I check if the data is valid
            self.validate()
            try:
                self.dbcomputer.save()
            except IntegrityError:
                raise ValueError("Integrity error, probably the hostname already exists in the DB")
        else:
            self.logger.error("Trying to store an already saved computer")
            raise ModificationNotAllowed("The computer was already stored")

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
        if self.to_be_stored:
            raise ModificationNotAllowed("Cannot set a property after having stored the entry")
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
        from aida.common.exceptions import DbContentError
        import json
        try:
            return json.loads(self.dbcomputer.transport_params)
        except ValueError:
            raise DbContentError(
                "Error while reading transport_params for computer {}".format(
                    self.hostname))

    def set_transport_params(self,val):
        import json

        if self.to_be_stored:
             try:
                 self.dbcomputer.transport_params = json.dumps(val)
             except ValueError:
                 raise ValueError("The set of transport_params are not JSON-able")
        else:
            raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_workdir(self):
        return self.dbcomputer.workdir

    def set_workdir(self,val):
        if self.to_be_stored:
            self.dbcomputer.workdir = val
        else:
            raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_hostname(self):
        return self.dbcomputer.hostname

    def set_hostname(self,val):
        if self.to_be_stored:
            self.dbcomputer.hostname = val
        else:
            raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_scheduler_type(self):
        return self.dbcomputer.scheduler_type

    def set_scheduler_type(self,val):
        if self.to_be_stored:
            self.dbcomputer.scheduler_type = val
        else:
            raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_transport_type(self):
        return self.dbcomputer.transport_type

    def set_transport_type(self,val):
        if self.to_be_stored:
            self.dbcomputer.transport_type = val
        else:
            raise ModificationNotAllowed("Cannot set a property after having stored the entry")
        
    def get_scheduler(self):
        import aida.scheduler
        from aida.common.pluginloader import load_plugin

        try:
            ThisPlugin = load_plugin(aida.scheduler.Scheduler, 'aida.scheduler.plugins',
                               self.get_scheduler_type())
            # I call the init without any parameter
            return ThisPlugin()
        except MissingPluginError as e:
            raise ConfigurationError('No scheduler found for {} [type {}], message: {}'.format(
                self.hostname, self.scheduler_type, e.message))


