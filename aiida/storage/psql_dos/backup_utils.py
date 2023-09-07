# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Utility functions for running the psql_dos backend backups."""

import logging
import pathlib
import subprocess
from typing import Optional

from aiida.storage.log import STORAGE_LOGGER


def run_cmd(args: list, remote: Optional[str] = None, check: bool = True, logger: logging.Logger = STORAGE_LOGGER):
    """
    Run a command locally or remotely.
    """
    all_args = args[:]
    if remote:
        all_args = ['ssh', remote] + all_args

    try:
        res = subprocess.run(all_args, capture_output=True, text=True, check=check)
    except subprocess.CalledProcessError as exc:
        logger.error(exc)
        return False

    logger.info(f'stdout: {all_args}\n{res.stdout}')
    logger.info(f'stderr: {all_args}\n{res.stderr}')

    success = not bool(res.returncode)

    return success


def check_path_exists(path, remote: Optional[str] = None):
    cmd = ['[', '-e', str(path), ']']
    return run_cmd(cmd, remote=remote, check=False)


def check_path_is_empty_folder(path, remote: Optional[str] = None):
    cmd = ['[', '-d', str(path), ']', '&&', '[', '-z', f'$(ls -A "{str(path)}")', ']']
    return run_cmd(cmd, remote=remote, check=False)


def call_rsync(
    args: list,
    src: pathlib.Path,
    dest: pathlib.Path,
    link_dest: Optional[pathlib.Path] = None,
    remote: Optional[str] = None,
    src_trailing_slash: bool = False,
    dest_trailing_slash: bool = False,
    logger: logging.Logger = STORAGE_LOGGER
) -> bool:
    """Call rsync with specified arguments and handle possible errors & stdout/stderr

        :param link_dest:
            Path to the hardlinked files location (previous backup).

        :param src_trailing_slash:
            Add a trailing slash to the source path. This makes rsync copy the contents
            of the folder instead of the folder itself.

        :param dest_trailing_slash:
            Add a trailing slash to the destination path. This makes rsync interpret the
            destination as a folder and create it if it doesn't exists.

        :return:
            True if successful and False if unsuccessful.
        """

    all_args = args[:]
    if link_dest:
        if not remote:
            # for local paths, use resolve() to get absolute path
            link_dest_str = str(link_dest.resolve())
        else:
            # for remote paths, we require absolute paths anyways
            link_dest_str = str(link_dest)
        all_args += [f'--link-dest={link_dest_str}']

    if src_trailing_slash:
        all_args += [str(src) + '/']
    else:
        all_args += [str(src)]

    dest_str = str(dest)
    if dest_trailing_slash:
        dest_str += '/'

    if not remote:
        all_args += [dest_str]
    else:
        all_args += [f'{remote}:{dest_str}']

    try:
        res = subprocess.run(all_args, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        logger.error(exc)
        return False

    logger.info(f'stdout: {all_args}\n{res.stdout}')
    logger.info(f'stderr: {all_args}\n{res.stderr}')

    success = not bool(res.returncode)

    return success
