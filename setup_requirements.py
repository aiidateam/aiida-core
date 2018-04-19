# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# Requirements for core AiiDA functionalities

install_requires = [
    'reentry==1.2.0',
    'python-dateutil==2.6.0',
    'python-mimeparse==0.1.4',
    'django==1.7.11',  # upgrade to Django 1.9 does prevent AiiDA functioning
    'django-extensions==1.5.0',
    'tzlocal==1.3',
    'pytz==2014.10',
    'pyyaml',
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
    'psutil==5.4.0',
    'meld3==1.0.0',
    'numpy==1.12.0',
    'plumpy==0.7.12',
    'portalocker==1.1.0',
    'SQLAlchemy==1.0.19',  # upgrade to SQLalchemy 1.1.5 does break tests, see #465
    'SQLAlchemy-Utils==0.33.0',
    'alembic==0.9.6',
    'ujson==1.35',
    'enum34==1.1.6',
    'voluptuous==0.8.11',
    'aldjemy==0.6.0',
    'passlib==1.7.1',
    'validate-email==1.3',
    'click==6.7',
    'click-plugins',
    'click-spinner',
    'tabulate==0.7.5',
    'ete3==3.0.0b35',
    'uritools==1.0.2',
    'psycopg2-binary==2.7.4',
    # Requirements for ssh transport
    'paramiko==2.4.0',
    'ecdsa==0.13',
    'pycrypto==2.6.1',
    # Requirements for verdi shell (version of ipython non enforced, because
    # there are people who still prefer version 4 rather than the latest)
    'ipython<6.0',
    'scipy<1.0.0'  # At this moment the install of 1.0.0 release is broken
]

extras_require = {
    # Requirements for Python 2 only
    ':python_version < "3"': ['chainmap', 'singledispatch >= 3.4.0.3'],
    # Requirements for ssh transport with authentification through Kerberos
    # token
    # N. B.: you need to install first libffi and MIT kerberos GSSAPI including header files.
    # E.g. for Ubuntu 14.04: sudo apt-get install libffi-dev libkrb5-dev
    'ssh_kerberos': [
        'pyasn1==0.3.7',
        'python-gssapi==0.6.4',
    ],
    # Requirements for RESTful API
    'rest': [
        'Flask==0.10.1',
        'Flask-RESTful==0.3.6',
        'Flask-Cors==3.0.1',
        'pyparsing==2.1.10',
        'Pattern==2.6',
        'Flask-SQLAlchemy==2.1',
        'sqlalchemy-migrate==0.10.0',
        'marshmallow-sqlalchemy==0.10.0',
        'flask-marshmallow==0.7.0',
        'itsdangerous==0.24',
        'Flask-HTTPAuth==3.2.0',
        'Flask-Cache==0.13.1',
        'python-memcached==1.58',
    ],
    # Requirements to buiilding documentation
    'docs': [
        'Sphinx==1.7.2',
        'Pygments==2.2.0',
        'docutils==0.13.1',
        'Jinja2==2.9.5',
        'MarkupSafe==0.23',
        # Required by readthedocs
        'sphinx-rtd-theme==0.2.5b2',
    ],
    # Requirements for non-core funciontalities that rely on external atomic
    # manipulation/processing software
    'atomic_tools': [
        'spglib==1.9.10.1',
        # support for symmetry detection in aiida.orm.data.structure. Has no
        # easily accessible version number
        'pymatgen==4.5.3',  # support for NWChem I/O
        'ase==3.12.0',  # support for crystal structure manipulation
        'PyMySQL==0.7.9',  # required by ICSD tools
        'PyCifRW==4.2.1',
        'seekpath==1.8.0',
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
        'sqlalchemy-diff==0.1.3',
        'coverage==4.5.1',
        'codecov'
    ],
    'dev_precommit': [
        'pre-commit==1.3.0',
        'yapf==0.19.0',
        'prospector==0.12.7',
        'pylint==1.7.4',
        'toml'
    ]
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
