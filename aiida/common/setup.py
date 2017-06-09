# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
import aiida
import logging
import json

# The username (email) used by the default superuser, that should also run
# as the daemon
from aiida.common.exceptions import ConfigurationError


DEFAULT_AIIDA_USER = "aiida@localhost"

AIIDA_CONFIG_FOLDER = "~/.aiida"
CONFIG_FNAME = 'config.json'
SECRET_KEY_FNAME = 'secret_key.dat'

DAEMON_SUBDIR = "daemon"
LOG_SUBDIR = "daemon/log"
DAEMON_CONF_FILE = "aiida_daemon.conf"

WORKFLOWS_SUBDIR = "workflows"

# The key inside the configuration file
DEFAULT_USER_CONFIG_FIELD = 'default_user_email'

# This is the default process used by load_dbenv when no process is specified
DEFAULT_PROCESS = 'verdi'

# The default umask for file creation under AIIDA_CONFIG_FOLDER
DEFAULT_UMASK = 0077

# Profile keys
aiidadb_backend_key = "AIIDADB_BACKEND"

# Profile values
aiidadb_backend_value_django = "django"

# Repository for tests
TEMP_TEST_REPO = None

# Keyword that is used in test profiles, databases and repositories to
# differentiate them from non-testing ones.
TEST_KEYWORD = "test_"


def get_aiida_dir():
    return os.path.expanduser(AIIDA_CONFIG_FOLDER)


def backup_config():
    """
    Backup the previous configuration file.
    """
    import shutil

    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    conf_file = os.path.join(aiida_dir, CONFIG_FNAME)
    if (os.path.isfile(conf_file)):
        old_umask = os.umask(DEFAULT_UMASK)
        try:
            shutil.copy(conf_file, conf_file + "~")
        finally:
            os.umask(old_umask)


def get_config():
    """
    Return all the configurations
    """
    import json
    from aiida.common.exceptions import ConfigurationError
    from aiida.backends.settings import IN_DOC_MODE, DUMMY_CONF_FILE

    if IN_DOC_MODE:
        return DUMMY_CONF_FILE

    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    conf_file = os.path.join(aiida_dir, CONFIG_FNAME)
    try:
        with open(conf_file, "r") as json_file:
            return json.load(json_file)
    except IOError:
        # No configuration file
        raise ConfigurationError("No configuration file found")


def get_or_create_config():
    from aiida.common.exceptions import ConfigurationError
    try:
        config = get_config()
    except ConfigurationError:
        config = {}
        store_config(config)
    return config


def store_config(confs):
    """
    Given a configuration dictionary, stores it in the configuration file.

    :param confs: the dictionary to store.
    """
    import json

    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    conf_file = os.path.join(aiida_dir, CONFIG_FNAME)
    old_umask = os.umask(DEFAULT_UMASK)
    try:
        with open(conf_file, "w") as json_file:
            json.dump(confs, json_file)
    finally:
        os.umask(old_umask)


def install_daemon_files(aiida_dir, daemon_dir, log_dir, local_user,
                         daemon_conf=None):
    """
    Install the files needed to run the daemon.
    """
    local_daemon_conf = """
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
command=celery worker -A tasks --loglevel=INFO --beat --schedule={daemon_dir}/celerybeat-schedule
directory={aiida_code_home}/daemon/
user={local_user}
numprocs=1
stdout_logfile={log_dir}/aiida_daemon.log
stderr_logfile={log_dir}/aiida_daemon.log
autostart=true
autorestart=true
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; When resorting to send SIGKILL to the program to terminate it
; send SIGKILL to its whole process group instead,
; taking care of its children as well.
killasgroup=true

; Set Celery priority higher than default (999)
; so, if rabbitmq is supervised, it will start first.
priority=1000
"""
    if daemon_conf is None:
        daemon_conf = local_daemon_conf

    old_umask = os.umask(DEFAULT_UMASK)
    try:
        with open(os.path.join(aiida_dir, daemon_dir, DAEMON_CONF_FILE), "w") as f:
            f.write(daemon_conf.format(daemon_dir=daemon_dir, log_dir=log_dir,
                                       local_user=local_user,
                                       aiida_code_home=os.path.split(
                                           os.path.abspath(
                                               aiida.__file__))[0]))
    finally:
        os.umask(old_umask)


def generate_random_secret_key():
    """
    Generate a random secret key to put in the django settings module.

    This should be the same function used by Django in
    core/management/commands/startproject.
    """
    from aiida.common.hashing import get_random_string

    return get_random_string(length=50)


def try_create_secret_key():
    """
    Creates a new secret key file, if this does not exist, otherwise do nothing
    (to avoid that the secret key is regenerated each time).

    If you really want that the secret key is regenerated, delete the
    secret key file, and then call this function again.
    """
    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    secret_key_full_name = os.path.join(aiida_dir, SECRET_KEY_FNAME)

    if os.path.exists(secret_key_full_name):
        # If for some reason the file is empty, regenerate it
        with open(secret_key_full_name) as f:
            if f.read().strip():
                return

    old_umask = os.umask(DEFAULT_UMASK)
    try:
        with open(secret_key_full_name, 'w') as f:
            f.write(generate_random_secret_key())
    finally:
        os.umask(old_umask)


def create_htaccess_file():
    """
    Creates a suitable .htaccess file in the .aiida folder (if it does not
    exist yet), that is important

    .. note:: some default Apache configurations ignore the ``.htaccess``
    files unless otherwise specified: read the documentation on
    how to setup properly your Apache server!

    .. note:: if a ``.htaccess`` file already exists, this is not overwritten.
    """
    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    htaccess_full_name = os.path.join(aiida_dir, ".htaccess")

    if os.path.exists(htaccess_full_name):
        return

    old_umask = os.umask(DEFAULT_UMASK)
    try:
        with open(htaccess_full_name, 'w') as f:
            f.write(
                """#### No one should read this folder!
                ## Please double check, though, that your Apache configuration honors
                ## the .htaccess files.
                deny from all
                """)
    finally:
        os.umask(old_umask)


def get_secret_key():
    """
    Return the secret key.

    Raise ConfigurationError if the secret key cannot be found/read from the disk.
    """
    from aiida.common.exceptions import ConfigurationError
    from aiida.backends.settings import IN_DOC_MODE

    if IN_DOC_MODE:
        return ""

    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    secret_key_full_name = os.path.join(aiida_dir, SECRET_KEY_FNAME)

    try:
        with open(secret_key_full_name) as f:
            secret_key = f.read()
    except (OSError, IOError):
        raise ConfigurationError("Unable to find the secret key file "
                                 "(or to read from it): did you run "
                                 "'verdi install'?")

    return secret_key.strip()


def create_base_dirs(config_dir=None):
    """
    Create dirs for AiiDA, and install default daemon files.
    """
    import getpass

    # For the daemon, to be hard-coded when ok
    aiida_dir = os.path.expanduser(config_dir or AIIDA_CONFIG_FOLDER)
    aiida_daemon_dir = os.path.join(aiida_dir, DAEMON_SUBDIR)
    aiida_log_dir = os.path.join(aiida_dir, LOG_SUBDIR)
    local_user = getpass.getuser()

    old_umask = os.umask(DEFAULT_UMASK)
    try:
        if (not os.path.isdir(aiida_dir)):
            os.makedirs(aiida_dir)

        if (not os.path.isdir(aiida_daemon_dir)):
            os.makedirs(aiida_daemon_dir)

        if (not os.path.isdir(aiida_log_dir)):
            os.makedirs(aiida_log_dir)
    finally:
        os.umask(old_umask)

    # Install daemon files
    install_daemon_files(aiida_dir, aiida_daemon_dir, aiida_log_dir, local_user)

    # Create the secret key file, if needed
    try_create_secret_key()

    create_htaccess_file()


def set_default_profile(process, profile, force_rewrite=False):
    """
    Set a default db profile to be used by a process (default for verdi,
    default for daemon, ...)

    :param process: A string identifying the process to modify (e.g. ``verdi``
      or ``daemon``).
    :param profile: A string specifying the profile that should be used
      as default.
    :param force_rewrite: if False, does not change the default profile
      if this was already set. Otherwise, forces the default profile to be
      the value specified as ``profile`` also if a default profile for the
      given ``process`` was already set.
    """
    from aiida.common.exceptions import ProfileConfigurationError

    if profile not in get_profiles_list():
        raise ProfileConfigurationError(
            'Profile {} has not been configured'.format(profile))
    confs = get_config()

    try:
        confs['default_profiles']
    except KeyError:
        confs['default_profiles'] = {}

    if force_rewrite:
        confs['default_profiles'][process] = profile
    else:
        confs['default_profiles'][process] = confs['default_profiles'].get(
            process, profile)
    backup_config()
    store_config(confs)


def get_default_profile(process):
    """
    Return the profile name to be used by process

    :return: None if no default profile is found, otherwise the name of the
      default profile for the given process
    """
    confs = get_config()
    try:
        return confs['default_profiles'][process]
    except KeyError:
        return None
        # raise ConfigurationError("No default profile found for the process {}".format(process))


def get_profiles_list():
    """
    Return the list of names of installed configurations
    """
    from aiida.common.exceptions import ConfigurationError

    all_config = get_config()
    try:
        return all_config['profiles'].keys()
    except KeyError:
        return ConfigurationError("Please run the setup")


def get_profile_config(profile, conf_dict=None, set_test_location=True):
    """
    Return the profile specific configurations

    :param conf_dict: if passed, use the provided dictionary rather than reading
        it from file.
    :param set_test_location: if True, sets a new folder for storing repository
        files during testing (to avoid to replace/overwrite the real repository)
        Set to False for calls where the folder should not be changed (i.e., if
        you only want to get the profile
    """
    import sys
    import tempfile

    from aiida.common.exceptions import (
        ConfigurationError, ProfileConfigurationError)

    if conf_dict is None:
        confs = get_config()
    else:
        confs = conf_dict

    test_string = ""
    # is_test = False
    # test_prefix = "test_"
    # if profile.startswith(test_prefix):
    #     # Use the same profile
    #     profile = profile[len(test_prefix):]
    #     is_test = True
    #     test_string = "(test) "

    try:
        profile_info = confs['profiles'][profile]
    except KeyError:
        raise ProfileConfigurationError(
            "No {}profile configuration found for {}, "
            "allowed values are: {}.".format(test_string, profile,
                                             ", ".join(get_profiles_list())))

    # if is_test and set_test_location:
    #     # import traceback
    #     # traceback.print_stack()
    #     # Change the repository and print a message
    #     ###################################################################
    #     # IMPORTANT! Choose a different repository location, otherwise
    #     # real data will be destroyed during tests!!
    #     # The location is automatically created with the tempfile module
    #     # Typically, under linux this is created under /tmp
    #     # and is not deleted at the end of the run.
    #     global TEMP_TEST_REPO
    #     if TEMP_TEST_REPO is None:
    #         TEMP_TEST_REPO = tempfile.mkdtemp(prefix=TEMP_TEST_REPO_PREFIX)
    #         # We write the local repository on stderr, so that the user running
    #         # the tests knows where the files are being stored
    #         print >> sys.stderr, "############################################"
    #         print >> sys.stderr, "# Creating LOCAL AiiDA REPOSITORY FOR TESTS:"
    #         print >> sys.stderr, "# {}".format(TEMP_TEST_REPO)
    #         print >> sys.stderr, "############################################"
    #     if 'AIIDADB_REPOSITORY_URI' not in profile_info:
    #         raise ConfigurationError("Config file has not been found, run "
    #                                  "verdi install first")
    #     profile_info['AIIDADB_REPOSITORY_URI'] = 'file://' + TEMP_TEST_REPO

    return profile_info


key_explanation = {
    "AIIDADB_ENGINE": "Database engine",
    "AIIDADB_PASS": "AiiDA Database password",
    "AIIDADB_NAME": "AiiDA Database name",
    "AIIDADB_HOST": "Database host",
    "AIIDADB_BACKEND": "AiiDA backend",
    "AIIDADB_PORT": "Database port",
    "AIIDADB_REPOSITORY_URI": "AiiDA repository directory",
    "AIIDADB_USER": "AiiDA Database user",
    DEFAULT_USER_CONFIG_FIELD: "Default user email"
}


def profile_exists(profile):
    '''return True if profile exists, else return False'''
    config = get_or_create_config()
    profiles = config.get('profiles', {})
    return profile in profiles


def update_config(settings, write=True):
    '''
    back up the config file, create or change config.

    :param settings: dictionary with the new or changed configuration
    :param write: if False, do not touch the config file (dryrun)
    :return: the new / changed configuration
    '''
    config = get_or_create_config()
    config.update(settings)
    if write:
        backup_config()
        store_config(config)
    return config


def update_profile(profile, updates, write=True):
    '''
    back up the config file, create or changes profile

    :param profile: name of the profile
    :param updates: dictionary with the new or changed profile
    :param write: if False, do not touch the config file (dryrun)
    :return: the new / changed profile
    '''
    config = get_or_create_config()
    config['profiles'] = config.get('profiles', {})
    profiles = config['profiles']
    profiles[profile] = profiles.get(profile, {})
    profile = profiles[profile]
    profile.update(updates)
    update_config(config, write=write)
    return profile


def create_config_noninteractive(profile='default', force_overwrite=False, dry_run=False, **kwargs):
    '''
    Non-interactively creates a profile.
    :raises: a ValueError if the profile exists.
    :raises: a ValueError if one of the values not a valid input
    :param profile: The profile to be configured
    :param values: The configuration inputs
    :return: The populated profile that was also stored
    '''
    if profile_exists(profile) and not force_overwrite:
        raise ValueError(
            ('profile {profile} exists! '
             'Cannot non-interactively edit a profile.').format(profile=profile)
        )

    new_profile = {}

    # setting backend
    backend_possibilities = ['django', 'sqlalchemy']
    backend_v = kwargs.pop('backend')
    if backend_v in backend_possibilities:
        new_profile['AIIDADB_BACKEND'] = backend_v
    else:
        raise ValueError(
            '{} is not a valid backend choice.'.format(
                backend_v))

    # Setting email
    from validate_email import validate_email
    email_v = kwargs.pop('email')
    if validate_email(email_v):
        new_profile[DEFAULT_USER_CONFIG_FIELD] = email_v
    else:
        raise ValueError(
            '{} is not a valid email address.'.format(
                email_v))

    # setting up db
    new_profile['AIIDADB_ENGINE'] = 'postgresql_psycopg2'
    new_profile['AIIDADB_HOST'] = kwargs.pop('db_host')
    new_profile['AIIDADB_PORT'] = kwargs.pop('db_port')
    new_profile['AIIDADB_NAME'] = kwargs.pop('db_name')
    new_profile['AIIDADB_USER'] = kwargs.pop('db_user')
    new_profile['AIIDADB_PASS'] = kwargs.pop('db_pass', '')

    # setting repo
    repo_v = kwargs.pop('repo')
    repo_path = os.path.expanduser(repo_v)
    if not os.path.isabs(repo_path):
        raise ValueError('The repository path must be an absolute path')
    if (not os.path.isdir(repo_path)):
        old_umask = os.umask(DEFAULT_UMASK)
        try:
            os.makedirs(repo_path)
        finally:
            os.umask(old_umask)
    new_profile['AIIDADB_REPOSITORY_URI'] = 'file://' + repo_path

    # finalizing
    write = not dry_run
    old_profiles = get_profiles_list()
    new_profile = update_profile(profile, new_profile, write=write)
    if write:
        if not old_profiles:
            set_default_profile('verdi', profile)
            set_default_profile('daemon', profile)
    return new_profile


def create_configuration(profile='default'):
    """
    :param profile: The profile to be configured
    :return: The populated profile that was also stored.
    """
    import readline
    from aiida.common.exceptions import ConfigurationError
    from validate_email import validate_email
    from aiida.common.utils import query_yes_no

    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)

    print("Setting up profile {}.".format(profile))

    is_test_profile = False
    if profile.startswith(TEST_KEYWORD):
        print("This is a test profile. All the data that will be stored under "
              "this profile are subjected to possible deletion or "
              "modification (repository and database data).")
        is_test_profile = True

    try:
        confs = get_config()
    except ConfigurationError:
        # No configuration file found
        confs = {}

        # first time creation check
    try:
        confs['profiles']
    except KeyError:
        confs['profiles'] = {}

    # load the old configuration for the given profile
    try:
        this_existing_confs = confs['profiles'][profile]
    except KeyError:
        this_existing_confs = {}

    # if there is an existing configuration, print it and ask if the user wants
    # to modify it.
    updating_existing_prof = False
    if this_existing_confs:
        print("The following configuration found corresponding to "
              "profile {}.".format(profile))
        for k, v in this_existing_confs.iteritems():
            if key_explanation.has_key(k):
                print("{}: {}".format(key_explanation.get(k), v))
            else:
                print("{}: {}".format(k, v))
        answ = query_yes_no("Would you like to change it?", "no")
        # If the user doesn't want to change it, we abandon
        if answ is False:
            return this_existing_confs
        # Otherwise, we continue.
        else:
            updating_existing_prof = True

    this_new_confs = {}

    try:
        # Defining the backend to be used
        aiida_backend = this_existing_confs.get('AIIDADB_BACKEND')
        if updating_existing_prof:
            print("The backend of already stored profiles can not be "
                  "changed. The current backend is {}.".format(aiida_backend))
            this_new_confs['AIIDADB_BACKEND'] = aiida_backend
        else:
            backend_possibilities = ['django', 'sqlalchemy']
            if len(backend_possibilities) > 0:

                valid_aiida_backend = False
                while not valid_aiida_backend:
                    backend_ans = raw_input(
                        'AiiDA backend (available: {} - sqlalchemy is in beta mode): '
                            .format(', '.join(backend_possibilities)))
                    if backend_ans in backend_possibilities:
                        valid_aiida_backend = True
                    else:
                        print "* ERROR! Invalid backend inserted."
                        print ("*        The available middlewares are {}"
                               .format(', '.join(backend_possibilities)))
                this_new_confs['AIIDADB_BACKEND'] = backend_ans
                aiida_backend = backend_ans

        # Setting the email
        valid_email = False
        readline.set_startup_hook(lambda: readline.insert_text(
            this_existing_confs.get(DEFAULT_USER_CONFIG_FIELD,
                                    DEFAULT_AIIDA_USER)))
        while not valid_email:
            this_new_confs[DEFAULT_USER_CONFIG_FIELD] = raw_input(
                'Default user email: ')
            valid_email = validate_email(
                this_new_confs[DEFAULT_USER_CONFIG_FIELD])
            if not valid_email:
                print "** Invalid email provided!"

        # Setting the database engine
        db_possibilities = []
        if aiida_backend == 'django':
            db_possibilities.extend(['postgresql_psycopg2', 'mysql'])
        elif aiida_backend == 'sqlalchemy':
            db_possibilities.extend(['postgresql_psycopg2'])
        if len(db_possibilities) > 0:
            db_engine = this_existing_confs.get('AIIDADB_ENGINE', db_possibilities[0])
            readline.set_startup_hook(lambda: readline.insert_text(
                db_engine))

            valid_db_engine = False
            while not valid_db_engine:
                db_engine_ans = raw_input(
                    'Database engine (available: {} - mysql is deprecated): '
                        .format(', '.join(db_possibilities)))
                if db_engine_ans in db_possibilities:
                    valid_db_engine = True
                else:
                    print "* ERROR! Invalid database engine inserted."
                    print ("*        The available engines are {}"
                           .format(', '.join(db_possibilities)))
            this_new_confs['AIIDADB_ENGINE'] = db_engine_ans

        if 'postgresql_psycopg2' in this_new_confs['AIIDADB_ENGINE']:
            this_new_confs['AIIDADB_ENGINE'] = 'postgresql_psycopg2'

            old_host = this_existing_confs.get('AIIDADB_HOST', 'localhost')
            if not old_host:
                old_host = 'localhost'
            readline.set_startup_hook(lambda: readline.insert_text(
                old_host))
            this_new_confs['AIIDADB_HOST'] = raw_input('PostgreSQL host: ')

            old_port = this_existing_confs.get('AIIDADB_PORT', '5432')
            if not old_port:
                old_port = '5432'
            readline.set_startup_hook(lambda: readline.insert_text(
                old_port))
            this_new_confs['AIIDADB_PORT'] = raw_input('PostgreSQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                this_existing_confs.get('AIIDADB_NAME')))
            db_name = ''
            while True:
                db_name = raw_input('AiiDA Database name: ')
                if is_test_profile and db_name.startswith(TEST_KEYWORD):
                    break
                if (not is_test_profile and not
                db_name.startswith(TEST_KEYWORD)):
                    break
                print("The test databases should start with the prefix {} and "
                      "the non-test databases should not have this prefix."
                      .format(TEST_KEYWORD))
            this_new_confs['AIIDADB_NAME'] = db_name

            old_user = this_existing_confs.get('AIIDADB_USER', 'aiida')
            if not old_user:
                old_user = 'aiida'
            readline.set_startup_hook(lambda: readline.insert_text(
                old_user))
            this_new_confs['AIIDADB_USER'] = raw_input('AiiDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                this_existing_confs.get('AIIDADB_PASS')))
            this_new_confs['AIIDADB_PASS'] = raw_input('AiiDA Database password: ')

        elif 'mysql' in this_new_confs['AIIDADB_ENGINE']:
            this_new_confs['AIIDADB_ENGINE'] = 'mysql'

            old_host = this_existing_confs.get('AIIDADB_HOST', 'localhost')
            if not old_host:
                old_host = 'localhost'
            readline.set_startup_hook(lambda: readline.insert_text(
                old_host))
            this_new_confs['AIIDADB_HOST'] = raw_input('mySQL host: ')

            old_port = this_existing_confs.get('AIIDADB_PORT', '3306')
            if not old_port:
                old_port = '3306'
            readline.set_startup_hook(lambda: readline.insert_text(
                old_port))
            this_new_confs['AIIDADB_PORT'] = raw_input('mySQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                this_existing_confs.get('AIIDADB_NAME')))
            db_name = ''
            while True:
                db_name = raw_input('AiiDA Database name: ')
                if is_test_profile and db_name.startswith(TEST_KEYWORD):
                    break
                if (not is_test_profile and not
                db_name.startswith(TEST_KEYWORD)):
                    break
                print("The test databases should start with the prefix {} and "
                      "the non-test databases should not have this prefix."
                      .format(TEST_KEYWORD))
            this_new_confs['AIIDADB_NAME'] = db_name

            old_user = this_existing_confs.get('AIIDADB_USER', 'aiida')
            if not old_user:
                old_user = 'aiida'
            readline.set_startup_hook(lambda: readline.insert_text(
                old_user))
            this_new_confs['AIIDADB_USER'] = raw_input('AiiDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                this_existing_confs.get('AIIDADB_PASS')))
            this_new_confs['AIIDADB_PASS'] = raw_input('AiiDA Database password: ')
        else:
            raise ValueError("You have to specify a valid database "
                             "(valid choices are 'mysql', 'postgres')")

        # This part for the time being is a bit oddly written
        # it should change in the future to add the possibility of having a
        # remote repository. Atm, I act as only a local repo is possible
        existing_repo = this_existing_confs.get('AIIDADB_REPOSITORY_URI',
                                                os.path.join(aiida_dir, "repository-{}/".format(profile)))
        default_protocol = 'file://'
        if existing_repo.startswith(default_protocol):
            existing_repo = existing_repo[len(default_protocol):]
        readline.set_startup_hook(lambda: readline.insert_text(existing_repo))
        new_repo_path = raw_input('AiiDA repository directory: ')

        # Constructing the repo path
        new_repo_path = os.path.expanduser(new_repo_path)
        if not os.path.isabs(new_repo_path):
            raise ValueError("You must specify an absolute path")

        # Check if the new repository is a test repository and if it already
        # exists.
        if is_test_profile:
            if TEST_KEYWORD not in new_repo_path:
                raise ValueError("The test prefix {} should be contained only"
                                 "in repository names related to test "
                                 "profiles.".format(TEST_KEYWORD))

            if os.path.isdir(new_repo_path):
                print("The repository {} already exists. It will be used for "
                      "tests. Any content may be deleted."
                      .format(new_repo_path))
        else:
            if TEST_KEYWORD in new_repo_path:
                raise ValueError("Only test profiles can have a test "
                                 "repository. Your repository contains the "
                                 "test prefix {}.".format(TEST_KEYWORD))

        if not os.path.isdir(new_repo_path):
            print("The repository {} will be created.".format(new_repo_path))
            old_umask = os.umask(DEFAULT_UMASK)
            try:
                os.makedirs(new_repo_path)
            finally:
                os.umask(old_umask)

        this_new_confs['AIIDADB_REPOSITORY_URI'] = 'file://' + new_repo_path

        confs['profiles'][profile] = this_new_confs

        backup_config()
        store_config(confs)

        return this_new_confs
    finally:
        readline.set_startup_hook(lambda: readline.insert_text(""))


# A table of properties.
# The key is the property name to use in the code;
# The value is a tuple, where:
# - the first entry is a string used as the key in the
# JSON config file
# - the second is the expected data type for data
#   conversion if the property is passed as a string.
#   For valid data type strings, see the implementation of set_property
# - the third entry is the description of the field
# - the fourth entry is the default value. Use _NoDefaultValue() if you want
#   an exception to be raised if no property is found.

class _NoDefaultValue(object):
    pass


# Only properties listed here can be changed/set with the command line.
# These properties are stored in the aiida config file.
# Each entry key is the name of the property used on the command line;
# the value must be a 4-tuple, whose elements are
# 1. the key actually used in the config json file
# 2. the type
# 3. A human-readable description
# 4. The default value, if no setting is found
# 5. A list of valid values, or None if no such list makes sense
_property_table = {
    "verdishell.modules": (
        "modules_for_verdi_shell",
        "string",
        "Additional modules/functions/classes to be automaticaly loaded in the "
        "verdi shell (but not in the runaiida environment); it should be a "
        "string with the full paths for each module,"
        " function or class, separated by colons, e.g. "
        "'aiida.backends.djsite.db.models:aiida.orm.querytool.Querytool'",
        "",
        None),
    "logging.aiida_loglevel": (
        "logging_aiida_log_level",
        "string",
        "Minimum level to log to the file ~/.aiida/daemon/log/aiida_daemon.log "
        "and to the DbLog table for the 'aiida' logger; for the DbLog, see "
        "also the logging.db_loglevel variable to further filter messages going "
        "to the database",
        "REPORT",
        ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.paramiko_loglevel": (
        "logging_paramiko_log_level",
        "string",
        "Minimum level to log to the file ~/.aiida/daemon/log/aiida_daemon.log "
        "for the 'paramiko' logger",
        "WARNING",
        ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.celery_loglevel": (
        "logging_celery_log_level",
        "string",
        "Minimum level to log to the file ~/.aiida/daemon/log/aiida_daemon.log "
        "for the 'celery' logger",
        "WARNING",
        ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.db_loglevel": (
        "logging_db_log_level",
        "string",
        "Minimum level to log to the DbLog table",
        "REPORT",
        ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "tcod.depositor_username": (
        "tcod_depositor_username",
        "string",
        "Username for TCOD deposition",
        None,
        None),
    "tcod.depositor_password": (
        "tcod_depositor_password",
        "string",
        "Password for TCOD deposition",
        None,
        None),
    "tcod.depositor_email": (
        "tcod_depositor_email",
        "string",
        "E-mail address for TCOD deposition",
        None,
        None),
    "tcod.depositor_author_name": (
        "tcod_depositor_author_name",
        "string",
        "Author name for TCOD depositions",
        None,
        None),
    "tcod.depositor_author_email": (
        "tcod_depositor_author_email",
        "string",
        "E-mail address for TCOD depositions",
        None,
        None),
    "warnings.showdeprecations": (
        "show_deprecations",
        "bool",
        "Boolean whether to print deprecation warnings",
        False,
        None)
}


def exists_property(name):
    """
    Check if a property exists in the DB.

    .. note:: this is useful if one wants explicitly to know if a property
      is defined just because it has a default value, or because it is
      explicitly defined in the config file.

    :param name: the name of the property to check.

    :raise ValueError: if the given name is not a valid property (as stored in
      the _property_table dictionary).
    """
    from aiida.common.exceptions import ConfigurationError

    try:
        key, _, _, table_defval, _ = _property_table[name]
    except KeyError:
        raise ValueError("{} is not a recognized property".format(name))

    try:
        config = get_config()
        return key in config
    except ConfigurationError:  # No file found
        return False


def get_property(name, default=_NoDefaultValue()):
    """
    Get a property from the json file.

    :param name: the name of the property to get.
    :param default: if provided, this value is returned if no value is found
      in the database.

    :raise ValueError: if the given name is not a valid property (as stored in
      the _property_table dictionary).
    :raise KeyError: if the given property is not found in the config file, and
      no default value is given or provided in _property_table.
    """
    from aiida.common.exceptions import ConfigurationError
    import aiida.utils.logger as logger

    try:
        key, _, _, table_defval, _ = _property_table[name]
    except KeyError:
        raise ValueError("{} is not a recognized property".format(name))

    value = None
    try:
        config = get_config()
        value = config[key]
    except (KeyError, ConfigurationError):
        if isinstance(default, _NoDefaultValue):
            if isinstance(table_defval, _NoDefaultValue):
                raise
            else:
                value = table_defval
        else:
            value = default

    # This translation is necessary because the logging module can only
    # accept numerical log levels (except for the predefined ones).
    # A side-effect of this is that:
    # verdi devel getproperty logging.[x]_loglevel
    # will return the corresponding integer, even though a string is stored in
    # the config.
    if name.startswith('logging.') and name.endswith('loglevel'):
        value = logger.LOG_LEVELS[value]

    return value


def del_property(name):
    """
    Delete a property in the json file.

    :param name: the name of the property to delete.
    :raise: KeyError if the key is not found in the configuration file.
    """
    from aiida.common.exceptions import ConfigurationError

    try:
        key, _, _, _, _ = _property_table[name]
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
        key, type_string, _, _, valid_values = _property_table[name]
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
    elif type_string == "string":
        actual_value = unicode(value)
    elif type_string == "int":
        actual_value = int(value)
    else:
        # Implement here other data types
        raise NotImplementedError("Type string '{}' not implemented yet".format(
            type_string))

    if valid_values is not None:
        if actual_value not in valid_values:
            raise ValueError("'{}' is not among the list of accepted values "
                             "for property {}".format(actual_value, name))

    try:
        config = get_config()
    except ConfigurationError:
        config = {}

    config[key] = actual_value

    store_config(config)


def parse_repository_uri(repository_uri):
    """
    This function validates the REPOSITORY_URI, that should be in the
    format protocol://address

    :note: At the moment, only the file protocol is supported.

    :return: a tuple (protocol, address).
    """
    import uritools
    parts = uritools.urisplit(repository_uri)

    if parts.scheme != u'file':
        raise ConfigurationError("The current AiiDA version supports only a "
                                 "local repository")

    if parts.scheme == u'file':
        if not os.path.isabs(parts.path):
            raise ConfigurationError("The current repository is specified with a "
                                     "file protocol but with a relative path")

        # Normalize path to its absolute path
        return parts.scheme, os.path.expanduser(parts.path)
