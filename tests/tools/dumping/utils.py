###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from pathlib import Path

def compare_tree(expected: dict, base_path: Path, relative_path: Path = Path()):
    """Recursively compares an expected directory structure with an actual path.

    Args:
        expected (dict): The expected directory structure.
        base_path (Path): The root directory where the actual structure is located.
        relative_path (Path): The relative path inside the base directory (used internally for recursion).
    """
    actual_path = base_path / relative_path

    assert actual_path.exists(), f"Path does not exist: {actual_path}"
    assert actual_path.is_dir(), f"Path is not a directory: {actual_path}"

    for name, content in expected.items():
        item_path = actual_path / name
        assert item_path.exists(), f"Missing: {item_path}"

        if isinstance(content, list):  # It's a directory with files (list of filenames)
            assert item_path.is_dir(), f"Expected a directory: {item_path}"
            # Check that all files exist inside the directory
            for filename in content:
                file_path = item_path / filename
                assert file_path.exists(), f"Missing file: {file_path}"
                assert file_path.is_file(), f"Expected a file: {file_path}"
        elif isinstance(content, dict):  # It's a subdirectory
            assert item_path.is_dir(), f"Expected a directory: {item_path}"
            compare_tree(content, base_path, relative_path / name)
