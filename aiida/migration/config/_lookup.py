def _0_add_config_version_(config):
    from ._utils import CURRENT_KEY, OLDEST_KEY, VERSION_KEY
    config[VERSION_KEY] = {CURRENT_KEY: 1, OLDEST_KEY: 0}
    return config

_MIGRATION_LOOKUP = {
    0: _0_add_config_version_
}
