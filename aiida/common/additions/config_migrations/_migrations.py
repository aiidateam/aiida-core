"""
Defines the migration functions between different config versions.
"""

import uuid

# The current configuration version. Increment this value whenever a change
# to the config.json structure is made.
CURRENT_CONFIG_VERSION = 2
# The oldest config version where no backwards-incompatible changes have been
# made since. When doing backwards-incompatible changes, set this to the current
# version.
OLDEST_COMPATIBLE_CONFIG_VERSION = 0

class ConfigMigration(object):
    """
    Defines a config migration.

    :param migrate_function: Function which transforms the config dict. This function does not need to change the CONFIG_VERSION values.

    :param current_version: Current config version after the migration.
    :type current_version: int

    :param oldest_version: Oldest compatible config version after the migration.
    :type oldest_version: int
    """
    def __init__(
        self,
        migrate_function,
        current_version,
        oldest_version
    ):
        self.migrate_function = migrate_function
        self.current_version = int(current_version)
        self.oldest_version = int(oldest_version)

    def apply(self, config):
        from ._utils import VERSION_KEY, CURRENT_KEY, OLDEST_KEY
        from ._utils import add_config_version
        config = self.migrate_function(config)
        add_config_version(
            config,
            current_version=self.current_version,
            oldest_version=self.oldest_version
        )
        return config

def _1_add_rmq_prefix(config):
    for profile in config.get('profiles', {}).values():
        profile['RMQ_PREFIX'] = uuid.uuid4().hex
    return config

# Maps the initial config version to the ConfigMigration which updates it.
_MIGRATION_LOOKUP = {
    0: ConfigMigration(
        migrate_function=lambda x: x,
        current_version=1,
        oldest_version=0
    ),
    1: ConfigMigration(
        migrate_function=_1_add_rmq_prefix,
        current_version=2,
        oldest_version=0
    )
}
