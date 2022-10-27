# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This file contains the main routines to submit, check and retrieve calculation
results. These are general and contain only the main logic; where appropriate,
the routines make reference to the suitable plugins for all
plugin-specific operations.
"""
from collections.abc import Mapping
from logging import LoggerAdapter
import os
import pathlib
import shutil
from tempfile import NamedTemporaryFile
from typing import Any, List
from typing import Mapping as MappingType
from typing import Optional, Tuple, Union

from aiida.common import AIIDA_LOGGER, exceptions
from aiida.common.datastructures import CalcInfo
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.manage.configuration import get_config_option
from aiida.orm import CalcJobNode, Code, FolderData, Node, PortableCode, RemoteData, load_node
from aiida.orm.utils.log import get_dblogger_extra
from aiida.repository.common import FileType
from aiida.schedulers.datastructures import JobState
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


def upload_calculation(
    node: CalcJobNode,
    transport: Transport,
    calc_info: CalcInfo,
    folder: SandboxFolder,
    inputs: Optional[MappingType[str, Any]] = None,
    dry_run: bool = False
) -> None:
    """Upload a `CalcJob` instance

    :param node: the `CalcJobNode`.
    :param transport: an already opened transport to use to submit the calculation.
    :param calc_info: the calculation info datastructure returned by `CalcJob.presubmit`
    :param folder: temporary local file system folder containing the inputs written by `CalcJob.prepare_for_submission`
    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements

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
        workdir = transport.getcwd()
    else:
        remote_user = transport.whoami()
        remote_working_directory = computer.get_workdir().format(username=remote_user)
        if not remote_working_directory.strip():
            raise exceptions.ConfigurationError(
                "[submission of calculation {}] No remote_working_directory configured for computer '{}'".format(
                    node.pk, computer.label
                )
            )

        # If it already exists, no exception is raised
        try:
            transport.chdir(remote_working_directory)
        except IOError:
            logger.debug(
                '[submission of calculation {}] Unable to chdir in {}, trying to create it'.format(
                    node.pk, remote_working_directory
                )
            )
            try:
                transport.makedirs(remote_working_directory)
                transport.chdir(remote_working_directory)
            except EnvironmentError as exc:
                raise exceptions.ConfigurationError(
                    '[submission of calculation {}] '
                    'Unable to create the remote directory {} on '
                    "computer '{}': {}".format(node.pk, remote_working_directory, computer.label, exc)
                )
        # Store remotely with sharding (here is where we choose
        # the folder structure of remote jobs; then I store this
        # in the calculation properties using _set_remote_dir
        # and I do not have to know the logic, but I just need to
        # read the absolute path from the calculation properties.
        transport.mkdir(calc_info.uuid[:2], ignore_existing=True)
        transport.chdir(calc_info.uuid[:2])
        transport.mkdir(calc_info.uuid[2:4], ignore_existing=True)
        transport.chdir(calc_info.uuid[2:4])

        try:
            # The final directory may already exist, most likely because this function was already executed once, but
            # failed and as a result was rescheduled by the eninge. In this case it would be fine to delete the folder
            # and create it from scratch, except that we cannot be sure that this the actual case. Therefore, to err on
            # the safe side, we move the folder to the lost+found directory before recreating the folder from scratch
            transport.mkdir(calc_info.uuid[4:])
        except OSError:
            # Move the existing directory to lost+found, log a warning and create a clean directory anyway
            path_existing = os.path.join(transport.getcwd(), calc_info.uuid[4:])
            path_lost_found = os.path.join(remote_working_directory, REMOTE_WORK_DIRECTORY_LOST_FOUND)
            path_target = os.path.join(path_lost_found, calc_info.uuid)
            logger.warning(
                f'tried to create path {path_existing} but it already exists, moving the entire folder to {path_target}'
            )

            # Make sure the lost+found directory exists, then copy the existing folder there and delete the original
            transport.mkdir(path_lost_found, ignore_existing=True)
            transport.copytree(path_existing, path_target)
            transport.rmtree(path_existing)

            # Now we can create a clean folder for this calculation
            transport.mkdir(calc_info.uuid[4:])
        finally:
            transport.chdir(calc_info.uuid[4:])

        # I store the workdir of the calculation for later file retrieval
        workdir = transport.getcwd()
        node.set_remote_workdir(workdir)

    # I first create the code files, so that the code can put
    # default files to be overwritten by the plugin itself.
    # Still, beware! The code file itself could be overwritten...
    # But I checked for this earlier.
    for code in input_codes:
        if isinstance(code, PortableCode):
            # Note: this will possibly overwrite files
            for root, dirnames, filenames in code.base.repository.walk():
                # mkdir of root
                transport.makedirs(root, ignore_existing=True)

                # remotely mkdir first
                for dirname in dirnames:
                    transport.makedirs((root / dirname), ignore_existing=True)

                # Note, once #2579 is implemented, use the `node.open` method instead of the named temporary file in
                # combination with the new `Transport.put_object_from_filelike`
                # Since the content of the node could potentially be binary, we read the raw bytes and pass them on
                for filename in filenames:
                    with NamedTemporaryFile(mode='wb+') as handle:
                        content = code.base.repository.get_object_content((pathlib.Path(root) / filename), mode='rb')
                        handle.write(content)
                        handle.flush()
                        transport.put(handle.name, (root / filename))
            transport.chmod(code.filepath_executable, 0o755)  # rwxr-xr-x

    # local_copy_list is a list of tuples, each with (uuid, dest_path, rel_path)
    # NOTE: validation of these lists are done inside calculation.presubmit()
    local_copy_list = calc_info.local_copy_list or []
    remote_copy_list = calc_info.remote_copy_list or []
    remote_symlink_list = calc_info.remote_symlink_list or []
    provenance_exclude_list = calc_info.provenance_exclude_list or []

    for uuid, filename, target in local_copy_list:
        logger.debug(f'[submission of calculation {node.uuid}] copying local file/folder to {target}')

        try:
            data_node = load_node(uuid=uuid)
        except exceptions.NotExistent:
            data_node = _find_data_node(inputs, uuid) if inputs else None

        if data_node is None:
            logger.warning(f'failed to load Node<{uuid}> specified in the `local_copy_list`')
        else:

            # If no explicit source filename is defined, we assume the top-level directory
            filename_source = filename or '.'
            filename_target = target or ''

            # Make the target filepath absolute and create any intermediate directories if they don't yet exist
            filepath_target = pathlib.Path(folder.abspath) / filename_target
            filepath_target.parent.mkdir(parents=True, exist_ok=True)

            if data_node.base.repository.get_object(filename_source).file_type == FileType.DIRECTORY:
                # If the source object is a directory, we copy its entire contents
                data_node.base.repository.copy_tree(filepath_target, filename_source)
                sources = data_node.base.repository.list_object_names(filename_source)
                if filename_target:
                    sources = [str(pathlib.Path(filename_target) / subpath) for subpath in sources]
                provenance_exclude_list.extend(sources)
            else:
                # Otherwise, simply copy the file
                with folder.open(target, 'wb') as handle:
                    with data_node.base.repository.open(filename, 'rb') as source:
                        shutil.copyfileobj(source, handle)

                provenance_exclude_list.append(target)

    # In a dry_run, the working directory is the raw input folder, which will already contain these resources
    if not dry_run:
        for filename in folder.get_content_list():
            logger.debug(f'[submission of calculation {node.pk}] copying file/folder {filename}...')
            transport.put(folder.get_abs_path(filename), filename)

        for (remote_computer_uuid, remote_abs_path, dest_rel_path) in remote_copy_list:
            if remote_computer_uuid == computer.uuid:
                logger.debug(
                    '[submission of calculation {}] copying {} remotely, directly on the machine {}'.format(
                        node.pk, dest_rel_path, computer.label
                    )
                )
                try:
                    transport.copy(remote_abs_path, dest_rel_path)
                except (IOError, OSError):
                    logger.warning(
                        '[submission of calculation {}] Unable to copy remote resource from {} to {}! '
                        'Stopping.'.format(node.pk, remote_abs_path, dest_rel_path)
                    )
                    raise
            else:
                raise NotImplementedError(
                    '[submission of calculation {}] Remote copy between two different machines is '
                    'not implemented yet'.format(node.pk)
                )

        for (remote_computer_uuid, remote_abs_path, dest_rel_path) in remote_symlink_list:
            if remote_computer_uuid == computer.uuid:
                logger.debug(
                    '[submission of calculation {}] copying {} remotely, directly on the machine {}'.format(
                        node.pk, dest_rel_path, computer.label
                    )
                )
                try:
                    transport.symlink(remote_abs_path, dest_rel_path)
                except (IOError, OSError):
                    logger.warning(
                        '[submission of calculation {}] Unable to create remote symlink from {} to {}! '
                        'Stopping.'.format(node.pk, remote_abs_path, dest_rel_path)
                    )
                    raise
            else:
                raise IOError(
                    f'It is not possible to create a symlink between two different machines for calculation {node.pk}'
                )
    else:

        if remote_copy_list:
            filepath = os.path.join(workdir, '_aiida_remote_copy_list.txt')
            with open(filepath, 'w', encoding='utf-8') as handle:  # type: ignore[assignment]
                for remote_computer_uuid, remote_abs_path, dest_rel_path in remote_copy_list:
                    handle.write(
                        'would have copied {} to {} in working directory on remote {}'.format(
                            remote_abs_path, dest_rel_path, computer.label
                        )
                    )

        if remote_symlink_list:
            filepath = os.path.join(workdir, '_aiida_remote_symlink_list.txt')
            with open(filepath, 'w', encoding='utf-8') as handle:  # type: ignore[assignment]
                for remote_computer_uuid, remote_abs_path, dest_rel_path in remote_symlink_list:
                    handle.write(
                        'would have created symlinks from {} to {} in working directory on remote {}'.format(
                            remote_abs_path, dest_rel_path, computer.label
                        )
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
                    node.base.repository._repository.put_object_from_filelike(handle, relpath)  # pylint: disable=protected-access

    # Since the node is already stored, we cannot use the normal repository interface since it will raise a
    # `ModificationNotAllowed` error. To bypass it, we go straight to the underlying repository instance to store the
    # files, however, this means we have to manually update the node's repository metadata.
    node.base.repository._update_repository_metadata()  # pylint: disable=protected-access

    if not dry_run:
        # Make sure that attaching the `remote_folder` with a link is the last thing we do. This gives the biggest
        # chance of making this method idempotent. That is to say, if a runner gets interrupted during this action, it
        # will simply retry the upload, unless we got here and managed to link it up, in which case we move to the next
        # task. Because in that case, the check for the existence of this link at the top of this function will exit
        # early from this command.
        remotedata = RemoteData(computer=computer, remote_path=workdir)
        remotedata.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='remote_folder')
        remotedata.store()


def submit_calculation(calculation: CalcJobNode, transport: Transport) -> str:
    """Submit a previously uploaded `CalcJob` to the scheduler.

    :param calculation: the instance of CalcJobNode to submit.
    :param transport: an already opened transport to use to submit the calculation.
    :return: the job id as returned by the scheduler `submit_from_script` call
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
    job_id = scheduler.submit_from_script(workdir, submit_script_filename)
    calculation.set_job_id(job_id)

    return job_id


def stash_calculation(calculation: CalcJobNode, transport: Transport) -> None:
    """Stash files from the working directory of a completed calculation to a permanent remote folder.

    After a calculation has been completed, optionally stash files from the work directory to a storage location on the
    same remote machine. This is useful if one wants to keep certain files from a completed calculation to be removed
    from the scratch directory, because they are necessary for restarts, but that are too heavy to retrieve.
    Instructions of which files to copy where are retrieved from the `stash.source_list` option.

    :param calculation: the calculation job node.
    :param transport: an already opened transport.
    """
    from aiida.common.datastructures import StashMode
    from aiida.orm import RemoteStashFolderData

    logger_extra = get_dblogger_extra(calculation)

    stash_options = calculation.get_option('stash')
    stash_mode = stash_options.get('mode', StashMode.COPY.value)
    source_list = stash_options.get('source_list', [])

    if not source_list:
        return

    if stash_mode != StashMode.COPY.value:
        EXEC_LOGGER.warning(f'stashing mode {stash_mode} is not implemented yet.')
        return

    cls = RemoteStashFolderData

    EXEC_LOGGER.debug(f'stashing files for calculation<{calculation.pk}>: {source_list}', extra=logger_extra)

    uuid = calculation.uuid
    source_basepath = pathlib.Path(calculation.get_remote_workdir())
    target_basepath = pathlib.Path(stash_options['target_base']) / uuid[:2] / uuid[2:4] / uuid[4:]

    for source_filename in source_list:

        if transport.has_magic(source_filename):
            copy_instructions = []
            for globbed_filename in transport.glob(str(source_basepath / source_filename)):
                target_filepath = target_basepath / pathlib.Path(globbed_filename).relative_to(source_basepath)
                copy_instructions.append((globbed_filename, target_filepath))
        else:
            copy_instructions = [(source_basepath / source_filename, target_basepath / source_filename)]

        for source_filepath, target_filepath in copy_instructions:
            # If the source file is in a (nested) directory, create those directories first in the target directory
            target_dirname = target_filepath.parent
            transport.makedirs(str(target_dirname), ignore_existing=True)

            try:
                transport.copy(str(source_filepath), str(target_filepath))
            except (IOError, ValueError) as exception:
                EXEC_LOGGER.warning(f'failed to stash {source_filepath} to {target_filepath}: {exception}')
            else:
                EXEC_LOGGER.debug(f'stashed {source_filepath} to {target_filepath}')

    remote_stash = cls(
        computer=calculation.computer,
        target_basepath=str(target_basepath),
        stash_mode=StashMode(stash_mode),
        source_list=source_list,
    ).store()
    remote_stash.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='remote_stash')


def retrieve_calculation(calculation: CalcJobNode, transport: Transport, retrieved_temporary_folder: str) -> None:
    """Retrieve all the files of a completed job calculation using the given transport.

    If the job defined anything in the `retrieve_temporary_list`, those entries will be stored in the
    `retrieved_temporary_folder`. The caller is responsible for creating and destroying this folder.

    :param calculation: the instance of CalcJobNode to update.
    :param transport: an already opened transport to use for the retrieval.
    :param retrieved_temporary_folder: the absolute path to a directory in which to store the files
        listed, if any, in the `retrieved_temporary_folder` of the jobs CalcInfo
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
        transport.chdir(workdir)

        # First, retrieve the files of folderdata
        retrieve_list = calculation.get_retrieve_list()
        retrieve_temporary_list = calculation.get_retrieve_temporary_list()

        with SandboxFolder(filepath_sandbox) as folder:
            retrieve_files_from_list(calculation, transport, folder.abspath, retrieve_list)
            # Here I retrieved everything; now I store them inside the calculation
            retrieved_files.base.repository.put_object_from_tree(folder.abspath)

        # Retrieve the temporary files in the retrieved_temporary_folder if any files were
        # specified in the 'retrieve_temporary_list' key
        if retrieve_temporary_list:
            retrieve_files_from_list(calculation, transport, retrieved_temporary_folder, retrieve_temporary_list)

            # Log the files that were retrieved in the temporary folder
            for filename in os.listdir(retrieved_temporary_folder):
                EXEC_LOGGER.debug(
                    f"[retrieval of calc {calculation.pk}] Retrieved temporary file or folder '{filename}'",
                    extra=logger_extra
                )

        # Store everything
        EXEC_LOGGER.debug(
            f'[retrieval of calc {calculation.pk}] Storing retrieved_files={retrieved_files.pk}', extra=logger_extra
        )
        retrieved_files.store()

    # Make sure that attaching the `retrieved` folder with a link is the last thing we do. This gives the biggest chance
    # of making this method idempotent. That is to say, if a runner gets interrupted during this action, it will simply
    # retry the retrieval, unless we got here and managed to link it up, in which case we move to the next task.
    retrieved_files.base.links.add_incoming(
        calculation, link_type=LinkType.CREATE, link_label=calculation.link_label_retrieved
    )


def kill_calculation(calculation: CalcJobNode, transport: Transport) -> None:
    """
    Kill the calculation through the scheduler

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
    result = scheduler.kill(job_id)

    if result is not True:

        # Failed to kill because the job might have already been completed
        running_jobs = scheduler.get_jobs(jobs=[job_id], as_dict=True)
        job = running_jobs.get(job_id, None)

        # If the job is returned it is still running and the kill really failed, so we raise
        if job is not None and job.job_state != JobState.DONE:
            raise exceptions.RemoteOperationError(f'scheduler.kill({job_id}) was unsuccessful')
        else:
            EXEC_LOGGER.warning(
                'scheduler.kill() failed but job<{%s}> no longer seems to be running regardless', job_id
            )


def retrieve_files_from_list(
    calculation: CalcJobNode, transport: Transport, folder: str, retrieve_list: List[Union[str, Tuple[str, str, int],
                                                                                           list]]
) -> None:
    """
    Retrieve all the files in the retrieve_list from the remote into the
    local folder instance through the transport. The entries in the retrieve_list
    can be of two types:

        * a string
        * a list

    If it is a string, it represents the remote absolute filepath of the file.
    If the item is a list, the elements will correspond to the following:

        * remotepath
        * localpath
        * depth

    If the remotepath contains file patterns with wildcards, the localpath will be
    treated as the work directory of the folder and the depth integer determines
    upto what level of the original remotepath nesting the files will be copied.

    :param transport: the Transport instance.
    :param folder: an absolute path to a folder that contains the files to copy.
    :param retrieve_list: the list of files to retrieve.
    """
    # pylint: disable=too-many-branches
    for item in retrieve_list:
        if isinstance(item, (list, tuple)):
            tmp_rname, tmp_lname, depth = item
            # if there are more than one file I do something differently
            if transport.has_magic(tmp_rname):
                remote_names = transport.glob(tmp_rname)
                local_names = []
                for rem in remote_names:
                    if depth is None:
                        local_names.append(os.path.join(tmp_lname, rem))
                    else:
                        to_append = rem.split(os.path.sep)[-depth:] if depth > 0 else []
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
        else:  # it is a string
            if transport.has_magic(item):
                remote_names = transport.glob(item)
                local_names = [os.path.split(rem)[1] for rem in remote_names]
            else:
                remote_names = [item]
                local_names = [os.path.split(item)[1]]

        for rem, loc in zip(remote_names, local_names):
            transport.logger.debug(f"[retrieval of calc {calculation.pk}] Trying to retrieve remote item '{rem}'")
            transport.get(rem, os.path.join(folder, loc), ignore_nonexisting=True)
