import subprocess

from aiida.manage import get_manager
from aiida.manage.configuration import reset_config


def set_aiida_loglevel(level: str):
    """Set the AiiDA log level."""
    subprocess.run(
        ['verdi', 'config', 'set', 'logging.aiida_loglevel', level],
        check=True,
    )
    get_manager().unload_profile()
    reset_config()
