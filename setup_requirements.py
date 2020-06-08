# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

install_requires = [
    'reentry==1.2.2',
    'python-dateutil==2.7.2',
    'python-mimeparse==1.6.0',
    'django==1.7.11',  # Upgrade to Django 1.9 does prevent AiiDA functioning
    'django-extensions==1.5.0',
    'tzlocal==1.5.1',
    'pytz==2018.4',
    'PyYAML==3.12',
    'six==1.11.0',
    'future==0.16.0',
    'pathlib2==2.3.0',
    # We need for the time being to stay with an old version
    # of celery, including the versions of the AMQP libraries below,
    # because the support for a SQLA broker has been dropped in later
    # versions... Actually, this might be source or problems with
    # SQLA for us... probably switch to using rabbitmq?
    # Note that however this requires a new server process.
    # We also need to fix the celery version because support for Django 1.7
    # was dropped from celery 3.2
    'celery==3.1.25',
    # The next two are internal dependencies of celery, but since
    # in the past we had version mismatch problems, we freeze them
    # as well
    'billiard==3.3.0.23',
    'amqp==1.4.9',
    'anyjson==0.3.3',
    'plumpy==0.7.12',
    'portalocker==1.1.0',
    'psutil==5.4.5',
    'meld3==1.0.2',
    'numpy==1.15.4',
    'SQLAlchemy==1.0.19',  # Upgrade to SQLalchemy 1.1.5 does break tests, see #465
    'SQLAlchemy-Utils==0.33.0',
    'alembic==0.9.9',
    'ujson==1.35',
    'enum34==1.1.6',
    'voluptuous==0.11.1',
    'aldjemy==0.8.0',
    'passlib==1.7.1',
    'validate-email==1.3',
    'click==6.7',
    'click-plugins==1.0.3',
    'click-spinner==0.1.7',
    'tabulate==0.8.2',
    'ete3==3.1.1',
    'uritools==2.1.0',
    'psycopg2-binary==2.7.4',
    'paramiko==2.4.2',
    'ecdsa==0.13',
    'ipython<6.0',  # Version of ipython non enforced, because some still prefer version 4 rather than the latest
]

extras_require = {
    ':python_version < "3"': ['singledispatch >= 3.4.0.3'],
    # Requirements for ssh transport with authentification through Kerberos token
    # N. B.: you need to install first libffi and MIT kerberos GSSAPI including header files.
    # E.g. for Ubuntu 14.04: sudo apt-get install libffi-dev libkrb5-dev
    'ssh_kerberos': [
        'pyasn1==0.4.2',
        'python-gssapi==0.6.4',
    ],
    # Requirements for RESTful API
    'rest': [
        'Flask==1.0.2',
        'Flask-RESTful==0.3.6',
        'Flask-Cors==3.0.4',
        'pyparsing==2.2.0',
        'Pattern==2.6',
        'Flask-SQLAlchemy==2.3.2',
        'sqlalchemy-migrate==0.11.0',
        'marshmallow-sqlalchemy==0.13.2',
        'flask-marshmallow==0.9.0',
        'itsdangerous==0.24',
        'Flask-HTTPAuth==3.2.3',
        'Flask-Cache==0.13.1',
        'python-memcached==1.59',
    ],
    # Requirements to building documentation
    'docs': [
        'Sphinx==1.8.4',
        'Pygments==2.3.1',
        'docutils==0.14',
        'Jinja2==2.10',
        'MarkupSafe==1.1.1',
        'sphinx-rtd-theme==0.4.3',  # Required by readthedocs
        'sphinxcontrib-contentui==0.2.2',
    ],
    # Requirements for non-core functionalities that rely on external atomic manipulation/processing software
    'atomic_tools': [
        'spglib==1.10.3.65',
        'pymatgen==2018.12.12',  # last version with py2 support
        'monty~=2.0.7',  # last version with py2 support
        'ase==3.12.0',  # Updating breaks tests
        'PyMySQL==0.8.0',  # Required by ICSD tools
        'PyCifRW==4.2.1',  # Updating breaks tests
        'seekpath==1.8.1',
        'qe-tools==1.1.0',
    ],
    # Requirements for jupyter notebook
    'notebook': [
        'jupyter==1.0.0',
    ],
    # Requirements for testing
    'testing': [
        'mock==2.0.0',
        'pgtest==1.1.0',
        'pg8000<1.13.0',
        'sqlalchemy-diff==0.1.3',
        'coverage==4.5.1',
        'codecov==2.0.15'
    ],
    'dev_precommit': [
        'pre-commit==1.13.0',
        'yapf==0.24.0',
        'prospector==0.12.7',
        'pylint==1.8.4',
        'toml==0.9.4'
    ],
}


# There are a number of optional dependencies that are not
# listed even as optional dependencies as they are quite
# cumbersome to install and there is a risk that a user, wanting
# to install all dependencies (including optional ones)
# does not manage and thinks it's an AiiDA problem.
#
# These include:
#  - mayavi>=4.5.0
#    plotting package, requires to have the vtk code installed first;
#    moreover requires to have numpy installed before, but it is not in
#    the requirements (and there is no easy way on our side to fix a specific
#    installation order of dependencies)
extras_require['testing'] += extras_require['rest'] + extras_require['atomic_tools']
extras_require['all'] = [item for sublist in extras_require.values() for item in sublist]
