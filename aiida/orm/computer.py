# -*- coding: utf-8 -*-
from aiida.common.exceptions import (
    ConfigurationError, DbContentError, InvalidOperation,
    MissingPluginError)
from aiida.common.utils import classproperty

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

def delete_computer(computer):
    """
    Delete a computer from the DB. 
    It assumes that the DB backend does the proper checks and avoids
    to delete computers that have nodes attached to them.
    
    Implemented as a function on purpose, otherwise complicated logic would be
    needed to set the internal state of the object after calling 
    computer.delete(). 
    """
    from django.db.models.deletion import ProtectedError
    if not isinstance(computer, Computer):
        raise TypeError("computer must be an instance of "
                        "aiida.orm.computer.Computer")

    try:    
        computer.dbcomputer.delete()
    except ProtectedError:
        raise InvalidOperation("Unable to delete the requested computer: there"
                               "is at least one node using this computer")

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
    
    _logger = logging.getLogger(__name__)
        
    @classproperty
    def _conf_attributes(self):
        """
        Return the configuration attributes to be used in the 'setup' phase.
    
        The return value is a list of tuples. Each tuple has three elements:
        1. an internal name (used to find the 
           _set_internalname_string, and get_internalname_string methods)
        2. a short human-readable name
        3. A long human-readable description
        4. True if it is a multi-line input, False otherwise  
    
        For the implementation, see in aiida.cmdline.computer
        
        .. note: you can define a ``_shouldcall_internalname`` method that returns
          either True or False if the specific configuration option has to be
          called or not. If such a method is not found, the option is always 
          asked to the user. In this case, you typically also want to define a
          ``_cleanup_internalname`` method to remove any previous configuration 
          associated to internalname, in case ``_shouldcall_internalname``
          returns False.
        
        .. note: IMPORTANT! For each entry, remember to define the 
          ``_set_internalname_string`` and ``get_internalname_string`` methods.
          Moreover, the ``_set_internalname_string`` method should also
          immediately validate the value. 
        
        ..note: Defining it as a property increases the overall execution
          of the code because it does not require to calculate
          Transport.get_valid_transports() at each load of this class.
        """
        from aiida.transport import Transport
        from aiida.scheduler import Scheduler

        return [
            ("hostname",
             "Fully-qualified hostname",
             "The fully qualified host-name of this computer",
             False,
            ),
            ("description",
             "Description",
             "A human-readable description of this computer",
             False,
            ),                        
            ("enabled_state",
             "Enabled",
             "True or False; if False, the computer is disabled and calculations\n"
             "associated with it will not be submitted",
             False,
            ), 
            ("transport_type",
             "Transport type",
             "The name of the transport to be used. Valid names are: {}".format(
                ",".join(Transport.get_valid_transports())),
             False,
             ),
            ("scheduler_type",
             "Scheduler type",
             "The name of the scheduler to be used. Valid names are: {}".format(
                ",".join(Scheduler.get_valid_schedulers())),
             False,
             ),
            ("workdir",
             "AiiDA work directory",
             "The absolute path of the directory on the computer where AiiDA will\n"
             "run the calculations (typically, the scratch of the computer). You\n"
             "can use the {username} replacement, that will be replaced by your\n"
             "username on the remote computer",
             False,
             ),
            # Must be called after the scheduler!
            ("mpirun_command",
             "mpirun command",
             "The mpirun command needed on the cluster to run parallel MPI\n"
             "programs. You can use the {tot_num_mpiprocs} replacement, that will be \n"
             "replaced by the total number of cpus, or the other scheduler-dependent\n"
             "replacement fields (see the scheduler docs for more information)",
             False,
             ),
             ("default_mpiprocs_per_machine",
             "Default number of CPUs per machine",
             "Enter here the default number of CPUs per machine (node) that \n"
             "should be used if nothing is otherwise specified. Leave empty \n"
             "if you do not want to provide a default value.\n",
             False,
             ),           
            ("prepend_text",
             "Text to prepend to each command execution",
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
        from django.core.exceptions import ObjectDoesNotExist
        from aiida.common.exceptions import NotExistent 
        
        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            if kwargs:
                raise ValueError("If you pass a uuid, you cannot pass any "
                                 "further parameter")
            try:
                dbcomputer = DbComputer.objects.get(uuid=uuid)
            except ObjectDoesNotExist:
                raise NotExistent("No entry with UUID={} found".format(uuid))

            self._dbcomputer = dbcomputer
        else:            
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
    
            # Set all remaining parameters, stop if unknown
            self.set(**kwargs)

    def set(self, **kwargs):
        import collections
        
        for k, v in kwargs.iteritems():
            try:
                method = getattr(self,'set_{}'.format(k))
            except AttributeError:
                raise ValueError("Unable to set '{0}', no set_{0} method "
                                 "found".format(k))
            if not isinstance(method, collections.Callable):
                raise ValueError("Unable to set '{0}', set_{0} is not "
                                 "callable!".format(k))
            method(v)

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
        ret_lines.append("Computer name:     {}".format(self.name))
        ret_lines.append(" * PK:             {}".format(self.pk))
        ret_lines.append(" * UUID:           {}".format(self.uuid))
        ret_lines.append(" * Description:    {}".format(self.description))
        ret_lines.append(" * Hostname:       {}".format(self.hostname))
        ret_lines.append(" * Transport type: {}".format(self.get_transport_type()))
        ret_lines.append(" * Scheduler type: {}".format(self.get_scheduler_type()))
        ret_lines.append(" * Work directory: {}".format(self.get_workdir()))
        ret_lines.append(" * mpirun command: {}".format(" ".join(
            self.get_mpirun_command())))
        def_cpus_machine = self.get_default_mpiprocs_per_machine()
        if def_cpus_machine is not None:
            ret_lines.append(" * Default number of cpus per machine: {}".format(
                def_cpus_machine))
        ret_lines.append(" * Used by:        {} nodes".format(
            len(self.dbcomputer.dbnodes.all())))
        
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

    def _get_default_mpiprocs_per_machine_string(self):
        """
        Get the default number of CPUs per machine (node) as a string
        """
        def_cpus_per_machine = self.get_default_mpiprocs_per_machine()
        if def_cpus_per_machine is None:
            return ""
        else:
            return str(def_cpus_per_machine)
        

    def _set_default_mpiprocs_per_machine_string(self, string):
        """
        Set the default number of CPUs per machine (node) from a string (set to
        None if the string is empty)
        """       
        from aiida.common.exceptions import ValidationError
        
        if not string:
            def_cpus_per_machine = None
        else:
            try:
                def_cpus_per_machine = int(string)
            except ValueError:
                raise ValidationError("Invalid value for default_mpiprocs_per_machine, "
                                      "must be a positive integer, or an empty "
                                      "string if you do not want to provide a "
                                      "default value.")                
        
        self._default_mpiprocs_per_machine_validator(def_cpus_per_machine)
        
        self.set_default_mpiprocs_per_machine(def_cpus_per_machine)

    def _default_mpiprocs_per_machine_validator(self, def_cpus_per_machine):
        """
        Validates the default number of CPUs per machine (node)
        """
        from aiida.common.exceptions import ValidationError

        if def_cpus_per_machine is None:
            return
        
        if not isinstance(def_cpus_per_machine, (
                int,long)) or def_cpus_per_machine <= 0:
            raise ValidationError("Invalid value for default_mpiprocs_per_machine, "
                                  "must be a positive integer, or an empty "
                                  "string if you do not want to provide a "
                                  "default value.")
        
    def _shouldcall_default_mpiprocs_per_machine(self):
        """
        Return True if the scheduler can accept 'default_mpiprocs_per_machine',
        False otherwise.
        
        If there is a problem in determining the scheduler, return True to
        avoid exceptions.
        """
        from aiida.scheduler import SchedulerFactory
        
        try:
            SchedulerClass = SchedulerFactory(self.get_scheduler_type())
        except MissingPluginError:
            # Return True if the Scheduler was not found...
            return True
    
        JobResourceClass = SchedulerClass._job_resource_class
        if JobResourceClass is None:
            # Odd situation...
            return False
        
        return JobResourceClass.accepts_default_mpiprocs_per_machine()

    def _cleanup_default_mpiprocs_per_machine(self):
        """
        Called by the command line utility in case the _shouldcall_ routine
        returns False, to remove possible values that were previously set
        (e.g. if one used before a pbspro scheduler and set the
        default_mpiprocs_per_machine, and then switches to sge, the question is
        not asked, but the value should also be removed from the DB.
        """
        self.set_default_mpiprocs_per_machine(None)

    def _get_enabled_state_string(self):
        return "True" if self.is_enabled() else "False"

    def _set_enabled_state_string(self,string):
        """
        Set the enabled state starting from a string.
        """
        from aiida.common.exceptions import ValidationError
        
        upper_string = string.upper()
        if upper_string in ['YES', 'Y', 'T', 'TRUE']:
            enabled_state = True
        elif upper_string in ['NO', 'N', 'F', 'FALSE']:
            enabled_state = False
        else:
            raise ValidationError("Invalid value '{}' for the enabled state, must "
                                  "be a boolean".format(string))
            
        self._enabled_state_validator(enabled_state)
        
        self.set_enabled_state(enabled_state)
        
    @classmethod
    def _enabled_state_validator(cls,enabled_state):
        """
        Validates the hostname.
        """
        from aiida.common.exceptions import ValidationError
    
        if not isinstance(enabled_state,bool):
            raise ValidationError("Invalid value '{}' for the enabled state, must "
                                  "be a boolean".format(str(enabled_state)))

    def _get_description_string(self):
        return self.get_description()

    def _set_description_string(self,string):
        """
        Set the description starting from a string.
        """
        self._description_validator(string)
        self.set_description(string)
        
    @classmethod
    def _description_validator(cls,description):
        """
        Validates the description.
        """
        # The description is always valid 
        pass

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

    def _get_prepend_text_string(self):
        return self.get_prepend_text()

    def _set_prepend_text_string(self,string):
        """
        Set the prepend_text starting from a string.
        """
        self._prepend_text_validator(string)
        self.set_prepend_text(string)

    @classmethod
    def _prepend_text_validator(cls, prepend_text):
        """
        Validates the prepend text string.
        """
        # no validation done
        pass

    def _get_append_text_string(self):
        return self.get_append_text()

    def _set_append_text_string(self,string):
        """
        Set the append_text starting from a string.
        """
        self._append_text_validator(string)
        self.set_append_text(string)

    @classmethod
    def _append_text_validator(cls, append_text):
        """
        Validates the append text string.
        """
        # no validation done
        pass

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
            raise ValidationError("In workdir there is an unknown replacement "
                                  "field '{}'".format(e.message))
        except ValueError as e:
            raise ValidationError("Error in the string: '{}'".format(e.message))
        
        if not os.path.isabs(convertedwd):
            raise ValidationError("The workdir must be an absolute path")

    def _get_mpirun_command_string(self):
        return " ".join(self.get_mpirun_command())

    def _set_mpirun_command_string(self,string):
        """
        Set the mpirun command string (from a string to a list).
        """
        converted_cmd = str(string).strip().split(" ")
        if converted_cmd == ['']:
            converted_cmd = []
        self._mpirun_command_validator(converted_cmd)
        self.set_mpirun_command(converted_cmd)

    def _mpirun_command_validator(self, mpirun_cmd):
        """
        Validates the mpirun_command variable. MUST be called after properly
        checking for a valid scheduler.
        """
        from aiida.common.exceptions import ValidationError

        if not isinstance(mpirun_cmd,(tuple,list)) or not(
            all(isinstance(i,basestring) for i in mpirun_cmd)):
                raise ValidationError("the mpirun_command must be a list of strings")

        try:
            job_resource_keys = self.get_scheduler()._job_resource_class.get_valid_keys()
        except MissingPluginError:
            raise ValidationError("Unable to load the scheduler for this computer")
        
        subst = {i: 'value' for i in job_resource_keys}
        subst['tot_num_mpiprocs'] = 'value'        

        try:
            for arg in mpirun_cmd:
                arg.format(**subst)
        except KeyError as e:
            raise ValidationError("In workdir there is an unknown replacement "
                                  "field '{}'".format(e.message))
        except ValueError as e:
            raise ValidationError("Error in the string: '{}'".format(e.message))


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

        self._description_validator(self.get_description())

        self._enabled_state_validator(self.is_enabled())

        self._transport_type_validator(self.get_transport_type())

        self._scheduler_type_validator(self.get_scheduler_type())

        self._workdir_validator(self.get_workdir())

        try:
            mpirun_cmd = self.get_mpirun_command()
        except DbContentError:
            raise ValidationError("Error in the DB content of the transport_params")

        # To be called AFTER the validation of the scheduler
        self._mpirun_command_validator(mpirun_cmd)


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
    def name(self):
        return self.dbcomputer.name

    @property
    def description(self):
        return self.dbcomputer.description

    @property
    def hostname(self):
        return self.dbcomputer.hostname
        
    def _get_metadata(self):
        import json
        return json.loads(self.dbcomputer.metadata)

    def _set_metadata(self,metadata_dict):
        """
        Set the metadata.
        
        .. note: You still need to call the .store() method to actually save
           data to the database! (The store method can be called multiple
           times, differently from AiiDA Node objects).
        """
        import json
#        if not self.to_be_stored:
#            raise ModificationNotAllowed("Cannot set a property after having stored the entry")
        self.dbcomputer.metadata = json.dumps(metadata_dict)

    def _del_property(self,k,raise_exception=True):
        olddata = self._get_metadata()
        try:
            del olddata[k]
        except KeyError:
            if raise_exception:
                raise AttributeError("'{}' property not found".format(k))
            else:
                # Do not reset the metadata, it is not necessary
                return
        self._set_metadata(olddata)

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
        """
        Return the mpirun command. Must be a list of strings, that will be
        then joined with spaces when submitting.
        
        I also provide a sensible default that may be ok in many cases.
        """
        return self._get_property("mpirun_command",
            ["mpirun", "-np", "{tot_num_mpiprocs}"])

    def set_mpirun_command(self,val):
        """
        Set the mpirun command. It must be a list of strings (you can use
        string.split() if you have a single, space-separated string).
        """
        if not isinstance(val,(tuple,list)) or not(
            all(isinstance(i,basestring) for i in val)):
                raise TypeError("the mpirun_command must be a list of strings")
        self._set_property("mpirun_command", val)

    def get_default_mpiprocs_per_machine(self):
        """
        Return the default number of CPUs per machine (node) for this computer,
        or None if it was not set.
        """
        return self._get_property("default_mpiprocs_per_machine",
            None)
    
    def set_default_mpiprocs_per_machine(self, def_cpus_per_machine):
        """
        Set the default number of CPUs per machine (node) for this computer.
        Accepts None if you do not want to set this value.
        """
        if def_cpus_per_machine is None:
            self._del_property("default_mpiprocs_per_machine", raise_exception=False)
        else:
            if not isinstance(def_cpus_per_machine, (int,long)):
                raise TypeError("def_cpus_per_machine must be an integer (or None)")
        self._set_property("default_mpiprocs_per_machine", def_cpus_per_machine)

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
        try:
            return self.dbcomputer.get_workdir()
        except ConfigurationError:
            # This happens the first time: I provide a reasonable default value
            return "/scratch/{username}/aiida_run/"

    def set_workdir(self,val):
        #if self.to_be_stored:
        metadata = self._get_metadata()
        metadata['workdir'] = val
        self._set_metadata(metadata)
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

    def get_description(self):
        return self.dbcomputer.description

    def set_description(self,val):
        #if self.to_be_stored:
            self.dbcomputer.description = val
        #else:
        #    raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def is_enabled(self):
        return self.dbcomputer.enabled

    def set_enabled_state(self, enabled):
        self.dbcomputer.enabled = enabled

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
    
    def get_transport_class(self):
        from aiida.transport import TransportFactory
        
        try:
            # I return the class, not an instance
            return TransportFactory(self.get_transport_type())
        except MissingPluginError as e:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.name, self.get_transport_type(), e.message))
        
    
    def get_scheduler(self):
        from aiida.scheduler import SchedulerFactory

        try:
            ThisPlugin = SchedulerFactory(self.get_scheduler_type())
            # I call the init without any parameter
            return ThisPlugin()
        except MissingPluginError as e:
            raise ConfigurationError('No scheduler found for {} [type {}], message: {}'.format(
                self.name, self.get_scheduler_type(), e.message))

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))
    
    def __str__(self):
        if self.is_enabled():
            return "{} ({}), pk={}".format(self.name, self.hostname,
                                           self.pk)
        else:
            return "{} ({}) [DISABLED], pk={}".format(self.name, self.hostname,
                                                      self.pk)
