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
    'pip==9.0.1',
    'setuptools>=18.5',
    'reentry >= 1.0.2',
    'wheel==0.29.0',
    'python-dateutil==2.6.0',
    'python-mimeparse==0.1.4',
    'django==1.7.4',  # upgrade to Django 1.9 does prevent AiiDA functioning
    'django_extensions==1.5',
    'tzlocal==1.3',
    'pytz==2014.10',
    'six==1.10',
    'future',
    'pathlib2',
    'singledispatch >= 3.4.0.0',
    # We need for the time being to stay with an old version
    # of celery, including the versions of the AMQP libraries below,
    # because the support for a SQLA broker has been dropped in later
    # versions... Actually, this might be source or problems with
    # SQLA for us... probably switch to using rabbitmq?
    # Note that however this requires a new server process.
    'celery==3.1.25',
    # The next two are internal dependencies of celery, but since
    # in the past we had version mismatch problems, we freeze them
    # as well
    'billiard==3.3.0.23',
    'amqp==1.4.9',
    'anyjson==0.3.3',
    'supervisor==3.1.3',
    'meld3==1.0.0',
    'numpy==1.12.0',
    'plumpy==0.7.9',
    'portalocker==1.1.0',
    'SQLAlchemy==1.0.12',  # upgrade to SQLalchemy 1.1.5 does break tests, see #465
    'SQLAlchemy-Utils==0.31.2',
    'alembic>=0.9.2',
    'ujson==1.35',
    'enum34==1.1.6',
    'voluptuous==0.8.11',
    'aldjemy==0.6.0',
    'passlib==1.7.1',
    'validate_email==1.3',
    'click==6.7',
    'tabulate==0.7.5',
    'ete3==3.0.0b35',
    'uritools==1.0.2',
    'psycopg2==2.7.1',
    # Requirements for ssh transport
    'paramiko==2.1.2',
    'ecdsa==0.13',
    'pycrypto==2.6.1',
    # Requirements for verdi shell (version of ipython non enforced, because
    # there are people who still prefer version 4 rather than the latest)
    'ipython < 6.0',
]

extras_require = {
    # Requirements for ssh transport with authentification through Kerberos
    # token
    # N. B.: you need to install first libffi and MIT kerberos GSSAPI including header files.
    # E.g. for Ubuntu 14.04: sudo apt-get install libffi-dev libkrb5-dev
    'ssh_kerberos': [
        'pyasn1==0.1.9',
        'python-gssapi==0.6.4',
    ],
    # Requirements for RESTful API
    'REST': [
        'flask==0.10.1',
        'flask_restful==0.3.5',
        'flask-cors==3.0.1',
        'pyparsing==2.1.10',
        'pattern==2.6',
        'Flask-SqlAlchemy==2.1',
        'SQLAlchemy-migrate==0.10.0',
        'marshmallow-sqlalchemy==0.10.0',
        'flask-marshmallow==0.7.0',
        'itsdangerous==0.24',
        'flask-httpauth==3.2.0',
        'flask-cache==0.13.1',
        'python-memcached==1.58',
    ],
    # Requirements to buiilding documentation
    'docs': [
        'Sphinx==1.5.2',
        'pygments==2.2.0',
        'docutils==0.13.1',
        'jinja2==2.9.5',
        'markupsafe==0.23',
        # Required by readthedocs
        'sphinx_rtd_theme==0.1.9',
    ],
    # Requirements for non-core funciontalities that rely on external atomic
    # manipulation/processing software
    'atomic_tools': [
        'spglib>=1.9',
        # support for symmetry detection in aiida.orm.data.structure. Has no
        # easily accessible version number
        'pymatgen==4.5.3',  # support for NWChem I/O
        'ase==3.12.0',  # support for crystal structure manipulation
        'PyMySQL==0.7.9',  # required by ICSD tools
        'PyCifRW==3.6.2.1',
        'seekpath>=1.4.0',
        # support for the AiiDA CifData class. Update to version 4 ddoes
        # break tests
    ],
    # Requirements for jupyter notebook
    'notebook': [
        'jupyter',
    ],
    # Requirements for testing
    'testing': [
        'mock',
        'pgtest'
    ],
    'dev_precommit': [
        'pre-commit',
        'yapf',
        'prospector',
        'pylint'
    ]
}

# There are a number of optional dependencies that are not
# listed even as optional dependencies as they are quite
# cumbersome to install and there is a risk that a user, wanting
# to install all dependencies (including optional ones)
# does not manage and thinks it's an AiiDA problem.
#
# These include:
#  - mayavi==4.5.0
#    plotting package, requires to have the vtk code installed first;
#    moreover requires to have numpy installed before, but it is not in
#    the requirements (and there is no easy way on our side to fix a specific
#    installation order of dependencies)

extras_require['testing'] += extras_require['REST'] + extras_require['atomic_tools']
