# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""
In this file various data management functions, needed for the SQLA test,
are added. They are "heavily inspired" by the sqlalchemy_utils.functions.database
(SQLAlchemy-Utils package).

However, they were corrected to work properly with a SQlAlchemy and PostgreSQL.
The main problem of the SQLAlchemy-Utils that were rewritten was that they
were not properly disposing the (SQLA) engine, resulting to error messages
from PostgreSQL.

"""


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from sqlalchemy_utils.functions.database import drop_database


def new_database(uri):
    """Drop the database at ``uri`` and create a brand new one. """
    destroy_database(uri)
    create_database(uri)


def destroy_database(uri):
    """Destroy the database at ``uri``, if it exists. """
    if database_exists(uri):
        drop_database(uri)


def database_exists(url):
    """Check if a database exists.

    This is a modification of sqlalchemy_utils.functions.database.database_exists
    since the latter one did not correctly work with SQLAlchemy and PostgreSQL.

    :param url: A SQLAlchemy engine URL.

    Performs backend-specific testing to quickly determine if a database
    exists on the server.

    """
    from sqlalchemy.engine.url import make_url
    from copy import copy
    import sqlalchemy as sa

    url = copy(make_url(url))
    database = url.database
    if url.drivername.startswith('postgresql'):
        url.database = 'template1'
    else:
        url.database = None

    engine = sa.create_engine(url)

    try:
        if engine.dialect.name == 'postgresql':
            text = "SELECT 1 FROM pg_database WHERE datname='%s'" % database
            return bool(engine.execute(text).scalar())

        else:
            raise Exception("Only PostgreSQL is supported.")
    finally:
        engine.dispose()


def create_database(url, encoding='utf8'):
    """Issue the appropriate CREATE DATABASE statement.

    This is a modification of sqlalchemy_utils.functions.database.create_database
    since the latter one did not correctly work with SQLAlchemy and PostgreSQL.

    :param url: A SQLAlchemy engine URL.
    :param encoding: The encoding to create the database as.


    It currently supports only PostgreSQL and the psycopg2 driver.
    """

    from sqlalchemy.engine.url import make_url
    from sqlalchemy_utils.functions.orm import quote
    from copy import copy
    import sqlalchemy as sa

    url = copy(make_url(url))

    database = url.database

    # A default PostgreSQL database to connect
    url.database = 'template1'

    engine = sa.create_engine(url)

    try:
        if engine.dialect.name == 'postgresql' and engine.driver == 'psycopg2':
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            engine.raw_connection().set_isolation_level(
                ISOLATION_LEVEL_AUTOCOMMIT
            )

            text = "CREATE DATABASE {0} ENCODING '{1}'".format(
                quote(engine, database),
                encoding
            )

            engine.execute(text)

        else:
            raise Exception("Only PostgreSQL with the psycopg2 driver is "
                            "supported.")
    finally:
        engine.dispose()