# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

def create_connection():
    engine = create_engine(
        'postgresql://aiida:aiida_db@localhost:5433/aiida_separate'
    )

    return engine.connect()


def migrate_denormalized(conn):
    # trans = conn.begin()
    # try:
    #     result = conn.execute("SELECT DISTINCT type FROM db_dbnode;")
    #
    #     values = set([e["type"] for e in result])
    #
    #     conn.execute("DROP INDEX IF EXISTS db_dbnode_type;")
    #     conn.execute("CREATE TABLE db_dbnode_type (id serial CONSTRAINT db_dbnode_type_pk PRIMARY KEY, name varchar(255) not null);")
    #
    #     conn.execute("INSERT INTO db_dbnode_type (name) VALUES {};".format(
    #         ", ".join(["('{}')".format(e) for e in values])
    #     ))
    #
    #     trans.commit()
    # except SQLAlchemyError as e:
    #     print("Error: {}".format(e))
    #     trans.rollback()

    trans = conn.begin()
    try:
        # result = conn.execute("SELECT id, name FROM db_dbnode_type;")
        # values = dict((v["name"], v["id"]) for v in result)
        #
        conn.execute(
            "ALTER TABLE db_dbnode ADD COLUMN type_id integer"
        )
        conn.execute(
            "ALTER TABLE db_dbnode ADD FOREIGN KEY (type_id) REFERENCES db_dbnode_type(id);"
        )

        conn.execute(
            "UPDATE db_dbnode SET type_id = db_dbnode_type.id "
            "FROM db_dbnode_type WHERE db_dbnode_type.name = db_dbnode.type"
        )

        # conn.execute(
        #     "ALTER TABLE db_dbnode DROP COLUMN type"
        # )
        trans.commit()
    except SQLAlchemyError as e:
        print("Error: {}".format(e))
        trans.rollback()


