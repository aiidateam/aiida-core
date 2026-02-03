###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This file contains the main routines to submit, check and retrieve calculation
results. These are general and contain only the main logic; where appropriate,
the routines make reference to the suitable plugins for all
plugin-specific operations.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Mapping
from logging import LoggerAdapter
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union
from typing import Mapping as MappingType

# typing.assert_never available since 3.11
from typing_extensions import assert_never

from aiida.common import AIIDA_LOGGER, exceptions
from aiida.common.datastructures import CalcInfo, FileCopyOperation
from aiida.common.folders import Folder, SandboxFolder
from aiida.common.links import LinkType
from aiida.common.typing import FilePath
from aiida.engine.processes.exit_code import ExitCode
from aiida.manage.configuration import get_config_option
from aiida.orm import CalcJobNode, Code, FolderData, Node, PortableCode, RemoteData, load_node
from aiida.orm.utils.log import get_dblogger_extra
from aiida.repository.common import FileType
from aiida.schedulers.datastructures import JobState
from aiida.transports.transport import has_magic

if TYPE_CHECKING:
    from aiida.transports import Transport

REMOTE_WORK_DIRECTORY_LOST_FOUND = 'lost+found'

EXEC_LOGGER = AIIDA_LOGGER.getChild('execmanager')


def _find_data_node(inputs: MappingType[str, Any], uuid: str) -> Optional[Node]:
    """Find and return the node with the given UUID from a nested mapping of input nodes.

    :param inputs: (nested) mapping of nodes
    :param uuid: UUID of the node to find
    :return: instance of `Node` or `None` if not found
    """
    data_node = None

    for input_node in inputs.values():
        if isinstance(input_node, Mapping):
            data_node = _find_data_node(input_node, uuid)
        elif isinstance(input_node, Node) and input_node.uuid == uuid:
            data_node = input_node
        if data_node is not None:
            break

    return data_node


async def upload_calculation(
    node: CalcJobNode,
    transport: Transport,
    calc_info: CalcInfo,
    folder: Folder,
    inputs: Optional[MappingType[str, Any]] = None,
    dry_run: bool = False,
) -> RemoteData | None:
    """Upload a `CalcJob` instance

    :param node: the `CalcJobNode`.
    :param transport: an already opened transport to use to submit the calculation.
    :param calc_info: the calculation info datastructure returned by `CalcJob.presubmit`
    :param folder: temporary local file system folder containing the inputs written by `CalcJob.prepare_for_submission`
    :returns: The ``RemoteData`` representing the working directory on the remote if, or ``None`` if  ``dry_run=True``.
    """
    # If the calculation already has a `remote_folder`, simply return. The upload was apparently already completed
    # before, which can happen if the daemon is restarted and it shuts down after uploading but before getting the
    # chance to perform the state transition. Upon reloading this calculation, it will re-attempt the upload.
    link_label = 'remote_folder'
    if node.base.links.get_outgoing(RemoteData, link_label_filter=link_label).first():
        EXEC_LOGGER.warning(f'CalcJobNode<{node.pk}> already has a `{link_label}` output: skipping upload')
        return calc_info

    computer = node.computer

    codes_info = calc_info.codes_info
    input_codes = [load_node(_.code_uuid, sub_classes=(Code,)) for _ in codes_info]

    logger_extra = get_dblogger_extra(node)
    transport.set_logger_extra(logger_extra)
    logger = LoggerAdapter(logger=EXEC_LOGGER, extra=logger_extra)

    if not dry_run and not node.is_stored:
        raise ValueError(
            f'Cannot submit calculation {node.pk} because it is not stored! If you just want to test the submission, '
            'set `metadata.dry_run` to True in the inputs.'
        )

    # If we are performing a dry-run, the working directory should actually be a local folder that should already exist
    if dry_run:
        workdir = Path(folder.abspath)
    else:
        remote_user = await transport.whoami_async()
        remote_working_directory = computer.get_workdir().format(username=remote_user)
        if not remote_working_directory.strip():
            raise exceptions.ConfigurationError(
                f'[submission of calculation {node.pk}] No remote_working_directory '
                f"configured for computer '{computer.label}'"
            )

        # If it already exists, no exception is raised
        if not await transport.path_exists_async(remote_working_directory):
            logger.debug(
                f'[submission of calculation {node.pk}] Path '
                f'{remote_working_directory} does not exist, trying to create it'
            )
            try:
                await transport.makedirs_async(remote_working_directory)
            except EnvironmentError as exc:
                raise exceptions.ConfigurationError(
                    f'[submission of calculation {node.pk}] '
                    f'Unable to create the remote directory {remote_working_directory} on '
                    f"computer '{computer.label}': {exc}"
                )
        # Store remotely with sharding (here is where we choose
        # the folder structure of remote jobs; then I store this
        # in the calculation properties using _set_remote_dir
        # and I do not have to know the logic, but I just need to
        # read the absolute path from the calculation properties.
        workdir = Path(remote_working_directory).joinpath(calc_info.uuid[:2], calc_info.uuid[2:4])
        await transport.makedirs_async(workdir, ignore_existing=True)

        try:
            # The final directory may already exist, most likely because this function was already executed once, but
            # failed and as a result was rescheduled by the engine. In this case it would be fine to delete the folder
            # and create it from scratch, except that we cannot be sure that this the actual case. Therefore, to err on
            # the safe side, we move the folder to the lost+found directory before recreating the folder from scratch
            await transport.mkdir_async(workdir.joinpath(calc_info.uuid[4:]))
        except OSError:
            # Move the existing directory to lost+found, log a warning and create a clean directory anyway
            path_existing = os.path.join(str(workdir), calc_info.uuid[4:])
            path_lost_found = os.path.join(remote_working_directory, REMOTE_WORK_DIRECTORY_LOST_FOUND)
            path_target = os.path.join(path_lost_found, calc_info.uuid)
            logger.warning(
                f'tried to create path {path_existing} but it already exists, moving the entire folder to {path_target}'
            )

            # Make sure the lost+found directory exists, then copy the existing folder there and delete the original
            await transport.mkdir_async(path_lost_found, ignore_existing=True)
            await transport.copytree_async(path_existing, path_target)
            await transport.rmtree_async(path_existing)

            # Now we can create a clean folder for this calculation
            await transport.mkdir_async(workdir.joinpath(calc_info.uuid[4:]))
        finally:
            workdir = workdir.joinpath(calc_info.uuid[4:])

        node.set_remote_workdir(str(workdir))

    # I first create the code files, so that the code can put
    # default files to be overwritten by the plugin itself.
    # Still, beware! The code file itself could be overwritten...
    # But I checked for this earlier.
    for code in input_codes:
        if isinstance(code, PortableCode):
            # Note: this will possibly overwrite files
            for root, dirnames, filenames in code.base.repository.walk():
                # mkdir of root
                await transport.makedirs_async(workdir.joinpath(root), ignore_existing=True)

                # remotely mkdir first
                for dirname in dirnames:
                    await transport.makedirs_async(workdir.joinpath(root, dirname), ignore_existing=True)

                # Note, once #2579 is implemented, use the `node.open` method instead of the named temporary file in
                # combination with the new `Transport.put_object_from_filelike`
                # Since the content of the node could potentially be binary, we read the raw bytes and pass them on
                for filename in filenames:
                    with NamedTemporaryFile(mode='wb+') as handle:
                        content = code.base.repository.get_object_content(Path(root) / filename, mode='rb')
                        handle.write(content)
                        handle.flush()
                        await transport.put_async(handle.name, workdir.joinpath(root, filename))
            if code.filepath_executable.is_absolute():
                await transport.chmod_async(code.filepath_executable, 0o755)  # rwxr-xr-x
            else:
                await transport.chmod_async(workdir.joinpath(code.filepath_executable), 0o755)  # rwxr-xr-x

    # local_copy_list is a list of tuples, each with (uuid, dest_path, rel_path)
    # NOTE: validation of these lists are done inside calculation.presubmit()
    local_copy_list = calc_info.local_copy_list or []
    remote_copy_list = calc_info.remote_copy_list or []
    remote_symlink_list = calc_info.remote_symlink_list or []
    provenance_exclude_list = calc_info.provenance_exclude_list or []

    file_copy_operation_order = calc_info.file_copy_operation_order or [
        FileCopyOperation.SANDBOX,
        FileCopyOperation.LOCAL,
        FileCopyOperation.REMOTE,
    ]

    for file_copy_operation in file_copy_operation_order:
        if file_copy_operation is FileCopyOperation.LOCAL:
            await _copy_local_files(logger, node, transport, inputs, local_copy_list, workdir=workdir)
        elif file_copy_operation is FileCopyOperation.REMOTE:
            if not dry_run:
                await _copy_remote_files(
                    logger, node, computer, transport, remote_copy_list, remote_symlink_list, workdir=workdir
                )
        elif file_copy_operation is FileCopyOperation.SANDBOX:
            if not dry_run:
                await _copy_sandbox_files(logger, node, transport, folder, workdir=workdir)
        else:
            raise RuntimeError(f'file copy operation {file_copy_operation} is not yet implemented.')

    # In a dry_run, the working directory is the raw input folder, which will already contain these resources
    if dry_run:
        if remote_copy_list:
            filepath = os.path.join(str(workdir), '_aiida_remote_copy_list.txt')
            with open(filepath, 'w', encoding='utf-8') as handle:  # type: ignore[assignment]
                for _, remote_abs_path, dest_rel_path in remote_copy_list:
                    handle.write(
                        f'would have copied {remote_abs_path} to {dest_rel_path} in working '
                        f'directory on remote {computer.label}'
                    )

        if remote_symlink_list:
            filepath = os.path.join(str(workdir), '_aiida_remote_symlink_list.txt')
            with open(filepath, 'w', encoding='utf-8') as handle:  # type: ignore[assignment]
                for _, remote_abs_path, dest_rel_path in remote_symlink_list:
                    handle.write(
                        f'would have created symlinks from {remote_abs_path} to {dest_rel_path} in working'
                        f'directory on remote {computer.label}'
                    )

    # Loop recursively over content of the sandbox folder copying all that are not in `provenance_exclude_list`. Note
    # that directories are not created explicitly. The `node.put_object_from_filelike` call will create intermediate
    # directories for nested files automatically when needed. This means though that empty folders in the sandbox or
    # folders that would be empty when considering the `provenance_exclude_list` will *not* be copied to the repo. The
    # advantage of this explicit copying instead of deleting the files from `provenance_exclude_list` from the sandbox
    # first before moving the entire remaining content to the node's repository, is that in this way we are guaranteed
    # not to accidentally move files to the repository that should not go there at all cost. Note that all entries in
    # the provenance exclude list are normalized first, just as the paths that are in the sandbox folder, otherwise the
    # direct equality test may fail, e.g.: './path/file.txt' != 'path/file.txt' even though they reference the same file
    provenance_exclude_list = [os.path.normpath(entry) for entry in provenance_exclude_list]

    for root, _, filenames in os.walk(folder.abspath):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            relpath = os.path.normpath(os.path.relpath(filepath, folder.abspath))
            dirname = os.path.dirname(relpath)

            # Construct a list of all (partial) filepaths
            # For example, if `relpath == 'some/sub/directory/file.txt'` then the list of relative directory paths is
            # ['some', 'some/sub', 'some/sub/directory']
            # This is necessary, because if any of these paths is in the `provenance_exclude_list` the file should not
            # be copied over.
            components = dirname.split(os.sep)
            dirnames = [os.path.join(*components[:i]) for i in range(1, len(components) + 1)]
            if relpath not in provenance_exclude_list and all(
                dirname not in provenance_exclude_list for dirname in dirnames
            ):
                with open(filepath, 'rb') as handle:  # type: ignore[assignment]
                    node.base.repository._repository.put_object_from_filelike(handle, relpath)

    # Since the node is already stored, we cannot use the normal repository interface since it will raise a
    # `ModificationNotAllowed` error. To bypass it, we go straight to the underlying repository instance to store the
    # files, however, this means we have to manually update the node's repository metadata.
    node.base.repository._update_repository_metadata()

    if not dry_run:
        return RemoteData(computer=computer, remote_path=str(workdir))

    return None


async def _copy_remote_files(logger, node, computer, transport, remote_copy_list, remote_symlink_list, workdir: Path):
    """Perform the copy instructions of the ``remote_copy_list`` and ``remote_symlink_list``."""
    for remote_computer_uuid, remote_abs_path, dest_rel_path in remote_copy_list:
        if remote_computer_uuid == computer.uuid:
            logger.debug(
                f'[submission of calculation {node.pk}] copying {dest_rel_path} '
                f'remotely, directly on the machine {computer.label}'
            )
            try:
                await transport.copy_async(remote_abs_path, workdir.joinpath(dest_rel_path))
            except FileNotFoundError:
                logger.warning(
                    f'[submission of calculation {node.pk}] Unable to copy remote '
                    f'resource from {remote_abs_path} to {dest_rel_path}! NOT Stopping but just ignoring!.'
                )
            except OSError:
                logger.warning(
                    f'[submission of calculation {node.pk}] Unable to copy remote '
                    f'resource from {remote_abs_path} to {dest_rel_path}! Stopping.'
                )
                raise
        else:
            raise NotImplementedError(
                f'[submission of calculation {node.pk}] Remote copy between two different machines is '
                'not implemented yet'
            )

    for remote_computer_uuid, remote_abs_path, dest_rel_path in remote_symlink_list:
        if remote_computer_uuid == computer.uuid:
            logger.debug(
                f'[submission of calculation {node.pk}] copying {dest_rel_path} remotely, '
                f'directly on the machine {computer.label}'
            )
            remote_dirname = Path(dest_rel_path).parent
            try:
                await transport.makedirs_async(workdir.joinpath(remote_dirname), ignore_existing=True)
                await transport.symlink_async(remote_abs_path, workdir.joinpath(dest_rel_path))
            except OSError:
                logger.warning(
                    f'[submission of calculation {node.pk}] Unable to create remote symlink '
                    f'from {remote_abs_path} to {dest_rel_path}! Stopping.'
                )
                raise
        else:
            raise OSError(
                f'It is not possible to create a symlink between two different machines for calculation {node.pk}'
            )


async def _copy_local_files(logger, node, transport, inputs, local_copy_list, workdir: Path):
    """Perform the copy instructions of the ``local_copy_list``."""
    for uuid, filename, target in local_copy_list:
        logger.debug(f'[submission of calculation {node.uuid}] copying local file/folder to {target}')

        try:
            data_node = load_node(uuid=uuid)
        except exceptions.NotExistent:
            data_node = _find_data_node(inputs, uuid) if inputs else None

        if data_node is None:
            logger.warning(f'failed to load Node<{uuid}> specified in the `local_copy_list`')
            continue

        # The transport class can only copy files directly from the file system, so the files in the source node's repo
        # have to first be copied to a temporary directory on disk.
        with TemporaryDirectory() as tmpdir:
            dirpath = Path(tmpdir)

            # If no explicit source filename is defined, we assume the top-level directory
            filename_source = filename or '.'
            filename_target = target or '.'

            file_type_source = data_node.base.repository.get_object(filename_source).file_type

            # The logic below takes care of an edge case where the source is a file but the target is a directory. In
            # this case, the v2.5.1 implementation would raise an `IsADirectoryError` exception, because it would try
            # to open the directory in the sandbox folder as a file when writing the contents.
            if file_type_source == FileType.FILE and target and await transport.isdir_async(workdir.joinpath(target)):
                raise IsADirectoryError

            # In case the source filename is specified and it is a directory that already exists in the remote, we
            # want to avoid nested directories in the target path to replicate the behavior of v2.5.1. This is done by
            # setting the target filename to '.', which means the contents of the node will be copied in the top level
            # of the temporary directory, whose contents are then copied into the target directory.
            if filename and await transport.isdir_async(workdir.joinpath(filename)):
                filename_target = '.'

            filepath_target = (dirpath / filename_target).resolve().absolute()
            filepath_target.parent.mkdir(parents=True, exist_ok=True)

            if file_type_source == FileType.DIRECTORY:
                # If the source object is a directory, we copy its entire contents
                data_node.base.repository.copy_tree(filepath_target, filename_source)
                await transport.put_async(
                    f'{filepath_target}/',
                    workdir.joinpath(target) if target else workdir.joinpath('.'),
                    overwrite=True,
                )
            else:
                # Otherwise, simply copy the file
                with filepath_target.open('wb') as handle:
                    with data_node.base.repository.open(filename_source, 'rb') as source:
                        shutil.copyfileobj(source, handle)
                await transport.makedirs_async(workdir.joinpath(Path(target).parent), ignore_existing=True)
                await transport.put_async(filepath_target, workdir.joinpath(target))


async def _copy_sandbox_files(logger, node, transport, folder, workdir: Path):
    """Copy the contents of the sandbox folder to the working directory."""
    for filename in folder.get_content_list():
        logger.debug(f'[submission of calculation {node.pk}] copying file/folder {filename}...')
        await transport.put_async(folder.get_abs_path(filename), workdir.joinpath(filename))


def submit_calculation(calculation: CalcJobNode, transport: Transport) -> str | ExitCode:
    """Submit a previously uploaded `CalcJob` to the scheduler.

    :param calculation: the instance of CalcJobNode to submit.
    :param transport: an already opened transport to use to submit the calculation.
    :return: the job id as returned by the scheduler `submit_job` call
    """
    job_id = calculation.get_job_id()

    # If the `job_id` attribute is already set, that means this function was already executed once and the scheduler
    # submit command was successful as the job id it returned was set on the node. This scenario can happen when the
    # daemon runner gets shutdown right after accomplishing the submission task, but before it gets the chance to
    # finalize the state transition of the `CalcJob` to the `UPDATE` transport task. Since the job is already submitted
    # we do not want to submit it a second time, so we simply return the existing job id here.
    if job_id is not None:
        return job_id

    scheduler = calculation.computer.get_scheduler()
    scheduler.set_transport(transport)

    submit_script_filename = calculation.get_option('submit_script_filename')
    workdir = calculation.get_remote_workdir()
    result = scheduler.submit_job(workdir, submit_script_filename)

    if isinstance(result, str):
        calculation.set_job_id(result)

    return result


async def stash_calculation(calculation: CalcJobNode, transport: Transport) -> None:
    """Stash files from the working directory of a completed calculation to a permanent remote folder.

    After a calculation has been completed, optionally stash files from the work directory to a storage location on the
    same remote machine. This is useful if one wants to keep certain files from a completed calculation to be removed
    from the scratch directory, because they are necessary for restarts, but that are too heavy to retrieve.
    Instructions of which files to copy where are retrieved from the `stash.source_list` option.

    :param calculation: the calculation job node.
    :param transport: an already opened transport.
    """
    from aiida.common.datastructures import StashMode
    from aiida.orm import RemoteStashCompressedData, RemoteStashCustomData, RemoteStashFolderData

    logger_extra = get_dblogger_extra(calculation)

    if calculation.process_type == 'aiida.calculations:core.stash':
        remote_node = load_node(calculation.inputs.source_node.pk)
        uuid = remote_node.uuid
        source_basepath = Path(remote_node.get_remote_path())
    else:
        uuid = calculation.uuid
        source_basepath = Path(calculation.get_remote_workdir())

    stash_options = calculation.get_option('stash')
    stash_mode = stash_options.get('stash_mode')
    source_list = stash_options.get('source_list', [])
    target_base = Path(stash_options['target_base'])
    dereference = stash_options.get('dereference', False)
    fail_on_missing = stash_options.get('fail_on_missing', False)

    if not source_list:
        EXEC_LOGGER.warning(f'stashing source_list is empty for calculation<{calculation.pk}>. Stashing skipped.')
        return

    if stash_mode not in [mode.value for mode in StashMode.__members__.values()]:
        EXEC_LOGGER.warning(f'stashing mode {stash_mode} is not supported. Stashing skipped.')
        return

    EXEC_LOGGER.debug(
        f'stashing files with mode {stash_mode} for calculation<{calculation.pk}>: {source_list}', extra=logger_extra
    )

    if stash_mode == StashMode.SUBMIT_CUSTOM_CODE.value:
        if calculation.process_type != 'aiida.calculations:core.stash':
            EXEC_LOGGER.warning(
                f'Stashing as {StashMode.SUBMIT_CUSTOM_CODE.value}'
                ' is only possible through job submission. Stashing skipped.'
            )
            # Note we could easily support it via `transport.exec_command_wait_async`
            # However, that may confuse users, as it's done in a different manner than job-submission
            # So just to stay safe, we decided not to provide this feature.
            return

        remote_stash = RemoteStashCustomData(
            computer=calculation.computer,
            stash_mode=StashMode(stash_mode),
            target_basepath=str(target_base),
            source_list=source_list,
        )

        remote_stash.store()
        remote_stash.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='remote_stash')
        return

    ###

    if stash_mode == StashMode.COPY.value:
        target_basepath = target_base / uuid[:2] / uuid[2:4] / uuid[4:]

        async def _do_copy():
            for source_filename in source_list:
                if has_magic(source_filename):
                    copy_instructions = []
                    for globbed_filename in await transport.glob_async(source_basepath / source_filename):
                        target_filepath = target_basepath / Path(globbed_filename).relative_to(source_basepath)
                        copy_instructions.append((globbed_filename, target_filepath))
                else:
                    copy_instructions = [(source_basepath / source_filename, target_basepath / source_filename)]

                for source_filepath, target_filepath in copy_instructions:
                    # If source is in a (nested) directory, create those directories first
                    target_dirname = target_filepath.parent
                    await transport.makedirs_async(target_dirname, ignore_existing=True)

                    try:
                        await transport.copy_async(source_filepath, target_filepath)
                    except (OSError, ValueError) as exc:
                        if not await transport.path_exists_async(source_filepath):
                            if not fail_on_missing:
                                EXEC_LOGGER.warning(
                                    f'File not found {source_filepath}. Skipping, because fail_on_missing=False'
                                )
                                continue
                            else:
                                raise exceptions.StashingError(
                                    f'File {source_filepath} does not exist. Stashing failed.'
                                ) from exc
                        raise exceptions.StashingError(
                            f'Failed to copy {source_filepath} to {target_filepath}: {exc}'
                        ) from exc
                    EXEC_LOGGER.debug(f'Stashed from {source_filepath} to {target_filepath}')

        try:
            await _do_copy()
        except exceptions.StashingError as exception:
            # try to clean up in case of a failure
            await transport.rmtree_async(target_base / uuid[:2])
            raise exception
        else:
            EXEC_LOGGER.debug(f'All files succesfully {source_list} stashed to {target_base / uuid[:2]}')

        remote_stash = RemoteStashFolderData(
            computer=calculation.computer,
            target_basepath=str(target_basepath),
            stash_mode=StashMode(stash_mode),
            source_list=source_list,
            fail_on_missing=fail_on_missing,
        ).store()

    elif stash_mode in [
        StashMode.COMPRESS_TAR.value,
        StashMode.COMPRESS_TARBZ2.value,
        StashMode.COMPRESS_TARGZ.value,
        StashMode.COMPRESS_TARXZ.value,
    ]:
        # stash_mode values are identical with compression_format in transport plugin:
        # 'tar', 'tar.gz', 'tar.bz2', or 'tar.xz'
        compression_format = stash_mode
        file_name = uuid
        authinfo = calculation.get_authinfo()
        aiida_remote_base = authinfo.get_workdir().format(username=transport.whoami())

        target_destination = str(target_base / file_name) + '.' + compression_format

        source_list_abs = [source_basepath / source for source in source_list]

        # When fail_on_missing is True, check that all files exist before compressing
        if fail_on_missing:
            for source_filepath in source_list_abs:
                if has_magic(str(source_filepath)):
                    raise exceptions.StashingError(
                        'Stashing with glob patterns is not supported when fail_on_missing is True. Stashing failed.'
                    )
                if not await transport.path_exists_async(source_filepath):
                    raise exceptions.StashingError(
                        f'File {source_filepath} does not exist and fail_on_missing is True. Stashing failed.'
                    )

        remote_stash = RemoteStashCompressedData(
            computer=calculation.computer,
            target_basepath=target_destination,
            stash_mode=StashMode(stash_mode),
            source_list=source_list,
            dereference=dereference,
            fail_on_missing=fail_on_missing,
        )

        try:
            await transport.compress_async(
                format=compression_format,
                remotesources=source_list_abs,
                remotedestination=target_destination,
                root_dir=aiida_remote_base,
                overwrite=False,
                dereference=dereference,
            )
        except (OSError, ValueError) as exception:
            EXEC_LOGGER.warning(f'Failed to stash {source_list} to {target_destination}: {exception}')
            return
            # note: if you raise here, you trigger the exponential backoff
            # and if you don't raise, it appears as successful in verdi process list: Finished [0]
            # An issue opened to investigate and fix this https://github.com/aiidateam/aiida-core/issues/6789
            # raise exceptions.RemoteOperationError(f'failed '
            # 'to compress {source_list} to {target_destination}: {exception}')
        else:
            EXEC_LOGGER.debug(f'Stashed {source_list} to {target_destination}')

        remote_stash.store()

    else:
        assert_never(stash_mode)

    remote_stash.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='remote_stash')


async def unstash_calculation(calculation: CalcJobNode, transport: Transport) -> None:
    """Unstash files from a previously stashed calculation to restore them to a target location.

    This function reverses the stashing operation by copying or extracting files from a stashed location
    back to either their original location or the working directory of the unstash calculation. It supports
    multiple unstashing modes and stash formats including direct copy and compressed archives.

    :param calculation: The CalcJobNode representing the unstash calculation. Must be of process type
        'aiida.calculations:core.unstash' and contain unstash options and a source_node input.
    :param transport: An already opened transport to use for file operations on the remote machine.

    :raises: Does not raise exceptions but logs errors for:
        - Invalid calculation process type (not 'aiida.calculations:core.unstash')
        - Missing connection to original CalcJob when using OriginalPlace mode
        - File copy/extraction failures
        - Mismatched source lists for compressed stash modes

    Note: All file operations are performed asynchronously and errors are logged rather than raised
    to avoid triggering exponential backoff in the daemon execution manager.
    """

    if calculation.process_type != 'aiida.calculations:core.unstash':
        EXEC_LOGGER.error('Unstashing is only supported via `UnstashCalculation`. Stashing failed!')
        return
    from aiida.common.datastructures import StashMode, UnstashTargetMode

    unstash_options = calculation.get_option('unstash')
    unstash_target_mode = unstash_options.get('unstash_target_mode')
    source_list = unstash_options.get('source_list', [])
    source_node = load_node(calculation.inputs.source_node.pk)
    stash_mode = source_node.stash_mode.value

    if stash_mode == StashMode.SUBMIT_CUSTOM_CODE.value:
        EXEC_LOGGER.debug('Stashing was performed via job submission, skip from engine.')
        return

    if unstash_target_mode == UnstashTargetMode.OriginalPlace.value:

        def traverse(node_):
            for link in node_.base.links.get_incoming():
                if (
                    isinstance(link.node, CalcJobNode) and link.node.process_type != 'aiida.calculations:core.stash'
                ) or (isinstance(link.node, RemoteData)):
                    return link.node
                return traverse(link.node)
            return None

        stash_calculation_node = traverse(source_node)

        if not stash_calculation_node:
            EXEC_LOGGER.error(
                'Your stash node is not connected to any calcjob node, cannot find the source path. Stashing failed!'
            )
            return
        target_basepath = Path(stash_calculation_node.get_remote_path())
    else:  # UnstashTargetMode.NewRemoteData.value
        target_basepath = Path(calculation.get_remote_workdir())

    source_basepath = Path(source_node.target_basepath)

    if stash_mode == StashMode.COPY.value:
        for source_filename in source_list:
            if has_magic(source_filename):
                copy_instructions = []
                for globbed_filename in await transport.glob_async(source_basepath / source_filename):
                    target_filepath = target_basepath / Path(globbed_filename).relative_to(source_basepath)
                    copy_instructions.append((globbed_filename, target_filepath))
            else:
                copy_instructions = [(source_basepath / source_filename, target_basepath / source_filename)]

            for source_filepath, target_filepath in copy_instructions:
                # If the source file is in a (nested) directory, create those directories first in the target directory
                target_dirname = target_filepath.parent
                await transport.makedirs_async(target_dirname, ignore_existing=True)

                try:
                    await transport.copy_async(source_filepath, target_filepath)
                except (OSError, ValueError) as exception:
                    EXEC_LOGGER.error(f'Failed to unstash {source_filepath} to {target_filepath}: {exception}')
                else:
                    EXEC_LOGGER.debug(f'unstashed from {source_filepath} to {target_filepath}')

    elif stash_mode in [
        StashMode.COMPRESS_TAR.value,
        StashMode.COMPRESS_TARBZ2.value,
        StashMode.COMPRESS_TARGZ.value,
        StashMode.COMPRESS_TARXZ.value,
    ]:
        if sorted(source_list) != sorted(source_node.source_list):
            EXEC_LOGGER.error(
                f'Failed to stash. When stash_mode is {stash_mode}, '
                f'{sorted(source_list)} has to be exactly euqual to {sorted(source_node.source_list)}'
            )
            return
        try:
            await transport.extract_async(
                remotesource=source_basepath,
                remotedestination=target_basepath,
                overwrite=True,
                strip_components=3,
            )
        except (OSError, ValueError) as exception:
            EXEC_LOGGER.error(f'Failed to stash {source_basepath!s} to {target_basepath}: {exception}')
            return
            # note: if you raise here, you trigger the exponential backoff
            # and if you don't raise, it appears as successful in verdi process list: Finished [0]
            # An issue opened to investigate and fix this https://github.com/aiidateam/aiida-core/issues/6789
        else:
            EXEC_LOGGER.debug(f'Stashed {source_basepath!s} to {target_basepath}')


async def retrieve_calculation(
    calculation: CalcJobNode, transport: Transport, retrieved_temporary_folder: FilePath
) -> FolderData | None:
    """Retrieve all the files of a completed job calculation using the given transport.

    If the job defined anything in the `retrieve_temporary_list`, those entries will be stored in the
    `retrieved_temporary_folder`. The caller is responsible for creating and destroying this folder.

    :param calculation: the instance of CalcJobNode to update.
    :param transport: an already opened transport to use for the retrieval.
    :param retrieved_temporary_folder: the absolute path to a directory in which to store the files
        listed, if any, in the `retrieved_temporary_folder` of the jobs CalcInfo.
    :returns: The ``FolderData`` into which the files have been retrieved, or ``None`` if the calculation already has
        a retrieved output node attached.
    """
    logger_extra = get_dblogger_extra(calculation)
    workdir = calculation.get_remote_workdir()
    filepath_sandbox = get_config_option('storage.sandbox') or None

    EXEC_LOGGER.debug(f'Retrieving calc {calculation.pk}', extra=logger_extra)
    EXEC_LOGGER.debug(f'[retrieval of calc {calculation.pk}] chdir {workdir}', extra=logger_extra)

    # If the calculation already has a `retrieved` folder, simply return. The retrieval was apparently already completed
    # before, which can happen if the daemon is restarted and it shuts down after retrieving but before getting the
    # chance to perform the state transition. Upon reloading this calculation, it will re-attempt the retrieval.
    link_label = calculation.link_label_retrieved
    if calculation.base.links.get_outgoing(FolderData, link_label_filter=link_label).first():
        EXEC_LOGGER.warning(
            f'CalcJobNode<{calculation.pk}> already has a `{link_label}` output folder: skipping retrieval'
        )
        return

    # Create the FolderData node into which to store the files that are to be retrieved
    retrieved_files = FolderData()

    with transport:
        # First, retrieve the files of folderdata
        retrieve_list = calculation.get_retrieve_list()
        retrieve_temporary_list = calculation.get_retrieve_temporary_list()

        with SandboxFolder(filepath_sandbox) as folder:
            await retrieve_files_from_list(calculation, transport, folder.abspath, retrieve_list)
            # Here I retrieved everything; now I store them inside the calculation
            retrieved_files.base.repository.put_object_from_tree(folder.abspath)

        # Retrieve the temporary files in the retrieved_temporary_folder if any files were
        # specified in the 'retrieve_temporary_list' key
        if retrieve_temporary_list:
            await retrieve_files_from_list(calculation, transport, retrieved_temporary_folder, retrieve_temporary_list)

            # Log the files that were retrieved in the temporary folder
            for filename in os.listdir(retrieved_temporary_folder):
                EXEC_LOGGER.debug(
                    f"[retrieval of calc {calculation.pk}] Retrieved temporary file or folder '{filename}'",
                    extra=logger_extra,
                )

        # Store everything
        EXEC_LOGGER.debug(
            f'[retrieval of calc {calculation.pk}] Storing retrieved_files={retrieved_files.pk}', extra=logger_extra
        )
        retrieved_files.store()

    return retrieved_files


def kill_calculation(calculation: CalcJobNode, transport: Transport) -> None:
    """Kill the calculation through the scheduler

    :param calculation: the instance of CalcJobNode to kill.
    :param transport: an already opened transport to use to address the scheduler
    """
    job_id = calculation.get_job_id()

    if job_id is None:
        # the calculation has not yet been submitted to the scheduler
        return

    # Get the scheduler plugin class and initialize it with the correct transport
    scheduler = calculation.computer.get_scheduler()
    scheduler.set_transport(transport)

    # Call the proper kill method for the job ID of this calculation
    result = scheduler.kill_job(job_id)

    if result is not True:
        # Failed to kill because the job might have already been completed
        running_jobs = scheduler.get_jobs(jobs=[job_id], as_dict=True)
        job = running_jobs.get(job_id, None)

        # If the job is returned it is still running and the kill really failed, so we raise
        if job is not None and job.job_state != JobState.DONE:
            raise exceptions.RemoteOperationError(f'scheduler.kill_job({job_id}) was unsuccessful')
        else:
            EXEC_LOGGER.warning(
                'scheduler.kill_job() failed but job<{%s}> no longer seems to be running regardless', job_id
            )


async def retrieve_files_from_list(
    calculation: CalcJobNode,
    transport: Transport,
    folder: str,
    retrieve_list: List[Union[str, Tuple[str, str, int], list]],
) -> None:
    """Retrieve all the files in the retrieve_list from the remote into the
    local folder instance through the transport. The entries in the retrieve_list
    can be of two types:

        * a string
        * a list

    If it is a string, it represents the remote absolute or relative filepath of the file.
    If the item is a list, the elements will correspond to the following:

        * remotepath (relative path)
        * localpath
        * depth

    If the remotepath contains file patterns with wildcards, the localpath will be
    treated as the work directory of the folder and the depth integer determines
    upto what level of the original remotepath nesting the files will be copied.

    :param transport: the Transport instance.
    :param folder: an absolute path to a folder that contains the files to retrieve.
    :param retrieve_list: the list of files to retrieve.
    """
    workdir = Path(calculation.get_remote_workdir())
    for item in retrieve_list:
        if isinstance(item, (list, tuple)):
            tmp_rname, tmp_lname, depth = item
            # if there are more than one file I do something differently
            if has_magic(tmp_rname):
                remote_names = await transport.glob_async(workdir.joinpath(tmp_rname))
                local_names = []
                for rem in remote_names:
                    # get the relative path so to make local_names relative
                    rel_rem = os.path.relpath(rem, str(workdir))
                    if depth is None:
                        local_names.append(os.path.join(tmp_lname, rel_rem))
                    else:
                        to_append = rel_rem.split(os.path.sep)[-depth:] if depth > 0 else []
                        local_names.append(os.path.sep.join([tmp_lname] + to_append))
            else:
                remote_names = [tmp_rname]
                to_append = tmp_rname.split(os.path.sep)[-depth:] if depth > 0 else []
                local_names = [os.path.sep.join([tmp_lname] + to_append)]
            if depth is None or depth > 1:  # create directories in the folder, if needed
                for this_local_file in local_names:
                    new_folder = os.path.join(folder, os.path.split(this_local_file)[0])
                    if not os.path.exists(new_folder):
                        os.makedirs(new_folder)
        else:
            abs_item = item if item.startswith('/') else str(workdir.joinpath(item))

            if has_magic(abs_item):
                remote_names = await transport.glob_async(abs_item)
                local_names = [os.path.split(rem)[1] for rem in remote_names]
            else:
                remote_names = [abs_item]
                local_names = [os.path.split(abs_item)[1]]

        for rem, loc in zip(remote_names, local_names):
            transport.logger.debug(f"[retrieval of calc {calculation.pk}] Trying to retrieve remote item '{rem}'")

            if rem.startswith('/'):
                to_get = rem
            else:
                to_get = workdir.joinpath(rem)

            await transport.get_async(to_get, os.path.join(folder, loc), ignore_nonexisting=True)
