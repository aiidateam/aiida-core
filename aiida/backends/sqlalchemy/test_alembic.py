from alembic.config import Config
from alembic import command
import os
# from script import ScriptDirectory
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from alembic import util


def get_curr_version_orig(config):
    script = ScriptDirectory.from_config(config)

    head_only = False
    verbose = False

    if head_only:
        util.warn("--head-only is deprecated")

    def display_version(rev, context):
        if verbose:
            config.print_stdout(
                "Current revision(s) for %s:",
                util.obfuscate_url_pw(context.connection.engine.url)
            )
        for rev in script.get_all_current(rev):
            config.print_stdout(rev.cmd_format(verbose))

        return []

    with EnvironmentContext(
        config,
        script,
        fn=display_version
    ):
        script.run_env()


def get_curr_version(config):
    script = ScriptDirectory.from_config(config)

    head_only = False
    verbose = False

    def display_version(rev, context):
        revs_to_return = list()

        for rev in script.get_all_current(rev):
            config.print_stdout(rev.cmd_format(verbose))

        # return "bla"

    with EnvironmentContext(
        config,
        script,
        fn=display_version
    ):
        script.run_env()


def print_current_head(config):
    script = ScriptDirectory.from_config(config)

    return script.get_current_head()


def print_curr_revision_wc(config):
    script = ScriptDirectory.from_config(config)

    # return script.get_current_head()

    with EnvironmentContext(
        config,
        script
    ):
        return script.get_current_head()


def print_curr_base(config):
    script = ScriptDirectory.from_config(config)

    return script.get_base()


def get_curr_version_spyros(config):
    script = ScriptDirectory.from_config(config)

    head_only = False
    verbose = False
    my_rev = None

    def display_version(rev, context):
        revs_to_return = list()

        for rev in script.get_all_current(rev):
            config.print_stdout(rev.cmd_format(verbose))

        # return "bla"

    with EnvironmentContext(
        config,
        script,
        fn=display_version
    ):
        script.run_env()



print "curr_dir: ", os.path.dirname(os.path.realpath(__file__))

alembic_cfg = Config("/home/aiida/aiida-code/aiida_core/aiida/backends/sqlalchemy/alembic.ini")
# alembic_cfg = Config("alembic.ini")
# command.upgrade(alembic_cfg, "head")

print "History"
command.history(alembic_cfg)

print "Current"
command.current(alembic_cfg)

print "Spyros get_curr_version_orig"
get_curr_version_orig(alembic_cfg)

print "Spyros print_current_head"
print print_current_head(alembic_cfg)

print "Spyros print_curr_base"
print print_curr_base(alembic_cfg)


