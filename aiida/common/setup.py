# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functions to interactively or non-interactively set up the AiiDA instance and a profile."""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os

from six.moves import input

from aiida.common import exceptions
from aiida.manage.configuration import Profile

USE_TZ = True

# Keyword that is used in test profiles, databases and repositories to
# differentiate them from non-testing ones.
TEST_KEYWORD = 'test_'


def validate_email(email):
    """Validate an email address using Django's email validator.

    :param email: the email address
    :return: boolean, True if email address is valid, False otherwise
    """
    from django.core.validators import validate_email as django_validate_email  # pylint: disable=import-error,no-name-in-module
    from django import forms  # pylint: disable=no-name-in-module

    try:
        django_validate_email(email)
    except forms.ValidationError:
        return False
    else:
        return True


def create_profile_noninteractive(config, profile_name='default', force_overwrite=False, **kwargs):
    """
    Non-interactively creates a profile.
    :raises: a ValueError if the profile exists.
    :raises: a ValueError if one of the values not a valid input
    :param profile: The profile to be configured
    :param values: The configuration inputs
    :return: The populated profile that was also stored
    """
    from aiida.manage.configuration.settings import DEFAULT_UMASK
    from aiida.manage.configuration import load_config

    config = load_config()

    try:
        existing_profile = config.get_profile(profile_name)
    except exceptions.ProfileConfigurationError:
        existing_profile = None

    if existing_profile and not force_overwrite:
        raise ValueError(('profile {} exists! Cannot non-interactively edit a profile.').format(profile_name))

    profile = {}

    # setting backend
    backend_possibilities = ['django', 'sqlalchemy']
    backend_v = kwargs.pop('backend')
    if backend_v in backend_possibilities:
        profile['AIIDADB_BACKEND'] = backend_v
    else:
        raise ValueError('{} is not a valid backend choice.'.format(backend_v))

    # Setting email
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
    if not os.path.isdir(repo_path):
        old_umask = os.umask(DEFAULT_UMASK)
        try:
            os.makedirs(repo_path)
        finally:
            os.umask(old_umask)
    profile['AIIDADB_REPOSITORY_URI'] = 'file://' + repo_path

    # Generate a new profile UUID or get it from the existing profile that is being overwritten
    if existing_profile:
        profile[Profile.KEY_PROFILE_UUID] = existing_profile.uuid
    else:
        profile[Profile.KEY_PROFILE_UUID] = Profile.generate_uuid()

    return profile


def create_profile(config, profile_name='default'):
    """
    :param profile_name: The profile to be configured
    :return: The populated profile that was also stored.
    """
    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    import click
    import readline
    from aiida.manage.configuration.settings import DEFAULT_UMASK, DEFAULT_AIIDA_USER

    print("Setting up profile {}.".format(profile_name))

    is_test_profile = False
    if profile_name.startswith(TEST_KEYWORD):
        print("This is a test profile. All the data that will be stored under "
              "this profile are subjected to possible deletion or "
              "modification (repository and database data).")
        is_test_profile = True

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
        for key, value in profile.items():
            if key in profile_key_explanation:
                print("{}: {}".format(profile_key_explanation.get(key), value))
            else:
                print("{}: {}".format(key, value))
        # If the user doesn't want to change it, we abandon
        if not click.confirm('Would you like to change it?'):
            return profile

        # Otherwise, we continue.
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
            if backend_possibilities:

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
        if db_possibilities:
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
            raise ValueError("You have to specify a valid database (valid choices are 'mysql', 'postgres')")

        # This part for the time being is a bit oddly written
        # it should change in the future to add the possibility of having a
        # remote repository. Atm, I act as only a local repo is possible
        repository_dirpath = os.path.join(config.dirpath, 'repository/{}/'.format(profile_name))
        existing_repo = profile.get('AIIDADB_REPOSITORY_URI', repository_dirpath)
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

        return this_new_confs
    finally:
        readline.set_startup_hook(lambda: readline.insert_text(""))


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
