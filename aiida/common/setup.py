import os

import aiida

# The username (email) used by the default superuser, that should also run 
# as the daemon
DEFAULT_AIIDA_USER="aiida@localhost"

AIIDA_CONFIG_FOLDER = "~/.aiida"
CONFIG_FNAME = 'config.json'
SECRET_KEY_FNAME = 'secret_key.dat'

DAEMON_SUBDIR    = "daemon"
LOG_DIR          = "daemon/log"
DAEMON_CONF_FILE = "aiida_daemon.conf"

# The key inside the configuration file
DEFAULT_USER_CONFIG_FIELD = 'default_user_email'

def backup_config(): 
    """
    Backup the previous configuration file.
    """  
    import shutil
    aiida_dir   = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    conf_file   = os.path.join(aiida_dir, CONFIG_FNAME)
    if (os.path.isfile(conf_file)):
        shutil.copy(conf_file, conf_file+"~")
    
def get_config():
    """
    Load the previous configuration and return a dictionary.
    
    :raise ConfigurationError: If no configuration file is found.
    :raise ValueError: if the JSON is not valid.
    """
    import json
    
    from aiida.common.exceptions import ConfigurationError
    
    aiida_dir   = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    conf_file   = os.path.join(aiida_dir, CONFIG_FNAME)
    try:
        with open(conf_file,"r") as json_file:
            return json.load(json_file)
    except IOError:
        # No configuration file
        raise ConfigurationError("No configuration file found")

def store_config(confs):
    """
    Given a configuration dictionary, stores it in the configuration file.
    
    :param confs: the dictionary to store.
    """
    import json
    
    aiida_dir    = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    conf_file   = os.path.join(aiida_dir, CONFIG_FNAME)
    with open(conf_file,"w") as json_file:
        json.dump(confs, json_file)

def install_daemon_files(aiida_dir, daemon_dir, log_dir, local_user):
    """
    Install the files needed to run the daemon.
    """
    daemon_conf = """
[unix_http_server]
file={daemon_dir}/supervisord.sock   ; (the path to the socket file)

[supervisord]
logfile={log_dir}/supervisord.log
logfile_maxbytes=10MB 
logfile_backups=2         
loglevel=info                
pidfile={daemon_dir}/supervisord.pid
nodaemon=false               
minfds=1024                 
minprocs=200                 

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///{daemon_dir}/supervisord.sock

;=======================================
; Main AiiDA Daemon
;=======================================
[program:aiida-daemon]
command=python "{aiida_module_dir}/djsite/manage.py" celeryd --loglevel=INFO
directory={daemon_dir}
user={local_user}
numprocs=1
stdout_logfile={log_dir}/aiida_daemon.log
stderr_logfile={log_dir}/aiida_daemon.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=30
process_name=%(process_num)s

; ==========================================
; AiiDA Deamon BEAT - for scheduled tasks
; ==========================================
[program:aiida-daemon-beat]
command=python "{aiida_module_dir}/djsite/manage.py" celerybeat
directory={daemon_dir}
user={local_user}
numprocs=1
stdout_logfile={log_dir}/aiida_daemon_beat.log
stderr_logfile={log_dir}/aiida_daemon_beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs = 30
process_name=%(process_num)s
"""
    with open(os.path.join(aiida_dir,daemon_dir,DAEMON_CONF_FILE), "w") as f:
        f.write(daemon_conf.format(daemon_dir=daemon_dir, log_dir=log_dir,
            local_user=local_user,
            aiida_module_dir = os.path.split(os.path.abspath(
                aiida.__file__))[0]))

def generate_random_secret_key():
    """
    Generate a random secret key to put in the django settings module.
    
    This should be the same function used by Django in
    core/management/commands/startproject.
    """
    from django.utils.crypto import get_random_string
    
    # Create a random SECRET_KEY hash to put it in the main settings.
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    secret_key = get_random_string(50, chars)
    return secret_key

def try_create_secret_key():
    """
    Creates a new secret key file, if this does not exist, otherwise do nothing
    (to avoid that the secret key is regenerated each time).
    
    If you really want that the secret key is regenerated, delete the
    secret key file, and then call this function again.
    """
    aiida_dir            = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    secret_key_full_name = os.path.join(aiida_dir,SECRET_KEY_FNAME)
    
    if os.path.exists(secret_key_full_name):
        return
    
    with open(secret_key_full_name, 'w') as f:
        f.write(generate_random_secret_key())
    
def get_secret_key():
    """
    Return the secret key.
    
    Raise ConfigurationError if the secret key cannot be found/read from the disk.
    """
    from aiida.common.exceptions import ConfigurationError
    
    aiida_dir            = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    secret_key_full_name = os.path.join(aiida_dir,SECRET_KEY_FNAME)
    
    try:
        with open(secret_key_full_name) as f:
            secret_key = f.read()
    except (OSError, IOError):
        raise ConfigurationError("Unable to find the secret key file "
                                 "(or to read from it): did you run "
                                 "'verdi install'?")
                                 
    return secret_key.strip()

def ask_for_timezone(existing_timezone):
    """
    Interactively ask for the current timezone.
    
    :param existing_timezone: the string for the already configured timezone,
      or None if there is no previous configuration.
    :return: a string with the timezone as chosen by the user.
    """
    import time
    import pytz
    import datetime
    
    if existing_timezone is not None:
        print "Configured timezone: {}".format(existing_timezone)
        answer = raw_input("Do you want to change it? [y/N] ")
        if answer.lower() != 'y':
            # No configuration to do, return the existing value
            return existing_timezone
    
    # If we are here, either there was no configuration, or the user asked to
    # change it.
    
    # Try to get a set of valid timezones, as suggested in 
    # one of the answers of http://stackoverflow.com/questions/7669938

    # Get some information on the local TZ and the local offset, doing the
    # right thing it we are in DST. (time.daylight just tells whether the
    # local timezone has DST, not the current state
    if time.daylight and time.localtime().tm_isdst > 0:
        local_offset = time.altzone
        localtz = time.tzname[1]
    else:
        local_offset = time.timezone
        localtz = time.tzname[0]
     
    # convert to a datetime.timedelta object   
    local_offset = datetime.timedelta(seconds=-local_offset)
    
    valid_zones = []
    # Iterate over all valid TZ
    for name in pytz.all_timezones:
        # get the TZ obejct
        timezone = pytz.timezone(name)
        #skip if a TZ has no info
        if not hasattr(timezone, '_tzinfos'):
            continue
        # Append to the list if the offset and the localtz match
        for (utcoffset, daylight, tzname), _ in timezone._tzinfos.iteritems():
            if utcoffset == local_offset and tzname == localtz:
                valid_zones.append(name)       
    
    print "# These seem to be valid timezones for the current environment:"
    for z in sorted(valid_zones):
        print "* {}".format(z)
    
    print "# Type here a valid timezone (one of the above, or if the detection "
    print "# did not work, any other valid timezone string)"

    valid_zone = False
    while not valid_zone:
        answer = raw_input("Insert your timezone: ")
        if answer in pytz.all_timezones:
            valid_zone = True
        else:
            print "* ERROR! Invalid timezone inserted."
            print "*        Valid timezones can be obtainedin a python shell with"
            print "*        the 'import pytz; print pytz.all_timezones' command"
    
    return answer

def create_base_dirs():
    """
    Create dirs for AiiDA, and install default daemon files.
    """
    import getpass
    
    # For the daemon, to be hard-coded when ok    
    aiida_dir        = os.path.expanduser(AIIDA_CONFIG_FOLDER) 
    aiida_daemon_dir = os.path.join(aiida_dir,DAEMON_SUBDIR)
    aiida_log_dir    = os.path.join(aiida_dir,LOG_DIR)
    local_user       = getpass.getuser()
  
    if (not os.path.isdir(aiida_dir)):
        os.makedirs(aiida_dir)
    
    if (not os.path.isdir(aiida_daemon_dir)):
        os.makedirs(aiida_daemon_dir)
      
    if (not os.path.isdir(aiida_log_dir)):
        os.makedirs(aiida_log_dir)
        
    # Install daemon files 
    install_daemon_files(aiida_dir, aiida_daemon_dir, aiida_log_dir, local_user)

    # Create the secret key file, if needed
    try_create_secret_key()

def create_configuration():    
    import readline
    from aiida.common.exceptions import ConfigurationError
    # BE CAREFUL: THIS IS THE DJANGO VALIDATIONERROR
    from django.core.exceptions import ValidationError as DjangoValidationError
    from aiida.common.additions import CustomEmailValidator
    
    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    
    try:
        confs = get_config()
        backup_config()
    except ConfigurationError:
        # No configuration file found
        confs = {}  

    # Set the timezone
    timezone = ask_for_timezone(existing_timezone=confs.get('TIMEZONE', None))
    confs['TIMEZONE'] = timezone
      
    try:
        valid_email = False
        email_validator = CustomEmailValidator()
        readline.set_startup_hook(lambda: readline.insert_text(
                confs.get(DEFAULT_USER_CONFIG_FIELD, DEFAULT_AIIDA_USER)))
        while not valid_email:
            confs[DEFAULT_USER_CONFIG_FIELD] = raw_input('Default user email: ')
            try:
                email_validator(confs[DEFAULT_USER_CONFIG_FIELD])
                valid_email = True
            except DjangoValidationError:
                print "** Invalid email provided!"
                
        
        readline.set_startup_hook(lambda: readline.insert_text(
                confs.get('AIIDADB_ENGINE','sqlite3')))
        confs['AIIDADB_ENGINE'] = raw_input('Database engine: ')

        if 'sqlite' in confs['AIIDADB_ENGINE']:
            confs['AIIDADB_ENGINE'] = 'sqlite3'          
            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_NAME', os.path.join(aiida_dir,"aiida.db"))))
            confs['AIIDADB_NAME'] = raw_input('AiiDA Database location: ')
            confs['AIIDADB_HOST'] = ""
            confs['AIIDADB_PORT'] = ""
            confs['AIIDADB_USER'] = ""
            confs['AIIDADB_PASS'] = ""

        elif 'postgre' in confs['AIIDADB_ENGINE']:
            confs['AIIDADB_ENGINE'] = 'postgresql_psycopg2'
            
            old_host = confs.get('AIIDADB_HOST','localhost')
            if not old_host:
                old_host = 'localhost'
            readline.set_startup_hook(lambda: readline.insert_text(
                    old_host))
            confs['AIIDADB_HOST'] = raw_input('PostgreSQL host: ')

            old_port = confs.get('AIIDADB_PORT','5432')
            if not old_port:
                old_port = '5432'
            readline.set_startup_hook(lambda: readline.insert_text(
                    old_port))
            confs['AIIDADB_PORT'] = raw_input('PostgreSQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_NAME','aiidadb')))
            confs['AIIDADB_NAME'] = raw_input('AiiDA Database name: ')

            old_user = confs.get('AIIDADB_USER','aiida')
            if not old_user:
                old_user = 'aiida'
            readline.set_startup_hook(lambda: readline.insert_text(
                    old_user))
            confs['AIIDADB_USER'] = raw_input('AiiDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_PASS','aiida_password')))
            confs['AIIDADB_PASS'] = raw_input('AiiDA Database password: ')

        elif 'mysql' in confs['AIIDADB_ENGINE']:
            confs['AIIDADB_ENGINE'] = 'mysql'
            
            old_host = confs.get('AIIDADB_HOST','localhost')
            if not old_host:
                old_host = 'localhost'
            readline.set_startup_hook(lambda: readline.insert_text(
                old_host))
            confs['AIIDADB_HOST'] = raw_input('mySQL host: ')

            old_port = confs.get('AIIDADB_PORT','3306')
            if not old_port:
                old_port = '3306'
            readline.set_startup_hook(lambda: readline.insert_text(
                    old_port))
            confs['AIIDADB_PORT'] = raw_input('mySQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_NAME','aiidadb')))
            confs['AIIDADB_NAME'] = raw_input('AiiDA Database name: ')

            old_user = confs.get('AIIDADB_USER','aiida')
            if not old_user:
                old_user = 'aiida'
            readline.set_startup_hook(lambda: readline.insert_text(
                    old_user))
            confs['AIIDADB_USER'] = raw_input('AiiDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_PASS','aiida_password')))
            confs['AIIDADB_PASS'] = raw_input('AiiDA Database password: ')
        else:
            raise ValueError("You have to specify a valid database "
               "(valid choices are 'sqlite', 'mysql', 'postgres')")

        readline.set_startup_hook(lambda: readline.insert_text(
                confs.get('AIIDADB_REPOSITORY',
                          os.path.join(aiida_dir,"repository/"))))
        confs['AIIDADB_REPOSITORY'] = raw_input('AiiDA repository directory: ')
        if (not os.path.isdir(confs['AIIDADB_REPOSITORY'])):
            os.makedirs(confs['AIIDADB_REPOSITORY'])

        store_config(confs)
    finally:
        readline.set_startup_hook(lambda: readline.insert_text(""))

        
# A table of properties.
# The key is the property name to use in the code;
# The value is a tuple, where:
# - the first entry is a string used as the key in the
#   JSON config file
# - the second is the expected data type for data 
#   conversion if the property is passed as a string.
#   For valid data type strings, see the implementation of set_property
# - the third entry is the description of the field
# - the fourth entry is the default value. Use _NoDefaultValue() if you want 
#   an exception to be raised if no property is found.

class _NoDefaultValue(object):
    pass

_property_table = {
    "tests.use_sqlite": (
        "use_inmemory_sqlite_for_tests",
        "bool",
        "Whether to use an in-memory SQLite DB for tests (default: True)",
        True),
    }

def get_property(name, default=_NoDefaultValue()):
    """
    Get a property from the json file.
    
    :param default: if provided, this value is returned if no value is found
      in the database.
    
    :raise ValueError: if the given name is not a valid property (as stored in
      the _property_table dictionary).
    :raise KeyError: if the given property is not found in the config file, and
      no default value is given or provided in _property_table.
    """
    from aiida.common.exceptions import ConfigurationError
    
    try:
        key, _, _, table_defval = _property_table[name]
    except KeyError:
        raise ValueError("{} is not a recognized property".format(name))
    
    try:
        try:
            config = get_config()
            return config[key]
        except ConfigurationError:
            raise KeyError("No configuration file found")
    except KeyError:
        if isinstance(default, _NoDefaultValue):
            if isinstance(table_defval, _NoDefaultValue):
                raise
            else:
                return table_defval
        else:
            return default

def del_property(name):
    """
    Delete a property in the json file.
    
    :raise: KeyError if the key is not found in the configuration file.
    """
    from aiida.common.exceptions import ConfigurationError
    
    try:
        key, _, _, _ = _property_table[name]
    except KeyError:
        raise ValueError("{} is not a recognized property".format(name))
    
    try:
        config = get_config()
        del config[key]
    except ConfigurationError:
        raise KeyError("No configuration file found")
        
    # If we are here, no exception was raised
    store_config(config)
    
def set_property(name, value):
    """
    Set a property in the json file.
    
    :param name: The name of the property value to set.
    :param value: the value to set. If it is a string, it is possibly casted
      to the correct type according to the information in the _property_table
      dictionary.
    
    :raise ValueError: if the provided name is not among the set of valid 
      properties, or if the value provided as a string cannot be casted to the
      correct type.
    """
    from aiida.common.exceptions import ConfigurationError

    try:
        key, type_string, _, _ = _property_table[name]
    except KeyError:
        raise ValueError("'{}' is not a recognized property".format(name))

    actual_value = False

    if type_string == "bool":
        if isinstance(value, basestring):
            if value.strip().lower() in ["0", "false", "f"]:            
                actual_value = False
            elif value.strip().lower() in ["1", "true", "t"]:
                actual_value = True
            else:
                raise ValueError("Invalid bool value for property {}".format(name))
        else:
            actual_value = bool(value)
    else:
        # Implement here other data types
        raise NotImplementedError("Type string '{}' not implemented yet".format(
            type_string))
        
    try:
        config = get_config()
    except ConfigurationError:
        config = {}

    config[key] = actual_value
    
    store_config(config)
    