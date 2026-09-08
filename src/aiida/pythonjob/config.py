import json
from pathlib import Path

from aiida.manage import get_config


def load_config() -> dict:
    """Load the configuration from the config file."""
    config = get_config()
    config_file_path = Path(config.dirpath) / "pythonjob.json"
    try:
        with config_file_path.open("r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    return config


config = load_config()
