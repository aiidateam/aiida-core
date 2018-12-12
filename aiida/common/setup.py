# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os

import six
from six.moves import input

from aiida.common import exceptions
from aiida.manage.configuration import Profile

USE_TZ = True

# Keyword that is used in test profiles, databases and repositories to
# differentiate them from non-testing ones.
TEST_KEYWORD = 'test_'


def create_config_noninteractive(profile_name='default', force_overwrite=False, **kwargs):
    """
    Non-interactively creates a profile.
    :raises: a ValueError if the profile exists.
    :raises: a ValueError if one of the values not a valid input
    :param profile: The profile to be configured
    :param values: The configuration inputs
    :return: The populated profile that was also stored
    """
    from aiida.manage import load_config
    from aiida.manage.configuration.settings import DEFAULT_UMASK

    config = load_config(create=True)

    if config.profile_exists(profile_name) and not force_overwrite:
        raise ValueError(('profile {} exists, cannot non-interactively edit a profile.').format(profile_name))

    profile = {}

    # setting backend
    backend_possibilities = ['django', 'sqlalchemy']
    backend_v = kwargs.pop('backend')
    if backend_v in backend_possibilities:
        profile['AIIDADB_BACKEND'] = backend_v
    else:
        raise ValueError('{} is not a valid backend choice.'.format(backend_v))

    # Setting email
    from validate_email import validate_email
    email_v = kwargs.pop('email')
    if validate_email(email_v):
        profile[Profile.KEY_DEFAULT_USER] = email_v
    else:
        raise ValueError('{} is not a valid email address.'.format(email_v))

    # setting up db
    profile['AIIDADB_ENGINE'] = 'postgresql_psycopg2'
    profile['AIIDADB_HOST'] = kwargs.pop('db_host')
    profile['AIIDADB_PORT'] = kwargs.pop('db_port')
    profile['AIIDADB_NAME'] = kwargs.pop('db_name')
    profile['AIIDADB_USER'] = kwargs.pop('db_user')
    profile['AIIDADB_PASS'] = kwargs.pop('db_pass', '')

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
    profile['AIIDADB_REPOSITORY_URI'] = 'file://' + repo_path

    # Generate the profile uuid
    profile[Profile.KEY_PROFILE_UUID] = Profile.generate_uuid()

    # finalizing
    config.add_profile(profile_name, profile)
    config.set_default_profile(profile_name)

    return profile


def create_configuration(profile_name='default'):
    """
    :param profile_name: The profile to be configured
    :return: The populated profile that was also stored.
    """
    import readline
    from validate_email import validate_email
    from aiida.manage import load_config
    from aiida.manage.configuration.settings import AIIDA_CONFIG_FOLDER, DEFAULT_UMASK, DEFAULT_AIIDA_USER
    from aiida.common.utils import query_yes_no

    print("Setting up profile {}.".format(profile_name))

    is_test_profile = False
    if profile_name.startswith(TEST_KEYWORD):
        print("This is a test profile. All the data that will be stored under "
              "this profile are subjected to possible deletion or "
              "modification (repository and database data).")
        is_test_profile = True

    config = load_config(create=True)

    try:
        profile = config.get_profile(profile_name).dictionary
    except exceptions.ProfileConfigurationError:
        profile = {}

    profile_key_explanation = {
        "AIIDADB_ENGINE": "Database engine",
        "AIIDADB_PASS": "AiiDA Database password",
        "AIIDADB_NAME": "AiiDA Database name",
        "AIIDADB_HOST": "Database host",
        "AIIDADB_BACKEND": "AiiDA backend",
        "AIIDADB_PORT": "Database port",
        "AIIDADB_REPOSITORY_URI": "AiiDA repository directory",
        "AIIDADB_USER": "AiiDA Database user",
        Profile.KEY_DEFAULT_USER: "Default user email",
        Profile.KEY_PROFILE_UUID: "UUID that identifies the AiiDA profile",
    }

    # if there is an existing configuration, print it and ask if the user wants to modify it.
    updating_existing_prof = False
    if profile:
        print("The following configuration found corresponding to profile {}.".format(profile_name))
        for k, v in profile.items():
            if k in profile_key_explanation:
                print("{}: {}".format(profile_key_explanation.get(k), v))
            else:
                print("{}: {}".format(k, v))
        answ = query_yes_no("Would you like to change it?", "no")
        # If the user doesn't want to change it, we abandon
        if answ is False:
            return profile
        # Otherwise, we continue.
        else:
            updating_existing_prof = True

    this_new_confs = {}

    try:
        # Defining the backend to be used
        aiida_backend = profile.get('AIIDADB_BACKEND')
        if updating_existing_prof:
            print("The backend of already stored profiles can not be "
                  "changed. The current backend is {}.".format(aiida_backend))
            this_new_confs['AIIDADB_BACKEND'] = aiida_backend
        else:
            backend_possibilities = ['django', 'sqlalchemy']
            if len(backend_possibilities) > 0:

                valid_aiida_backend = False
                while not valid_aiida_backend:
                    backend_ans = input('AiiDA backend (available: {} - sqlalchemy is in beta mode): '.format(
                        ', '.join(backend_possibilities)))
                    if backend_ans in backend_possibilities:
                        valid_aiida_backend = True
                    else:
                        print("* ERROR! Invalid backend inserted.")
                        print("*        The available middlewares are {}".format(', '.join(backend_possibilities)))
                this_new_confs['AIIDADB_BACKEND'] = backend_ans
                aiida_backend = backend_ans

        # Setting the email
        valid_email = False
        readline.set_startup_hook(lambda: readline.insert_text(profile.get(DEFAULT_AIIDA_USER)))
        while not valid_email:
            this_new_confs[Profile.KEY_DEFAULT_USER] = input('Default user email: ')
            valid_email = validate_email(this_new_confs[Profile.KEY_DEFAULT_USER])
            if not valid_email:
                print("** Invalid email provided!")

        # Setting the database engine
        db_possibilities = []
        if aiida_backend == 'django':
            db_possibilities.extend(['postgresql_psycopg2', 'mysql'])
        elif aiida_backend == 'sqlalchemy':
            db_possibilities.extend(['postgresql_psycopg2'])
        if len(db_possibilities) > 0:
            db_engine = profile.get('AIIDADB_ENGINE', db_possibilities[0])
            readline.set_startup_hook(lambda: readline.insert_text(db_engine))

            valid_db_engine = False
            while not valid_db_engine:
                db_engine_ans = input('Database engine (available: {} - mysql is deprecated): '.format(
                    ', '.join(db_possibilities)))
                if db_engine_ans in db_possibilities:
                    valid_db_engine = True
                else:
                    print("* ERROR! Invalid database engine inserted.")
                    print("*        The available engines are {}".format(', '.join(db_possibilities)))
            this_new_confs['AIIDADB_ENGINE'] = db_engine_ans

        if 'postgresql_psycopg2' in this_new_confs['AIIDADB_ENGINE']:
            this_new_confs['AIIDADB_ENGINE'] = 'postgresql_psycopg2'

            old_host = profile.get('AIIDADB_HOST', 'localhost')
            if not old_host:
                old_host = 'localhost'
            readline.set_startup_hook(lambda: readline.insert_text(old_host))
            this_new_confs['AIIDADB_HOST'] = input('PostgreSQL host: ')

            old_port = profile.get('AIIDADB_PORT', '5432')
            if not old_port:
                old_port = '5432'
            readline.set_startup_hook(lambda: readline.insert_text(old_port))
            this_new_confs['AIIDADB_PORT'] = input('PostgreSQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(profile.get('AIIDADB_NAME')))
            db_name = ''
            while True:
                db_name = input('AiiDA Database name: ')
                if is_test_profile and db_name.startswith(TEST_KEYWORD):
                    break
                if (not is_test_profile and not db_name.startswith(TEST_KEYWORD)):
                    break
                print("The test databases should start with the prefix {} and "
                      "the non-test databases should not have this prefix.".format(TEST_KEYWORD))
            this_new_confs['AIIDADB_NAME'] = db_name

            old_user = profile.get('AIIDADB_USER', 'aiida')
            if not old_user:
                old_user = 'aiida'
            readline.set_startup_hook(lambda: readline.insert_text(old_user))
            this_new_confs['AIIDADB_USER'] = input('AiiDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(profile.get('AIIDADB_PASS')))
            this_new_confs['AIIDADB_PASS'] = input('AiiDA Database password: ')

        elif 'mysql' in this_new_confs['AIIDADB_ENGINE']:
            this_new_confs['AIIDADB_ENGINE'] = 'mysql'

            old_host = profile.get('AIIDADB_HOST', 'localhost')
            if not old_host:
                old_host = 'localhost'
            readline.set_startup_hook(lambda: readline.insert_text(old_host))
            this_new_confs['AIIDADB_HOST'] = input('mySQL host: ')

            old_port = profile.get('AIIDADB_PORT', '3306')
            if not old_port:
                old_port = '3306'
            readline.set_startup_hook(lambda: readline.insert_text(old_port))
            this_new_confs['AIIDADB_PORT'] = input('mySQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(profile.get('AIIDADB_NAME')))
            db_name = ''
            while True:
                db_name = input('AiiDA Database name: ')
                if is_test_profile and db_name.startswith(TEST_KEYWORD):
                    break
                if (not is_test_profile and not db_name.startswith(TEST_KEYWORD)):
                    break
                print("The test databases should start with the prefix {} and "
                      "the non-test databases should not have this prefix.".format(TEST_KEYWORD))
            this_new_confs['AIIDADB_NAME'] = db_name

            old_user = profile.get('AIIDADB_USER', 'aiida')
            if not old_user:
                old_user = 'aiida'
            readline.set_startup_hook(lambda: readline.insert_text(old_user))
            this_new_confs['AIIDADB_USER'] = input('AiiDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(profile.get('AIIDADB_PASS')))
            this_new_confs['AIIDADB_PASS'] = input('AiiDA Database password: ')
        else:
            raise ValueError("You have to specify a valid database " "(valid choices are 'mysql', 'postgres')")

        # This part for the time being is a bit oddly written
        # it should change in the future to add the possibility of having a
        # remote repository. Atm, I act as only a local repo is possible
        existing_repo = profile.get('AIIDADB_REPOSITORY_URI',
                                    os.path.join(AIIDA_CONFIG_FOLDER, "repository/{}/".format(profile_name)))
        default_protocol = 'file://'
        if existing_repo.startswith(default_protocol):
            existing_repo = existing_repo[len(default_protocol):]
        readline.set_startup_hook(lambda: readline.insert_text(existing_repo))
        new_repo_path = input('AiiDA repository directory: ')

        # Constructing the repo path
        new_repo_path = os.path.expanduser(new_repo_path)
        if not os.path.isabs(new_repo_path):
            raise ValueError("You must specify an absolute path")

        # Check if the new repository is a test repository and if it already exists.
        if is_test_profile:
            if TEST_KEYWORD not in os.path.basename(new_repo_path.rstrip('/')):
                raise ValueError("The repository directory for test profiles should "
                                 "contain the test keyword '{}'".format(TEST_KEYWORD))

            if os.path.isdir(new_repo_path):
                print("The repository {} already exists. It will be used for "
                      "tests. Any content may be deleted.".format(new_repo_path))
        else:
            if TEST_KEYWORD in os.path.basename(new_repo_path):
                raise ValueError("The repository directory for non-test profiles cannot "
                                 "contain the test keyword '{}'".format(TEST_KEYWORD))

        if not os.path.isdir(new_repo_path):
            print("The repository {} will be created.".format(new_repo_path))
            old_umask = os.umask(DEFAULT_UMASK)
            try:
                os.makedirs(new_repo_path)
            finally:
                os.umask(old_umask)

        this_new_confs['AIIDADB_REPOSITORY_URI'] = 'file://' + new_repo_path

        # Add the profile uuid
        this_new_confs[Profile.KEY_PROFILE_UUID] = Profile.generate_uuid()

        config.add_profile(profile_name, this_new_confs)

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
    "runner.poll.interval": ("runner_poll_interval", "int",
                             "The polling interval in seconds to be used by process runners", 1, None),
    "daemon.timeout": ("daemon_timeout", "int", "The timeout in seconds for calls to the circus client",
                       20, None),
    "verdishell.modules": ("modules_for_verdi_shell", "string",
                           "Additional modules/functions/classes to be automaticaly loaded in the "
                           "verdi shell (but not in the runaiida environment); it should be a "
                           "string with the full paths for each module,"
                           " function or class, separated by colons, e.g. "
                           "'aiida.backends.djsite.db.models:aiida.orm.querytool.Querytool'", "", None),
    "verdishell.calculation_list": ("projections_for_calculation_list", "list_of_str",
                                    "A list of the projections that should be shown by default "
                                    "when typing 'verdi calculation list'. "
                                    "Set by passing the projections space separated as a string, for example: "
                                    "verdi devel setproperty verdishell.calculation_list 'pk time job_state'",
                                    ('pk', 'ctime', 'process_state', 'type', 'job_state'), None),
    "logging.aiida_loglevel": ("logging_aiida_log_level", "string",
                               "Minimum level to log to the file ~/.aiida/daemon/log/aiida_daemon.log "
                               "and to the DbLog table for the 'aiida' logger; for the DbLog, see "
                               "also the logging.db_loglevel variable to further filter messages going "
                               "to the database", "REPORT", ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO",
                                                             "DEBUG"]),
    "logging.tornado_loglevel":
    ("logging_tornado_log_level", "string", "Minimum level to log to the file ~/.aiida/daemon/log/aiida_daemon.log "
     "for the 'tornado' loggers", "WARNING", ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.plumpy_loglevel":
    ("logging_plumpy_log_level", "string", "Minimum level to log to the file ~/.aiida/daemon/log/aiida_daemon.log "
     "for the 'plumpy' logger", "WARNING", ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.kiwipy_loglevel":
    ("logging_kiwipy_log_level", "string", "Minimum level to log to the file ~/.aiida/daemon/log/aiida_daemon.log "
     "for the 'kiwipy' logger", "WARNING", ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.paramiko_loglevel": ("logging_paramiko_log_level", "string",
                                  "Minimum level to log to the file ~/.aiida/daemon/log/aiida_daemon.log "
                                  "for the 'paramiko' logger", "WARNING",
                                  ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.alembic_loglevel": ("logging_alembic_log_level", "string", "Minimum level to log to the console",
                                 "WARNING", ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.sqlalchemy_loglevel": ("logging_sqlalchemy_loglevel", "string", "Minimum level to log to the console",
                                    "WARNING", ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.circus_loglevel": ("logging_circus_log_level", "string",
                                "Minimum level to log to the circus daemon log file"
                                "for the 'circus' logger", "INFO",
                                ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "logging.db_loglevel": ("logging_db_log_level", "string", "Minimum level to log to the DbLog table", "REPORT",
                            ["CRITICAL", "ERROR", "WARNING", "REPORT", "INFO", "DEBUG"]),
    "tcod.depositor_username": ("tcod_depositor_username", "string", "Username for TCOD deposition", None, None),
    "tcod.depositor_password": ("tcod_depositor_password", "string", "Password for TCOD deposition", None, None),
    "tcod.depositor_email": ("tcod_depositor_email", "string", "E-mail address for TCOD deposition", None, None),
    "tcod.depositor_author_name": ("tcod_depositor_author_name", "string", "Author name for TCOD depositions", None,
                                   None),
    "tcod.depositor_author_email": ("tcod_depositor_author_email", "string", "E-mail address for TCOD depositions",
                                    None, None),
    "warnings.showdeprecations": ("show_deprecations", "bool", "Boolean whether to print AiiDA deprecation warnings",
                                  True, None)
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
    from aiida.manage import load_config

    try:
        key, _, _, table_defval, _ = _property_table[name]
    except KeyError:
        raise ValueError("{} is not a recognized property".format(name))

    try:
        config = load_config()
        return key in config.dictionary
    except exceptions.MissingConfigurationError:  # No file found
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
    from aiida.common.log import LOG_LEVELS
    from aiida.manage import load_config

    try:
        key, _, _, table_defval, _ = _property_table[name]
    except KeyError:
        raise ValueError("{} is not a recognized property".format(name))

    value = None
    try:
        config = load_config()
        value = config.dictionary[key]
    except (KeyError, exceptions.MissingConfigurationError):
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
        value = LOG_LEVELS[value]

    return value


def del_property(name):
    """
    Delete a property in the json file.

    :param name: the name of the property to delete.
    :raise: MissingConfigurationError if the key is not found in the configuration file.
    """
    from aiida.manage import load_config

    try:
        key, _, _, _, _ = _property_table[name]
    except KeyError:
        raise ValueError("{} is not a recognized property".format(name))

    config = load_config()
    del config.dictionary[key]

    config.store()


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
    from aiida.manage import load_config

    try:
        key, type_string, _, _, valid_values = _property_table[name]
    except KeyError:
        raise ValueError("'{}' is not a recognized property".format(name))

    actual_value = False

    if type_string == "bool":
        if isinstance(value, six.string_types):
            if value.strip().lower() in ["0", "false", "f"]:
                actual_value = False
            elif value.strip().lower() in ["1", "true", "t"]:
                actual_value = True
            else:
                raise ValueError("Invalid bool value for property {}".format(name))
        else:
            actual_value = bool(value)
    elif type_string == "string":
        actual_value = six.text_type(value)
    elif type_string == "int":
        actual_value = int(value)
    elif type_string == 'list_of_str':
        # I expect the results as a list of strings
        actual_value = value.split()
    else:
        # Implement here other data types
        raise NotImplementedError("Type string '{}' not implemented yet".format(type_string))

    if valid_values is not None:
        if actual_value not in valid_values:
            raise ValueError("'{}' is not among the list of accepted values "
                             "for property {}".format(actual_value, name))

    config = load_config()
    config.dictionary[key] = actual_value
    config.store()


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
        raise exceptions.ConfigurationError("The current AiiDA version supports only a local repository")

    if parts.scheme == u'file':
        if not os.path.isabs(parts.path):
            raise exceptions.ConfigurationError("The current repository is specified with a "
                                     "file protocol but with a relative path")

        # Normalize path to its absolute path
        return parts.scheme, os.path.expanduser(parts.path)
