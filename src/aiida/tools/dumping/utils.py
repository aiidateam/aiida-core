from logging import Logger
from pathlib import Path


def _validate_make_dump_path(
    overwrite: bool, validate_path: Path, logger: Logger, safeguard_file: str = '.aiida_node_metadata.yaml'
) -> Path:
    """Create default dumping directory for a given process node and return it as absolute path.

    :param validate_path: Path to validate for dumping.
    :param safeguard_file: Dumping-specific file to avoid deleting wrong directory.
        Default: `.aiida_node_metadata.yaml`
    :return: The absolute created dump path.
    """
    import shutil

    if validate_path.is_dir():
        # Existing, empty directory -> OK
        if not any(validate_path.iterdir()):
            pass

        # Existing, non-empty directory and overwrite False -> FileExistsError
        elif not overwrite:
            raise FileExistsError(f'Path `{validate_path}` already exists and overwrite set to False.')

        # Existing, non-empty directory and overwrite True
        # Check for safeguard file ('.aiida_node_metadata.yaml') for safety
        # If present -> Remove directory
        elif (validate_path / safeguard_file).is_file():
            logger.info(f'Overwrite set to true, will overwrite directory `{validate_path}`.')
            shutil.rmtree(validate_path)

        # Existing and non-empty directory and overwrite True
        # Check for safeguard file ('.aiida_node_metadata.yaml') for safety
        # If absent -> Don't remove directory as to not accidentally remove a wrong one
        else:
            raise Exception(
                f"Path `{validate_path}` already exists and doesn't contain safeguard file {safeguard_file}."
                f' Not removing for safety reasons.'
            )

    # Not included in if-else as to avoid having to repeat the `mkdir` call.
    # `exist_ok=True` as checks implemented above
    validate_path.mkdir(exist_ok=True, parents=True)

    return validate_path.resolve()
