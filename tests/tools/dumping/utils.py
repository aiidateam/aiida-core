###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from pathlib import Path
from typing import Any

# TODO: Possibly move this under test directory


def tree_to_dict(root_path: Path) -> dict[str, list[Any]]:
    """
    Convert a directory tree structure into a dictionary representation.

    The representation follows this format:
    - Each directory is represented as a dictionary with the directory name as key
      and a list of its contents as value
    - Files are represented as strings in the list
    - Subdirectories are represented as dictionaries in the list

    Args:
        root_path (Path): The root directory to convert

    Returns:
        Dict[str, List[Any]]: Dictionary representation of the directory structure
    """
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(f'The path {root_path} does not exist or is not a directory')

    # Get the directory name
    dir_name = root_path.name

    # Initialize the content list for this directory
    contents = []

    # Process all entries in the directory (sorted alphabetically)
    entries = sorted(root_path.iterdir(), key=lambda p: p.name)

    # First, add all files to the content list
    for entry in entries:
        if entry.is_file():
            contents.append(entry.name)

    # Then, recursively process all directories
    for entry in entries:
        if entry.is_dir():
            # Create a dictionary for this subdirectory
            subdir_dict = tree_to_dict(entry)
            contents.append(subdir_dict)

    # Return the directory as a dictionary with its contents
    return {dir_name: contents}


def tree_to_dict_dirs_only(root_path: Path) -> dict[str, list[Any]]:
    """
    Convert a directory tree structure into a dictionary representation,
    including only directories and ignoring files.

    The representation follows this format:
    - Each directory is represented as a dictionary with the directory name as key
      and a list of its subdirectories as value
    - Only directories are included, files are completely ignored
    - Subdirectories are represented as nested dictionaries in the list

    Args:
        root_path (Path): The root directory to convert

    Returns:
        Dict[str, List[Any]]: Dictionary representation of the directory structure
                              containing only directories
    """
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(f'The path {root_path} does not exist or is not a directory')

    # Get the directory name
    dir_name = root_path.name

    # Initialize the content list for this directory
    contents = []

    # Get all subdirectories in the current directory (sorted alphabetically)
    subdirs = sorted([entry for entry in root_path.iterdir() if entry.is_dir()], key=lambda p: p.name)

    # Recursively process all subdirectories
    for subdir in subdirs:
        # Create a dictionary for this subdirectory
        subdir_dict = tree_to_dict_dirs_only(subdir)
        contents.append(subdir_dict)

    # Return the directory as a dictionary with its contents
    return {dir_name: contents}


def compare_tree(expected: dict, base_path: Path, relative_path: Path = Path()):
    """Recursively compares an expected directory structure with an actual path.
    Verifies both that all expected elements exist and that no unexpected elements exist.

    Args:
        expected (dict): The expected directory structure.
        base_path (Path): The root directory where the actual structure is located.
        relative_path (Path): The relative path inside the base directory (used internally for recursion).
    """
    for dir_name, content_list in expected.items():
        dir_path = base_path / relative_path / dir_name

        assert dir_path.exists(), f'Path does not exist: {dir_path}'
        assert dir_path.is_dir(), f'Path is not a directory: {dir_path}'

        # Extract all expected files and subdirectories at this level
        expected_entries = set()
        expected_dirs = {}

        for item in content_list:
            if isinstance(item, str):  # It's a file
                expected_entries.add(item)
                file_path = dir_path / item
                assert file_path.exists(), f'Missing file: {file_path}'
                assert file_path.is_file(), f'Expected a file: {file_path}'
            elif isinstance(item, dict):  # It's a subdirectory
                # Get the subdirectory name (the first key in the dict)
                subdir_name = next(iter(item))
                expected_entries.add(subdir_name)
                expected_dirs[subdir_name] = item
                # Recursively check the subdirectory
                compare_tree(item, base_path, relative_path / dir_name)

        # Check for unexpected entries
        actual_entries = set(entry.name for entry in dir_path.iterdir())
        unexpected_entries = actual_entries - expected_entries

        assert not unexpected_entries, f'Unexpected entries found in {dir_path}: {unexpected_entries}'


def compare_tree_dirs_only(expected: dict, base_path: Path, relative_path: Path = Path()):
    """Recursively compares an expected directory structure with an actual path,
    focusing only on directories and ignoring files.

    Args:
        expected (dict): The expected directory structure.
        base_path (Path): The root directory where the actual structure is located.
        relative_path (Path): The relative path inside the base directory (used internally for recursion).
    """
    for dir_name, content_list in expected.items():
        dir_path = base_path / relative_path / dir_name

        assert dir_path.exists(), f'Path does not exist: {dir_path}'
        assert dir_path.is_dir(), f'Path is not a directory: {dir_path}'

        # Extract all expected subdirectories at this level
        expected_dirs = {}

        for item in content_list:
            if isinstance(item, dict):  # It's a subdirectory
                # Get the subdirectory name (the first key in the dict)
                subdir_name = next(iter(item))
                expected_dirs[subdir_name] = item

        # Check for unexpected directories
        actual_dirs = {entry.name: entry for entry in dir_path.iterdir() if entry.is_dir()}
        unexpected_dirs = set(actual_dirs.keys()) - set(expected_dirs.keys())

        assert not unexpected_dirs, f'Unexpected directories found in {dir_path}: {unexpected_dirs}'

        assert not unexpected_dirs, f'Unexpected directories found in {dir_path}: {unexpected_dirs}'

        # Recursively check the expected subdirectories
        for subdir_name, subdir_content in expected_dirs.items():
            compare_tree_dirs_only(subdir_content, base_path, relative_path / dir_name)
