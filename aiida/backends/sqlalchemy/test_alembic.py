from alembic.config import Config
from alembic import command
import os
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext


def get_migration_head(config):
    script = ScriptDirectory.from_config(config)
    return script.get_current_head()


def get_migration_base(config):
    script = ScriptDirectory.from_config(config)
    return script.get_base()


def get_db_version(config):
    script = ScriptDirectory.from_config(config)

    def get_db_version(rev, _):
        if isinstance(rev, tuple) and len(rev) > 0:
            config.attributes['rev'] = rev[0]
        else:
            config.attributes['rev'] = None

        return []

    with EnvironmentContext(
        config,
        script,
        fn=get_db_version
    ):
        script.run_env()
        return config.attributes['rev']


print "curr_dir: ", os.path.dirname(os.path.realpath(__file__))

alembic_cfg = Config("/home/aiida/aiida-code/aiida_core/aiida/backends/sqlalchemy/alembic.ini")
# alembic_cfg = Config("alembic.ini")
# command.upgrade(alembic_cfg, "head")

print "History"
command.history(alembic_cfg)

print "Current"
command.current(alembic_cfg)

print "Spyros get_migration_head"
get_migration_head(alembic_cfg)

print "Spyros get_migration_base"
print get_migration_base(alembic_cfg)

print "Spyros get_db_version"
print get_db_version(alembic_cfg)



