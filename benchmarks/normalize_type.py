# -*- coding: utf-8 -*-

from sqlalchemy import create_engine


def create_connection():
    engine = create_engine(
        'postgresql://aiida:aiida_db@localhost:5433/aiida_separate'
    )

    return engine.connect()


def migrate_denormalized(conn):
    trans = conn.begin()
    try:
        result = conn.execute("SELECT DISTINCT type FROM db_dbnode;")

        values = set([e["type"] for e in result])

        conn.execute("DROP INDEX db_dbnode_type;")
        conn.execute("CREATE TABLE db_dbnode_type (id serial CONSTRAINT db_dbnode_type_pk PRIMARY KEY, name varchar(255) not null);")

        conn.execute("INSERT INTO db_dbnode_type (name) VALUES {};".format(
            ", ".join(["('{}')".format(e) for e in values])
        ))

        trans.commit()
    except:
        trans.rollback()

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

        conn.execute(
            "ALTER TABLE db_dbnode DROP COLUMN type"
        )
    except:
        trans.rollback()


