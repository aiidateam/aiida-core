# Changelog

## v2.7.0 - 2025-06-24

- [Asynchronous SSH connection](#asynchronous-ssh-connection-6626)
- [Extended dumping support for profiles and groups](#extended-dumping-support-for-profiles-and-groups-6723)
- [Forcefully killing processes](#forcefully-killing-processes-6793)
- [Serialization of ORM nodes](#serialization-of-orm-nodes-6723)
- [Miscellaneous](#miscellaneous)
- [Full list of changes for users](#full-list-of-changes-for-users)
    - [Features](#features)
    - [Fixes](#fixes)
    - [Documentation](#documentation)
- [Full list of changes for developers](#full-list-of-changes-for-developers)
    - [Source code](#source-code)
    - [Tests](#tests)
    - [Devops](#devops)

### Asynchronous SSH connection ([#6626](https://github.com/aiidateam/aiida-core/pull/6626))

Previously, when data transfer with a remote computer was active, the responsible transport plugins blocked further program execution until the communication was completed.
This long-standing limitation presented a potential opportunity for performance improvements.
With the introduction of the new asynchronous SSH transport plugin (`core.ssh_async`), multiple communications with a remote machine can now happen concurrently.
As an added benefit, for the configuration of a `Computer` with the `core.ssh_async` transport plugin, it is not necessary anymore to manually provide all SSH connection details during the execution of `verdi computer core.ssh_async configure`.
Instead, one only needs to provide the `hostname` as it is given in the `~/.ssh/config` file, and the transport plugin then uses OpenSSH of the OS to automatically configure the `Computer`, using the system configuration.

#### 🚀 When `core.ssh_async` outperforms `core.ssh`

`core.ssh_async` offers significant performance gains in scenarios where the worker is blocked by heavy transfer tasks, such as uploading, downloading, or copying large files.

**Example: Submitting two WorkGraphs/WorkChains with the following logic:**

1. **WorkGraph 1 – Heavy I/O operations**

   - Uploads a 10 MB file
   - Remotely copies a 1 GB file
   - Retrieves a 1 GB file

2. **WorkGraph 2 – Lightweight task**

   - Executes a simple shell command: `touch file`

**Measured time until the second WorkGraph is processed (single worker):**

- **`core.ssh_async`:** **Only 4 seconds!** 🚀🚀🚀🚀 *A dramatic improvement!*
- **`core.ssh`:** **108 seconds** (the second task waits for the first to finish)

#### ⚖️ When `core.ssh_async` and `core.ssh` perform similarly

For mixed workloads involving numerous uploads and downloads—a common real-world use case—the performance gains depend on the specific conditions.

##### **Large file Transfers (~1 GB):**

`core.ssh_async` typically outperforms due to concurrent upload and download streams.
In favorable network conditions, this can nearly double the effective bandwidth.

> *Example: On a network with a baseline of 11.8 MB/s, the asynchronous mode approached nearly twice that speed under light load (see graph in PR [#6626](https://github.com/aiidateam/aiida-core/pull/6626)).*

**Test case:**\
Two WorkGraphs: one uploads 1 GB, the other retrieves 1 GB using `RemoteData`.

- **`core.ssh_async`:** **120 seconds**
- **`core.ssh`:** **204 seconds**

##### **Small file transfers (many small files):**

Here, the overhead of managing asynchronous operations can outweigh the benefits.

**Test case:**\
25 WorkGraphs, each transferring several ~1 MB files.

- **`core.ssh_async`:** **105 seconds**
- **`core.ssh`:** **65 seconds**

To conclude, the choice of which transport plugin is the best bet for your use case depends on your specific application:
use `core.ssh_async` for workloads involving large file transfers or when you need to prevent I/O operations from blocking other tasks, but stick with `core.ssh` for scenarios dominated by many small file transfers where the asynchronous overhead may reduce performance.

### Extended dumping support for profiles and groups ([#6723](https://github.com/aiidateam/aiida-core/pull/6723))

In version `v2.6.0`, AiiDA introduced the ability to dump processes from the database into a human-readable, structured folder format.
Building on this feature, support has now been extended to allow dumping of entire **groups** and **profiles**, enabling users to retrieve AiiDA data more easily.
This enhancement is part of our broader roadmap to improve AiiDA's usability—especially for new users—who may find it challenging to construct the appropriate queries to extract data from the database manually.
The functionality is accessible via the `verdi` CLI:

```bash
verdi profile dump --all          # This dumps the whole current profile
verdi profile dump --groups <PK>  # This dumps one selected group as part of the profile dumping operation
verdi group dump <PK>             # This dumps only the selected group, disregarding other profile data
```

Since dumping an entire profile can be a resource- and I/O-intensive operation (for large profiles), significant effort has been made to provide flexible options for fine-tuning which nodes are included in the dump.
To avoid initiating dumping operations on large profiles, if no filters (e.g., groups, codes, computers, node `mtime`, etc.) are set, by default, no data is being dumped.
If all data of a profile should be dumped, this must be actively requested using the `--all` option, or one must explicitly select the subset of data to be included in the dump via the provided filter options.
Below is a snippet from the command's help output:

```bash
Usage: verdi profile dump [OPTIONS] [--]

  Dump all data in an AiiDA profiles storage to disk.

Options:
  -p, --path PATH                 Base path for dump operations that write to
                                  disk.
  -n, --dry-run                   Perform a dry run.
  -o, --overwrite                 Overwrite file/directory when writing to
                                  disk.
  -a, --all                       Include all entries, disregarding all other
                                  filter options and flags.
  -X, --codes CODE...             One or multiple codes identified by their
                                  ID, UUID or label.
  -Y, --computers COMPUTER...     One or multiple computers identified by
                                  their ID, UUID or label.
  -G, --groups GROUP...           One or multiple groups identified by their
                                  ID, UUID or label.
  -u, --user USER                 Email address of the user.
  -p, --past-days PAST_DAYS       Only include entries created in the last
                                  PAST_DAYS number of days.
  --start-date TEXT               Start date for node mtime range selection
                                  for node collection dumping.
  --end-date TEXT                 End date for node mtime range selection for
                                  node collection dumping.
  --filter-by-last-dump-time / --no-filter-by-last-dump-time
                                  Only select nodes whose mtime is after the
                                  last dump time.  [default: filter-by-last-
                                  dump-time]
  --only-top-level-calcs / --no-only-top-level-calcs
                                  Dump calculations in their own dedicated
                                  directories, not just as part of the dumped
                                  workflow.  [default: only-top-level-calcs]
  --only-top-level-workflows / --no-only-top-level-workflows
                                  If a top-level workflow calls sub-workflows,
                                  create a designated directory only for the
                                  top-level workflow.  [default: only-top-
                                  level-workflows]
  --delete-missing / --no-delete-missing
                                  If a previously dumped group or node is
                                  deleted from the DB, delete the
                                  corresponding dump directory.  [default:
                                  delete-missing]
  --symlink-calcs / --no-symlink-calcs
                                  Symlink workflow sub-calculations to their
                                  own dedicated directories.  [default: no-
                                  symlink-calcs]
  --organize-by-groups / --no-organize-by-groups
                                  If the collection of nodes to be dumped is
                                  organized in groups, reproduce its
                                  hierarchy.  [default: organize-by-groups]
  --also-ungrouped / --no-also-ungrouped
                                  Dump also data of nodes that are not part of
                                  any group.  [default: no-also-ungrouped]
  --relabel-groups / --no-relabel-groups
                                  Update directories and log entries for the
                                  dumping if groups have been relabeled since
                                  the last dump.  [default: relabel-groups]
  --include-inputs / --exclude-inputs
                                  Include linked input nodes of
                                  `CalculationNode`(s).  [default: include-
                                  inputs]
  --include-outputs / --exclude-outputs
                                  Include linked output nodes of
                                  `CalculationNode`(s).  [default: exclude-
                                  outputs]
  --include-attributes / --exclude-attributes
                                  Include attributes in the
                                  `aiida_node_metadata.yaml` written for every
                                  `ProcessNode`.  [default: include-
                                  attributes]
  --include-extras / --exclude-extras
                                  Include extras in the
                                  `aiida_node_metadata.yaml` written for every
                                  `ProcessNode`.  [default: exclude-extras]
  -f, --flat                      Dump files in a flat directory for every
                                  step of a workflow.
  --dump-unsealed / --no-dump-unsealed
                                  Also allow the dumping of unsealed process
                                  nodes.  [default: no-dump-unsealed]
  -v, --verbosity [notset|debug|info|report|warning|error|critical]
                                  Set the verbosity of the output.
  -h, --help                      Show this message and exit.

```

Another key feature is the incremental nature of the command, which ensures that the dumping process synchronizes the output folder with the internal state of AiiDA's DB by gradually adding or removing files on successive executions of the command.
This allows for efficient updates without having to overwrite everything, and is in contrast to AiiDA archive creation, which is a one-shot process.
The behavior can further be adjusted using:

- `--dry-run` (`-n`): to simulate the dump without writing any files.
- `--overwrite` (`-o`): to fully overwrite the target directory if it already exists.

Finally, the command provides various options to customize the output folder structure, for instance, to reflect the group hierarchy of AiiDA's internal DB state, symlink duplicate calculations (e.g., which are contained in multiple groups), create dedicated directories for sub-workflows and calculations of top-level workflows, and more.

These enhancements aim to make data export from AiiDA more robust, customizable, and user-friendly.

### Stashing ([#6746](https://github.com/aiidateam/aiida-core/pull/6746), [#6772](https://github.com/aiidateam/aiida-core/pull/6772))

With this feature, you can bundle your data to a (compressed) tar archive during stashing by specifying one of the `stash_mode` options `"tar"`, `"tar.bz2"`, `"tar.gz"`, or `"tar.xz"`.
When specifying the stashing operation during the setup of your calculation, compression can be configured as follows:

```python
from aiida.plugins import CalculationFactory
from aiida.engine import run
from aiida.common import StashMode
from aiida.orm import load_computer

inputs = {
    ...,
    'metadata': {
        'computer': load_computer(label="localhost"),
        'options': {
            'resources': {'num_machines': 1},
            'stash': {
                'stash_mode':  StashMode.COMPRESS_TARGZ.value,
                'target_base': '/scratch/',
                'source_list': ['heavy_data.xyz'],  # ['*'] to stash everything
            },
        },
    },
}
# If you use a builder, use
# builder.metadata = {'options': {...}, ...}

run(MyCalculation, **inputs)
```

In addition, it was historically only possible to enable stashing when it was instructed before running a generic `CalcJob`.
This means that the instruction had to be "attached" to the original `CalcJob` before its execcution.
However, if a user would realize they need to stash something only after running the calculation, this would not be possible.
With `v2.7.0`, we introduce the new `StashCalculation` `CalcJob` which is able to perform a stashing operation after a calculation has finished—provenance included!
The usage is very similar, and for consistency and user-friendliness, we keep the instructions as part of the metadata.
The only main input is the `remote_folder` output node (an instance of `RemoteData`) of the calculation source node to be stashed, for example:

```python
from aiida.plugins import CalculationFactory
from aiida.engine import run
from aiida.common import StashMode
from aiida.orm import load_node

StashCalculation = CalculationFactory('core.stash')

calcjob_node = load_node(<CALCJOB_PK>)
inputs = {
    'metadata': {
        'computer': calcjob_node.computer,
        'options': {
            'resources': {'num_machines': 1},
            'stash': {
                'stash_mode':  StashMode.COPY.value,
                'target_base': '/scratch/',
                'source_list': ['heavy_data.xyz'],
            },
        },
    },
    'source_node': calcjob_node.outputs.remote_folder,
}

result = run(StashCalculation, **inputs)
```

### Forcefully killing processes ([#6793](https://github.com/aiidateam/aiida-core/pull/6793))

Prior to version `v2.7.0`, the `verdi process kill` command could hang if a connection to the remote computer could not be established.
A new `--force` option has been introduced to terminate a process without waiting for a response from the remote machine.\
**Note:** Using `--force` may result in orphaned jobs on the remote system if the remote job cancellation fails.

```bash
verdi process kill --force <PROCESS_ID>
```

We also now cancel the old killing action if it is resend by the user.
This allows the user to adapt the parameters for the exponential backoff mechanism (EBM) applied by AiiDA in the `verdi config` and then resend the kill command with the new parameters.

```bash
verdi process kill --timeout 5 <PROCESS_ID>
verdi config set transport.task_maximum_attempts 1
verdi config set transport.task_retry_initial_interval 5
verdi daemon restart
verdi process kill <PROCESS_ID>
```

Furthermore, the `timeout` and `wait` options were not behaving correctly, so they are now fixed and both merged into the single `timeout` option.
By passing `--timeout 0` it replicates the `--no-wait` functionality, meaning the command does not block until the action has finished, and by passing `--timeout inf` (default option, replicating `--wait` without a `timeout`), the command blocks until a response.
For more information see issue [#6524](https://github.com/aiidateam/aiida-core/issues/6524).

### Serialization of ORM nodes ([#6723](https://github.com/aiidateam/aiida-core/pull/6723))

AiiDA's Python API provides an object relational mapper (ORM) that abstracts the various entities that can be stored inside the provenance graph (via the SQL database) and the relationships between them.
In most use cases, users use this ORM directly in Python to construct new instances of entities and retrieve existing ones, in order to get access to their data and manipulate it.
A shortcoming of the current ORM is that it is not possible to programmatically introspect the schema of each entity: that is to say, what data each entity stores.
This makes it difficult for external applications to provide interfaces to create and or retrieve entity instances.
It also makes it difficult to take the data outside of the Python environment since the data would have to be serialized.
However, without a well-defined schema, doing this without an ad-hoc solution is practically impossible.

With the implementation of a `pydantic` `Model` for each Entity we now allow external applications to programmatically determine the schema of all AiiDA ORM entities and automatically (de)serialize entity instances to and from other data formats, e.g., JSON.
An example how this is done for an AiiDA integer node:

```python
node = Int(5) # Can be any ORM node
serialized_node = node.serialize()
print(serialized_node)
# Out: {'pk': None, 'uuid': '485c2ec8-441d-484d-b7d9-374a3cdd98ae', 'node_type': 'data.core.int.Int.', 'process_type': None, 'repository_metadata': {}, 'ctime': datetime.datetime(2025, 5, 2, 10, 20, 41, 275443, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200), 'CEST')), 'mtime': None, 'label': '', 'description': '', 'attributes': {'value': 5}, 'extras': {}, 'computer': None, 'user': 1, 'repository_content': {}, 'source': None, 'value': 5}
uuid: 77e9c19a-5ecb-40cf-8238-ea5c55fbb83f (unstored) value: 5
node_deserialized = Int.from_serialized(**serialized_node)
print(node_deserialized)
# Out: uuid: 77e9c19a-5ecb-40cf-8238-ea5c55fbb83f (unstored) value: 5
```

For an extensive overview of the implications see [AEP 010](https://github.com/aiidateam/AEP/blob/983a645c9285ba65c7cf07fe6064c23e7e994c06/010_orm_schema/readme.md).

### Miscellaneous

- `aiida-core` is now compatible with Python 3.13 [#6600](https://github.com/aiidateam/aiida-core/pull/6600)
- OpenSSH backend for transport `core.ssh_async` for multiplexing [#6795](https://github.com/aiidateam/aiida-core/pull/6795) 
- Improved Windows support [#6715](https://github.com/aiidateam/aiida-core/pull/6715)
- `RemoteData` extended by member function `get_size_on_disk` [#6584](https://github.com/aiidateam/aiida-core/pull/6584)
- `SinglefileData` extended by constructor `from_bytes` [#6653](https://github.com/aiidateam/aiida-core/pull/6653)
- Allow zero memory specification for SLURM [#6605](https://github.com/aiidateam/aiida-core/pull/6605)
- Add filters to `verdi group delete` [#6556](https://github.com/aiidateam/aiida-core/pull/6556)
- `verdi storage maintain` shows a progress bar [#6562](https://github.com/aiidateam/aiida-core/pull/6562)
- New transport endpoints `compress` & `extract` [#6743](https://github.com/aiidateam/aiida-core/pull/6743)
- Implementation of missing SQLite endpoints (en route to full feature parity between PostgreSQL and SQLite):
  - `get_creation_statistics` [#6763](https://github.com/aiidateam/aiida-core/pull/6763)
  - `contains` [#6619](https://github.com/aiidateam/aiida-core/pull/6619)


### Full list of changes for users

#### Features
- CLI: Accept mulitple node identifiers in `verdi node graph generate` (#6443) [[6d2edc919]](https://github.com/aiidateam/aiida-core/commit/6d2edc919e3340b67d8097c425a5e5f6971707f8)
- CLI: Add default for `output_file` in computer and code export commands (#6486) [[9355a9878]](https://github.com/aiidateam/aiida-core/commit/9355a9878134b7c8e3e75bb029c251f0bf0a7357)
- CLI: Validate storage in `verdi storage version` (#6551) [[ad1a431f3]](https://github.com/aiidateam/aiida-core/commit/ad1a431f33a6e57d8b6867447ecdfd8ff41bc8f5)
- CLI: Add filters to verdi group delete. (#6556) [[72a6b183b]](https://github.com/aiidateam/aiida-core/commit/72a6b183b8048d5c31b2b827efe6b8b969038e28)
- CLI: verdi storage maintain: show a progress bar (#6562) [[c7c289d38]](https://github.com/aiidateam/aiida-core/commit/c7c289d3892bf76894714f53f58b7ce5b0761178)
- implement has_key filter for SQLite backend [[779cc29d8]](https://github.com/aiidateam/aiida-core/commit/779cc29d8a47eddabdf9b274d7fa711220ee1aa9)
- ORM: Add `from_bytes` `classmethod` to `orm.SinglefileData` (#6653) [[0f0b88a39]](https://github.com/aiidateam/aiida-core/commit/0f0b88a39ff670fb452678c9b47ef6978e075005)
- ORM: Add `get_size_on_disk` method to `RemoteData` (#6584) [[02cbe0ceb]](https://github.com/aiidateam/aiida-core/commit/02cbe0ceb7d9f9343911592e31abe6310d2bd38b)
- QB: Re-introduction of `contains` Filter Operator for SQLite (#6619) [[aa0aa262a]](https://github.com/aiidateam/aiida-core/commit/aa0aa262ab30e40211c0bd4d2c08a7172c2fd257)
- Transport: `AsyncTransport`  plugin (#6626) [[eba6954bf]](https://github.com/aiidateam/aiida-core/commit/eba6954bf97999bbfd07210b33641d3b494ce221)
- Add support for running direct jobs on bash environment on Windows [[ce9dcf421]](https://github.com/aiidateam/aiida-core/commit/ce9dcf421346ae2e6aedc0cdc2ff325d073fcf65)
- `Transport`: feat `compress` & `extract` methods (#6743) [[f4c55f5f7]](https://github.com/aiidateam/aiida-core/commit/f4c55f5f78cd7fde9a5b4a4e48cad2159fd666b2)
- `CLI`: add option `--clean-workdir` to `verdi node delete` (#6756) [[c53592850]](https://github.com/aiidateam/aiida-core/commit/c53592850d7d39a4158ac7c8f25b219c848e9a6c)
- `RemoteStashCompressedData` new data class, and it's deployment to `execmanager.py` to support compressed file formats while stashing. [[ae49af6c3]](https://github.com/aiidateam/aiida-core/commit/ae49af6c304ba155c2e4fc2ea8f69fb8cfcacb4c)
- [QueryBuilder] Implement `get_creation_statistics` for SQLite backend (#6763) [[83454c713]](https://github.com/aiidateam/aiida-core/commit/83454c713cac6e05ac6f0b1c238f576306e87191)
- Support for Python 3.13 (#6600) [[eb34b0606]](https://github.com/aiidateam/aiida-core/commit/eb34b06062f1aad1ab78b12330706d12979b73d2)
- `StashCalculation`: a new `CalcJob` plugin (#6772) [[bc253236d]](https://github.com/aiidateam/aiida-core/commit/bc253236d7ba16b988e6cf34d58287ffb9610ccb)
- ORM: Use pydantic to specify a schema for each ORM entity (#6255) [[958bfd05c]](https://github.com/aiidateam/aiida-core/commit/958bfd05cabe403cd0ccf2832478d397c177685e)
- Add force-kill option when killing a process (#6793) [[b6d0fe50d]](https://github.com/aiidateam/aiida-core/commit/b6d0fe50dd087997a77e4120095fde19db9f92df)
- Align the yes/no prompt in `verdi computer delete` with other prompts [[71fc14f3c2a501ff8d704d20df76a297edc8e8bc]](https://github.com/aiidateam/aiida-core/commit/71fc14f3c2a501ff8d704d20df76a297edc8e8bc)
- Profile data dumping (#6723) [[88df72a46073359bd4bdaa03cb5f4c5a92aa67af]](https://github.com/aiidateam/aiida-core/commit/88df72a46073359bd4bdaa03cb5f4c5a92aa67af)
- `Transport`: Add OpenSSH as backend option to `AsyncSshTransport` (#6795) [[c7fdf1cfaf50b555698ef039d55b7f295a71644a]](https://github.com/aiidateam/aiida-core/commit/c7fdf1cfaf50b555698ef039d55b7f295a71644a)

#### Fixes
- CLI: Catch `NotImplementedError` in `verdi calcjob gotocomputer` (#6525) [[120c8ac6d]](https://github.com/aiidateam/aiida-core/commit/120c8ac6dcd15cec1ff3260ab65276c60027dd5f)
- Scheduler: Allow a memory specification of zero for the SLURM plugin (#6605) [[0fa958285]](https://github.com/aiidateam/aiida-core/commit/0fa958285bb07ece05b944cbd694aed663b5193a)
- `QueryBuilder`: Fix type bugs for PostgreSQL backend (#6658) [[53be73730]](https://github.com/aiidateam/aiida-core/commit/53be73730aae0d14fef11cf497e60dcd528c5228)
- Fix verdi devel check-undesired-imports when tui extra is installed (#6693) [[8039ad914]](https://github.com/aiidateam/aiida-core/commit/8039ad9147d2a4bc61bc86845a1c82c2fd484eae)
- `Transport`: Bug fix in `rename` method (#6735) [[f56fcc31c]](https://github.com/aiidateam/aiida-core/commit/f56fcc31c70e3bd6a1422eb6cfee3f5fab5eaac4)
- Cover tests that may randomly fail because DB racing in xdist test (#6713) [[4d374f465]](https://github.com/aiidateam/aiida-core/commit/4d374f465808fe64d30ef89679b820169ffd3f74)
- 'Storage': `sqlite_zip` add a filter to `tar.extractall` method to be compatible with python 3.12 (#6770) [[b95fd2189]](https://github.com/aiidateam/aiida-core/commit/b95fd21897aa83c3da25e1c18381b5613904115f)
- Post release: update version number after v2.6.3 release (#6797) [[0b2222e2b]](https://github.com/aiidateam/aiida-core/commit/0b2222e2bceba6acad21840ae69cfea50a542a9d)
- 👌 Align behavior of `puttree` method for nested folders [[834b2942e]](https://github.com/aiidateam/aiida-core/commit/834b2942eebfbf56380b900f03e94d161a5fd161)
- 🐛 Fix `local_copy_list` behavior for nested target folder [[9fe8d5090]](https://github.com/aiidateam/aiida-core/commit/9fe8d5090cbe4fbfbe34558a04cca32ecb65422f)
- Fix the pydantic model for `RemoteData` (#6845) [[936185b7f]](https://github.com/aiidateam/aiida-core/commit/936185b7f3f61c40bd5f1579f7921ea788233af1)
- Update/add models for `RemoteData` and `RemoteStashCompressedData` (#6844) [[2fd4b8931d4abd7799f6c17aec21612a7f85d1b3]](https://github.com/aiidateam/aiida-core/commit/2fd4b8931d4abd7799f6c17aec21612a7f85d1b3)
- StashCalculation: throw a warning if the computer node mismatches with the one of source_node (#6862) [[582bd5322d1d147049eb34f54b868517c19cf4f6]](https://github.com/aiidateam/aiida-core/commit/582bd5322d1d147049eb34f54b868517c19cf4f6)
- Sending multiple `process_kill` actions reschedules the cancelation of scheduler job (#6870) [[e768b70383ee605feeafd05862a17b8481447880]](https://github.com/aiidateam/aiida-core/commit/e768b70383ee605feeafd05862a17b8481447880)
- Include usage of `filter_size` for importing logs, user, computer (#6889) [[ee87c790c998e06a9ce3b7f2f7a49be433bc49c0]](https://github.com/aiidateam/aiida-core/commit/ee87c790c998e06a9ce3b7f2f7a49be433bc49c0)
- Rename `--force-kill` option to `--force` in kill action (#6908) [[5167e2cbc93dfe1d54f8fa6dd56a53248feb21ae]](https://github.com/aiidateam/aiida-core/commit/5167e2cbc93dfe1d54f8fa6dd56a53248feb21ae)
- Merge `wait` and `timeout` to one CLI option for `verdi process {kill|play|pause}` (#6902) [[ec9d53e9cbb270ef45df1d1ef74bddaa4f94c029]](https://github.com/aiidateam/aiida-core/commit/ec9d53e9cbb270ef45df1d1ef74bddaa4f94c029)
- Fix wrong config folder setup in `aiida_instance` fixture [[a4edcf2a2099186b3eec6833a48ba1ded7afced7]](https://github.com/aiidateam/aiida-core/commit/a4edcf2a2099186b3eec6833a48ba1ded7afced7)
- `Transport`: bug fix on glob (#6917) [[2d8dd7a1c4821c3a01589195c5ed0abac79099b0]](https://github.com/aiidateam/aiida-core/commit/2d8dd7a1c4821c3a01589195c5ed0abac79099b0)

### Documentation
- Docs: Add overview of common `core` plugins (#6654) [[baf8d7c3e]](https://github.com/aiidateam/aiida-core/commit/baf8d7c3efd18c0e3337ea5a6b09631fa449220c)
- Docs: add google-site-verification meta tag (#6792) [[660fec70e]](https://github.com/aiidateam/aiida-core/commit/660fec70ef43a64be7edae3c12f0a0fd5ef84349)
- Docs: Enhancements to Installation, Introduction, and Tutorial Sections (#6806) [[ee1cc9fb8]](https://github.com/aiidateam/aiida-core/commit/ee1cc9fb820fc34f1996b6ea338014cefdc69e36)
- Docs: Fix the logic in FizzBuzz WorkChain example (#6812) [[cfd2052a4]](https://github.com/aiidateam/aiida-core/commit/cfd2052a42c977e43699f8ff429d406b15c9740a)
- Doc: Add `StashCalculation` explanation to RTD (#6861) [[85a84fc73c16151ba5320c7a9c7dfafc8c7572ab]](https://github.com/aiidateam/aiida-core/commit/85a84fc73c16151ba5320c7a9c7dfafc8c7572ab)
- Doc: Update the RTD regarding `verdi process {kill|pause|play}` (#6909) [[d79137d2e730e479a9bcf1453cd19d7bf31f479b]](https://github.com/aiidateam/aiida-core/commit/d79137d2e730e479a9bcf1453cd19d7bf31f479b)

### Full list of changes for developers

#### Source code
- Add the `SshAutoTransport` transport plugin (#6154) [[71422eb87]](https://github.com/aiidateam/aiida-core/commit/71422eb872040a9ba23047d2ec031f6deaa6a7cc)
- Dependencies: Update requirements for `kiwipy` and `plumpy` [[d86017f42]](https://github.com/aiidateam/aiida-core/commit/d86017f42cb5359d0272694247756d547057a663)
- `Manager`: Catch `TimeoutError` when closing communicator [[e91371573]](https://github.com/aiidateam/aiida-core/commit/e91371573a84d4a68d6107f33c392b8718f2f26f)
- `SqliteDosStorage`: Make the migrator compatible with SQLite (#6429) [[6196dcd3b]](https://github.com/aiidateam/aiida-core/commit/6196dcd3b321758ae8dfb84b22a59e1c77d8e933)
- Dependencies: Update requirement to `psycopg~=3.0` (#6362) [[cba6e7c75]](https://github.com/aiidateam/aiida-core/commit/cba6e7c757ec74194afc63809b5dac72bb81a771)
- `Scheduler`: Refactor interface to make it more generic (#6043) [[954cbdd3e]](https://github.com/aiidateam/aiida-core/commit/954cbdd3ee5127d6618db9d144508505e41cffcc)
- Post release: add the `.post0` qualifier to version attribute [[16b8fe4a0]](https://github.com/aiidateam/aiida-core/commit/16b8fe4a0912ac36973fb82f14691723e72599a7)
- Post release: update version number and CHANGELOG after v2.6.2 release [[fb3686271]](https://github.com/aiidateam/aiida-core/commit/fb3686271fcdeb5506838a5a3069955546b05460)
- Dependencies: Update requirement `paramiko~=3.0` (#6559) [[c52ec6758]](https://github.com/aiidateam/aiida-core/commit/c52ec6758a0d5c5191e4099cabbbd1a7314284ed)
- Refactor: Add the `_prepare_yaml` method to `AbstractCode` (#6565) [[98ffc331d]](https://github.com/aiidateam/aiida-core/commit/98ffc331d154cc7717861fde6c908ec510003926)
- Dependencies: version check on `sqlite` C-language (#6567) [[d0c9572c8]](https://github.com/aiidateam/aiida-core/commit/d0c9572c83aa953f1490f35c1110f5815dc15ac3)
- Add `verdi devel launch-multiply-add` [[b7c82867b]](https://github.com/aiidateam/aiida-core/commit/b7c82867b5cca08f1ee77bda31bf11d77e96b548)
- Add `aiida_profile_clean` to `test_devel.py` [[2ed19dcd8]](https://github.com/aiidateam/aiida-core/commit/2ed19dcd824e1b9a5003dae93613a56ecca7c3a7)
- `Transport` & `Engine`: factor out `getcwd()` & `chdir()` for compatibility with upcoming async transport (#6594) [[6f5c35ed1]](https://github.com/aiidateam/aiida-core/commit/6f5c35ed16beaf585e2c3045cab5ed4fb0ef3bc1)
- Changes required make it possible to run with pytest-xdist (#6631) [[1c5f10968]](https://github.com/aiidateam/aiida-core/commit/1c5f10968f40934b81eef72ed72dc814497707a8)
- Update changelog for release v2.6.3 (#6637) [[54c4a0d06]](https://github.com/aiidateam/aiida-core/commit/54c4a0d06660f522717d87ffae1ca84211d8c79e)
- Typing: mypy fix for `orm.List` the `pop` and `index` methods (#6635) [[36eab7797]](https://github.com/aiidateam/aiida-core/commit/36eab779793a6dd0184c83f0b0af6a75a62fac82)
- Use only one global var for marking config folder tree (#6610) [[9baf3ca96]](https://github.com/aiidateam/aiida-core/commit/9baf3ca96caa5577ec8ed6cef69512f430bb5675)
- Make `load_profile` and methods in aiida.__init__ importable from aiida module (#6609) [[ec52f4ef3]](https://github.com/aiidateam/aiida-core/commit/ec52f4ef321f9ef1fa24e5a3056153ea55bce7d4)
- Adapt message arguments passing to process controller (#6668) [[80c1741ca]](https://github.com/aiidateam/aiida-core/commit/80c1741ca3df607c75254a61fd664018dc043219)
- Disable `apparent-size` in `du` command of `get_size_on_disk` (#6702) [[2da3f9600]](https://github.com/aiidateam/aiida-core/commit/2da3f9600aa69e90977370377b1bf81edd9856a1)
- Engine: Async run (#6708) [[d71ef9810]](https://github.com/aiidateam/aiida-core/commit/d71ef98100a0d0b5ff2e71d078cde4303e1cdd1b)
- ORM: Use `skip_orm` as the default implementation for `SqlaGroup.add_nodes` and `SqlaGroup.remove_nodes` (#6720) [[d2fbf214a]](https://github.com/aiidateam/aiida-core/commit/d2fbf214ad2fcfe5e39f9ebe2982f05557196397)
- A new common funcion:`assert_never` to assert certain part of the code is never reached. [[d7c382a24]](https://github.com/aiidateam/aiida-core/commit/d7c382a2447260320a36be4f5c6de285f9d37bdc)
- Replace usage of aiida.common.utils.strip_prefix with built-in removeprefix (#6758) [[290045b17]](https://github.com/aiidateam/aiida-core/commit/290045b171626a94f717e1e066e3cced50dab5a3)
- Revert "Add the `SshAutoTransport` transport plugin (#6154)" (#6852) [[cf2614fa2]](https://github.com/aiidateam/aiida-core/commit/cf2614fa26ce1e8b15656a659a9f3b9fcec88b55)
- Transport: Three bug fixed in `test_execmanager` and `AsyncSshTransport` (#6855) [[474e0fabcb4e2331253e10c1fbcd8ba6a323f6d2]](https://github.com/aiidateam/aiida-core/commit/474e0fabcb4e2331253e10c1fbcd8ba6a323f6d2)
- Update package metadata with suppport of py3.13 (#6863) [[e257b3cb2f0e7a088d2ac4ebfb463492beea321d]](https://github.com/aiidateam/aiida-core/commit/e257b3cb2f0e7a088d2ac4ebfb463492beea321d)
- Enable `defer_build` for `Entity.Model` and `Sealable.Model` (#6867) [[cf07e9f9db63a3e484b9df99b70510bee7b17ff7]](https://github.com/aiidateam/aiida-core/commit/cf07e9f9db63a3e484b9df99b70510bee7b17ff7)
- Deprecate in `verdi quicksetup` the `--db-engine` option (#6906) [[8dd094873cefcf0fc342edc676a7689a2300d080]](https://github.com/aiidateam/aiida-core/commit/8dd094873cefcf0fc342edc676a7689a2300d080)
- Fix typing errors in `src/aiida/manage/tests` module (#6903) [[5a9c9e8c0e899c7b2027cf15178eb0fdecd6ae2e]](https://github.com/aiidateam/aiida-core/commit/5a9c9e8c0e899c7b2027cf15178eb0fdecd6ae2e)
- Rename `machine_or_host` to `host` and simplify prompts (#6914) [[bf34c953326123f011585ead16a635e761943436]](https://github.com/aiidateam/aiida-core/commit/bf34c953326123f011585ead16a635e761943436)

#### Tests
- Tests: Remove test for `make_aware` using fixed date [[9fe7672f3]](https://github.com/aiidateam/aiida-core/commit/9fe7672f36c706c7eca87a4807012a1c8a5c0259)
- Devops: Change tempfile to pytest's tmp_path [[309352f8b]](https://github.com/aiidateam/aiida-core/commit/309352f8bf29e52057bd31153858eb8a3560e704)
- Devops: Determine command directory dynamically with `which` [[d3e9333f5]](https://github.com/aiidateam/aiida-core/commit/d3e9333f517ce833b8ce288652007c10e0b99f9f)
- Tests: add --db-backend pytest option (#6625) [[a863d1e88]](https://github.com/aiidateam/aiida-core/commit/a863d1e887822334df4db9120421cd38ded04d3e)
- Test refactoring: use tmp path fixture to mock remote and local for transport plugins (#6627) [[197c666d3]](https://github.com/aiidateam/aiida-core/commit/197c666d362b3a7dd03bec9ccc1e41bb44023e7c)
- Set pytest timeout to 60s for every test (#6674) [[17ab39519]](https://github.com/aiidateam/aiida-core/commit/17ab3951956c54de29d328809d54f88d89bd66ba)
- Timeout for single pytest to 240s (#6692) [[8ae66fb66]](https://github.com/aiidateam/aiida-core/commit/8ae66fb66a4fdc876b9f429a09072f41c4ed48bd)
- Clean profile in orm/test_codes.py::test_input_code [[3f5e2c132]](https://github.com/aiidateam/aiida-core/commit/3f5e2c132554e58c868660b3ee874661925366ca)
- Only emit path to daemon log path in pytest tmp folder (#6698) [[7a460c0fd]](https://github.com/aiidateam/aiida-core/commit/7a460c0fd45ffd8da790807b3ea214e6fab01c5b)
- Store default profile in `aiida_profile_factory` (#6893) [[43176cba3e39f4d04ef3529cd50d3e368e1d78aa]](https://github.com/aiidateam/aiida-core/commit/43176cba3e39f4d04ef3529cd50d3e368e1d78aa)
- Separate testing of legacy pytest fixtures from unittests [[229c35affd72d9fa5835b865f2e6209d250f01ba]](https://github.com/aiidateam/aiida-core/commit/229c35affd72d9fa5835b865f2e6209d250f01ba)
- Merge pull request #6904 fixing legacy pytest-fixture [[48991abbbc8456552cd7389adb54b9efdef17564]](https://github.com/aiidateam/aiida-core/commit/48991abbbc8456552cd7389adb54b9efdef17564)

#### Devops
- Devops: Update pre-commit dependencies (#6504) [[14bb05f4b]](https://github.com/aiidateam/aiida-core/commit/14bb05f4b4e7fbda86682ea2cf4e3881b3a3e8dc)
- Docker: Fix release tag in publish workflow (#6520) [[c740b99f2]](https://github.com/aiidateam/aiida-core/commit/c740b99f2bfe366a733f140164a21048cd51198e)
- Devops: Mark `test_leak_ssh_calcjob` as nightly (#6521) [[a5da4eda1]](https://github.com/aiidateam/aiida-core/commit/a5da4eda131f844c3639bdb01a256b9e9a7873a2)
- Devops: Add type hints to `aiida.orm.utils.remote` (#6503) [[2bdcb7f00]](https://github.com/aiidateam/aiida-core/commit/2bdcb7f00dac93b3287baef042f873cd5f6ee247)
- Docker: Make warning test insensitive to deprecation warnings (#6541) [[f1be224c4]](https://github.com/aiidateam/aiida-core/commit/f1be224c4680407984eda8652692ec0ea708a3e1)
- CI: Update ignore comment as the way that presumably updated mypy expects (#6566) [[655da5acc]](https://github.com/aiidateam/aiida-core/commit/655da5acc183ef81120f5d77f1fdc760e186c64c)
- Update the issue template with the Discourse group (#6588) [[a7d8dd04e]](https://github.com/aiidateam/aiida-core/commit/a7d8dd04ea63bb362e9414a8bd55554f30424bf1)
- Fix broken troubleshooting link in bug report issue template (#6589) [[f57591655]](https://github.com/aiidateam/aiida-core/commit/f57591655a8f91d1b37bd0f46e8c6dc6a9566c2c)
- Devops: Add tox environment for pytest with presto mark [[e2699118e]](https://github.com/aiidateam/aiida-core/commit/e2699118ea880c3619f0985defec7c5ad09b926e)
- CLI: Dump only `sealed` process nodes (#6591) [[70572380b]](https://github.com/aiidateam/aiida-core/commit/70572380bf05998f27ea54df3653ec357e44fc69)
- CLI: Check user execute in `verdi code test` for `InstalledCode` (#6597) [[8350df0cb]](https://github.com/aiidateam/aiida-core/commit/8350df0cb0c48588899d732feb26ce7e43903173)
- Devops: Bump `peter-evans/create-pull-request` (#6576) [[dd866ce81]](https://github.com/aiidateam/aiida-core/commit/dd866ce816e986285f2c5794f431b6e3c68a369b)
- Bump mypy version to ~=1.13.0 (#6630) [[c93fb4f75]](https://github.com/aiidateam/aiida-core/commit/c93fb4f75554802e46fdcb7cf8caf27318ad04d0)
- CI: remove ci-style.yml (#6638) [[451375b7c]](https://github.com/aiidateam/aiida-core/commit/451375b7cfa08c7a373654f4ac64d6e1204bd865)
- Pre-commit: exclude mypy for all tests (#6639) [[846c11f8c]](https://github.com/aiidateam/aiida-core/commit/846c11f8c323c60a8e17eb715980e114cc9e6363)
- Add helper script for creating patch releases from a list of commits (#6602) [[ec8a055a5]](https://github.com/aiidateam/aiida-core/commit/ec8a055a533b6422ed95b4ec30faf70efd667761)
- CLI: Handle `None` process states in build_call_graph (#6590) [[f74adb94c]](https://github.com/aiidateam/aiida-core/commit/f74adb94cc1e8439c8076f563ec112466fdd174b)
- Bump ruff version (#6614) [[c915a9734]](https://github.com/aiidateam/aiida-core/commit/c915a97348ffb344ab48fe031711120238f6976a)
- DevOp: Using xdist to run pytest in parallel (#6620) [[090dc1c73]](https://github.com/aiidateam/aiida-core/commit/090dc1c7300ab9d25ee75498d040ecf1cd3bb1d7)
- Bump codecov/codecov-action from 4 to 5 in the gha-dependencies group (#6648) [[835d13b73]](https://github.com/aiidateam/aiida-core/commit/835d13b735e068883ed414755717b0fc366642b0)
- Amend type call error after using AiiDAConfigDir (#6646) [[dbdc36c63]](https://github.com/aiidateam/aiida-core/commit/dbdc36c635ae3596905ab54f0905e97026b85f49)
- CI: Turn off verbose pytest output (#6633) [[41a0fd92b]](https://github.com/aiidateam/aiida-core/commit/41a0fd92bf6233a758b10a785534f6186b567e16)
- Bump ruff to v0.8.0 (#6634) [[333992be5]](https://github.com/aiidateam/aiida-core/commit/333992be53d2e9a54ce116470a7a5534b2a28f07)
- CI: Utilize uv lockfile for reproducible test environments (#6640) [[04cc34488]](https://github.com/aiidateam/aiida-core/commit/04cc34488220de645289f23f126501f63beabbd8)
- CI: Test with RabbitMQ 4.0.x (#6649) [[a1872b1e7]](https://github.com/aiidateam/aiida-core/commit/a1872b1e7f99f8673211bde10cbbc68a1d697ad5)
- CI: quick fix on failed benchmark CI using uv run pytest (#6652) [[37e5431e6]](https://github.com/aiidateam/aiida-core/commit/37e5431e6802aae5de4a5079af2fcdc1b6a2ff66)
- Typing-extensions as dependency for py3.9 (#6664) [[c532b34a1]](https://github.com/aiidateam/aiida-core/commit/c532b34a199f86d2e117cfbfa47affd4afe9d28b)
- Update uv.lock + CI tweaks + fix pymatgen issue (#6676) [[10930266f]](https://github.com/aiidateam/aiida-core/commit/10930266fb6c644a7467a41268fe27f4bc40ea13)
- Devops: Update pre-commit dependencies (#6683) [[0eb77b8ae]](https://github.com/aiidateam/aiida-core/commit/0eb77b8ae5e54716d7c9f4d22aac880939285198)
- CI: Add matrix testing for both SQLite and PostgreSQL database backends [[a3ccec96d]](https://github.com/aiidateam/aiida-core/commit/a3ccec96d894ea7ce79dee4c14914ce4ebb869c6)
- Fix redundant "tests/" in test-install.yml (#6695) [[5e8bbe1ae]](https://github.com/aiidateam/aiida-core/commit/5e8bbe1ae08ad5b8ae3d25a70be0a059c9ce260f)
- CI: Drop workaround to pass pymatgen related failed tests (#6694) [[d17c2931a]](https://github.com/aiidateam/aiida-core/commit/d17c2931a96782ec89704d656dd41bcfd671410a)
- Devops: Add explicit `sphinx.configuration` key to RTD conf (#6700) [[8440416a5]](https://github.com/aiidateam/aiida-core/commit/8440416a58d901e0030c7088c41be8ed94922594)
- Use uv lockfile in readthedocs build (#6685) [[15b5caf23]](https://github.com/aiidateam/aiida-core/commit/15b5caf239cefce144386ec846edff0546b0637a)
- Run mypy on src/aiida/orm/nodes/caching.py (#6703) [[199a0276c]](https://github.com/aiidateam/aiida-core/commit/199a0276c4becfa23f64014b4f426a0c317068fe)
- CI: Set runners to ubuntu-24.04 (#6696) [[b43261143]](https://github.com/aiidateam/aiida-core/commit/b43261143a136a58afddcfa1438036c99b39f8b7)
- CI: fix failed test_containerized.py integration test for containerized code (#6707) [[738705611]](https://github.com/aiidateam/aiida-core/commit/738705611bf18cdd2bf337531268a8ec7465322a)
- Nightly tests adjust run test_memory_leak in test move high_link to nightly (#6701) [[b3569508c]](https://github.com/aiidateam/aiida-core/commit/b3569508c8edcc1aa2b1126481ab60d9133f0189)
- Set minimum uv version in pyproject.toml (#6714) [[c88fc05ba]](https://github.com/aiidateam/aiida-core/commit/c88fc05ba111f82e089553e5413b2c7c4d482f6f)
- Use uv-pre-commit to validate lockfile (#6699) [[208d6a967]](https://github.com/aiidateam/aiida-core/commit/208d6a967203dcaa4b685f336e413491cdceb7a2)
- Use Github arm runners for docker arm build tests (#6717) [[f43a51010]](https://github.com/aiidateam/aiida-core/commit/f43a51010b3c84b1e9526d167401fc9ac07c556a)
- CI: Ignore mamba Warning Message on stderr to Prevent JSON Parsing Errors (#6748) [[8c5c709be]](https://github.com/aiidateam/aiida-core/commit/8c5c709bece13c56af1d91384957e7ccb8dd320b)
- Fix docker arm build (#6759) [[c4dfadabf]](https://github.com/aiidateam/aiida-core/commit/c4dfadabfa3183118bbbc416307529f50ebc9fd0)
- `CI`: `RTD` tail errors and warnings (#6776) [[bb5f93daa]](https://github.com/aiidateam/aiida-core/commit/bb5f93daaf50ee48e18856000522c2da757b022e)
- Bump the gha-dependencies group with 2 updates (#6778) [[48bd2acbc]](https://github.com/aiidateam/aiida-core/commit/48bd2acbcd6f3dd1e6b4f7b46abea5451d6a96c9)
- Revert "Bump the gha-dependencies group with 2 updates (#6778)" (#6838) [[61be15d54]](https://github.com/aiidateam/aiida-core/commit/61be15d548eab6001a43127eb851aa766d514067)
- Add Python 3.13 to `tests` job in `test-install` workflow and for verdi and presto jobs in `ci-code` workflow (#6843) [[6cb2c712d]](https://github.com/aiidateam/aiida-core/commit/6cb2c712dcc62e6429f990b9e4f29d84036ca69e)
- Add back pre-commit job for mypy type-checking (#6827) [[6eb17a7d0]](https://github.com/aiidateam/aiida-core/commit/6eb17a7d0999adb2bf7ba2449b2667049996a65b)
- RTD: add a developer comment in `.readthedocs.yml` (#6864) [[5807a390927a5892cd349bf8e3f3da5ef233eca5]](https://github.com/aiidateam/aiida-core/commit/5807a390927a5892cd349bf8e3f3da5ef233eca5)
-  Devops: Skip upload step in benchmarks if not pushed to main (#6895) [[6b5578602b0f00b22ac457c070c764168ac8cbd4]](https://github.com/aiidateam/aiida-core/commit/6b5578602b0f00b22ac457c070c764168ac8cbd4)
- Devops: Upgrade `uv>=v0.7.6` and `astral-sh/setup-uv@v6` (#6887) [[5fbfe12f2a1805c0c69ee9c77f1a0d29106b1aad]](https://github.com/aiidateam/aiida-core/commit/5fbfe12f2a1805c0c69ee9c77f1a0d29106b1aad)
- Upgrade uv lockfile (#6886) [[edb8c7e88fde03510e05fb9cc48cc58aa7112dc5]](https://github.com/aiidateam/aiida-core/commit/edb8c7e88fde03510e05fb9cc48cc58aa7112dc5)


## v2.6.4 - 2025-05-22

### Fixes
- Dependencies: Pin click to `~=8.1.0` (#6888) [[e1d55fa]](https://github.com/aiidateam/aiida-core/commit/e1d55fa0d6c268db7a25e9740679a5a0fbe412b8)


## v2.6.3 - 2024-11-06

### Fixes
- CLI: Fix exception for `verdi plugin list` (#6560) [[c3b10b7]](https://github.com/aiidateam/aiida-core/commit/c3b10b759a9cd062800ef120591d5c7fd0ae4ee7)
- `DirectScheduler`: Ensure killing child processes (#6572) [[fddffca]](https://github.com/aiidateam/aiida-core/commit/fddffca67b4f7e3b76b19df7db8e1511c449d2d9)   
- Engine: Fix state change broadcast before process node is updated  (#6580) [[867353c]](https://github.com/aiidateam/aiida-core/commit/867353c415c61d94a2427d5225dd5224a1b95fb9)

### Devops
- Docker: Replace sleep with `s6-notifyoncheck` (#6475) [[9579378b]](https://github.com/aiidateam/aiida-core/commit/9579378ba063237baa5b73380eb8e9f0a28529ee)
- Fix failed docker CI using more reasoning grep regex to parse python version (#6581) [[332a4a91]](https://github.com/aiidateam/aiida-core/commit/332a4a915771afedcb144463b012558e4669e529)
- DevOps: Fix json query in reading the docker names to filter out fields not starting with aiida (#6573) [[e1467edc]](https://github.com/aiidateam/aiida-core/commit/e1467edca902867e53605e0e60b67f8767bf8d3e)


## v2.6.2 - 2024-08-07

### Fixes
- `LocalTransport`: Fix typo for `ignore_nonexisting` in `put` (#6471) [[ecda558d0]](https://github.com/aiidateam/aiida-core/commit/ecda558d08c5608880308f69a21c05fe918be89f)
- CLI: `verdi computer test` report correct failed tests (#6536) [[9c3f2bb58]](https://github.com/aiidateam/aiida-core/commit/9c3f2bb589f1a6cc920ed2fbf0627924d8fce954)
- CLI: Fix `verdi storage migrate` for profile without broker (#6550) [[389fc487d]](https://github.com/aiidateam/aiida-core/commit/389fc487d092c2e34713d228e38c8164608bab2d)
- CLI: Fix bug `verdi presto` when tab-completing without config (#6535) [[efcf75e40]](https://github.com/aiidateam/aiida-core/commit/efcf75e405dcef8ca8c51b19d6262ca81f4413c3)
- Engine: Change signature of `set_process_state_change_timestamp` [[923fd9f6e]](https://github.com/aiidateam/aiida-core/commit/923fd9f6ec3cb39b8985ac149985046e720438f8)
- Engine: Ensure node is sealed when process excepts (#6549) [[e3ed9a2f3]](https://github.com/aiidateam/aiida-core/commit/e3ed9a2f3bf84e72cdc4c90e21494dc2b9c1cd56)
- Engine: Fix bug in upload calculation for `PortableCode` with SSH (#6519) [[740ae2040]](https://github.com/aiidateam/aiida-core/commit/740ae20408e4e3047c26c91221de5b96b8d7afbe)
- Engine: Ignore failing process state change for `core.sqlite_dos` [[fb4f9815f]](https://github.com/aiidateam/aiida-core/commit/fb4f9815fbd3bfe053cc0d1e3abb5b86bbc9dffd)

### Dependencies
- Pin requirement to minor version `sphinx~=7.2.0` (#6527) [[25cb73188]](https://github.com/aiidateam/aiida-core/commit/25cb731880d45045773f7674fee9367d792aeda9)

### Documentation
- Add `PluggableSchemaValidator` to nitpick exceptions (#6515) [[0ce3c0025]](https://github.com/aiidateam/aiida-core/commit/0ce3c0025384e95006d43e98da2a96b2cfadde70)
- Add `robots.txt` to only allow indexing of `latest` and `stable` (#6517) [[a492e3492]](https://github.com/aiidateam/aiida-core/commit/a492e349288ee90896193575edf319c2b7ea4c85)
- Add succint overview of limitations of no-services profile [[d7ca5657b]](https://github.com/aiidateam/aiida-core/commit/d7ca5657b0dec83cb8a440d0b8e11c9c84e38149)
- Correct signature of `get_daemon_client` example snippet (#6554) [[92d391658]](https://github.com/aiidateam/aiida-core/commit/92d391658e5e92113ad9a32d61444e23342ee0ae)
- Fix typo in pytest plugins codeblock (#6513) [[eb23688fe]](https://github.com/aiidateam/aiida-core/commit/eb23688febacb5b828d0f45ebdeedee65d0c00fe)
- Move limitations warning to top of quick install [[493e529a7]](https://github.com/aiidateam/aiida-core/commit/493e529a7aec052f81d1bbfed33e5b44db9434e2)
- Remove note in installation guide regarding Python requirement [[9aa2044e4]](https://github.com/aiidateam/aiida-core/commit/9aa2044e4ce665d64bb3a1c26f166512287aa28b)
- Update `redirects.txt` for installation pages (#6509) [[508a9fb2a]](https://github.com/aiidateam/aiida-core/commit/508a9fb2a7f6eb6f31b40b3f28d13c96f7875503)

### Devops
- Fix pymatgen import causing mypy to fail (#6540) [[813374fe1]](https://github.com/aiidateam/aiida-core/commit/813374fe1ee003c8c05f9aa191147ec928dfa918)


## v2.6.1 - 2024-07-01

### Fixes
- Fixtures: Make `pgtest` truly an optional dependency [[9fe8fd2e0]](https://github.com/aiidateam/aiida-core/commit/9fe8fd2e0b88e746ee2156eccb71b7adbab6b2c5)


## v2.6.0 - 2024-07-01

This minor release comes with a number of features that are focused on user friendliness and ease-of-use of the CLI and the API.
The caching mechanism has received a number of improvements guaranteeing even greater savings of computational time.
For existing calculations to be valid cache sources in the new version, their hash has to be regenerated (see [Improvements and changes to caching](#improvements-and-changes-to-caching) for details).

- [Making RabbitMQ optional](#making-rabbitmq-optional)
- [Simplifying profile setup](#simplifying-profile-setup)
- [Improved test fixtures without services](#improved-test-fixtures-without-services)
- [Improvements and changes to caching](#improvements-and-changes-to-caching)
- [Programmatic syntax for query builder filters and projections](#programmatic-syntax-for-query-builder-filters-and-projections)
- [Automated profile storage backups](#automated-profile-storage-backups)
- [Full list of changes](#full-list-of-changes)
    - [Features](#features)
    - [Performance](#performance)
    - [Changes](#changes)
    - [Fixes](#fixes)
    - [Deprecations](#deprecations)
    - [Dependencies](#dependencies)
    - [Refactoring](#refactoring)
    - [Documentation](#documentation)
    - [Devops](#devops)


### Making RabbitMQ optional

The RabbitMQ message broker service is now optional for running AiiDA.
The requirement was added in AiiDA v1.0 when the engine was completely overhauled.
Although it significantly improved the scaling and responsiveness, it also made it more difficult to start using AiiDA.
As of v2.6, profiles can now be configured without RabbitMQ, at the cost that the daemon can not be used and all processes have to be run locally.

### Simplifying profile setup

With the removal of RabbitMQ as a hard requirement, combined with storage plugins that replace PostgreSQL with the serverless SQLite that were introduced in v2.5, it is now possible to setup a profile that requires no services.
A new command is introduced, `verdi presto`, that automatically creates a profile with sensible defaults.
This now in principle makes it possible to run just the two following commands on any operating system:
```
pip install aiida-core
verdi presto
```
and get a working AiiDA installation that is ready to go.
As a bonus, it also configures the localhost as a `Computer`.
See the [documentation for more details](https://aiida.readthedocs.io/projects/aiida-core/en/v2.6.0/installation/guide_quick.html).

### Improved test fixtures without services

Up till now, running tests would always require a fully functional profile, which meant that PostgreSQL and RabbitMQ had to be available.
As described in the section above, it is now possible to set up a profile without these services.
This new feature is leveraged to provide a set of `pytest` fixtures that provide a test profile that can be used essentially on any system that just has AiiDA installed.
To start writing tests, simply create a `conftest.py` and import the fixtures with:
```python
pytest_plugins = 'aiida.tools.pytest_fixtures'
```
The new fixtures include the `aiida_profile` fixture which is session-scoped and automatically loaded.
The fixture creates a temporary test profile at the start of the test session and automatically deletes it when the session ends.
For more information and an overview of all available fixtures, please refer to [the documentation on `pytest` fixtures](https://aiida.readthedocs.io/projects/aiida-core/en/v2.6.0/topics/plugins.html#plugin-test-fixtures).

### Improvements and changes to caching

A number of fixes and changes to the caching mechanism were introduced (see the [changes](#changes) subsection of the [full list of changes](#full-list-of-changes) for a more detailed overview).
For existing calculations to be valid cache sources in the new version, their hash has to be regenerated by running `verdi node rehash`.
Note that this can take a while for large databases.

Since its introduction, the cache would essentially be reset each time AiiDA or any of the plugin packages would be updated, since the version of these packages were included in the calculation of the node hashes.
This was originally done out of precaution to err on the safe-side and limit the possibility of false-positives in cache hits.
However, this strategy has turned out to be unnecessarily cautious and severely limited the effectiveness of caching.

The package version information is no longer included in the hash and therefore no longer impacts the caching.
This change does now make it possible for false positives if the implementation of a `CalcJob` or `Parser` plugin changes signficantly.
Therefore, a mechanism is introduced to give control to these plugins to effectively reset the cache of existing nodes.
Please refer to the [documentation on controlling caching](https://aiida.readthedocs.io/projects/aiida-core/en/v2.6.0/topics/provenance/caching.html#calculation-jobs-and-parsers) for more details.

### Programmatic syntax for query builder filters and projections

In the `QueryBuilder`, fields to filter on or project always had to be provided with strings:
```python
QueryBuilder().append(Node, filters={'label': 'some-label'}, project=['id', 'ctime'])
```
and it is not always trivial to know what fields exist that _can_ be filtered on and can be projected.
In addition, there was a discrepancy for some fields, most notably the `pk` property, which had to be converted to `id` in the query builder syntax.

These limitations have been solved as each class in AiiDA's ORM now defines the `fields` property, which allows to discover these fields programmatically.
The example above would convert to:
```python
QueryBuilder().append(Node, filters={Node.fields.label: 'some-label'}, project=[Node.fields.pk, Node.fields.ctime])
```
The `fields` property provides tab-completion allowing easy discovery of available fields for an ORM class in IDEs and interactive shells.
The fields also allow to express logical conditions programmatically and more.
For more details, please refer to the [documentation on programmatic field syntax](https://aiida.readthedocs.io/projects/aiida-core/en/v2.6.0/howto/query.html#programmatic-syntax-for-filters).

Data plugins can also define custom fields, adding on top of the fields inherited from their base class(es).
The [documentation on data plugin fields](https://aiida.readthedocs.io/projects/aiida-core/en/v2.6.0/topics/data_types.html#fields) provides more information, but the API is currently in beta and guaranteed to be changed in an upcoming version.
It is therefore recommended for plugin developers to hold off making use of this new API.

### Automated profile storage backups

A generic mechanism has been implemented to allow easily backing up the data of a profile.
The command `verdi storage backup` automatically maintains a directory structure of previous backups allowing efficient incremental backups.
Note that the exact details of the backup mechanism is dependent on the storage plugin that is used by the profile and not all storage plugins necessarily implement it.
For now the storage plugins `core.psql_dos`, and `core.sqlite_dos` implement the functionality.
For more information, please refer [to the documentation](https://aiida.readthedocs.io/projects/aiida-core/en/v2.6.0/howto/installation.html#backing-up-your-installation).
Please refer to [this section of the documentation](https://aiida.readthedocs.io/projects/aiida-core/en/v2.6.0/howto/installation.html#restoring-data-from-a-backup) for instructions to restore from a backup.

### Full list of changes

#### Features
- `CalcJob`: Allow to define order of copying of input files [[6898ff4d8]](https://github.com/aiidateam/aiida-core/commit/6898ff4d8c263cf08707c61411a005f6a7f731dd)
- `SqliteDosStorage`: Implement the backup functionality [[18e447c77]](https://github.com/aiidateam/aiida-core/commit/18e447c77f48a18f361e458186cd87b2355aea75)
- `SshTransport`: Return `FileNotFoundError` if destination parent does not exist [[d86bb38bf]](https://github.com/aiidateam/aiida-core/commit/d86bb38bf9a0ced8029f8a4b895e1a6be1ccb339)
- Add improved more configurable versions of `pytest` fixtures [[e3a60460e]](https://github.com/aiidateam/aiida-core/commit/e3a60460ef1208a5c46ecd6af35d891a88ee784e)
- Add the `orm.Entity.fields` interface for `QueryBuilder` [[4b9abe2bd]](https://github.com/aiidateam/aiida-core/commit/4b9abe2bd0bb82449547a3377c2b6dbc7c174123)
- CLI: `verdi computer test` make unexpected output check optional [[589a3b2c0]](https://github.com/aiidateam/aiida-core/commit/589a3b2c03d44cebd26e88243ca34fcdb0e23ff4)
- CLI: `verdi node graph generate` root nodes as arguments [[06f8f4cfb]](https://github.com/aiidateam/aiida-core/commit/06f8f4cfb0731ff699d5c01ad85418b6db0f6778)
- CLI: Add `--most-recent-node` option to `verdi process watch` [[72692fa5c]](https://github.com/aiidateam/aiida-core/commit/72692fa5cb667e2a7462770af18b7cedeaf8b3f0)
- CLI: Add `--sort/--no-sort` to `verdi code export` [[80c606890]](https://github.com/aiidateam/aiida-core/commit/80c60689063f1517c3de91d86eef80f7852667e3)
- CLI: Add `verdi process dump` and the `ProcessDumper` [[6291accf0]](https://github.com/aiidateam/aiida-core/commit/6291accf0538eafe7426e89bc4c1e9eb90ce0385)
- CLI: Add RabbitMQ options to `verdi profile setup` [[f553f805e]](https://github.com/aiidateam/aiida-core/commit/f553f805e86d766da6208eb1682f7cf12c7907ac)
- CLI: Add the `-M/--most-recent-node` option [[5aae874aa]](https://github.com/aiidateam/aiida-core/commit/5aae874aaa44459ce8cf3ddd3bf1a82d8a2e8d37)
- CLI: Add the `verdi computer export` command [[9e3ebf6ea]](https://github.com/aiidateam/aiida-core/commit/9e3ebf6ea55d883c7857a1dbafe398b9579cca03)
- CLI: Add the `verdi node list` command [[cf091e80f]](https://github.com/aiidateam/aiida-core/commit/cf091e80ff2b6aa03f41b56ba1976abb97298972)
- CLI: Add the `verdi presto` command [[6b6e1520f]](https://github.com/aiidateam/aiida-core/commit/6b6e1520f2d3807e366dd672e7917f381ea7b524)
- CLI: Add the `verdi profile configure-rabbitmq` command [[202a3ece9]](https://github.com/aiidateam/aiida-core/commit/202a3ece9705289a1f12c85e64cf90307ca85c39)
- CLI: Allow `verdi computer delete` to delete associated nodes  [[348777571]](https://github.com/aiidateam/aiida-core/commit/3487775711e7412fb2cb82600fb266316d6ce12a)
- CLI: Allow multiple root nodes in `verdi node graph generate` [[f16c432af]](https://github.com/aiidateam/aiida-core/commit/f16c432af107b1f9c01a12e03cbd0a9ecc2744ad)
- Engine: Allow `CalcJob` monitors to return outputs [[b7e59a0db]](https://github.com/aiidateam/aiida-core/commit/b7e59a0dbc0dd629be5c8178e98c70e7a2c116e9)
- Make `postgres_cluster` and `config_psql_dos` fixtures configurable [[35d7ca63b]](https://github.com/aiidateam/aiida-core/commit/35d7ca63b44f051a26d3f96d84e043919eb3f101)
- Process: Add the `metadata.disable_cache` input [[4626b11f8]](https://github.com/aiidateam/aiida-core/commit/4626b11f85cd0d95a17d8f5766a90b88ddddd689)
- Storage: Add backup mechanism to the interface [[bf79f23ee]](https://github.com/aiidateam/aiida-core/commit/bf79f23eef66d362a34aac170577ba8f5c2088ba)
- Transports: fix overwrite behaviour for `puttree`/`gettree` [[a55451703]](https://github.com/aiidateam/aiida-core/commit/a55451703aa8f8d330b25bc5da95d41caf0db9ac)

#### Performance
- CLI: Speed up tab-completion by lazily importing `Config` [[9524cda0b]](https://github.com/aiidateam/aiida-core/commit/9524cda0b8c742fb5bf740d7b0035e326eace28f)
- Improve import time of `aiida.orm` and `aiida.storage` [[fb9b6cc3b]](https://github.com/aiidateam/aiida-core/commit/fb9b6cc3b3df244549fdd78576c34f6d9dfd4568)
- ORM: Cache the logger adapter for `ProcessNode` [[1d104d06b]](https://github.com/aiidateam/aiida-core/commit/1d104d06b95da36c71cab132c7b6fec52a005e18)

#### Changes
- Caching: `NodeCaching._get_objects_to_hash` return type to `dict` [[c9c7c4bd8]](https://github.com/aiidateam/aiida-core/commit/c9c7c4bd8e1cd306271b5cf267095d3cbd8aafe2)
- Caching: Add `CACHE_VERSION` attribute to `CalcJob` and `Parser` [[39d0f312d]](https://github.com/aiidateam/aiida-core/commit/39d0f312d212a642d1537ca89e7622e48a23e701)
- Caching: Include the node's class in objects to hash [[68ce11161]](https://github.com/aiidateam/aiida-core/commit/68ce111610c40e3d9146e128c0a698fc60b6e5e5)
- Caching: Make `NodeCaching._get_object_to_hash` public [[e33000402]](https://github.com/aiidateam/aiida-core/commit/e330004024ad5121f9bc82cbe972cd283f25fec8)
- Caching: Remove core and plugin information from hash calculation [[4c60bbef8]](https://github.com/aiidateam/aiida-core/commit/4c60bbef852eef55a06b48b813d3fbcc8fb5a43f)
- Caching: Rename `get_hash` to `compute_hash` [[b544f7cf9]](https://github.com/aiidateam/aiida-core/commit/b544f7cf95a0e6e698224f36c1bea57d1cd99e7d)
- CLI: Always do hard reset in `verdi daemon restart` [[8ac642410]](https://github.com/aiidateam/aiida-core/commit/8ac6424108d1528bd3279c81da62dd44855b6ebc)
- CLI: Change `--profile` to `-p/--profile-name` for `verdi profile setup` [[8ea203cd9]](https://github.com/aiidateam/aiida-core/commit/8ea203cd9b1d2fbb4a3b38ba67beec97bb8c7145)
- CLI: Let `-v/--verbosity` only affect `aiida` and `verdi` loggers [[487c6bf04]](https://github.com/aiidateam/aiida-core/commit/487c6bf047030ee19deed49d5fbf9a093253538e)
- Engine: Set the `to_aiida_type` as default inport port serializer [[2fa7a5305]](https://github.com/aiidateam/aiida-core/commit/2fa7a530511a94ead83d79669efed71706a0a472)
- `QueryBuilder`: Remove implementation for `has_key` in SQLite storage [[24cfbe27e]](https://github.com/aiidateam/aiida-core/commit/24cfbe27e7408b78fca8e6f69799ebad3659400b)

#### Fixes
- `BandsData`: Use f-strings in `_prepare_gnuplot` [[dba117437]](https://github.com/aiidateam/aiida-core/commit/dba117437782abc6d11f9ef208923f7e70f79ed2)
- `BaseRestartWorkChain`: Fix handler overrides used only first iteration [[65786a6bd]](https://github.com/aiidateam/aiida-core/commit/65786a6bda1c74dfb4aea90becd0664de6b1abde)
- `SlurmScheduler`: Make detailed job info fields dynamic [[4f9774a68]](https://github.com/aiidateam/aiida-core/commit/4f9774a689b81a446fac37ad8281b2d854eefa7a)
- `SqliteDosStorage`: Fix exception when importing archive [[af0c260bb]](https://github.com/aiidateam/aiida-core/commit/af0c260bb1c32c3b33c50175d790907774561b3e)
- `StructureData`: Fix the pbc constraints of `get_pymatgen_structure` [[adcce4bcd]](https://github.com/aiidateam/aiida-core/commit/adcce4bcd0b59c8371be73058a060bedcaba40f6)
- Archive: Automatically create nested output directories [[212f6163b]](https://github.com/aiidateam/aiida-core/commit/212f6163b03b8762509ae2230c30172af8c02fed)
- Archive: Respect `filter_size` in query for existing nodes [[ef60b66aa]](https://github.com/aiidateam/aiida-core/commit/ef60b66aa3ce76d654abe5e7caafef3f221defd0)
- CLI: Ensure deprecation warnings are printed before any prompts [[deb293d0e]](https://github.com/aiidateam/aiida-core/commit/deb293d0e6a566256fac5069881de4846d77f6d1)
- CLI: Fix `verdi archive create --dry-run` for empty file repository [[cc96c9d04]](https://github.com/aiidateam/aiida-core/commit/cc96c9d043c6616a068a5498f557fa21a728eb96)
- CLI: Fix `verdi plugin list` incorrectly not displaying description [[e952d7717]](https://github.com/aiidateam/aiida-core/commit/e952d7717c1d8001555e8d19f54f4fa349da6c6e)
- CLI: Fix `verdi process [show|report|status|watch|call-root]` no output [[a56a1389d]](https://github.com/aiidateam/aiida-core/commit/a56a1389dee5cb9ae70a5511d77aad248ea21731)
- CLI: Fix `verdi process list` if no available workers [[b44afcb3c]](https://github.com/aiidateam/aiida-core/commit/b44afcb3c1a7efa452d4e72aa6f8a615f652aaa4)
- CLI: Fix `verdi quicksetup` when profiles exist where storage is not `core.psql_dos` [[6cb91c181]](https://github.com/aiidateam/aiida-core/commit/6cb91c18163ac6228ed4a64c1c467dfd0398a624)
- CLI: Fix dry-run resulting in critical error in `verdi archive import` [[36991c6c8]](https://github.com/aiidateam/aiida-core/commit/36991c6c84f4ba0b4553e8cd6689bbc1815dbd35)
- CLI: Fix logging not showing in `verdi daemon worker` [[9bd8585bd]](https://github.com/aiidateam/aiida-core/commit/9bd8585bd5e7989e24646a0018710e86836e5a9f)
- CLI: Fix the `ctx.obj.profile` attribute not being initialized [[8a286f26e]](https://github.com/aiidateam/aiida-core/commit/8a286f26e8d303c498ac2eabd49be5f1f4ced9ef)
- CLI: Hide misleading message for `verdi archive create --test-run` [[7e42d7aa7]](https://github.com/aiidateam/aiida-core/commit/7e42d7aa7d16fa9e81cbd300ada14e4dea2426ce)
- CLI: Improve error message of `PathOrUrl` and `FileOrUrl` [[ffc6e4f70]](https://github.com/aiidateam/aiida-core/commit/ffc6e4f706277854dbd454d6f3164cec31e7819a)
- CLI: Only configure logging in `set_log_level` callback once [[66a2dcedd]](https://github.com/aiidateam/aiida-core/commit/66a2dcedd0a9428b5b2218b8c82bad9c9aff4956)
- CLI: Unify help of `verdi process` commands [[d91e0a58d]](https://github.com/aiidateam/aiida-core/commit/d91e0a58dabfd242b5f886d692c8761499a6719c)
- Config: Set existing user as default for read-only storages [[e66592509]](https://github.com/aiidateam/aiida-core/commit/e665925097bb3344fde4bcc66ee185a2d9207ac3)
- Config: Use UUID in `Manager.load_profile` to identify profile [[b01038bf1]](https://github.com/aiidateam/aiida-core/commit/b01038bf1fca7d33c4915aee904acea89a847614)
- Daemon: Log the worker's path and Python interpreter [[ae2094169]](https://github.com/aiidateam/aiida-core/commit/ae209416996ec361c474aeaf0fa06f49dd59f296)
- Docker: Start and stop daemon only when a profile exists [[0a5b20023]](https://github.com/aiidateam/aiida-core/commit/0a5b200236419d8caf8e05bb04ba80d03a438e03)
- Engine: Add positional inputs for `Process.submit` [[d1131fe94]](https://github.com/aiidateam/aiida-core/commit/d1131fe9450972080207db6e9615784490b3252b)
- Engine: Catch `NotImplementedError`in `get_process_state_change_timestamp` [[04926fe20]](https://github.com/aiidateam/aiida-core/commit/04926fe20da15065f8f086f1ff3cb14cc163aa08)
- Engine: Fix paused work chains not showing it in process status [[40b22d593]](https://github.com/aiidateam/aiida-core/commit/40b22d593875b97355996bbfc15e2850ad1f0495)
- Fix passwords containing `@` not being accepted for Postgres databases [[d14c14db2]](https://github.com/aiidateam/aiida-core/commit/d14c14db2f82d3a678e9747bd463ec1a61642120)
- ORM: Correct field type of `InstalledCode` and `PortableCode` models [[0079cc1e4]](https://github.com/aiidateam/aiida-core/commit/0079cc1e4b46c61edf2323b2d42af46367fe04b6)
- ORM: Fix `ProcessNode.get_builder_restart` [[0dee9d8ef]](https://github.com/aiidateam/aiida-core/commit/0dee9d8efba5c48615e8510f5ada706724b4a2e8)
- ORM: Fix deprecation warning being shown for new code types [[a9155713b]](https://github.com/aiidateam/aiida-core/commit/a9155713bbb10e57fe91cd320e2a12391d098a46)
- Runner: Close event loop in `Runner.close()` [[53cc45837]](https://github.com/aiidateam/aiida-core/commit/53cc458377685e54179eb1e1b73bb0383c8dae13)

#### Deprecations
- CLI: Deprecate `verdi profile setdefault` and rename to `verdi profile set-default` [[ab48a4f62]](https://github.com/aiidateam/aiida-core/commit/ab48a4f627b4c9eec9133b5efa9fb888ce2c4914)
- CLI: Deprecate accepting `0` for `default_mpiprocs_per_machine` [[acec0c190]](https://github.com/aiidateam/aiida-core/commit/acec0c190cbb45ba267c6eb8ee7ceba18cf3302b)
- CLI: Deprecate the `deprecated_command` decorator [[4c11c0616]](https://github.com/aiidateam/aiida-core/commit/4c11c0616c583236119f838a1780a606c58b4ee2)
- CLI: Remove the deprecated `verdi database` command [[3dbde9e31]](https://github.com/aiidateam/aiida-core/commit/3dbde9e311781509b738202ad6f1de3bbd4b7a82)
- ORM: Undo deprecation of `Code.get_description` [[1b13014b1]](https://github.com/aiidateam/aiida-core/commit/1b13014b14274024dcb6bb0a721eb62665567987)

### Dependencies
- Update `tabulate>=0.8.0,<0.10.0` [[6db2f4060]](https://github.com/aiidateam/aiida-core/commit/6db2f4060d4ece4552f5fe757c0f7d938810f4d1)

#### Refactoring
- Abstract message broker functionality [[69389e038]](https://github.com/aiidateam/aiida-core/commit/69389e0387369d8437e1219487b88430b7b2e679)
- Config: Refactor `get_configuration_directory_from_envvar` [[65739f524]](https://github.com/aiidateam/aiida-core/commit/65739f52446087439ba93158eb948b58ed081ce5)
- Config: Refactor the `create_profile` function and method [[905e93444]](https://github.com/aiidateam/aiida-core/commit/905e93444cf996461e679cd458511d1c471a7e02)
- Engine: Refactor handling of `remote_folder` and `retrieved` outputs [[28adacaf8]](https://github.com/aiidateam/aiida-core/commit/28adacaf8ae21357bf6e5a2a48c43ed56d3bd78b)
- ORM: Switch to `pydantic` for code schema definition [[06189d528]](https://github.com/aiidateam/aiida-core/commit/06189d528c2362516f42e0d48840882812b97fe4)
- Replace deprecated `IOError` with `OSError` [[7f9129fd1]](https://github.com/aiidateam/aiida-core/commit/7f9129fd193374bdbeaa7ba4dd8c3cdf706db97d)
- Storage: Move profile locking to the abstract base class [[ea5f51bcb]](https://github.com/aiidateam/aiida-core/commit/ea5f51bcb6af172eb1a754df3981003bf7bad959)

#### Documentation
- Add more instructions on how to use docker image [[aaf44afcc]](https://github.com/aiidateam/aiida-core/commit/aaf44afcce0f90fff2eb38bc47d28b4adf87db24)
- Add the updated cheat sheet [[09f9058a7]](https://github.com/aiidateam/aiida-core/commit/09f9058a7444f3ac1d3f243b608fa3f24f771f27)
- Add tips for common problems with conda PostgreSQL setup [[cd5313825]](https://github.com/aiidateam/aiida-core/commit/cd5313825afdb1771ca19d899567e4ed4774a2bc)
- Customize the color scheme through custom style sheet [[a6cf7fc7e]](https://github.com/aiidateam/aiida-core/commit/a6cf7fc7e02a48a7e3b9c4ba6ce5e2cd413e6b23)
- Docs: Clarify `Transport.copy` requires `recursive=True` if source is a directory [[310ff1db7]](https://github.com/aiidateam/aiida-core/commit/310ff1db77bc75b6cadedf77394b96af05456f43)
- Fix example of the `entry_points` fixture [[081fc5547]](https://github.com/aiidateam/aiida-core/commit/081fc5547370e1b5a19b1fb507681091c632bb7a)
- Fixing several small issues [[6a3a59b29]](https://github.com/aiidateam/aiida-core/commit/6a3a59b29ba64401828d9ab51dc123060868278b)
- Minor cheatsheet update for v2.6 release [[c3cc169c4]](https://github.com/aiidateam/aiida-core/commit/c3cc169c487a88e2357b7377e897f0521c23f05a)
- Reorganize the tutorial content [[5bd960efa]](https://github.com/aiidateam/aiida-core/commit/5bd960efae5a7f916b978a420f5f43501c9bc529)
- Rework the installation section [[0ee0a0c6a]](https://github.com/aiidateam/aiida-core/commit/0ee0a0c6ae13588e82edf1cf9e8cb9857c94c31b)
- Standardize usage of `versionadded` directive [[bf5dac848]](https://github.com/aiidateam/aiida-core/commit/bf5dac8484638d7ba5c492e91975b5fcc0cc9770)
- Update twitter logo [[5e4f60d83]](https://github.com/aiidateam/aiida-core/commit/5e4f60d83160774ca83defe4bf1f6c6381aaa1a0)
- Use uv installer in readthedocs build [[be0db3cc4]](https://github.com/aiidateam/aiida-core/commit/be0db3cc49506294ae1845b6e746e40cd76f39a9)

#### Devops
- Add `check-jsonschema` pre-commit hook for GHA workflows [[14c5bb0f7]](https://github.com/aiidateam/aiida-core/commit/14c5bb0f764f0fd7933df205aa22d61c85ec0cf2)
- Add Dependabot config for maintaining GH actions [[0812f4b9e]](https://github.com/aiidateam/aiida-core/commit/0812f4b9eeffdff5a8c3d0802aea94c8919d9922)
- Add docker image `aiida-core-dev` for development [[6d0984109]](https://github.com/aiidateam/aiida-core/commit/6d0984109478ec1c0fd96dfd1d3f2b54e0b75dd2)
- Add Python 3.12 tox environment [[6b0d43960]](https://github.com/aiidateam/aiida-core/commit/6b0d4396068a43b6823eca8c78b9048044b0b4b8)
- Add the `slurm` service to nightly workflow [[5460a0414]](https://github.com/aiidateam/aiida-core/commit/5460a0414d55e3531eb86e6906ee963a6b712aae)
- Add typing to `aiida.common.hashing` [[ba21ba1d4]](https://github.com/aiidateam/aiida-core/commit/ba21ba1d40a76df73a2e27ce6f1a4f68aba7fb9a)
- Add workflow to build Docker images on PRs from forks [[23d2aa5ee]](https://github.com/aiidateam/aiida-core/commit/23d2aa5ee3c08438cfc4b4734e9670e19c090150)
- Address internal deprecation warnings [[ceed7d55d]](https://github.com/aiidateam/aiida-core/commit/ceed7d55dfb7df8dbe52c4557d145593d83f788a)
- Allow unit test suite to be ran against SQLite [[0dc8bbcb2]](https://github.com/aiidateam/aiida-core/commit/0dc8bbcb261b745683bc542c1aced2412ebd66a0)
- Bump the gha-dependencies group with 4 updates [[ccb56286c]](https://github.com/aiidateam/aiida-core/commit/ccb56286c40f6be0d61a0c62442993e43faf1ba6)
- Dependencies: Update the requirements files [[61ae1a55b]](https://github.com/aiidateam/aiida-core/commit/61ae1a55b94c50979b4e47bb7572e1d4c9b2391f)
- Disable code coverage in `test-install.yml` [[4cecda517]](https://github.com/aiidateam/aiida-core/commit/4cecda5177c456cee252c16295416c3842bb5d2d)
- Do not pin the mamba version [[82bba1307]](https://github.com/aiidateam/aiida-core/commit/82bba130792f6c965f0ede8b221eee70fd01d9f1)
- Fix Docker build not defining `REGISTRY` [[e7953fd4d]](https://github.com/aiidateam/aiida-core/commit/e7953fd4dd14875e380b125b99f86c12ce15359b)
- Fix publishing to DockerHub using incorrect secret name [[9c9ff7986]](https://github.com/aiidateam/aiida-core/commit/9c9ff79865225b125ba5f9fe23969d4c2c8fb9b2)
- Fix Slack notification for nightly tests [[082589f45]](https://github.com/aiidateam/aiida-core/commit/082589f456201fbd79d3df809e2cfc5fb5f27922)
- Fix the `test-install.yml` workflow [[22ea06362]](https://github.com/aiidateam/aiida-core/commit/22ea06362e9de5d314f103332da2e25ae6080f61)
- Fix the Docker builds [[3404c0192]](https://github.com/aiidateam/aiida-core/commit/3404c01925da941c08f246e231b6587f53ce445b)
- Increase timeout for the `test-install` workflow [[e36a3f11f]](https://github.com/aiidateam/aiida-core/commit/e36a3f11fdd165eea3af9f3337382e1bbd181390)
- Move RabbitMQ CI to nightly and update versions [[b47a56698]](https://github.com/aiidateam/aiida-core/commit/b47a56698e8fdf350a10c7abfd8ba00443fabd8d)
- Refactor the GHA Docker build [[e47932ee9]](https://github.com/aiidateam/aiida-core/commit/e47932ee9e0833dca546c7c7b5b584f2687d9073)
- Remove `verdi tui` from CLI reference documentation [[1b4a19a44]](https://github.com/aiidateam/aiida-core/commit/1b4a19a44461271aea58e54acd93e896220b413d)
- Run Docker workflow only for pushes to origin [[b1a714155]](https://github.com/aiidateam/aiida-core/commit/b1a714155ec9e51263e453a4354934fa91d04f33)
- Tests: Convert hierarchy functions into fixtures [[a02abc470]](https://github.com/aiidateam/aiida-core/commit/a02abc4701e81b75284164510be966ff0fd04dab)
- Tests: extend `node_and_calc_info` fixture to `core.ssh` [[9cf28f208]](https://github.com/aiidateam/aiida-core/commit/9cf28f20875fe6c3b0f2844bff16415b1dfc7b6f)
- Tests: Remove test classes for transport plugins [[b77e51f8c]](https://github.com/aiidateam/aiida-core/commit/b77e51f8c15c7ddea80d7d6328737abb705c6ce8)
- Tests: Unskip test in `tests/cmdline/commands/test_archive_import.py` [[7b7958c7a]](https://github.com/aiidateam/aiida-core/commit/7b7958c7aee150162cb4db0562a7352764a94c04)
- Update codecov action [[fc2a84d9b]](https://github.com/aiidateam/aiida-core/commit/fc2a84d9bd045d48d46511153dfde389070bf552)
- Update deprecated `whitelist_externals` option in tox config [[8feef5189]](https://github.com/aiidateam/aiida-core/commit/8feef5189ab9a2ba4b358bb6937d5d7c3f555ad8)
- Update pre-commit hooks [[3dda84ff3]](https://github.com/aiidateam/aiida-core/commit/3dda84ff3057a97e422b809a6adc778cbf60c125)
- Update pre-commit requirement `ruff==0.3.5` [[acd54543d]](https://github.com/aiidateam/aiida-core/commit/acd54543dffca05df7189f36c71afd2bb0065f34)
- Update requirements `mypy` and `pre-commit`[[04b3260a0]](https://github.com/aiidateam/aiida-core/commit/04b3260a098f061301edb0f56f1675fe9283b41b)
- Update requirements to address deprecation warnings [[566f681f7]](https://github.com/aiidateam/aiida-core/commit/566f681f72426a9a08200ff1d86c604f4c37bbcf)
- Use `uv` to install package in CI and CD [[73a734ae3]](https://github.com/aiidateam/aiida-core/commit/73a734ae3cd0977a97c631f97ddb781fa293864a)
- Use recursive dependencies for `pre-commit` extra [[6564e78dd]](https://github.com/aiidateam/aiida-core/commit/6564e78ddb349b89f6a3e9bfa81ce357ce865961)


## v2.5.1 - 2024-01-31

This is a patch release with a few bug fixes, but mostly devops changes related to the package structure.

### Fixes
- CLI: Fix `verdi process repair` not actually repairing [[784ad6488]](https://github.com/aiidateam/aiida-core/commit/784ad64885e23c8c93fb21554dc3c7d1f6bdde0f)
- Docker: Allow default profile parameters to be configured through env variables [[06ea130df]](https://github.com/aiidateam/aiida-core/commit/06ea130df8854f621e25853af6ac723c37397ed0)

### Dependencies
- Dependencies: Fix incompatibility with `spglib>=2.3` [[fa8b9275e]](https://github.com/aiidateam/aiida-core/commit/fa8b9275e74d16df7df4884b7c2eff4ad0cca1ce)

### Devops
- Devops: Move the source directory into `src/` [[53748d4de]](https://github.com/aiidateam/aiida-core/commit/53748d4de609c79b37cf9c7e0170c913e8d6dd0d)
- Devops: Remove post release action for uploading pot to transifex [[9feda35eb]](https://github.com/aiidateam/aiida-core/commit/9feda35ebac0101c7fa16629cefcd411ed994425)
- Pre-commit: Add `ruff` as the new linter and formatter [[64c5e6a82]](https://github.com/aiidateam/aiida-core/commit/64c5e6a82d8bb515d07fea84b611dc35cce1263b)
- Pre-commit: Update a number of pre-commit hooks [[a4ced7a67]](https://github.com/aiidateam/aiida-core/commit/a4ced7a67e10e0e88a2fe09a4f5c5c597789d43a)
- Pre-commit: Add YAML and TOML formatters [[c27aa33f3]](https://github.com/aiidateam/aiida-core/commit/c27aa33f33a7417da5d0b571b1927668f6505707)
- Update pre-commit CI configuration [[cb95f0c4c]](https://github.com/aiidateam/aiida-core/commit/cb95f0c4cb5ac0f56b0a3ec6654409cb6f22b5ba)
- Update pre-commit dependencies [[8dfab0e09]](https://github.com/aiidateam/aiida-core/commit/8dfab0e0928da5b8bbe5182e97825a701ca0130b)
- Dependencies: Pin `mypy` to minor version `mypy~=1.7.1` [[d65fa3d2d]](https://github.com/aiidateam/aiida-core/commit/d65fa3d2d724b126c26631771fa7840a2583d1a4)

### Documentation
- Streamline and fix typos in `docs/topics/processes/usage.rst` [[45ba27732]](https://github.com/aiidateam/aiida-core/commit/45ba27732bb8ff8d6714c6a6114bc2c00d14c18c)
- Update process function section on file deduplication [[f35d7ae98]](https://github.com/aiidateam/aiida-core/commit/f35d7ae9801423c55e04fca22500ca23bca90739)
- Correct a typo in `docs/source/topics/data_types.rst` [[6ee278ceb]](https://github.com/aiidateam/aiida-core/commit/6ee278cebe8fb58cd6e69517d678b97570d0d661)
- Fix the ADES paper citation [[80117f8f7]](https://github.com/aiidateam/aiida-core/commit/80117f8f7b36a0932bb8a2ec843d37f28bd41f87)


## v2.5.0 - 2023-12-20

This minor release comes with a number of features that are focused on user friendliness of the CLI and the API.
It also reduces the import time of modules, which makes the CLI faster to load and so tab-completion should be snappier.
The release adds support for Python 3.12 and a great number of bugs are fixed.

- [Create profiles without a database server](#create-profiles-without-a-database-server)
- [Changes in process launch functions](#changes-in-process-launch-functions)
- [Improvements for built-in data types](#improvements-for-built-in-data-types)
- [Repository interface improvements](#repository-interface-improvements)
- [Full list of changes](#full-list-of-changes)
    - [Features](#features)
    - [Performance](#performance)
    - [Changes](#changes)
    - [Fixes](#fixes)
    - [Deprecations](#deprecations)
    - [Documentation](#documentation)
    - [Dependencies](#dependencies)
    - [Devops](#devops)


### Create profiles without a database server

A new storage backend plugin has been added that uses [`SQLite`](https://www.sqlite.org/index.html) instead of PostgreSQL.
This makes it a lot easier to setup across all platforms.
A new profile using this storage backend can be created in a single command:
```shell
verdi profile setup core.sqlite_dos -n --profile <PROFILE_NAME> --email <EMAIL>
```
Although easier to setup compared to the default storage backend that uses PostgreSQL, it is less performant.
This makes this storage ideally suited for use-cases that want to test or demonstrate AiiDA, or to just play around a bit.
The storage is compatible with most of AiiDA's functionality, except for automated database migrations and some very specific `QueryBuilder` functionality.
Therefore, for production databases, the default `core.psql_dos` storage entry point remains the recommended storage.

It is now also possible to create a profile using an export archive:
```shell
verdi profile setup core.sqlite_dos -n --profile <PROFILE_NAME> --filepath <ARCHIVE>
```
where `<ARCHIVE>` should point to an export archive on disk.
You can now use this profile like any other profile to inspect the data of the export archive.
Note that this profile is read-only, so you will not be able to use it to mutate existing data or add new data to the profile.
See the [documentation for more details and a more in-depth example](https://aiida.readthedocs.io/projects/aiida-core/en/v2.5.0/howto/archive_profile.html).

Finally, the original storage plugin `core.psql_dos`, which uses PostgreSQL for the database is also accessible through `verdi profile setup core.psql_dos`.
Essentially this is the same as the `verdi setup` command, which is kept for now for backwards compatibility.

See the [documentation on storage plugins](https://aiida.readthedocs.io/projects/aiida-core/en/v2.5.0/topics/storage.html) for more details on the differences between these storage plugins and when to use which.

The `verdi profile delete` command can now also be used to delete a profile for any of these storage plugins.
You will be prompted whether you also want to delete all the data, or you can specify this with the `--delete-data` or `--keep-data` flags.

### Changes in process launch functions

The `aiida.engine.submit` method now accepts the argument `wait`.
When set to `True`, instead of returning the process node straight away, the function will wait for the process to terminate before returning.
By default it is set to `False` so the current behavior remains unchanged.
```python
from aiida.engine import submit
node = submit(Process, wait=True)  # This call will block until process is terminated
assert node.is_terminated
```

This new feature is mostly useful for interactive demos and tutorials in notebooks.
In these situations, it might be beneficial to use `aiida.engine.run` because the cell will be blocking until it is finished, indicating to the user that something is processing.
When using `submit`, the cell returns immediately, but the results are not ready yet and typically the next cell cannot yet be executed.
Instead, the demo should redirect the user to using something like `verdi process list` to query the status of the process.

However, using `run` has downsides as well, most notably that the process will be lost if the notebook gets disconnected.
For processes that are expected to run longer, this can be really problematic, and so `submit` will have to be used regardless.
With the new `wait` argument, `submit` provides the best of both worlds.

Although very useful, the introduction of this feature does break any processes that define `wait` or `wait_interval` as an input.
Since the inputs to a process are defined as keyword arguments, these inputs would overlap with the arguments to the `submit` method.
To solve this problem, inputs can now _also_ be passed as a dictionary, e.g., where one would do before:
```python
submit(SomeProcess, x=Int(1), y=Int(2), code=load_code('some-code'))
# or alternatively
inputs = {
    'x': Int(1),
    'y': Int(2),
    'code': load_code('some-code'),
}
submit(SomeProcess, **inputs)
```
The new syntax allows the following:
```python
inputs = {
    'x': Int(1),
    'y': Int(2),
    'code': load_code('some-code'),
}
submit(SomeProcess, inputs)
```
Passing inputs as keyword arguments is still supported because sometimes that notation is still more legible than defining an intermediate dictionary.
However, if both an input dictionary and keyword arguments are define, an exception is raised.

### Improvements for built-in data types

The `XyData` and `ArrayData` data plugins now allow to directly pass the content in the constructor.
This allows defining the complete node in a single line
```python
import numpy as np
from aiida.orm import ArrayData, XyData

xy = XyData(np.array([1, 2]), np.array([3, 4]), x_name='x', x_units='E', y_names='y', y_units='F')
assert all(xy.get_x()[1] == np.array([1, 2]))

array = ArrayData({'a': np.array([1, 2]), 'b': np.array([3, 4])})
assert all(array.get_array('a') == np.array([1, 2]))
```
It is now also no longer required to specify the name in `ArrayData.get_array` as long as the node contains just a single array:
```python
import numpy as np
from aiida.orm import ArrayData

array = ArrayData(np.array([1, 2]))
assert all(array.get_array() == np.array([1, 2]))
```

### Repository interface improvements

As of `v2.0.0`, the repository interface of the `Node` class was moved to the `Node.base.repository` namespace.
This was done to clean up the top-level namespace of the `Node` class which was getting very crowded, and in most use-cases, a user never needs to directly access these methods.
It is up to the data plugin to provide specific methods to retrieve data that might be stored in the repository.
For example, with the `ArrayData`, a user should now have to go to `ArrayData.base.repository.get_object_content` to retrieve an array from the repository, but the class provides `ArrayData.get_array` as a shortcut.

A few data plugins that ship with `aiida-core` didn't respect this guideline, most notably the `FolderData` and `SinglefileData` plugins.
This has been corrected in this release: for `FolderData`, all the repository methods are now once again directly available on the top-level namespace.
The `SinglefileData` now makes it easier to get the content as bytes.
Before, one had to do:
```python
from aiida.orm import SinglefileData
node = SinglefileData.from_string('some content')
with node.open(mode='rb') as handle:
    byte_content = handle.read()
```
this can now be achieved with:
```python
from aiida.orm import SinglefileData
node = SinglefileData.from_string('some content')
byte_content = node.get_content(mode='rb')
```

As of v2.0, due to the repository redesign, it was no longer possible to access a file directly by a filepath on disk.
The repository interface only interacts with file-like objects to stream the content.
However, a lot of Python libraries expect filepaths on disk and do not support file-like objects.
This would force an AiiDA user to write the file from the repository to a temporary file on disk, and pass that temporary filepath.
For example, consider the `numpy.loadtxt` function which requires a filepath, the code would look something like:
```python
import pathlib
import shutil
import tempfile

with tempfile.TemporaryDirectory() as tmp_path:

    # Copy the entire content to the temporary folder
    dirpath = pathlib.Path(tmp_path)
    node.base.repository.copy_tree(dirpath)

    # Or copy the content of a file. Should use streaming
    # to avoid reading everything into memory
    filepath = (dirpath / 'some_file.txt')
    with filepath.open('rb') as target:
        with node.base.repository.open('rb') as source:
            shutil.copyfileobj(source, target)

    # Now use `filepath` to library call, e.g.
    numpy.loadtxt(filepath)
```
This burdensome boilerplate has now been made obsolete by the `as_path` method:
```python
with node.base.repository.as_path() as filepath:
    numpy.loadtxt(filepath)
```
For the `FolderData` and `SinglefileData` plugins, the method can be accessed on the top-level namespace of course.

### Full list of changes

#### Features
- Add the `SqliteDosStorage` storage backend [[702f88788]](https://github.com/aiidateam/aiida-core/commit/702f8878829b8e2a65d81623cc2238eb40791bc6)
- `XyData`: Allow defining array(s) on construction [[f11598dc6]](https://github.com/aiidateam/aiida-core/commit/f11598dc68a80bbfa026db064158aae64ac0e802)
- `ArrayData`: Make `name` optional in `get_array` [[7fbe67cb6]](https://github.com/aiidateam/aiida-core/commit/7fbe67cb6273cf2bae4256cdbda284aeb89a9372)
- `ArrayData`: Allow defining array(s) on construction [[35e669fe8]](https://github.com/aiidateam/aiida-core/commit/35e669fe86ca467e656f4e500f11d533f7492107)
- `FolderData`: Expose repository API on top-level namespace [[3e1f87373]](https://github.com/aiidateam/aiida-core/commit/3e1f87373e3cf2c40e8a3134ac848d4c16b9dbcf)
- Repository: Add the `as_path` context manager [[b0546e8ed]](https://github.com/aiidateam/aiida-core/commit/b0546e8ed12b0982617293ab4a03ba3ec2d8ea44)
- Caching: Add the `strict` argument configuration validation [[f272e197e]](https://github.com/aiidateam/aiida-core/commit/f272e197e2992f445b2b51608a6ffe17a2a8f4c1)
- Caching: Try to import an identifier if it is a class path [[2c56fc234]](https://github.com/aiidateam/aiida-core/commit/2c56fc234139e624eb1da5ee016c1761b7b1a70a)
- CLI: Add the command `verdi profile setup` [[351021164]](https://github.com/aiidateam/aiida-core/commit/351021164d00aa3a2a78b5b6e43e8a87a8553151)
- CLI: Add `cached` and `cached_from` projections to `verdi process list` [[3b445c4f1]](https://github.com/aiidateam/aiida-core/commit/3b445c4f1c793ecc9b5c2efce863620748610d61)
- CLI: Add `--all` flag to `verdi process kill` [[db1375949]](https://github.com/aiidateam/aiida-core/commit/db1375949b9ec133ee3b06bc3bfe2f8185eceeb6)
- CLI: Lazily validate entry points in parameter types [[d3807d422]](https://github.com/aiidateam/aiida-core/commit/d3807d42229ffbad4e74752b6842a60f66bbafed)
- CLI: Add repair hint to `verdi process play/pause/kill` [[8bc31bfd1]](https://github.com/aiidateam/aiida-core/commit/8bc31bfd1dae84a2240470a8163b3407eb27ae03)
- CLI: Add the `verdi process repair` command [[3e3d9b9f7]](https://github.com/aiidateam/aiida-core/commit/3e3d9b9f70bb1ae2f7ae86db06469b73c5ebdfae)
- CLI: Validate strict in `verdi config set caching.disabled_for` [[9cff59232]](https://github.com//commit/9cff5923263cd349da731b02d309120e754c0b95)
- `DynamicEntryPointCommandGroup`: Allow entry points to be excluded [[9e30ec8ba]](https://github.com//commit/9e30ec8baeee74ae6d1c08459cb6eacd46d12e8a)
- Add the `aiida.common.log.capture_logging` utility [[9006eef3a]](https://github.com/aiidateam/aiida-core/commit/9006eef3ac1bb7b47c8ced63766e2f5346d46e91)
- `Config`: Add the `create_profile` method [[ae7abe8a6]](https://github.com/aiidateam/aiida-core/commit/ae7abe8a6bddcf8d59b6ac213a73deeb65d4c056)
- Engine: Add the `await_processes` utility function [[45767f050]](https://github.com/aiidateam/aiida-core/commit/45767f0509513fecd287e334fb26299db2adf14b)
- Engine: Add the `wait` argument to `submit` [[8f5e929d1]](https://github.com/aiidateam/aiida-core/commit/8f5e929d1660b663894bac52f385874011e47872)
- ORM: Add the `User.is_default` property [[a43c4cd0f]](https://github.com/aiidateam/aiida-core/commit/a43c4cd0fcee252202f9a5a3016aef156a36ac29)
- ORM: Add `NodeCaching.CACHED_FROM_KEY` for `_aiida_cached_from` constant [[35fc3ae57]](https://github.com/aiidateam/aiida-core/commit/35fc3ae5790023022d4d78cf2fe7274a72b590d2)
- ORM: Add the `Entity.get_collection` classmethod [[305f1dbf4]](https://github.com/aiidateam/aiida-core/commit/305f1dbf4ccb3e0e2e79865aee8d248e5ad55b95)
- ORM: Add the `Dict.get` method [[184fcd16e]](https://github.com//commit/184fcd16e9a88fbf9d4e754870416f4a56de55b5)
- ORM: Register `numpy.ndarray` with the `to_aiida_type` to `ArrayData` [[d8dd776a6]](https://github.com/aiidateam/aiida-core/commit/d8dd776a68f438702aa07b58d754b35ab0745937)
- Manager: Add the `set_default_user_email` [[8f8f55807]](https://github.com/aiidateam/aiida-core/commit/8f8f55807fd02872e7a345b7bd10eb68f65cbcda)
- `CalcJob`: Add support for nested targets in `remote_symlink_list` [[0ec650c1a]](https://github.com/aiidateam/aiida-core/commit/0ec650c1ae31ac42f80940103ac81cb0eb53f06d)
- `RemoteData`: Add the `is_cleaned` property [[2a2353d3d]](https://github.com/aiidateam/aiida-core/commit/2a2353d3dd2712afda8f1ebbcf749c7cc99f06fd)
- `SqliteTempBackend`: Add support for reading from and writing to archives [[83fc5cf69]](https://github.com/aiidateam/aiida-core/commit/83fc5cf69e8fcecba1f4c47ccb6599e6d78ba9dc)
- `StorageBackend`: Add the `read_only` class attribute [[8a4303ff5]](https://github.com//commit/8a4303ff53ec0b14fe43fbf1f4e01b69efc689df)
- `SinglefileData`: Add `mode` keyword to `get_content` [[d082df7f1]](https://github.com/aiidateam/aiida-core/commit/d082df7f1b53057e15c8cbbc7e662ec808c27722)
- `BaseRestartWorkChain`: Factor out attachment of outputs [[d6093d101]](https://github.com/aiidateam/aiida-core/commit/d6093d101ddcdaba74a14b44bdd91eea95628903)
- Add support for `NodeLinksManager` to YAML serializer [[6905c134e]](https://github.com//commit/6905c134e737183a1f366d9f86d9f77dd4d74730)

#### Performance
- CLI: Make loading of config lazy for improved responsiveness [[d533b7a54]](https://github.com/aiidateam/aiida-core/commit/d533b7a540ab9d420acec1833bb7e23f50d8a7c1)
- Cache the lookup of entry points [[12cc930db]](https://github.com/aiidateam/aiida-core/commit/12cc930dbf8f377527d89f6f39bc28a4638f8377)
- Refactor: Delay import of heavy packages to speed up import time [[5dda6fd97]](https://github.com/aiidateam/aiida-core/commit/5dda6fd9749a886585cebf9afc288ebc46f00429)
- Refactor: Delay import of heavy packages to speed up import time [[8e6e08dc7]](https://github.com/aiidateam/aiida-core/commit/8e6e08dc780152333e4a6b6966469a98e51fe061)
- Do not import `aiida.cmdline` in `aiida.orm` [[0879a4e27]](https://github.com/aiidateam/aiida-core/commit/0879a4e27559ac368545afd18a1f061e9c29b8c7)
- Lazily define `__type_string` in `orm.Group` [[ebf3101d9]](https://github.com/aiidateam/aiida-core/commit/ebf3101d9b2c6298070853bae6c7b06489a363ca)
- Lazily define `_plugin_type_string` and `_query_type_string of `Node` [[3a61a7003]](https://github.com/aiidateam/aiida-core/commit/3a61a70032d6ace3d27f1a701be048f3f2026b43)

#### Changes
- CLI: `verdi profile delete` is now storage plugin agnostic [[5015f5fe1]](https://github.com//commit/5015f5fe12d93024ed0d7594d860f1f2cd977548)
- CLI: Usability improvements for interactive `verdi setup` [[c53ea20a4]](https://github.com/aiidateam/aiida-core/commit/c53ea20a497f66bc88f68d0603cf9a32614fc4c2)
- CLI: Do not load config in defaults and callbacks during tab-completion [[062058862]](https://github.com/aiidateam/aiida-core/commit/06205886204c142f771dab37f1a78f3bf0ba7251)
- Engine: Make process inputs in launchers positional [[6d18ccb86]](https://github.com//commit/6d18ccb8680f16e8da80deffe40808cc2e669de0)
- Remove `aiida.manage.configuration.load_documentation_profile` [[9941266ce]](https://github.com//commit/9941266ced93f31191152034606bf5b1e049cc79)
- ORM: `Sealable.seal()` return `self` instead of `None` [[16e3bd3b5]](https://github.com/aiidateam/aiida-core/commit/16e3bd3b5087b95d31983df2147d4c14bb331077)
- ORM: Move deprecation warnings from module level [[c4afdb9be]](https://github.com//commit/c4afdb9be5633b68d72121c36916dfc6791d8b29)
- Config: Switch from `jsonschema` to `pydantic` [[4203f162d]](https://github.com/aiidateam/aiida-core/commit/4203f162df803946b2396ca820e6b6139a3ecc61)
- `DynamicEntryPointCommandGroup`: Use `pydantic` to define config model [[1d8ea2a27]](https://github.com/aiidateam/aiida-core/commit/1d8ea2a27381feeabfe38f5a3647d22ac1b825e4)
- Config: Remove use of `NO_DEFAULT` for `Option.default` [[275718cc8]](https://github.com/aiidateam/aiida-core/commit/275718cc8dae866a6fc847fa898a3290672e9d7a)

#### Fixes
- Add the `report` method to `logging.LoggerAdapter` [[7d6684ce1]](https://github.com/aiidateam/aiida-core/commit/7d6684ce1f46862e69c59e9b48da97ab63d9f786)
- `CalcJob`: Fix MPI behavior if `withmpi` option default is True [[84737506e]](https://github.com//commit/84737506e99860beb3ecfa329c1d1e9d4636cd16)
- `CalcJobNode`: Fix validation for `depth=None` in `retrieve_list` [[03c86d5c9]](https://github.com/aiidateam/aiida-core/commit/03c86d5c988d9d2e1f656ba28bd2b8292fc7b02d)
- CLI: Fix bug in `verdi data core.trajectory show` for various formats [[fd4c1269b]](https://github.com/aiidateam/aiida-core/commit/fd4c1269bf913602660b13bdb49c3bc15360448a)
- CLI: Add missing entry point groups for `verdi plugin list` [[ae637d8c4]](https://github.com/aiidateam/aiida-core/commit/ae637d8c474a0071031c6a9bf6f65d2a924f2e81)
- CLI: Remove loading backend for `verdi plugin list` [[34e564ad0]](https://github.com/aiidateam/aiida-core/commit/34e564ad081143a4739c58a7aaa499e55d4e4651)
- CLI: Fix `repository` being required for `verdi quicksetup` [[d4666009e]](https://github.com/aiidateam/aiida-core/commit/d4666009e82fc104a1fa7965b1f50934bec36f0f)
- CLI: Fix `verdi config set` when setting list option [[314917801]](https://github.com/aiidateam/aiida-core/commit/314917801181d163f0760ca5788c543103d96bf5)
- CLI: Keep list unique in `verdi config set --append` [[3844f86c6]](https://github.com/aiidateam/aiida-core/commit/3844f86c6bb7da1dfc40542210b450a70b8950c5)
- CLI: Improve the formatting of `verdi user list` [[806d7e236]](https://github.com/aiidateam/aiida-core/commit/806d7e2366225bbe16ed982c320a708dbbf323f5)
- CLI: Set defaults for user details in profile setup [[8b8887e55]](https://github.com/aiidateam/aiida-core/commit/8b8887e559e02eadac832a89f7012872040e1cbc)
- CLI: Reuse options in `verdi user configure` from setup [[1c0b702ba]](https://github.com/aiidateam/aiida-core/commit/1c0b702bafb56c6452c975ad7020796303742405)
- `InteractiveOption`: Fix validation being skipped if `!` provided [[c4b183bc6]](https://github.com/aiidateam/aiida-core/commit/c4b183bc6d6083dad0754e42de19e96a867ff8ed)
- ORM: Fix problem with detached `DbAuthInfo` instances [[ec2c6a8fe]](https://github.com//commit/ec2c6a8fe3b397ab9f7314c556551114ea15c7df)
- ORM: Check nodes are from same backend in `validate_link` [[7bd546ebe]](https://github.com/aiidateam/aiida-core/commit/7bd546ebe67845b47c0dc14567c1ef7a557c23ef)
- ORM: `ProcessNode.is_valid_cache` is `False` for unsealed nodes [[a1f456d43]](https://github.com/aiidateam/aiida-core/commit/a1f456d436fee6a54327e4ba9b0841a980998f52)
- ORM: Explicitly pass backend when constructing new entity [[96667c8c6]](https://github.com/aiidateam/aiida-core/commit/96667c8c63b0053e79c8a1531707890027f10e6a)
- ORM: Replace `.collection(backend)` with `.get_collection(backend)` [[bac2152c4]](https://github.com/aiidateam/aiida-core/commit/bac2152c450a83cb6332516db315147cfc982265)
- Make `warn_deprecation` respect the `warnings.showdeprecations` option [[6c28c63e9]](https://github.com//commit/6c28c63e95323a4e3ba8730ef720e1a708d91133)
- `PsqlDosBackend`: Fix changes not persisted after `iterall` and `iterdict` [[2ea5087c0]](https://github.com/aiidateam/aiida-core/commit/2ea5087c079417d6d0b37cbc0502ed7cab173c11)
- `PsqlDosBackend`: Fix `Node.store` excepting when inside a transaction [[624dcd9fc]](https://github.com/aiidateam/aiida-core/commit/624dcd9fcc1f0f9aadf54c59afa435fd78598ef7)
- `Parser.parse_from_node`: Validate outputs against process spec [[d16792f3d]](https://github.com/aiidateam/aiida-core/commit/d16792f3d80fb1c497840ff1b0f6f1e114a262da)
- Fix `QueryBuilder.count` for storage backends using sqlite [[5dc1555bc]](https://github.com/aiidateam/aiida-core/commit/5dc1555bc186a7b0205323801833037ae9a6bc36)
- Process functions: Fix bug with variable arguments [[ca8bbc67f]](https://github.com//commit/ca8bbc67fcb40d6cec4e1cae32ce114495c0eb1d)
- `SqliteZipBackend`: Return `self` in `store` [[6a43b3f15]](https://github.com/aiidateam/aiida-core/commit/6a43b3f15ca9cc2eab1a13f6670921f71809a956)
- `SqliteZipBackend`: Ensure the `filepath` is absolute and exists [[5eac8b49d]](https://github.com//commit/5eac8b49df33287c3dc6cfbf46eae491c3196fc4)
- Remove `with_dbenv` use in `aiida.orm` [[35c57b9eb]](https://github.com/aiidateam/aiida-core/commit/35c57b9eb63b42531111f27ac7cc76e129ccd14a)

#### Deprecations
- Deprecated `aiida.orm.nodes.data.upf` and `verdi data core.upf` [[6625fd245]](https://github.com/aiidateam/aiida-core/commit/6625fd2456f4ee13297d797d08925a359474e30e)

#### Documentation
- Add topic section on storage [[83dbe1ad9]](https://github.com//commit/83dbe1ad92be580fa26412e5db4d1f370ec91c7a)
- Add important note on using `iterall` and `iterdict` [[0aea7e41b]](https://github.com/aiidateam/aiida-core/commit/0aea7e41b24fb479b2a1bbc71ab72f43e823f3a7)
- Add links about "entry point" and "plugin" to tutorial [[517ffcb1c]](https://github.com/aiidateam/aiida-core/commit/517ffcb1c5ce32f281589432cde1d58588fa83e0)
- Disable the `warnings.showdeprecations` option [[4adb06c0c]](https://github.com//commit/4adb06c0ce32335fffe5d970febfd36dcd85edd5)
- Fix instructions for inspecting archive files [[0a9c2788e]](https://github.com//commit/0a9c2788ea54926a202c5c3393d9d34815bf4356)
- Changes are reverted if exception during `iterall` [[17c5d8724]](https://github.com/aiidateam/aiida-core/commit/17c5d872495fbb1b6a80d985cb71088095083bb9)
- Various minor fixes to `run_docker.rst` [[d3788adea]](https://github.com/aiidateam/aiida-core/commit/d3788adea220107bce3582d246bcc9674b5e1571)
- Update `pydata-sphinx-theme` and add Discourse links [[13df42c14]](https://github.com/aiidateam/aiida-core/commit/13df42c14abc6145da3880616288a98b2d5ecc74)
- Correct example of `verdi config unset` in troubleshooting [[d6143dbc8]](https://github.com/aiidateam/aiida-core/commit/d6143dbc87bbbb3b6d4758b3922a47741493897e)
- Improvements to sections containing recently added functionality [[836419f66]](https://github.com/aiidateam/aiida-core/commit/836419f6694e9d4d8e580f1b6fd71ffa27f635ef)
- Fix typo in `run_codes.rst` [[9bde86ec7]](https://github.com/aiidateam/aiida-core/commit/9bde86ec7700b3dd2df55c69fb8efb9887ed07d6)
- Fixtures: Fix `suppress_warnings` of `run_cli_command` [[9807cede4]](https://github.com//commit/9807cede4601349a50ac2bff72a32173a0e3d702)
- Update citation suggestions [[1dafdf2dd]](https://github.com/aiidateam/aiida-core/commit/1dafdf2ddb38c801d2075d9af9bbde9e0d26c8ca)

#### Dependencies
- Add support for Python 3.12 [[c39b4fda4]](https://github.com/aiidateam/aiida-core/commit/c39b4fda40c88737f1c56f5ad6f42cbed974478b)
- Update to `sqlalchemy~=2.0` [[a216f5052]](https://github.com/aiidateam/aiida-core/commit/a216f5052c56bbbeffac296fcd59af177f703829)
- Update to `disk-objectstore~=1.0` [[56f9f6ca0]](https://github.com/aiidateam/aiida-core/commit/56f9f6ca03c7b69766e725449fd955848577055a)
- Add new extra `tui` that provides `verdi` as a TUI [[a42e09c02]](https://github.com/aiidateam/aiida-core/commit/a42e09c026e793e5670b88037d5f4863cc4097f0)
- Add upper limit `jedi<0.19` [[fae2a9cfd]](https://github.com/aiidateam/aiida-core/commit/fae2a9cfda461a26e80b648795e45087ea8133fd)
- Update requirement `mypy~=1.7` [[c2fcad4ab]](https://github.com/aiidateam/aiida-core/commit/c2fcad4ab3f6bc1899475af037e4b14f3497feec)
- Add compatibility for `pymatgen>=v2023.9.2` [[4e0e7d8e9]](https://github.com/aiidateam/aiida-core/commit/4e0e7d8e9fd10c4adc3630cf24cebdf749f95351)
- Bump `yapf` to `0.40.0` [[a8ae50853]](https://github.com/aiidateam/aiida-core/commit/a8ae508537d2b6e9ffa1de9beb140065282a30f8)
- Update pre-commit requirement `flynt==1.0.1` [[e01ea4b97]](https://github.com/aiidateam/aiida-core/commit/e01ea4b97d094f0543b0f0c631fa0463c8baf2f5)
- Docker: Pinning mamba version to 1.5.2 [[a6c2dbe1c]](https://github.com//commit/a6c2dbe1c434f0df7790e41632c5dc578edebb97)
- Docker: Bump Python version to 3.10.13 [[b168f2e12]](https://github.com//commit/b168f2e12776136a8601b42dd85d7b2bb4746e30)

#### Devops
- CI: Use Python 3.10 for `pre-commit` in CI and CD workflows [[f41c8ac90]](https://github.com/aiidateam/aiida-core/commit/f41c8ac9061c379f72286631bfb1c486cc302dc8)
- CI: Using concurrency for CI actions [[4db54b7f8]](https://github.com/aiidateam/aiida-core/commit/4db54b7f833096e2d5f3d439683c28749467b20d)
- CI: Update tox to use Python 3.9 [[227390a52]](https://github.com/aiidateam/aiida-core/commit/227390a52a6dc77faa20cb1cc6372ec7f66e0409)
- Docker: Bump `upload-artifact` action to v4 for Docker workflow [[bfdb2828a]](https://github.com//commit/bfdb2828a823052df52cb5cf61599cbc07b0bb4b)
- Refactor: Replace `all` with `iterall` where beneficial [[8a2fece02]](https://github.com/aiidateam/aiida-core/commit/8a2fece02411c982eb16e8fed8991ffaf75fa76f)
- Pre-commit: Disable `no-member` and `no-name-in-module` for `aiida.orm` [[15379bbee]](https://github.com/aiidateam/aiida-core/commit/15379bbee2cbf9889772d497e1a6b77e230aaa2f)
- Tests: Move memory leak tests to main unit test suite [[561f93cef]](https://github.com/aiidateam/aiida-core/commit/561f93cef15355e08a3ec19173132deec031ed67)
- Tests: Move ipython magic tests to main unit test suite [[ce9acc312]](https://github.com/aiidateam/aiida-core/commit/ce9acc312c0cfe351f188d399046de6a4248cb16)
- Tests: Remove deprecated `aiida/manage/tests/main` module [[5b9da7d1e]](https://github.com/aiidateam/aiida-core/commit/5b9da7d1eeb3cb01474f2c95526148ba136c6f3c)
- Tests: Refactor transport tests from `unittest` to `pytest` [[ec64780c2]](https://github.com/aiidateam/aiida-core/commit/ec64780c206cdb040eee740b17865e6f0ff81cd8)
- Tests: Fix failing `tests/cmdline/commands/test_setup.py` [[b6f7ec188]](https://github.com/aiidateam/aiida-core/commit/b6f7ec18830d8495a76eefb3ef59e0069db49f99)
- Tests: Print stack trace if CLI command excepts with `run_cli_command` [[08cba0f78]](https://github.com/aiidateam/aiida-core/commit/08cba0f78acbf3da760f8d9110426b80df20ab3a)
- Tests: Make `PsqlDosStorage` profile unload test more robust [[1c72eac1f]](https://github.com/aiidateam/aiida-core/commit/1c72eac1f91e02bc464c66328ea74911762b94fd)
- Tests: Fix flaky work chain tests using `recwarn` fixture [[207151784]](https://github.com/aiidateam/aiida-core/commit/2071517849820e218a28d3968e45d211e8cd6247)
- Tests: Fix `StructureData` test breaking for recent `pymatgen` versions [[d1d64e800]](https://github.com/aiidateam/aiida-core/commit/d1d64e8004c31209488f71a160a4f4824d02c081)
- Typing: Improve annotations of process functions [[a85af4f0c]](https://github.com/aiidateam/aiida-core/commit/a85af4f0c017b8c03426ef7927163a33add08004)
- Typing: Add type hinting for `aiida.orm.nodes.data.array.xy` [[2eaa5449b]](https://github.com/aiidateam/aiida-core/commit/2eaa5449bca55ac87475900dd64ca086bddc0023)
- Typing: Add type hinting for `aiida.orm.nodes.data.array.array` [[c19b1423a]](https://github.com/aiidateam/aiida-core/commit/c19b1423adfb0b8490cdfb899cabd8e88e03237f)
- Typing: Add overload signatures for `open` [[0986f6b59]](https://github.com/aiidateam/aiida-core/commit/0986f6b59086e2e0947906654c1642cf264b462e)
- Typing: Add overload signatures for `get_object_content` [[d18eedc8b]](https://github.com/aiidateam/aiida-core/commit/d18eedc8be565af12f36e48bd8392e9b29438c15)
- Typing: Correct type annotation of `WorkChain.on_wait` [[923cc314c]](https://github.com/aiidateam/aiida-core/commit/923cc314c527a183e55819b96de8ae027c9f0612)
- Typing: Improve type hinting for `aiida.orm.nodes.data.singlefile` [[b9d087dd4]](https://github.com/aiidateam/aiida-core/commit/b9d087dd47c2b09878d078fc6a64cede0e1ce5e1)


## v2.4.2 - 2023-11-30

### Docker
- Disable the consumer timeout for RabbitMQ [[5ce1e7ec3]](https://github.com/aiidateam/aiida-core/commit/5ce1e7ec37207013a7733b9df943977a15e421e5)
- Add `rsync` and `graphviz` to system requirements [[c4799add4]](https://github.com/aiidateam/aiida-core/commit/c4799add41a29944dd02be2ca44756eaf8035b1c)

### Dependencies
- Add upper limit `jedi<0.19` [[90e586fe3]](https://github.com/aiidateam/aiida-core/commit/90e586fe367daf8f9ebe953c2a976bc5c4d33903)


## v2.4.1 - 2023-11-15

This patch release comes with an improved set of Docker images and a few fixes to provide compatibility with recent versions of `pymatgen`.

### Docker
- Improved Docker images [[fec4e3bc4]](https://github.com/aiidateam/aiida-core/commit/fec4e3bc4dffd7d15b63e7ef0f306a8034ca3816)
- Add folders that automatically run scripts before/after daemon start in Docker image [[fe4bc1d3d]](https://github.com/aiidateam/aiida-core/commit/fe4bc1d3d380686094021515baf31babf47388ac)
- Pass environment variable to `aiida-prepare` script in Docker image [[ea47668ea]](https://github.com/aiidateam/aiida-core/commit/ea47668ea9b38581fbe1b6c72e133824043a8d38)
- Update the `.devcontainer` to use the new docker stack [[413a0db65]](https://github.com/aiidateam/aiida-core/commit/413a0db65cb31156e6e794dac4f8d36e74b0b2cb)

### Dependencies
- Add compatibility for `pymatgen>=v2023.9.2` [[1f6027f06]](https://github.com/aiidateam/aiida-core/commit/1f6027f062a9eca5d8006741df91545d8ec01ed3)

### Devops
- Tests: Make `PsqlDosStorage` profile unload test more robust [[f392459bd]](https://github.com/aiidateam/aiida-core/commit/f392459bd417bec8a3ce184ee8f753649bcb77b8)
- Tests: Fix `StructureData` test breaking for recent `pymatgen` versions [[093037d48]](https://github.com/aiidateam/aiida-core/commit/093037d48a2d92cbb6f068c1111fe1564a4500c0)
- Trigger Docker image build when pushing to `support/*` branch [[5cf3d1d75]](https://github.com/aiidateam/aiida-core/commit/5cf3d1d75e8d22d6a3f0909c84aa63cc228bcf4b)
- Use `aiida-core-base` image from `ghcr.io` [[0e5b1c747]](https://github.com/aiidateam/aiida-core/commit/0e5b1c7473030dd5b5027ea4eb0a658db9174091)
- Loosen trigger conditions for Docker build CI workflow [[22e8a8069]](https://github.com/aiidateam/aiida-core/commit/22e8a80690747b792b70f96a0e332906f0e65e97)
- Follow-up docker build runner macOS-ARM64 [[1bd9bf03d]](https://github.com/aiidateam/aiida-core/commit/1bd9bf03d19dda4c462728fb87cf4712b74c5f39)
- Upload artifact by PR from forks for docker workflow [[afc2dad8a]](https://github.com/aiidateam/aiida-core/commit/afc2dad8a68e280f01e89fcb5b13e7a60c2fd072)
- Update the image name for docker image [[17507b410]](https://github.com/aiidateam/aiida-core/commit/17507b4108b5dd1cd6e074b08e0bc2535bf0a164)


## v2.4.0 - 2023-06-22

This minor release comes with a number of new features and improvements as well as a significant amount of bug fixes.
Support for Python 3.8 has been officially dropped in accordance with [AEP 003](https://github.com/aiidateam/AEP/blob/master/003_adopt_nep_29/readme.md).

As a result of one of the bug fixes, related to the [caching of `CalcJob` nodes](https://github.com/aiidateam/aiida-core/commit/685e0f87d7c571df24aea8f0ce21c6c45dfbd8a0), a database migration had to be added, the first since the release of v2.0.
After ugrading to v2.4.0, you will be prompted to migrate your database.
The automated migration drops the hashes of existing `CalcJobNode`s and provides you with the optional command to recompute them.
Execute the command if existing `CalcJobNode`s need to be usable as valid cache sources.

### Features
- Config: Add option to change recursion limit in daemon workers [[226159fd9]](https://github.com/aiidateam/aiida-core/commit/226159fd96c01782f4e1b4b52db945e3aef76285)
- CLI: Added `compress` option to `verdi storage maintain` [[add474cbb]](https://github.com/aiidateam/aiida-core/commit/add474cbb0d67e278803e9340e521ea1046ef35c)
- Expose `get_daemon_client` so it can be imported from `aiida.engine` [[1a0c1ee93]](https://github.com/aiidateam/aiida-core/commit/1a0c1ee932f24a6b191dc2e4d770973b8b32d66e)
- `verdi computer test`: Improve messaging of login shell check [[062a58260]](https://github.com/aiidateam/aiida-core/commit/062a5826077907f43165084d4dc02db3f71bfb73)
- `verdi node rehash`: Add `aiida.node` as group for `--entry-point` [[2fd07514d]](https://github.com/aiidateam/aiida-core/commit/2fd07514d9a76ceb5576dd23c02596794dea0666)
- `verdi process status`: Add `call_link_label` to stack entries [[bd9372a5f]](https://github.com/aiidateam/aiida-core/commit/bd9372a5f4ce6681b16ef806338512c0fb02e25e)
- `SinglefileData`: Add the `from_string` classmethod [[c25de615e]](https://github.com/aiidateam/aiida-core/commit/c25de615e4680b809f5d65d42031afdf95bd6923)
- `DynamicEntryPointCommandGroup`: Add support for shared options [[220a65c76]](https://github.com/aiidateam/aiida-core/commit/220a65c76d9fcf3144ef77925caff8f5c653b2c9)
- `DynamicEntryPointCommandGroup`: Pass ctx to `command` callable [[7de711be4]](https://github.com/aiidateam/aiida-core/commit/7de711be468f91e09baf6def3e319d85288e3be1)
- `ProcessNode`: Add the `exit_code` property [[ad8a539ee]](https://github.com/aiidateam/aiida-core/commit/ad8a539ee2b481d526607b5924789fbbd1e14102)

### Fixes
- Engine: Dynamically update maximum stack size close to overflow to address `RecursionError` under heavy load [[f797b4766]](https://github.com/aiidateam/aiida-core/commit/f797b476622d9b2724d1460bbe55ef989166f57d)
- `CalcJobNode`: Fix the computation of the hash [[685e0f87d]](https://github.com/aiidateam/aiida-core/commit/685e0f87d7c571df24aea8f0ce21c6c45dfbd8a0)
- `CalcJob`: Ignore file in `remote_copy_list` not existing [[101a8d61b]](https://github.com/aiidateam/aiida-core/commit/101a8d61ba1c9f50a0231cd249c5a7f7ff1d77a4)
- `CalcJob`: Assign outputs from node in case of cache hit [[777b97601]](https://github.com/aiidateam/aiida-core/commit/777b976013d0041e059f86c1ac0d2f43b52884df)
- Fix log messages being logged twice to the daemon log file [[bfd63c790]](https://github.com/aiidateam/aiida-core/commit/bfd63c790a6bd5fdcb60a2d1b840c7b285c53334)
- Process control: Change language when not waiting for response [[68cb4579d]](https://github.com/aiidateam/aiida-core/commit/68cb4579d9e77b32dc6182dc704e6079b6f9c0c2)
- Do not assume `pgtest` cluster started in `postgres_cluster` fixture [[1de2ca576]](https://github.com/aiidateam/aiida-core/commit/1de2ca576c7fbe5c6586f53160304b46c99a3a10)
- Process control: Warn instead of except when daemon is not running [[ad4fbcccb]](https://github.com/aiidateam/aiida-core/commit/ad4fbcccb14ac68653a941bf17be2e532ca162bc)
- `DirectScheduler`: Add `?` as `JobState.UNDETERMINED` [[ffc869d8f]](https://github.com/aiidateam/aiida-core/commit/ffc869d8f91a860055b12f0d3803615895fa464f)
- CLI: Correct `verdi devel rabbitmq tasks revive` docstring [[13cadd05f]](https://github.com/aiidateam/aiida-core/commit/13cadd05f2463b0fd240dde2f979801fbac122f9)
- `SinglefileData`: Fix bug when `filename` is `pathlib.Path` [[f36bf583c]](https://github.com/aiidateam/aiida-core/commit/f36bf583c2bb4ac532d97f843141c907ee350f69)
- Improve clarity of various deprecation warnings [[c72a252ed]](https://github.com/aiidateam/aiida-core/commit/c72a252ed563c7f0a7604d15632331c094973b5f)
- `CalcJob`: Remove default of `withmpi` input and make it optional [[6a88cb315]](https://github.com/aiidateam/aiida-core/commit/6a88cb3158c0b84b601a289f50f51cfe6ae42687)
- `Process`: Have `inputs` property always return `AttributesFrozenDict` [[60756fe30]](https://github.com/aiidateam/aiida-core/commit/60756fe30dfaff443ab434d92196249eea47f166)
- `PsqlDos`: Add migration to remove hashes for all `CalcJobNodes` [[7ad916836]](https://github.com/aiidateam/aiida-core/commit/7ad91683643a5d9134c2a9532901e00b903996b4)
- `PsqlDosMigrator`: Commit changes when migrating existing schema [[f84fe5b60]](https://github.com/aiidateam/aiida-core/commit/f84fe5b608d0656c82a38edbcbcb7bf48b399562)
- `PsqlDos`: Add `entry_point_string` argument to `drop_hashes` [[c7a36fa3d]](https://github.com/aiidateam/aiida-core/commit/c7a36fa3d1fcd59e5ff31348c9f64619a7835b75)
- `PsqlDos`: Make hash reset migrations more explicit [[c447a1af3]](https://github.com/aiidateam/aiida-core/commit/c447a1af39f99f2b53cffef36828d2523ab720a5)
- `verdi process list`: Fix double percent sign in daemon usage [[68be866e6]](https://github.com/aiidateam/aiida-core/commit/68be866e653c610e9b957a3fdedc1b77e6e41a05)
- Fix the `daemon_client` fixture [[9e5f5eefd]](https://github.com/aiidateam/aiida-core/commit/9e5f5eefd0cd6be44f0be76efae157dcf6e160ed)
- Transports: Raise `FileNotFoundError` in `copy` if source doesn't exist [[d82069441]](https://github.com/aiidateam/aiida-core/commit/d82069441ce4bb002c8c9b5a419a9d8a8c4446b7)

### Devops
- Add `graphviz` to system requirements of RTD build runner [[3df02550e]](https://github.com/aiidateam/aiida-core/commit/3df02550eff02cd625d0e14eb35e6d6b01b4b12d)
- Add types for `DefaultFieldsAttributeDict` subclasses [[afed5dc46]](https://github.com/aiidateam/aiida-core/commit/afed5dc4630b25b72b2c5a27d542222c086067a7)
- Bump Python version for RTD build [[5df446cd3]](https://github.com/aiidateam/aiida-core/commit/5df446cd3558b1b7ee11d9b60d75287d6395a693)
- Pre-commit: Fix `mypy` warning in `aiida.orm.utils.serialize` [[c25922484]](https://github.com/aiidateam/aiida-core/commit/c2592248482c087807d550c8304fa3703744cdf2)
- Update Docker base image `aiida-prerequisites==0.7.0` [[ac755afae]](https://github.com/aiidateam/aiida-core/commit/ac755afaec836ffc9bc05e0617065eade5ef9ca7)
- Use f-strings in `aiida/engine/daemon/execmanager.py` [[49cffff21]](https://github.com/aiidateam/aiida-core/commit/49cffff21e9fedac517e0e3659eaf1aacb61e448)

### Dependencies
- Drop support for Python 3.8 [[3defb8bb7]](https://github.com/aiidateam/aiida-core/commit/3defb8bb70fab87c5a4375e34dc07144077036fd)
- Update requirement `pylint~=2.17.4` [[397634444]](https://github.com/aiidateam/aiida-core/commit/39763444499eac6fbe76e337fe7e7ca21d675a07)
- Update requirement `flask~=2.2` [[a2a05a69f]](https://github.com/aiidateam/aiida-core/commit/a2a05a69fb2fa6aae9a96d49d543e72008d2888f)

### Deprecations
- `QueryBuilder`: Deprecate `debug` argument and use logger [[603ff37a0]](https://github.com/aiidateam/aiida-core/commit/603ff37a0b6ecd3f5309c8148054b2ac5d022833)

### Documentation
- Add missing `core.` prefix to all `verdi data` subcommands [[99319b3c1]](https://github.com/aiidateam/aiida-core/commit/99319b3c175b260ebc813cbec78208deefcdb562)
- Clarify negation operator in `QueryBuilder` filters [[2c828811f]](https://github.com/aiidateam/aiida-core/commit/2c828811fbdf7e80358ae3cb223aca1dd67e9bb8)
- Correct "variable" to "variadic" arguments [[978217693]](https://github.com/aiidateam/aiida-core/commit/978217693af987f015b51dc1c422a2e71bd39f4f)
- Fix reference target warnings related to `flask_restful` [[4f76e0bd7]](https://github.com/aiidateam/aiida-core/commit/4f76e0bd75bdaf1bab1cae521c52c4a983708544)


## v2.3.1 - 2023-05-22

### Fixes
- `DaemonClient`: Clean stale PID file in `stop_daemon` [[#6007]](https://github.com/aiidateam/aiida-core/pull/6007)


## v2.3.0 - 2023-04-17

This release comes with a number of improvements, some of the more useful and important of which are quickly highlighted.
A full list of changes can be found below.

- [Process function improvements](#process-function-improvements)
- [Scheduler plugins: including `environment_variables`](#scheduler-plugins-including-environment_variables)
- [`WorkChain`: conditional predicates should return boolean-like](#workchain-conditional-predicates-should-return-boolean-like)
- [Controlling usage of MPI](#controlling-usage-of-mpi)
- [Add support for Docker containers](#add-support-for-docker-containers)
- [Exporting code configurations](#exporting-code-configurations)
- [Full list of changes](#full-list-of-changes)
    - [Features](#features)
    - [Fixes](#fixes)
    - [Deprecations](#deprecations)
    - [Changes](#changes)
    - [Documentation](#documentation)
    - [DevOps](#devops)
    - [Dependencies](#dependencies)
- [New contributors](#new-contributors)


### Process function improvements
A number of improvements in the usage of process functions, i.e., `calcfunction` and `workfunction`, have been added.
Each subsection title is a link to the documentation for more details.

#### [Variadic arguments](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/processes/functions.html#variadic-and-keyword-arguments)
Variadic arguments can be used in case the function should accept a list of inputs of unknown length.
Consider the example of a calculation function that computes the average of a number of `Int` nodes:
```python
@calcfunction
def average(*args):
    return sum(args) / len(args)

result = average(*(1, 2, 3))
```

#### [Automatic type validation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/processes/functions.html#type-validation)
Type hint annotations can now be used to add automatic type validation to process functions.
```python
@calcfunction
def add(x: Int, y: Int):
    return x + y

add(1, 1.0)  # Passes
add(1, '1.0')  # Raises an exception
```
Since the Python base types (`int`, `str`, `bool`, etc.) are automatically serialized, these can also be used in type hints.
The following example is therefore identical to the previous:
```python
@calcfunction
def add(x: int, y: int):
    return x + y
```

#### [Docstring parsing](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/processes/functions.html#docstring-parsing)
The `calcfunction` and `workfunction` generate a `Process` of the decorated function on-the-fly.
In doing so, it automatically defines the `ProcessSpec` that is normally done manually, such as for a `CalcJob` or a `WorkChain`.
Before, this would just define the ports that the function process accepts, but the `help` attribute of the port would be left empty.
This is now parsed from the docstring, if it can be correctly parsed:
```python
@calcfunction
def add(x: int, y: int):
    """Add two integers.

    :param x: Left hand operand.
    :param y: Right hand operand.
    """
    return x + y

assert add.spec().inputs['a'].help == 'Left hand operand.'
assert add.spec().inputs['b'].help == 'Right hand operand.'
```
This functionality is particularly useful when exposing process functions in work chains.
Since the process specification of the exposed function will be automatically inherited, the user can inspect the `help` string through the builder.
The automatic documentation produced by the Sphinx plugin will now also display the help string parsed from the docstring.

#### [Nested labels for output nodes](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/processes/functions.html#return-values)
The keys in the output dictionary can now contain nested namespaces:
```python
@calcfunction
def add(alpha, beta):
    return {'nested.sum': alpha + beta}

result = add(Int(1), Int(2))
assert result['nested']['sum'] == 3
```

#### [As class member methods](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/processes/functions.html#as-class-member-methods)
Process functions can now be defined as class member methods of work chains:
```python
class CalcFunctionWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x')
        spec.input('y')
        spec.output('sum')
        spec.outline(
            cls.run_compute_sum,
        )

    @staticmethod
    @calcfunction
    def compute_sum(x, y):
        return x + y

    def run_compute_sum(self):
        self.out('sum', self.compute_sum(self.inputs.x, self.inputs.y))
```
The function should be declared as a `staticmethod` and it should not include the `self` argument in its function signature.
It can then be called from within the work chain as `self.function_name(*args, **kwargs)`.


### Scheduler plugins: including `environment_variables`
The `Scheduler` base class implements the concrete method `_get_submit_script_environment_variables` which formats the lines for the submission script that set the environment variables that were defined in the `metadata.options.environment_variables` input.
Before it was left up to the plugins to actually call this method in the `_get_submit_script_header`, but this is now done by the base class in the `get_submit_script`.
You can now remove the call to `_get_submit_script_environment_variables` from your scheduler plugins, as the base class will take care of it.
A deprecation warning is emitted if the base class detects that the plugin is still calling it manually.
See the [pull request](https://github.com/aiidateam/aiida-core/pull/5948) for more details.

### `WorkChain`: conditional predicates should return boolean-like
Up till now, work chain methods that are used as the predicate in a conditional, e.g., `if_` or `while_` could return any type.
For example:

```python
class SomeWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.outline(if_(cls.some_conditional)())

    def some_conditional(self):
        if self.ctx.something == 'something':
            return True
```
The `some_conditional` method is used as the "predicate" of the `if_` conditional.
It returns `True` or `None`.
Since the `None` value in Python is "falsey", it would be considered as returning `False`.
However, this duck-typing could accidentally lead to unexpected situations, so we decided to be more strict on the return type.
As of now, a deprecation warning is emitted if the method returns anything that is not "boolean-like", i.e., does not implement the `__bool__` method.
If you see this warning, please make sure to return a boolean, like the built-ins `True` or `False`, or a `numpy.bool` or `aiida.orm.Bool`.
See the [pull request](https://github.com/aiidateam/aiida-core/pull/5924) for more details.

### Controlling usage of MPI
It is now possible to define on a code object whether it should be run with or without MPI through the `with_mpi` attribute.
It can be set from the Python API as `AbstractCode(with_mpi=with_mpi)` or through the `--with-mpi / --no-with-mpi` option of the `verdi code create` CLI command.
This option adds a manner to control the use of MPI in calculation jobs, in addition to the existing ones defined by the `CalcJob` plugin and the `metadata.options.withmpi` input.
For more details on how these are controlled and how conflicts are handled, please refer to [the documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/calculations/usage.html#controlling-mpi).

### Add support for Docker containers
Support is added for running calculation within Docker containers.
For example, to run Quantum ESPRESSO pw.x in a Docker container, write the following file to `config.yml`:
```yaml
label: qe-pw-on-docker
computer: localhost
engine_command: docker run -i -v $PWD:/workdir:rw -w /workdir {image_name} sh -c
image_name: haya4kun/quantum_espresso
filepath_executable: pw.x
default_calc_job_plugin: quantumespresso.pw
use_double_quotes: false
wrap_cmdline_params: true
```
and run the CLI command:
```
verdi code create core.code.containerized --config config.yml --non-interactive
```
This should create a `ContainerizedCode` that you can now use to launch a `PwCalculation`.
For more details, please refer to [the documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/data_types.html#supported-container-technologies).

### Exporting code configurations
It is now possible to export the configuration of an existing code through the `verdi code export` command.
The produced YAML file can be used to recreate the code through the `verdi code create` command.
Note that you should use the correct subcommand based on the type of the original code.
For example, if it was an `InstalledCode` you should use `verdi code create core.code.installed`.
For the legacy `Code` instances, you should use `verdi code setup`.
See the [pull request](https://github.com/aiidateam/aiida-core/pull/5860) for more details.

### Full list of changes

#### Features
- `AbstractCode`: Add the `with_mpi` attribute [[#5922]](https://github.com/aiidateam/aiida-core/pull/5922)
- `ContainerizedCode`: Add support for Docker images to use as `Code` for `CalcJob`s [[#5841]](https://github.com/aiidateam/aiida-core/pull/5841)
- `InstalledCode`: Allow relative path for `filepath_executable` [[#5879]](https://github.com/aiidateam/aiida-core/pull/5879)
- CLI: Allow specifying output filename in `verdi node graph generate` [[#5897]](https://github.com/aiidateam/aiida-core/pull/5897)
- CLI: Add `--timeout` option to all `verdi daemon` commands [[#5966]](https://github.com/aiidateam/aiida-core/pull/5966)
- CLI: Add the `verdi calcjob remotecat` command [[#4861]](https://github.com/aiidateam/aiida-core/pull/4861)
- CLI: Add the `verdi code export` command [[#5860]](https://github.com/aiidateam/aiida-core/pull/5860)
- CLI: Improved customizability and scriptability of `verdi storage maintain` [[#5936]](https://github.com/aiidateam/aiida-core/pull/5936)
- CLI: `verdi quicksetup`: Further reduce required user interaction [[#5768]](https://github.com/aiidateam/aiida-core/pull/5768)
- CLI: `verdi computer test`: Add test for login shell being slow [[#5845]](https://github.com/aiidateam/aiida-core/pull/5845)
- CLI: `verdi process list`: Add `exit_message` as projectable attribute [[#5853]](https://github.com/aiidateam/aiida-core/pull/5853)
- CLI: `verdi node delete`: Add verbose list of pks to be deleted [[#5878]](https://github.com/aiidateam/aiida-core/pull/5878)
- CLI: Fail command if `--config` file contains unknown key [[#5939]](https://github.com/aiidateam/aiida-core/pull/5939)
- CLI: `verdi daemon status`: Do not except when no profiles are defined [[#5874]](https://github.com/aiidateam/aiida-core/pull/5874)
- ORM: Add unary operations `+`, `-` and `abs` to `NumericType` [[#5946]](https://github.com/aiidateam/aiida-core/pull/5946)
- Process functions: Support class member functions as process functions [[#4963]](https://github.com/aiidateam/aiida-core/pull/4963)
- Process functions: Infer argument `valid_type` from type hints [[#5900]](https://github.com/aiidateam/aiida-core/pull/5900)
- Process functions: Parse docstring to set input port help attribute [[#5919]](https://github.com/aiidateam/aiida-core/pull/5919)
- Process functions: Add support for variadic arguments [[#5691]](https://github.com/aiidateam/aiida-core/pull/5691)
- Process functions: Allow nested output namespaces [[#5954]](https://github.com/aiidateam/aiida-core/pull/5954)
- `Process`: Store JSON-serializable metadata inputs on the node [[#5801]](https://github.com/aiidateam/aiida-core/pull/5801)
- `Port`: Add the `is_metadata` keyword [[#5801]](https://github.com/aiidateam/aiida-core/pull/5801)
- `ProcessBuilder`: Include metadata inputs in `get_builder_restart` [[#5801]](https://github.com/aiidateam/aiida-core/pull/5801)
- `StructureData`: Add `mode` argument to `get_composition` [[#5926]](https://github.com/aiidateam/aiida-core/pull/5926)
- `Scheduler`: Allow terminating job if submission script is invalid [[#5849]](https://github.com/aiidateam/aiida-core/pull/5849)
- `SlurmScheduler`: Detect broken submission scripts for invalid account [[#5850]](https://github.com/aiidateam/aiida-core/pull/5850)
- `SlurmScheduler`: Parse the `NODE_FAIL` state [[#5866]](https://github.com/aiidateam/aiida-core/pull/5866)
- `WorkChain`: Add dataclass serialisation to context [[#5833]](https://github.com/aiidateam/aiida-core/pull/5833)
- `IcsdDbImporter`: Add `is_theoretical` tag to queried entries [[#5868]](https://github.com/aiidateam/aiida-core/pull/5868)

#### Fixes
- CLI: Prefix the `verdi data` subcommands with `core.` [[#5846]](https://github.com/aiidateam/aiida-core/pull/5846)
- CLI: Respect config log levels if `--verbosity` not explicitly passed [[#5925]](https://github.com/aiidateam/aiida-core/pull/5925)
- CLI: `verdi config list`: Do not except if no profiles are defined [[#5921]](https://github.com/aiidateam/aiida-core/pull/5921)
- CLI: `verdi code show`: Add missing code attributes [[#5916]](https://github.com/aiidateam/aiida-core/pull/5916)
- CLI: `verdi quicksetup`: Fix error incorrect role when creating database [[#5828]](https://github.com/aiidateam/aiida-core/pull/5828)
- CLI: Fix error in `aiida.cmdline.utils.log.CliFormatter` [[#5957]](https://github.com/aiidateam/aiida-core/pull/5957)
- Daemon: Fix false-positive of stopped daemon in `verdi daemon status` [[#5862]](https://github.com/aiidateam/aiida-core/pull/5862)
- `DaemonClient`: Fix and homogenize use of `timeout` in client calls [[#5960]](https://github.com/aiidateam/aiida-core/pull/5960)
- `ProcessBuilder`: Fix bug in `_recursive_merge` [[#5801]](https://github.com/aiidateam/aiida-core/pull/5801)
- `QueryBuilder`: Catch new exception raised by `sqlalchemy>=1.4.45` [[#5875]](https://github.com/aiidateam/aiida-core/pull/5875)
- Fix the `%verdi` IPython magics utility [[#5961]](https://github.com/aiidateam/aiida-core/pull/5961)
- Fix bug in `aiida.engine.utils.instantiate_process` [[#5952]](https://github.com/aiidateam/aiida-core/pull/5952)
- Fix incorrect import of exception from `kiwipy.communications` [[#5947]](https://github.com/aiidateam/aiida-core/pull/5947)

#### Deprecations
- `Scheduler`: Move setting of environment variables into base class [[#5948]](https://github.com/aiidateam/aiida-core/pull/5948)
- `WorkChains`: Emit deprecation warning if predicate `if_/while_` does not return boolean-like [[#5924]](https://github.com/aiidateam/aiida-core/pull/5924)

#### Changes
- `DaemonClient`: Refactor to include parsing of client response [[#5850]](https://github.com/aiidateam/aiida-core/pull/5850)
- ORM: Remove `Entity.from_backend_entity` from the public API [[#5447]](https://github.com/aiidateam/aiida-core/pull/5447)
- `PbsproScheduler`: Replace deprecated `ppn` tag with `ncpus` [[#5910]](https://github.com/aiidateam/aiida-core/pull/5910)
- `ProcessBuilder`: Move `_prune` method to standalone utility [[#5801]](https://github.com/aiidateam/aiida-core/pull/5801)
- `verdi process list`: Simplify the daemon load implementation [[#5850]](https://github.com/aiidateam/aiida-core/pull/5850)

#### Documentation
- Add FAQ on MFA-enabled computers [[#5887]](https://github.com/aiidateam/aiida-core/pull/5887)
- Add link to all `metadata.options` inputs in `CalcJob` submission example [[#5912]](https://github.com/aiidateam/aiida-core/pull/5912)
- Add warning that `Data` constructor is not called on loading [[#5898]](https://github.com/aiidateam/aiida-core/pull/5898)
- Add note on how to create a code that uses Conda environment [[#5905]](https://github.com/aiidateam/aiida-core/pull/5905)
- Add `--without-daemon` flag to benchmark script [[#5839]](https://github.com/aiidateam/aiida-core/pull/5839)
- Add alternative for conda env activation in submission script [[#5950]](https://github.com/aiidateam/aiida-core/pull/5950)
- Clarify that process functions can be exposed in work chains [[#5919]](https://github.com/aiidateam/aiida-core/pull/5919)
- Fix the `intro/tutorial.md` notebook [[#5961]](https://github.com/aiidateam/aiida-core/pull/5961)
- Fix the overindentation of lists [[#5915]](https://github.com/aiidateam/aiida-core/pull/5915)
- Hide the "Edit this page" button on the API reference pages [[#5956]](https://github.com/aiidateam/aiida-core/pull/5956)
- Note that an entry point is required for using a data plugin [[#5907]](https://github.com/aiidateam/aiida-core/pull/5907)
- Set `use_login_shell=False` for `localhost` in performance benchmark [[#5847]](https://github.com/aiidateam/aiida-core/pull/5847)
- Small improvements to the benchmark script [[#5854]](https://github.com/aiidateam/aiida-core/pull/5854)
- Use mamba instead of conda [[#5891]](https://github.com/aiidateam/aiida-core/pull/5891)

#### DevOps
- Add devcontainer for easy integration with VSCode [[#5913]](https://github.com/aiidateam/aiida-core/pull/5913)
- CI: Update `sphinx-intl` and install transifex CLI [[#5908]](https://github.com/aiidateam/aiida-core/pull/5908)
- Fix the `test-install` workflow [[#5873]](https://github.com/aiidateam/aiida-core/pull/5873)
- Pre-commit: Improve typing of `aiida.schedulers.scheduler` [[#5849]](https://github.com/aiidateam/aiida-core/pull/5849)
- Pre-commit: Set `yapf` option `allow_split_before_dict_value = false`[[#5931]](https://github.com/aiidateam/aiida-core/pull/5931)
- Process functions: Replace `getfullargspec` with `signature` [[#5900]](https://github.com/aiidateam/aiida-core/pull/5900)
- Fixtures: Add argument `use_subprocess` to `run_cli_command` [[#5846]](https://github.com/aiidateam/aiida-core/pull/5846)
- Fixtures: Change default `use_subprocess=False` for `run_cli_command` [[#5846]](https://github.com/aiidateam/aiida-core/pull/5846)
- Tests: Use `use_subprocess=False` and `suppress_warnings=True` [[#5846]](https://github.com/aiidateam/aiida-core/pull/5846)
- Tests: Fix bugs revealed by running with `use_subprocess=True` [[#5846]](https://github.com/aiidateam/aiida-core/pull/5846)
- Typing: Annotate `aiida/orm/utils/serialize.py` [[#5832]](https://github.com/aiidateam/aiida-core/pull/5832)
- Typing: Annotate `aiida/tools/visualization/graph.py` [[#5821]](https://github.com/aiidateam/aiida-core/pull/5821)
- Typing: Use modern syntax for `aiida.engine.processes.functions` [[#5900]](https://github.com/aiidateam/aiida-core/pull/5900)

#### Dependencies
- Add compatibility for `ipython~=8.0` [[#5888]](https://github.com/aiidateam/aiida-core/pull/5888)
- Bump cryptography from 36.0.0 to 39.0.1 [[#5885]](https://github.com/aiidateam/aiida-core/pull/5885)
- Remove upper limit on `werkzeug` [[#5904]](https://github.com/aiidateam/aiida-core/pull/5904)
- Update pre-commit requirement `isort==5.12.0` [[#5877]](https://github.com/aiidateam/aiida-core/pull/5877)
- Update requirement `importlib-metadata~=4.13` [[#5963]](https://github.com/aiidateam/aiida-core/pull/5963)
- Bump `graphviz` version to `0.19` [[#5965]](https://github.com/aiidateam/aiida-core/pull/5965)

### New contributors
Thanks a lot to the following new contributors:

- [Ahmed Basem](https://github.com/AhmedBasem20)
- [Mahhheshh](https://github.com/Mahhheshh)
- [Kyle Wang](https://github.com/TurboKyle)
- [Kartikey Saran](https://github.com/kartikeysaran)
- [zahid47](https://github.com/zahid47)

## v2.2.2 - 2023-02-10

### Fixes
- Critical bug fix: Fix bug causing `CalcJob`s to except after restarting daemon [[#5886]](https://github.com/aiidateam/aiida-core/pull/5886)


## v2.2.1 - 2022-12-22

### Fixes
- Critical bug fix: Revert the changes of PR [[#5804]](https://github.com/aiidateam/aiida-core/pull/5804) released with v2.2.0, which addressed a bug when mutating nodes during `QueryBuilder.iterall`. Unfortunately, the change caused changes performed by `verdi` commands (as well as changes made in `verdi shell`) to not be persisted to the database. [[#5851]](https://github.com/aiidateam/aiida-core/pull/5851)


## v2.2.0 - 2022-12-13

This feature release comes with a significant feature and a number of improvements and fixes.

### Live calculation job monitoring

In certain use cases, it is useful to have a calculation job stopped prematurely, before it finished or the requested wallclock time runs out.
Examples are calculations that seem to be going nowhere and so continuing would only waste computational resources.
Up till now, a calculation job could only be "manually" stopped, through `verdi process kill`.
In this release, functionality is added that allows calculation jobs to be monitored automatically by the daemon and have them stopped when certain conditions are met.

Monitors can be attached to a calculation job through the `monitors` input namespace:
```python
builder = load_code().get_builder()
builder.monitors = {
    'monitor_a': Dict({'entry_point': 'some.monitor'}),
    'monitor_b': Dict({'entry_point': 'some.other.monitor'}),
}
```
Monitors are referenced by their entry points with which they are registered in the `aiida.calculations.monitors` entry point group.
A monitor is essentially a function that implements the following interface:
```python
from aiida.orm import CalcJobNode
from aiida.transports import Transport

def monitor(node: CalcJobNode, transport: Transport) -> str | CalcJobMonitorResult | None:
    """Retrieve and inspect files in working directory of job to determine whether the job should be killed.

    :param node: The node representing the calculation job.
    :param transport: The transport that can be used to retrieve files from remote working directory.
    :returns: A string if the job should be killed, `None` otherwise.
    """
```
The `transport` allows to fetch files from the working directory of the calculation.
If the job should be killed, the monitor simply returns a string with the message why and the daemon will send the message to kill the job.

For more information and a complete description of the interface, please refer to the [documentation](https://aiida.readthedocs.io/projects/aiida-core/en/v2.1.0/howto/run_codes.html#how-to-monitor-and-prematurely-stop-a-calculation).
This functionality was accepted based on [AEP 008](https://github.com/aiidateam/AEP/pull/36) which provides more detail on the design choices behind this implementation.


### Full list of changes

#### Features
- `CalcJob`: Add functionality that allows live monitoring [[#5659]](https://github.com/aiidateam/aiida-core/pull/5659)
- CLI: Add `--raw` option to `verdi code list` [[#5763]](https://github.com/aiidateam/aiida-core/pull/5763)
- CLI: Add the `-h` short-hand flag for `--help` to `verdi` [[#5792]](https://github.com/aiidateam/aiida-core/pull/5792)
- CLI: Add short option names for `verdi code create` [[#5799]](https://github.com/aiidateam/aiida-core/pull/5799)
- `StorageBackend`: Add the `initialise` method [[#5760]](https://github.com/aiidateam/aiida-core/pull/5760)
- Fixtures: Add support for `Process` inputs to `submit_and_await` [[#5780]](https://github.com/aiidateam/aiida-core/pull/5780)
- Fixtures: Add `aiida_computer_local` and `aiida_computer_ssh` [[#5786]](https://github.com/aiidateam/aiida-core/pull/5786)
- Fixtures: Modularize fixtures creating AiiDA test instance and profile [[#5758]](https://github.com/aiidateam/aiida-core/pull/5758)
- `Computer`: Add the `is_configured` property [[#5786]](https://github.com/aiidateam/aiida-core/pull/5786)
- Plugins: Add `aiida.storage` to `ENTRY_POINT_GROUP_FACTORY_MAPPING` [[#5798]](https://github.com/aiidateam/aiida-core/pull/5798)

### Fixes
- `verdi run`: Do not add `pathlib.Path` instance to `sys.path` [[#5810]](https://github.com/aiidateam/aiida-core/pull/5810)
- Process functions: Restore support for dynamic nested input namespaces [[#5808]](https://github.com/aiidateam/aiida-core/pull/5808)
- `Process`: properly cleanup when exception in state transition [[#5697]](https://github.com/aiidateam/aiida-core/pull/5697)
- `Process`: Update outputs before updating node process state [[#5813]](https://github.com/aiidateam/aiida-core/pull/5813)
- `PsqlDosMigrator`: refactor the connection handling [[#5783]](https://github.com/aiidateam/aiida-core/pull/5783)
- `PsqlDosBackend`: Use transaction whenever mutating session state, fixing exception when storing a node or group during `QueryBuilder.iterall` [[#5804]](https://github.com/aiidateam/aiida-core/pull/5804)
- `InstalledCode`: Fix bug in `validate_filepath_executable` for SSH [[#5787]](https://github.com/aiidateam/aiida-core/pull/5787)
- `WorkChain`: Protect public methods from being subclassed. Now if you accidentally override, for example, the `run` method of the `WorkChain`, an exception is raised instead of silently breaking the work chain [[#5779]](https://github.com/aiidateam/aiida-core/pull/5779)

#### Changes
- Rename `PsqlDostoreMigrator` to `PsqlDosMigrator` [[#5761]](https://github.com/aiidateam/aiida-core/pull/5761)
- ORM: Remove `pymatgen` version check in `StructureData.set_pymatgen_structure` [[#5777]](https://github.com/aiidateam/aiida-core/pull/5777)
- `StorageBackend`: Remove `recreate_user` from `_clear` [[#5772]](https://github.com/aiidateam/aiida-core/pull/5772)
- `PsqlDosMigrator`: Remove hardcoding of table name in database reset [[#5781]](https://github.com/aiidateam/aiida-core/pull/5781)

### Dependencies
- Dependencies: Add support for Python 3.11 [[#5778]](https://github.com/aiidateam/aiida-core/pull/5778)

### Documentation
- Docs: Correct command to enable `verdi` tab-completion for `fish` shell  [[#5784]](https://github.com/aiidateam/aiida-core/pull/5784)
- Docs: Fix transport & scheduler type in localhost setup [[#5785]](https://github.com/aiidateam/aiida-core/pull/5785)
- Docs: Fix minor formatting issues in "How to run a code" [[#5794]](https://github.com/aiidateam/aiida-core/pull/5794)

### DevOps
- CI: Increase load limit for `verdi` to 0.5 seconds [[#5773]](https://github.com/aiidateam/aiida-core/pull/5773)
- CI: Add `workflow_dispatch` trigger to `nightly.yml` [[#5760]](https://github.com/aiidateam/aiida-core/pull/5760)
- ORM: Fix typing of `aiida.orm.nodes.data.code` module [[#5830]](https://github.com/aiidateam/aiida-core/pull/5830)
- Pin version of `setuptools` as it breaks dependencies [[#5782]](https://github.com/aiidateam/aiida-core/pull/5782)
- Tests: Use explicit `aiida_profile_clean` in process control tests [[#5778]](https://github.com/aiidateam/aiida-core/pull/5778)
- Tests: Replace all use of `aiida_profile_clean` with `aiida_profile` where a clean profile is not necessary [[#5814]](https://github.com/aiidateam/aiida-core/pull/5814)
- Tests: Deal with `run_via_daemon` returning `None` in RPN tests [[#5813]](https://github.com/aiidateam/aiida-core/pull/5813)
- Make type-checking opt-out [[#5811]](https://github.com/aiidateam/aiida-core/pull/5811)


## v2.1.2 - 2022-11-14

### Fixes

- `BaseRestartWorkChain`: Fix bug in `_wrap_bare_dict_inputs` introduced in `v2.1.0` [[#5757]](https://github.com/aiidateam/aiida-core/pull/5757)


## v2.1.1 - 2022-11-10

### Fixes

- Engine: Remove `*args` from the `Process.submit` method. [[#5753]](https://github.com/aiidateam/aiida-core/pull/5753)
  Positional arguments were silently ignored leading to a misleading error message.
  For example, if a user called
  ```python
  inputs = {}
  self.submit(cls, inputs)
  ```
  instead of the intended
  ```python
  inputs = {}
  self.submit(cls, **inputs)
  ```
  The returned error message was that one of the required inputs was not defined.
  Now it will correctly raise a `TypeError` saying that positional arguments are not supported.
- Process functions: Add serialization for Python base type defaults [[#5744]](https://github.com/aiidateam/aiida-core/pull/5744)
  Defining Python base types as defaults, such as:
  ```python
  @calcfunction
  def function(a, b = 5):
      return a + b
  ```
  would raise an exception.
  The default is now automatically serialized, just as an input argument would be upon function call.
- Process control: Reinstate process status for paused/killed processes [[#5754]](https://github.com/aiidateam/aiida-core/pull/5754)
  Regression introduced in `aiida-core==2.1.0` caused the message `Killed through 'verdi process list'` to no longer be set on the `process_status` of the node.
- `QueryBuilder`: use a nested session in `iterall` and `iterdict` [[#5736]](https://github.com/aiidateam/aiida-core/pull/5736)
  Modifying entities yielded by `QueryBuilder.iterall` and `QueryBuilder.iterdict` would raise an exception, for example:
  ```python
  for [node] in QueryBuilder().append(Node).iterall():
      node.base.extras.set('some', 'extra')
  ```


## v2.1.0 - 2022-11-07

This feature release comes with a number of new features as well as quite a few fixes of bugs and stability issues.
Further down you will find a complete list of changes, after a short description of some of the most important changes:

- [Automatic input serialization in calculation and work functions](#automatic-input-serialization-in-calculation-and-work-functions)
- [Improved interface for creating codes](#improved-interface-for-creating-codes)
- [Support for running code in containers](#support-for-running-code-in-containers)
- [Control daemon and processes from the API](#control-daemon-and-processes-from-the-api)
- [REST API can serve multiple profiles](#rest-api-can-serve-multiple-profiles)
- [Pluginable data storage backends](#pluginable-data-storage-backends)
- [Full list of changes](#full-list-of-changes)

### Automatic input serialization in calculation and work functions

The inputs to `calcfunction`s and `workfunction`s are now automatically converted to AiiDA data types if they are one of the basic Python types (`bool`, `dict`, `Enum`, `float`, `int`, `list` or `str`).
This means that code that looked like:

```python
from aiida.engine import calcfunction
from aiida.orm import Bool, Float, Int, Str

@calcfunction
def function(switch, threshold, count, label):
    ...

function(Bool(True), Float(0.25), Int(10), Str('some-label'))
```

can now be simplified to:

```python
from aiida.engine import calcfunction
from aiida.orm import Bool, Float, Int, Str

@calcfunction
def function(switch, threshold, count, label):
    ...

function(True, 0.25, 10, 'some-label')
```

### Improved interface for creating codes

The `Code` data plugin was a single class that served two different types of codes: "remote" codes and "local" codes.
These names "remote" and "local" have historically caused a lot of confusion.
Likewise, using a single class `Code` for both implementations also has led to confusing interfaces.

To address this issue, the functionality has been split into two new classes [`InstalledCode`](https://aiida.readthedocs.io/projects/aiida-core/en/v2.1.0/topics/data_types.html#installedcode) and [`PortableCode`](https://aiida.readthedocs.io/projects/aiida-core/en/v2.1.0/topics/data_types.html#portablecode), that replace the "remote" and "local" code, respectively.
The installed code represents an executable binary that is already pre-installed on some compute resource.
The portable code represents a code (executable plus any additional required files) that are stored in AiiDA's storage and can be automatically transfered to any computer before being executed.

Creating a new instance of these new code types is easy:
```python
from pathlib import Path
from aiida.orm import InstalledCode, PortableCode

installed_code = InstalledCode(
    label='installed-code',
    computer=load_computer('localhost'),
    filepath_executable='/usr/bin/bash'
)

portable_code = PortableCode(
    label='portable-code',
    filepath_files=Path('/some/path/code'),
    filepath_executable='executable.exe'
)
```

Codes can also be created through the new `verdi` command `verdi code create`.
To specify the type of code to create, pass the corresponding entry point name as an argument.
For example, to create a new installed code, invoke:
```bash
verdi code create core.code.installed
````
The options for each subcommand are automatically generated based on the code type, and so only options that are relevant to that code type will be prompted for.

The new code classes both subclass the `aiida.orm.nodes.data.code.abstract.AbstractCode` base class.
This means that both `InstalledCode`s and `PortableCode`s can be used as the `code` input for `CalcJob`s without problems.

The old `Code` class remains supported for the time being as well, however, it is deprecated and will be remove at some point.
The same goes for the `verdi code setup` command; please use `verdi code create` instead.
Existing codes will be automatically migrated to either an `InstalledCode` or a `PortableCode`.
It is strongly advised that you update any code that creates new codes to use these new plugin types.

### Support for running code in containers

Support is added to run calculation jobs inside a container.
A containerized code can be setup through the CLI:
```bash
verdi code create core.code.containerized \
    --label containerized \
    --image-name docker://alpine:3 \
    --filepath-executable /bin/sh \
    --engine-command "singularity exec --bind $PWD:$PWD {image_name}"
```
as well as through the API:
```python
from aiida.orm import ContainerizedCode, load_computer
code = ContainerizedCode(
    computer=load_computer('some-computer')
    filepath_executable='/bin/sh'
    image_name='docker://alpine:3',
    engine_command='singularity exec --bind $PWD:$PWD {image_name}'
).store()
```
In the example above we use the [Singularity](https://singularity-docs.readthedocs.io/en/latest/) containerization technology.
For more information on what containerization programs are supported and how to configure them, please refer to the [documentation](https://aiida.readthedocs.io/projects/aiida-core/en/v2.1.0/topics/data_types.html#containerizedcode).

### Control daemon and processes from the API

Up till now, the daemon and live processes could only easily be controlled through `verdi daemon` and `verdi process`, respectively.
In this release, modules are added to provide the same functionality through the Python API.

#### Daemon API

The daemon can now be started and stopped through the `DaemonClient` which can be obtained through the `get_daemon_client` utility function:
```python
from aiida.engine.daemon.client import get_daemon_client
client = get_daemon_client()
```
By default, this will give the daemon client for the current default profile.
It is also possible to explicitly specify a profile:
```python
client = get_daemon_client(profile='some-profile')
```
The daemon can be started and stopped through the client:
```python
client.start_daemon()
assert client.is_daemon_running
client.stop_daemon(wait=True)
```

#### Process API

The functionality of `verdi process` to `play`, `pause` and `kill` is now made available through the `aiida.engine.process.control` module.
Processes can be played, paused or killed through the `play_processes`, `pause_processes`, and `kill_processes`, respectively.
The processes to act upon are defined through their `ProcessNode` which can be loaded using `load_node`.
```python
from aiida.engine.process import control

processes = [load_node(<PK1>), load_node(<PK2>)]

pause_processes(processes)  # Pause the processes
play_processes(processes)  # Play them again
kill_processes(processes)  # Kill the processes
```
Instead of specifying an explicit list of processes, the functions also take the `all_entries` keyword argument:
```python
pause_processes(all_entries=True)  # Pause all running processes
```

### REST API can serve multiple profiles

Before, a single REST API could only serve data of a single profile at a time.
This limitation has been removed and a single REST API instance can now serve data from all profiles of an AiiDA instance.
To maintain backwards compatibility, the new functionality needs to be explicitly enabled through the configuration:
```bash
verdi config set rest_api.profile_switching True
```
After the REST API is restarted, it will now accept the `profile` query parameter, for example:
```bash
http://127.0.0.1:5000/api/v4/computers?profile=some-profile-name
````
If the specified is already loaded, the REST API functions exactly as without profile switching enabled.
If another profile is specified, the REST API will first switch profiles before executing the request.

If the profile parameter is specified in a request and the REST API does not have profile switching enabled, a 400 response is returned.

### Pluginable data storage backends

Warning: this is beta functionality.
It is now possible to implement custom storage backends to control where all data of an AiiDA profile is stored.
To provide a data storage plugin, one should implement the `aiida.orm.implementation.storage_backend.StorageBackend` interface.
The default implementation provided by `aiida-core` is the `aiida.storage.psql_dos.backend.PsqlDosBackend` which uses a PostgreSQL database for the provenance graph and a [`disk-objectstore`](https://pypi.org/project/disk-objectstore/) container for repository files.

Storage backend plugins should be registered in the new entry point group `aiida.storage`.
The default storage backend `PsqlDosBackend` has the `core.psql_dos` entry point name.

The storage backend to be used for a profile can be specified using the `--db-backend` option in `verdi setup` and `verdi quicksetup`.
The entry point of the selected backend is stored in the `storage.backend` key of a profile configuration:
```json
{
    "profiles": {
        "profile-name": {
            "PROFILE_UUID": "",
            "storage": {
                "backend": "core.psql_dos",
                "config": {}
            },
            "process_control": {},
            "default_user_email": "aiida@localhost",
            "test_profile": false
        },

}
```

At the moment, it is not quite clear if the abstract interface `StorageBackend` properly abstracts everything that is needed to implement any storage backend.
For the time being then, it is advised to subclass the `PsqlDosBackend` and replace parts required for the use-case, such as just replacing the file repository implementation.


### Full list of changes

#### Features
- `Process`: Add hook to customize the `process_label` attribute [[#5713]](https://github.com/aiidateam/aiida-core/pull/5713)
- Add the `ContainerizedCode` data plugin [[#5667]](https://github.com/aiidateam/aiida-core/pull/5667)
- API: Add the `aiida.engine.processes.control` module [[#5630]](https://github.com/aiidateam/aiida-core/pull/5630)
- `PluginVersionProvider`: Add support for entry point strings [[#5662]](https://github.com/aiidateam/aiida-core/pull/5662)
- `verdi setup`: Add the `--profile-uuid` option [[#5673]](https://github.com/aiidateam/aiida-core/pull/5673)
- Process control: Add the `revive_processes` method [[#5677]](https://github.com/aiidateam/aiida-core/pull/5677)
- Process functions: Add the `get_source_code_function` method [[#4554]](https://github.com/aiidateam/aiida-core/pull/4554)
- CLI: Improve the quality of `verdi code list` output [[#5750]](https://github.com/aiidateam/aiida-core/pull/5750)
- CLI: Add the `verdi devel revive` command [[#5677]](https://github.com/aiidateam/aiida-core/pull/5677)
- CLI: `verdi process status --max-depth` [[#5727]](https://github.com/aiidateam/aiida-core/pull/5727)
- CLI: `verdi setup/quicksetup` store autofill user info early [[#5729]](https://github.com/aiidateam/aiida-core/pull/5729)
- CLI: Add the `devel launch-add` command [[#5733]](https://github.com/aiidateam/aiida-core/pull/5733)
- CLI: Make filename in `verdi node repo cat` optional for `SinglefileData` [[#5747]](https://github.com/aiidateam/aiida-core/pull/5747)
- CLI: Add the `verdi devel rabbitmq` command group [[#5718]](https://github.com/aiidateam/aiida-core/pull/5718)
- API: Add function to start the daemon [[#5625]](https://github.com/aiidateam/aiida-core/pull/5625)
- `BaseRestartWorkChain`: add the `get_outputs` hook [[#5618]](https://github.com/aiidateam/aiida-core/pull/5618)
- `CalcJob`: extend `retrieve_list` syntax with `depth=None` [[#5651]](https://github.com/aiidateam/aiida-core/pull/5651)
- `CalcJob`: allow wildcards in `stash.source_list` paths [[#5601]](https://github.com/aiidateam/aiida-core/pull/5601)
- Add global config option `rest_api.profile_switching` [[#5054]](https://github.com/aiidateam/aiida-core/pull/5054)
- REST API: make the profile configurable as request parameter [[#5054]](https://github.com/aiidateam/aiida-core/pull/5054)
- `ProcessFunction`: Automatically serialize Python base type inputs [[#5688]](https://github.com/aiidateam/aiida-core/pull/5688)
- `BaseRestartWorkChain`: allow to override priority in `handler_overrides` [[#5546]](https://github.com/aiidateam/aiida-core/pull/5546)
- ORM: add `entry_point` classproperty to `Node` and `Group` [[#5437]](https://github.com/aiidateam/aiida-core/pull/5437)
- Add the `aiida.storage` entry point group [[#5501]](https://github.com/aiidateam/aiida-core/pull/5501)
- Add the config option `storage.sandbox` [[#5501]](https://github.com/aiidateam/aiida-core/pull/5501)
- Add the `InstalledCode` and `PortableCode` data plugins [[#5510]](https://github.com/aiidateam/aiida-core/pull/5510)
- CLI: Add the `verdi code create` command group [[#5510]](https://github.com/aiidateam/aiida-core/pull/5510)
- CLI: Add the `DynamicEntryPointCommandGroup` command group [[#5510]](https://github.com/aiidateam/aiida-core/pull/5510)
- Add a client to connect to RabbitMQ Manamegement HTTP API [[#5718]](https://github.com/aiidateam/aiida-core/pull/5718)
- `LsfScheduler`: add support for `num_machines` [[#5153]](https://github.com/aiidateam/aiida-core/pull/5153)
- `JobResource`: add the `accepts_default_memory_per_machine` [[#5642]](https://github.com/aiidateam/aiida-core/pull/5642)
- `AbstractCode`: add abstraction methods for command line parameters [[#5664]](https://github.com/aiidateam/aiida-core/pull/5664)
- `ArithmeticAddCalculation`: Add the `metadata.options.sleep` input [[#5663]](https://github.com/aiidateam/aiida-core/pull/5663)
- `DaemonClient`: add the `get_env` method [[#5631]](https://github.com/aiidateam/aiida-core/pull/5631)
- Tests: Make daemon fixtures available to plugin packages [[#5701]](https://github.com/aiidateam/aiida-core/pull/5701)
- `verdi plugin list`: Show which exit codes invalidate cache [[#5710]](https://github.com/aiidateam/aiida-core/pull/5710)
- `verdi plugin list`: Show full help for input and output ports  [[#5711]](https://github.com/aiidateam/aiida-core/pull/5711)

#### Fixes
- `ArrayData`: replace `nan` and `inf` with `None` when dumping to JSON [[#5613]](https://github.com/aiidateam/aiida-core/pull/5613)
- Archive: add missing migration of transport entry points [[#5604]](https://github.com/aiidateam/aiida-core/pull/5604)
- `BaseRestartWorkChain`: fix `handler_overrides` ignoring `enabled=False` [[#5598]](https://github.com/aiidateam/aiida-core/pull/5598)
- CLI: allow setting options for config without profiles [[#5544]](https://github.com/aiidateam/aiida-core/pull/5544)
- CLI: normalize use of colors [[#5547]](https://github.com/aiidateam/aiida-core/pull/5547)
- `Config`: fix bug in downgrade past version 6 [[#5528]](https://github.com/aiidateam/aiida-core/pull/5528)
- `DaemonClient`: close `CircusClient` after call [[#5631]](https://github.com/aiidateam/aiida-core/pull/5631)
- Engine: Do not call serializer for `None` values [[#5694]](https://github.com/aiidateam/aiida-core/pull/5694)
- Engine: Do not let `DuplicateSubcriberError` except a `Process` [[#5715]](https://github.com/aiidateam/aiida-core/pull/5715)
- ORM: raise when trying to pickle instance of `Entity` [[#5549]](https://github.com/aiidateam/aiida-core/pull/5549)
- ORM: Return `None` in `get_function_source_code` instead of excepting [[#5730]](https://github.com/aiidateam/aiida-core/pull/5730)
- Fix `get_entry_point` not raising even for duplicate entry points [[#5531]](https://github.com/aiidateam/aiida-core/pull/5531)
- Fix: reference to command in message for `verdi storage maintain` [[#5558]](https://github.com/aiidateam/aiida-core/pull/5558)
- Fix: `is_valid_cache` setter for `ProcessNode`s [[#5583]](https://github.com/aiidateam/aiida-core/pull/5583)
- Fix exception when importing an archive into a profile with many nodes [[#5740]](https://github.com/aiidateam/aiida-core/pull/5740)
- `Profile`: make definition of daemon filepaths dynamic [[#5631]](https://github.com/aiidateam/aiida-core/pull/5631)
- Fixtures: Fix bug in reset of `empty_config` fixture [[#5717]](https://github.com/aiidateam/aiida-core/pull/5717)
- `PsqlDosBackend`: ensure sqla sessions are garbage-collected on `close` [[#5728]](https://github.com/aiidateam/aiida-core/pull/5728)
- `TrajectoryData`: Fix bug in `get_step_data` [[#5734]](https://github.com/aiidateam/aiida-core/pull/5734)
- `ProfileManager`: restart daemon in `clear_profile` [[#5751]](https://github.com/aiidateam/aiida-core/pull/5751)

#### Changes
- Mark relevant `Process` exit codes as `invalidates_cache=True`[[#5709]](https://github.com/aiidateam/aiida-core/pull/5709)
- `TemplatereplacerCalculation`: Change exit codes to be in 300 range [[#5709]](https://github.com/aiidateam/aiida-core/pull/5709)
- Add the prefix `core.` to all storage entry points [[#5501]](https://github.com/aiidateam/aiida-core/pull/5501)
- `CalcJob`: Fully abstract interaction with `AbstractCode` in presubmit [[#5666]](https://github.com/aiidateam/aiida-core/pull/5666)
- CLI: make label the default group list order in `verdi group list` [[#5523]](https://github.com/aiidateam/aiida-core/pull/5523)
- Config: add migration to properly prefix storage backend [[#5501]](https://github.com/aiidateam/aiida-core/pull/5501)
- Move query utils from `aiida.cmdline` to `aiida.tools` [[#5630]](https://github.com/aiidateam/aiida-core/pull/5630)
- `SandboxFolder`: decouple the location from the profile [[#5496]](https://github.com/aiidateam/aiida-core/pull/5496)
- `TemplatereplacerDoublerParser`: rename and generalize implementation [[#5669]](https://github.com/aiidateam/aiida-core/pull/5669)
- `Process`: Allow `None` for input ports that are not required [[#5722]](https://github.com/aiidateam/aiida-core/pull/5722)

#### Dependencies
- RabbitMQ: Remove support for v3.5 and older [[#5718]](https://github.com/aiidateam/aiida-core/pull/5718)
- Relax `wrapt` requirement [[#5607]](https://github.com/aiidateam/aiida-core/pull/5607)
- Set upper limit `werkzeug<2.2` [[#5606]](https://github.com/aiidateam/aiida-core/pull/5606)
- Update requirement `click~=8.1` [[#5504]](https://github.com/aiidateam/aiida-core/pull/5504)

#### Deprecations
- Deprecate `Profile.repository_path` [[#5516]](https://github.com/aiidateam/aiida-core/pull/5516)
- Deprecate: `verdi code setup` and `CodeBuilder` [[#5510]](https://github.com/aiidateam/aiida-core/pull/5510)
- Deprecate the method `aiida.get_strict_version` [[#5512]](https://github.com/aiidateam/aiida-core/pull/5512)
- Remove use of legacy `Code` [[#5510]](https://github.com/aiidateam/aiida-core/pull/5510)

#### Documentation
- Add section on basic performance benchmark with automated benchmark script [[#5724]](https://github.com/aiidateam/aiida-core/pull/5724)
- Add `-U` flag to PostgreSQL database backup command [[#5550]](https://github.com/aiidateam/aiida-core/pull/5550)
- Clarify excepted and killed calculations are not cached [[#5525]](https://github.com/aiidateam/aiida-core/pull/5525)
- Correct snippet for workchain context nested keys [[#5551]](https://github.com/aiidateam/aiida-core/pull/5551)
- Plugin package setup add PEP 621 example [[#5626]](https://github.com/aiidateam/aiida-core/pull/5626)
- Remove note on disk space for caching [[#5534]](https://github.com/aiidateam/aiida-core/pull/5534)
- Remove explicit release tag in Docker image name [[#5671]](https://github.com/aiidateam/aiida-core/pull/5671)
- Remove example REST API extension with POST requests [[#5737]](https://github.com/aiidateam/aiida-core/pull/5737)
- Resubmit a `Process` from a `ProcessNode` [[#5579]](https://github.com/aiidateam/aiida-core/pull/5579)

#### Devops
- Add a notification for nightly workflow on fail [[#5605]](https://github.com/aiidateam/aiida-core/pull/5605)
- CI: Remove `--use-feature` flag in `pip install` of CI [[#5703]](https://github.com/aiidateam/aiida-core/pull/5703)
- Fixtures: Add `started_daemon_client` and `stopped_daemon_client` [[#5631]](https://github.com/aiidateam/aiida-core/pull/5631)
- Fixtures: Add the `entry_points` fixture to dynamically add and remove entry points [[#5745]](https://github.com/aiidateam/aiida-core/pull/5745)
- Refactor: `Process` extract `CalcJob` specific input handling from `Process` [[#5539]](https://github.com/aiidateam/aiida-core/pull/5539)
- Refactor: remove unnecessary use of `tempfile.mkdtemp` [[#5639]](https://github.com/aiidateam/aiida-core/pull/5639)
- Refactor: Remove internal use of various deprecated resources [[#5716]](https://github.com/aiidateam/aiida-core/pull/5716)
- Refactor: Turn `aiida.manage.external.rmq` into a package [[#5718]](https://github.com/aiidateam/aiida-core/pull/5718)
- Tests: remove legacy `tests/utils/configuration.py` [[#5500]](https://github.com/aiidateam/aiida-core/pull/5500)
- Tests: fix the RPN work chains for the nightly build [[#5529]](https://github.com/aiidateam/aiida-core/pull/5529)
- Tests: Manually stop daemon after `verdi devel revive` test [[#5689]](https://github.com/aiidateam/aiida-core/pull/5689)
- Tests: Add verbose info if `submit_and_wait` times out [[#5689]](https://github.com/aiidateam/aiida-core/pull/5689)
- Tests: Do not set default memory for `localhost` fixture [[#5689]](https://github.com/aiidateam/aiida-core/pull/5689)
- Tests: Suppress RabbitMQ and developer version warnings [[#5689]](https://github.com/aiidateam/aiida-core/pull/5689)
- Tests: Add the `EntryPointManager` exposed as `entry_points` fixture [[#5656]](https://github.com/aiidateam/aiida-core/pull/5656)
- Tests: Only reset database connection at end of suite [[#5641]](https://github.com/aiidateam/aiida-core/pull/5641)
- Tests: Suppress logging and warnings from temporary profile fixture [[#5702]](https://github.com/aiidateam/aiida-core/pull/5702)


## v2.0.4 - 2022-09-22

[Full changelog](https://github.com/aiidateam/aiida-core/compare/v2.0.3...v2.0.4)

### Fixes
- Engine: Fix bug that allowed non-storable inputs to be passed to process [[#5532]](https://github.com/aiidateam/aiida-core/pull/5532)
- Engine: Fix bug when caching from process with nested outputs [[#5538]](https://github.com/aiidateam/aiida-core/pull/5538)
- Archive: Fix bug in archive creation after packing of file repository [[#5570]](https://github.com/aiidateam/aiida-core/pull/5570)
- `QueryBuilder`: apply escape `\` in `like` and `ilike` for a `sqlite` backend, such as export archives [[#5553]](https://github.com/aiidateam/aiida-core/pull/5553)
- `QueryBuilder`: Fix bug in distinct queries always projecting the first entity, even if not projected explicitly [[#5654]](https://github.com/aiidateam/aiida-core/pull/5654)
- `CalcJob`: fix bug in `local_copy_list` provenance exclusion [[#5648]](https://github.com/aiidateam/aiida-core/pull/5648)
- `Repository.copy_tree`: omit subdirectories from `path` when copying [[#5648]](https://github.com/aiidateam/aiida-core/pull/5648)
- Docs: Add intersphinx aliases for `__all__` imports. Now the shortcut imports can also be used in third-party packages (e.g. `aiida.orm.nodes.node.Node` as well as `aiida.orm.Node`) [[#5657]](https://github.com/aiidateam/aiida-core/pull/5657)


## v2.0.3 - 2022-08-09

[Full changelog](https://github.com/aiidateam/aiida-core/compare/v2.0.2...v2.0.3)

Update of the Dockerfile base image (`aiidateam/aiida-prerequisites`) to version `0.6.0`.


## v2.0.2 - 2022-07-13

[Full changelog](https://github.com/aiidateam/aiida-core/compare/v2.0.1...v2.0.2)

### Fixes
- REST API: treat `false` as `False` in URL parsing [[#5573]](https://github.com/aiidateam/aiida-core/pull/5573)
- REST API: add support for byte streams through a custom JSON encoder [[#5576]](https://github.com/aiidateam/aiida-core/pull/5576)


## v2.0.1 - 2022-04-28

[Full changelog](https://github.com/aiidateam/aiida-core/compare/v2.0.0...v2.0.1)

### Dependencies
- Fix incompatibility with `click>=8.1` and require `click==8.1` as a minimum by @sphuber in [[#5504]](https://github.com/aiidateam/aiida-core/pull/5504)


## v2.0.0 - 2022-04-27

[Full changelog](https://github.com/aiidateam/aiida-core/compare/v2.0.0b1...v2.0.0)

This release finalises the [v2.0.0b1 changes](release/2.0.0b1).

### Node namespace restructuring ♻️

:::{note}
The restructuring is fully back-compatible, and existing methods/attributes will continue to work, until aiida-core `v3.0`.

Deprecations warnings are also currently turned **off** by default.
To identify these deprecations in your code base (for example when running unit tests), activate the `AIIDA_WARN_v3` environmental variable:

```bash
export AIIDA_WARN_v3=1
```

:::

The `Node` class (and thus its subclasses) has many methods and attributes in its public namespace.
This has been noted [as being a problem](https://github.com/aiidateam/aiida-core/issues/4976) for those using auto-completion,
since it makes it difficult to select suitable methods and attributes.

These methods/attributes have now been partitioned into "sub-namespaces" for specific purposes:

`Node.base.attributes`
: Interface to the attributes of a node instance.

`Node.base.caching`
: Interface to control caching of a node instance.

`Node.base.comments`
: Interface for comments of a node instance.

`Node.base.extras`
: Interface to the extras of a node instance.

`Node.base.links`
: Interface for links of a node instance.

`Node.base.repository`
: Interface to the file repository of a node instance.

:::{dropdown} Full list of re-naming

| Current name                | New name                                        |
| --------------------------- | ----------------------------------------------- |
| `Collection`                | Deprecated, use `NodeCollection` directly       |
| `add_comment`               | `Node.base.comments.add`                        |
| `add_incoming`              | `Node.base.links.add_incoming`                  |
| `attributes`                | `Node.base.attributes.all`                      |
| `attributes_items`          | `Node.base.attributes.items`                    |
| `attributes_keys`           | `Node.base.attributes.keys`                     |
| `check_mutability`          | `Node._check_mutability_attributes`             |
| `clear_attributes`          | `Node.base.attributes.clear`                    |
| `clear_extras`              | `Node.base.extras.clear`                        |
| `clear_hash`                | `Node.base.caching.clear_hash`                  |
| `copy_tree`                 | `Node.base.repository.copy_tree`                |
| `delete_attribute`          | `Node.base.attributes.delete`                   |
| `delete_attribute_many`     | `Node.base.attributes.delete_many`              |
| `delete_extra`              | `Node.base.extras.delete`                       |
| `delete_extra_many`         | `Node.base.extras.delete_many`                  |
| `delete_object`             | `Node.base.repository.delete_object`            |
| `erase`                     | `Node.base.repository.erase`                    |
| `extras`                    | `Node.base.extras.all`                          |
| `extras_items`              | `Node.base.extras.items`                        |
| `extras_keys`               | `Node.base.extras.keys`                         |
| `get`                       | Deprecated, use `Node.objects.get`              |
| `get_all_same_nodes`        | `Node.base.caching.get_all_same_nodes`          |
| `get_attribute`             | `Node.base.attributes.get`                      |
| `get_attribute_many`        | `Node.base.attributes.get_many`                 |
| `get_cache_source`          | `Node.base.caching.get_cache_source`            |
| `get_comment`               | `Node.base.comments.get`                        |
| `get_comments`              | `Node.base.comments.all`                        |
| `get_extra`                 | `Node.base.extras.get`                          |
| `get_extra_many`            | `Node.base.extras.get_many`                     |
| `get_hash`                  | `Node.base.caching.get_hash`                    |
| `get_incoming`              | `Node.base.links.get_incoming`                  |
| `get_object`                | `Node.base.repository.get_object`               |
| `get_object_content`        | `Node.base.repository.get_object_content`       |
| `get_outgoing`              | `Node.base.links.get_outgoing`                  |
| `get_stored_link_triples`   | `Node.base.links.get_stored_link_triples`       |
| `glob`                      | `Node.base.repository.glob`                     |
| `has_cached_links`          | `Node.base.caching.has_cached_links`            |
| `id`                        | Deprecated, use `pk`                            |
| `is_created_from_cache`     | `Node.base.caching.is_created_from_cache`       |
| `is_valid_cache`            | `Node.base.caching.is_valid_cache`              |
| `list_object_names`         | `Node.base.repository.list_object_names`        |
| `list_objects`              | `Node.base.repository.list_objects`             |
| `objects`                   | `collection`                                    |
| `open`                      | `Node.base.repository.open`                     |
| `put_object_from_file`      | `Node.base.repository.put_object_from_file`     |
| `put_object_from_filelike`  | `Node.base.repository.put_object_from_filelike` |
| `put_object_from_tree`      | `Node.base.repository.put_object_from_tree`     |
| `rehash`                    | `Node.base.caching.rehash`                      |
| `remove_comment`            | `Node.base.comments.remove`                     |
| `repository_metadata`       | `Node.base.repository.metadata`                 |
| `repository_serialize`      | `Node.base.repository.serialize`                |
| `reset_attributes`          | `Node.base.attributes.reset`                    |
| `reset_extras`              | `Node.base.extras.reset`                        |
| `set_attribute`             | `Node.base.attributes.set`                      |
| `set_attribute_many`        | `Node.base.attributes.set_many`                 |
| `set_extra`                 | `Node.base.extras.set`                          |
| `set_extra_many`            | `Node.base.extras.set_many`                     |
| `update_comment`            | `Node.base.comments.update`                     |
| `validate_incoming`         | `Node.base.links.validate_incoming`             |
| `validate_outgoing`         | `Node.base.links.validate_outgoing`             |
| `validate_storability`      | `Node._validate_storability`                    |
| `verify_are_parents_stored` | `Node._verify_are_parents_stored`               |
| `walk`                      | `Node.base.repository.walk`                     |

:::

### IPython integration improvements 👌

The `aiida` [IPython magic commands](https://ipython.readthedocs.io/en/stable/interactive/magics.html) are now available to load via:

```ipython
%load_ext aiida
```

As well as the previous `%aiida` magic command, to load a profile,
one can also use the `%verdi` magic command.
This command runs the `verdi` CLI using the currently loaded profile of the IPython/Jupyter session.

```ipython
%verdi status
```

See the [Basic Tutorial](docs/source/tutorials/basic.md) for example usage.

### New `SqliteTempBackend` ✨

The `SqliteTempBackend` utilises an in-memory SQLite database to store data, allowing it to be transiently created/destroyed within a single Python session, without the need for Postgresql.

As such, it is useful for demonstrations and testing purposes, whereby no persistent storage is required.

To load a temporary profile, you can use the following code:

```python
from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

profile = load_profile(
    SqliteTempBackend.create_profile(
        'myprofile',
        options={
            'runner.poll.interval': 1
        },
        debug=False
    ),
)
```

See the [Basic Tutorial](docs/source/tutorials/basic.md) for example usage.

### Key Pull Requests

Below is a list of some key pull requests that have been merged into version 2.0.0:

- Node namespace re-structuring:
  - 🔧 MAINTAIN: Add `warn_deprecation` function, `Node.base`, and move `NodeRepositoryMixin -> NodeRepository` by @chrisjsewell in [#5472](https://github.com/aiidateam/aiida-core/pull/5472)
  - ♻️ REFACTOR: `EntityAttributesMixin` -> `NodeAttributes` by @chrisjsewell in [#5442](https://github.com/aiidateam/aiida-core/pull/5442)
  - ♻️ REFACTOR: Move methods to `Node.comments` by @chrisjsewell in [#5446](https://github.com/aiidateam/aiida-core/pull/5446)
  - ♻️ REFACTOR: `EntityExtrasMixin` -> `EntityExtras` by @chrisjsewell in [#5445](https://github.com/aiidateam/aiida-core/pull/5445)
  - ♻️ REFACTOR: Move link related methods to `Node.base.links` by @sphuber in [#5480](https://github.com/aiidateam/aiida-core/pull/5480)
  - ♻️ REFACTOR: Move caching related methods to `Node.base.caching` by @sphuber in [#5483](https://github.com/aiidateam/aiida-core/pull/5483)

- Storage:
  - ✨ NEW: Add SqliteTempBackend by @chrisjsewell in [#5448](https://github.com/aiidateam/aiida-core/pull/5448)
  - 👌 IMPROVE: Move default user caching to `StorageBackend` by @chrisjsewell in [#5460](https://github.com/aiidateam/aiida-core/pull/5460)
  - 👌 IMPROVE: Add JSON filtering for SQLite backends by @chrisjsewell in [#5448](https://github.com/aiidateam/aiida-core/pull/5448)

- ORM:
  - 👌 IMPROVE: `StructureData`: allow to be initialised without a specified cell by @ltalirz in [#5341](https://github.com/aiidateam/aiida-core/pull/5341)

- Processing:
  - 👌 IMPROVE: Allow `engine.run` to work without RabbitMQ by @chrisjsewell in [#5448](https://github.com/aiidateam/aiida-core/pull/5448)
  - 👌 IMPROVE: `JobTemplate`: change `CodeInfo` to `JobTemplateCodeInfo` in `codes_info` by @unkcpz in [#5350](https://github.com/aiidateam/aiida-core/pull/5350)
    - This is required for a containerized code implementation
  - 👌 IMPROVE: Add option to use double quotes for `Code` and `Computer` CLI arguments by @unkcpz in [#5478](https://github.com/aiidateam/aiida-core/pull/5478)

- Transport and Scheduler:
  - 👌 IMPROVE: `SlurmScheduler`: Parse out-of-walltime and out-of-memory errors from `stderr` by @sphuber in [#5458](https://github.com/aiidateam/aiida-core/pull/5458)
  - 👌 IMPROVE: `CalcJob`: always call `Scheduler.parse_output` by @sphuber in [#5458](https://github.com/aiidateam/aiida-core/pull/5458)
  - 👌 IMPROVE: `Computer`: fallback on transport for `get_minimum_job_poll_interval` default by @sphuber in [#5457](https://github.com/aiidateam/aiida-core/pull/5457)

- IPython:
  - ✨ NEW: Add `%verdi` IPython magic by @chrisjsewell in [#5448](https://github.com/aiidateam/aiida-core/pull/5448)

- Dependencies:
  - ♻️ REFACTOR: drop the `python-dateutil` library by @sphuber

(release/2.0.0b1)=
## v2.0.0b1 - 2022-03-15

[Full changelog](https://github.com/aiidateam/aiida-core/compare/v1.6.7...v2.0.0b1)

The version 2 release of `aiida-core` largely focusses on major improvements to the design of data storage within AiiDA, as well as updates to core dependencies and removal of deprecated APIs.

Assuming users have already addressed deprecation warnings from `aiida-core` v1.6.x, there should be limited impact on existing code.
For plugin developers, the [AiiDA 2.0 plugin migration guide](https://github.com/aiidateam/aiida-core/wiki/AiiDA-2.0-plugin-migration-guide) provides a step-by-step guide on how to update their plugins.

For existing profiles and archives, a migration will be required, before they are compatible with the new version.

:::{tip}
Before updating your `aiida-core` installation, it is advisable to make sure you create a full backup of your profiles,
using the current version of `aiida-core` you have installed.
For backup instructions, using aiida-core v1.6.7, see [this documentation](https://aiida.readthedocs.io/projects/aiida-core/en/v1.6.7/howto/installation.html#backing-up-your-installation).
:::

### Python support updated to 3.8 - 3.10 ⬆️

Following the [NEP 029](https://numpy.org/neps/nep-0029-deprecation_policy.html) timeline, support for Python 3.7 is dropped as of December 26 2021, and support for Python 3.10 is added.

### Plugin entry point updates 🧩

AiiDA's use of entry points, to allow plugins to extend the functionality of AiiDA, is described in the [plugins topic section](docs/source/topics/plugins.rst).

The use of `reentry scan`, for loading plugin entry points, is no longer necessary.

Use of the [reentry](https://pypi.org/project/reentry/) dependency has been replaced by the built-in [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html) library.
This library requires no additional loading step.

All entry points provided by `aiida-core` now start with a `core.` prefix, to make their origin more explicit and respect the naming guidelines of entry points in the AiiDA ecosystem.
The old names are still supported so as to not suddenly break existing code based on them, but they have now been deprecated.
For example:

```python
from aiida.plugins import DataFactory
Int = DataFactory('int')  # Old name
Int = DataFactory('core.int')  # New name
```

Note that entry point names are also used on the command line. For example:

```console
$ verdi computer setup -L localhost -T local -S direct
# now changed to
$ verdi computer setup -L localhost -T local -S core.direct
```

### Improvements to the AiiDA storage architecture ♻️

Full details on the AiiDA storage architecture are available in the [storage architecture section](docs/source/internals/storage/architecture.rst).

The storage refactor incorporates four major changes:

- The `django` and `sqlalchemy` storage backends have been merged into a single `psql_dos` backend (PostgreSQL + Disk-Objectstore).
  - See the [`psql_dos` storage format](docs/source/internals/storage/psql_dos.rst) for details.
  - This has allowed for the `django` dependency to be dropped.

- The file system node repository has been replaced with an object store implementation.
  - The object store automatically deduplicates files, and allows for the compression of many objects into a single file, thus significantly reducing the number of files on the file system and memory utilisation (by orders of magnitude).
  - Note, to make full use of object compression, one should periodically run `verdi storage maintain`.
  - See the [repository design section](docs/source/internals/storage/repository.rst) for details.

- Command-line interaction with a profile's storage has been moved from `verdi database` to `verdi storage`.

- The AiiDA archive format has been redesigned as the `sqlite_zip` storage backend.
  - See the [`sqlite_zip` storage format](docs/source/internals/storage/sqlite_zip.rst) for details.
  - The new format allows for streaming of data during exports and imports, significantly reducing both the time and memory utilisation of these actions.
  - The archive can now be loaded directly as a (read-only) profile, without the need to import it first, see [this Jupyter Notebook tutorial](docs/source/howto/archive_profile.md).

The storage redesign also allows for profile switching, within the same Python process, and profile access within a context manager.
For example:

```python
from aiida import load_profile, profile_context, orm

with profile_context('my_profile_1'):
    # The profile will be loaded within the context
    node_from_profile_1 = orm.load_node(1)
    # then the profile will be unloaded automatically

# load a global profile
load_profile('my_profile_2')
node_from_profile_2 = orm.load_node(1)

# switch to a different global profile
load_profile('my_profile_3', allow_switch=True)
node_from_profile_3 = orm.load_node(1)
```

See [How to interact with AiiDA](docs/source/howto/interact.rst) for more details.

On first using `aiida-core` v2.0, your AiiDA configuration will be automatically migrated to the new version (this can be reverted by `verdi config downgrade`).
To update existing profiles and archives to the new storage formats, simply use `verdi storage migrate` and `verdi archive migrate`, respectively.

:::{important}
The migration of large storage repositories is a potentially time-consuming process.
It may take several hours to complete, depending on the size of the repository.
It is also advisable to make a full manual backup of any AiiDA setup with important data: see [the installation management section](docs/source/howto/installation.rst) for more information.

See also this [testing of profile migrations](https://github.com/aiidateam/aiida-core/discussions/5379), for some indicative timings.
:::

### Improvements to the AiiDA ORM 👌

#### Node repository

Inline with the storage improvements, {class}`~aiida.orm.Node` methods associated with the repository have some backwards incompatible changes:

:::{dropdown} `Node` repository method changes

Altered:

- `FileType`: moved from `aiida.orm.utils.repository` to `aiida.repository.common`
- `File`: moved from `aiida.orm.utils.repository` to `aiida.repository.common`
- `File`: changed from namedtuple to class
- `File`: can no longer be iterated over
- `File`: `type` attribute was renamed to `file_type`
- `Node.put_object_from_tree`: `path` argument was renamed to `filepath`
- `Node.put_object_from_file`: `path` argument was renamed to `filepath`
- `Node.put_object_from_tree`: `key` argument was renamed to `path`
- `Node.put_object_from_file`: `key` argument was renamed to `path`
- `Node.put_object_from_filelike`: `key` argument was renamed to `path`
- `Node.get_object`: `key` argument was renamed to `path`
- `Node.get_object_content`: `key` argument was renamed to `path`
- `Node.open`: `key` argument was renamed to `path`
- `Node.list_objects`: `key` argument was renamed to `path`
- `Node.list_object_names`: `key` argument was renamed to `path`
- `SinglefileData.open`: `key` argument was renamed to `path`
- `Node.open`: can no longer be called without context manager
- `Node.open`: only mode `r` and `rb` are supported, [use `put_object_from_` methods instead](https://github.com/aiidateam/aiida-core/issues/4721#issuecomment-920100415)
- `Node.get_object_content`: only mode `r` and `rb` are supported
- `Node.put_object_from_tree`: argument `contents_only` was removed
- `Node.put_object_from_tree`: argument `force` was removed
- `Node.put_object_from_file`: argument `force` was removed
- `Node.put_object_from_filelike`: argument `force` was removed
- `Node.delete_object`: argument `force` was removed

Added:

- `Node.walk`
- `Node.copy_tree`
- `Node.is_valid_cache` setter
- `Node.objects.iter_repo_keys`

Additionally, `Node.open` should always be used as a context manager, for example:

```python
with node.open('filename.txt') as handle:
    content = handle.read()
```

:::

#### QueryBuilder

When using the {class}`~aiida.orm.QueryBuilder` to query the database, the following changes have been made:

- The `Computer`'s `name` field is now replaced with `label` (as previously deprecated in v1.6)
- The `QueryBuilder.queryhelp` attribute is deprecated, for the `as_dict` (and `from_dict`) methods
- The `QueryBuilder.first` method now allows the `flat` argument, which will return a single item, instead of a list of one item, if only a single projection is defined.

For example:

```python
from aiida.orm import QueryBuilder, Computer
query = QueryBuilder().append(Computer, filters={'label': 'localhost'}, project=['label']).as_dict()
QueryBuilder.from_dict(query).first(flat=True)  # -> 'localhost'
```

For further information, see [How to find and query for data](docs/source/howto/query.rst).

#### Dict usage

The {class}`~aiida.orm.Dict` class has been updated to support more native `dict` behaviour:

- Initialisation can now use `Dict({'a': 1})`, instead of `Dict(dict={'a': 1})`. This is also the case for `List([1, 2])`.
- Equality (`==`/`!=`) comparisons now compare the dictionaries, rather than the UUIDs
- The contains (`in`) operator now returns `True` if the dictionary contains the key
- The `items` method iterates a list of `(key, value)` pairs

For example:

```python
from aiida.orm import Dict

d1 = Dict({'a': 1})
d2 = Dict({'a': 1})

assert d1.uuid != d2.uuid
assert d1 == d2
assert not d1 != d2

assert 'a' in d1

assert list(d1.items()) == [('a', 1)]
```

#### New data types

Two new built-in data types have been added:

{class}`~aiida.orm.EnumData`
: A data plugin that wraps a Python `enum.Enum` instance.

{class}`~aiida.orm.JsonableData`
: A data plugin that allows one to easily wrap existing objects that are JSON-able (via an `as_dict` method).

See the [data types section](docs/source/topics/data_types.rst) for more information.

### Improvements to the AiiDA process engine 👌

#### CalcJob API

A number of minor improvements have been made to the `CalcJob` API:

- Both numpy arrays and `Enum` instances can now be serialized on process checkpoints.
- The `Calcjob.spec.metadata.options.rerunnable` option allows to specify whether the calculation can be rerun or requeued (dependent on the scheduler). Note, this should only be applied for idempotent codes.
- The `Calcjob.spec.metadata.options.environment_variables_double_quotes` option allows for double-quoting of environment variable declarations. In particular, this allows for use of the `$` character in the environment variable name, e.g. `export MY_FILE="$HOME/path/my_file"`.
- `CalcJob.local_copy_list` now allows for specifying entire directories to be copied to the local computer, in addition to individual files. Note that the directory itself won't be copied, just its contents.
- `WorkChain.to_context` now allows `.` delimited namespacing, which generate nested dictionaries. See [Nested context keys](docs/source/topics/workflows/usage.rst) for more information.

#### Importing existing computations

The new `CalcJobImporter` class has been added, to define importers for computations completed outside of AiiDA.
These can help onboard new users to your AiiDA plugin.
For more information, see [Writing importers for existing computations](docs/source/howto/plugin_codes.rst).

#### Scheduler plugins

Plugin's implementation of `Scheduler._get_submit_script_header` should now utilise `Scheduler._get_submit_script_environment_variables`, to format environment variable declarations, rather than handling it themselves. See the exemplar changes in [#5283](https://github.com/aiidateam/aiida-core/pull/5283).

The `Scheduler.get_valid_transports()` method has also been removed, use `get_entry_point_names('aiida.schedulers')` instead (see {func}`~aiida.plugins.entry_point.get_entry_point_names`).

See [Scheduler plugins](docs/source/topics/schedulers.rst) for more information.

#### Transport plugins

The `SshTransport` now supports the SSH `ProxyJump` option, for tunnelling through other SSH hosts.
See [How to setup SSH connections](docs/source/howto/ssh.rst) for more information.

Transport plugins now support also transferring bytes (rather than only Unicode strings) in the stdout/stderr of "remote" commands (see [#3787](https://github.com/aiidateam/aiida-core/pull/3787)).
The required changes for transport plugins:

- rename the `exec_command_wait` function in your plugin implementation with `exec_command_wait_bytes`
- ensure the method signature follows {meth}`~aiida.transports.transport.Transport.exec_command_wait_bytes`, and that `stdin` accepts a `bytes` object.
- return bytes for stdout and stderr (most probably internally you are already getting bytes - just do not decode them to strings)

For an exemplar implementation, see {meth}`~aiida.transports.plugins.local.LocalTransport.exec_command_wait_bytes`,
or see [Transport plugins](docs/source/topics/transport.rst) for more information.

The `Transport.get_valid_transports()` method has also been removed, use `get_entry_point_names('aiida.transports')` instead (see {func}`~aiida.plugins.entry_point.get_entry_point_names`).

### Improvements to the AiiDA command-line 👌

The AiiDA command-line interface (CLI) can now be accessed as both `verdi` and `/path/to/bin/python -m aiida`.

The underlying dependency for this CLI, `click`, has been updated to version 8, which contains built-in tab-completion support, to replace the old `click-completion`.
The completion works the same, except that the string that should be put in the activation script to enable it is now shell-dependent.
See [Activating tab-completion](docs/source/howto/installation.rst) for more information.

Logging for the CLI has been updated, to standardise its use across all CLI commands.
This means that all commands include the option:

```console
  -v, --verbosity [notset|debug|info|report|warning|error|critical]
                                  Set the verbosity of the output.
```

By default the verbosity is set to `REPORT` (see `verdi config list`), which relates to using `Logger.report`, as defined in {func}`~aiida.common.log.report`.

The following specific changes and improvements have been made to the CLI commands:

`verdi storage` (replaces `verdi database`)
: This command group replaces the `verdi database` command group, which is now deprecated, in order to represent its interaction with the full profile storage (not just database).
: `verdi storage info` provides information about the entities contained for a profile.
: `verdi storage maintain` has also been added, to allow for maintenance of the storage, for example, to optimise the storage size.

`verdi archive version` and `verdi archive info` (replace `verdi archive inspect`)
: This change synchronises the commands with the new `verdi storage version` and `verdi storage info` commands.

`verdi group move-nodes`
: This command moves nodes from a source group to a target group (removing them from one and adding them to the other).

`verdi code setup`
: There is a small change to the order of prompts, in interactive mode.
: The uniqueness of labels is now validated, for both remote and local codes.

`verdi code test`
: Run tests for a given code to check whether it is usable, including whether remote executable files are available.

See [AiiDA Command Line](docs/source/reference/command_line.rst) for more information.

### Development improvements

The build tool for `aiida-core` has been changed from `setuptools` to [`flit`](https://github.com/pypa/flit).
This allows for the project metadata to be fully specified in the `pyproject.toml` file, using the [PEP 621](https://www.python.org/dev/peps/pep-0621) format.
Note, editable installs (using the `-e` flag for `pip install`) of `aiida-core` now require `pip>=21`.

[Type annotations](https://peps.python.org/pep-0526/) have been added to most of the code base.
Plugin developers can use [mypy](https://mypy.readthedocs.io) to check their code against the new type annotations.

All module level imports are now defined explicitly in `__all__`.
See [Overview of public API](docs/source/reference/api/public.rst) for more information.

The `aiida.common.json` module is now deprecated.
Use the `json` standard library instead.

#### Changes to the plugin test fixtures 🧪

The deprecated `AiidaTestCase` class has been removed, in favour of the AiiDA pytest fixtures, which can be loaded in your `conftest.py` using:

```python
pytest_plugins = ['aiida.manage.tests.pytest_fixtures']
```

The fixtures `clear_database`, `clear_database_after_test`, `clear_database_before_test` are now deprecated, in favour of the `aiida_profile_clean` fixture, which ensures (before the test) the default profile is reset with clean storage, and that all previous resources are closed
If you only require the profile to be reset before a class of tests, then you can use `aiida_profile_clean_class`.

### Key Pull Requests

Below is a list of some key pull requests that have been merged into version `2.0.0b1`:

- Storage and migrations:
  - ♻️ REFACTOR: Implement the new file repository by @sphuber in [#4345](https://github.com/aiidateam/aiida-core/pull/4345)
  - ♻️ REFACTOR: New archive format by @chrisjsewell in [#5145](https://github.com/aiidateam/aiida-core/pull/5145)
  - ♻️ REFACTOR: Remove `QueryManager` by @chrisjsewell in [#5101](https://github.com/aiidateam/aiida-core/pull/5101)
  - ♻️ REFACTOR: Fully abstract QueryBuilder by @chrisjsewell in [#5093](https://github.com/aiidateam/aiida-core/pull/5093)
  - ✨ NEW: Add `Backend` bulk methods by @chrisjsewell in [#5171](https://github.com/aiidateam/aiida-core/pull/5171)
  - ⬆️ UPDATE: SQLAlchemy v1.4 (v2 API) by @chrisjsewell in [#5103](https://github.com/aiidateam/aiida-core/pull/5103) and [#5122](https://github.com/aiidateam/aiida-core/pull/5122)
  - 👌 IMPROVE: Configuration migrations by @chrisjsewell in [#5319](https://github.com/aiidateam/aiida-core/pull/5319)
  - ♻️ REFACTOR: Remove Django storage backend by @chrisjsewell in [#5330](https://github.com/aiidateam/aiida-core/pull/5330)
  - ♻️ REFACTOR: Move archive backend to `aiida/storage` by @chrisjsewell in [5375](https://github.com/aiidateam/aiida-core/pull/5375)
  - 👌 IMPROVE: Use `sqlalchemy.func` for JSONB QB filters by @ltalirz in [#5393](https://github.com/aiidateam/aiida-core/pull/5393)
  - ✨ NEW: Add Mechanism to lock profile access by @ramirezfranciscof in [#5270](https://github.com/aiidateam/aiida-core/pull/5270)
  - ✨ NEW: Add `verdi storage` CLI by @ramirezfranciscof in [#4965](https://github.com/aiidateam/aiida-core/pull/4965) and [#5156](https://github.com/aiidateam/aiida-core/pull/5156)

- ORM API:
  - ♻️ REFACTOR: Add the `core.` prefix to all entry points by @sphuber in [#5073](https://github.com/aiidateam/aiida-core/pull/5073)
  - 👌 IMPROVE: Replace `InputValidationError` with `ValueError` and `TypeError` by @sphuber in [#4888](https://github.com/aiidateam/aiida-core/pull/4888)
  - 👌 IMPROVE: Add `Node.walk` method to iterate over repository content by @sphuber in [#4935](https://github.com/aiidateam/aiida-core/pull/4935)
  - 👌 IMPROVE: Add `Node.copy_tree` method  by @sphuber in [#5114](https://github.com/aiidateam/aiida-core/pull/5114)
  - 👌 IMPROVE: Add `Node.is_valid_cache` setter property  by @sphuber in [#5114](https://github.com/aiidateam/aiida-core/pull/5207)
  - 👌 IMPROVE: Add `Node.objects.iter_repo_keys` by @chrisjsewell in [#5114](https://github.com/aiidateam/aiida-core/pull/4922)
  - 👌 IMPROVE: Allow storing `Decimal` in `Node.attributes` by @dev-zero in [#4964](https://github.com/aiidateam/aiida-core/pull/4964)
  - 🐛 FIX: Initialising a `Node` with a `User` by @chrisjsewell in [#5114](https://github.com/aiidateam/aiida-core/pull/4977)
  - 🐛 FIX: Deprecate double underscores in `LinkManager` contains by @sphuber in [#5067](https://github.com/aiidateam/aiida-core/pull/5067)
  - ♻️ REFACTOR: Rename `name` field of `Computer` to `label` by @sphuber in [#4882](https://github.com/aiidateam/aiida-core/pull/4882)
  - ♻️ REFACTOR: `QueryBuilder.queryhelp` -> `QueryBuilder.as_dict` by @chrisjsewell in [#5081](https://github.com/aiidateam/aiida-core/pull/5081)
  - 👌 IMPROVE: Add `AuthInfo` joins to `QueryBuilder` by @chrisjsewell in [#5195](https://github.com/aiidateam/aiida-core/pull/5195)
  - 👌 IMPROVE: `QueryBuilder.first` add `flat` keyword by @sphuber in [#5410](https://github.com/aiidateam/aiida-core/pull/5410)
  - 👌 IMPROVE: Add `Computer.default_memory_per_machine` attribute by @yakutovicha in [#5260](https://github.com/aiidateam/aiida-core/pull/5260)
  - 👌 IMPROVE: Add `Code.validate_remote_exec_path` method to check executable by @sphuber in [#5184](https://github.com/aiidateam/aiida-core/pull/5184)
  - 👌 IMPROVE: Allow `source` to be passed as a keyword to `Data.__init__` by @sphuber in [#5163](https://github.com/aiidateam/aiida-core/pull/5163)
  - 👌 IMPROVE: `Dict.__init__` and `List.__init__` by @mbercx in [#5165](https://github.com/aiidateam/aiida-core/pull/5165)
  - ‼️ BREAKING: Compare `Dict` nodes by content by @mbercx in [#5251](https://github.com/aiidateam/aiida-core/pull/5251)
  - 👌 IMPROVE: Implement the `Dict.__contains__` method by @sphuber in [#5251](https://github.com/aiidateam/aiida-core/pull/5328)
  - 👌 IMPROVE: Implement `Dict.items()` method by @mbercx in [#5251](https://github.com/aiidateam/aiida-core/pull/5333)
  - 🐛 FIX: `BandsData.show_mpl` allow NaN values by @PhilippRue in [#5024](https://github.com/aiidateam/aiida-core/pull/5024)
  - 🐛 FIX: Replace `KeyError` with `AttributeError` in `TrajectoryData` methods by @Crivella in [#5015](https://github.com/aiidateam/aiida-core/pull/5015)
  - ✨ NEW: `EnumData` data plugin by @sphuber in [#5225](https://github.com/aiidateam/aiida-core/pull/5225)
  - ✨ NEW: `JsonableData` data plugin by @sphuber in [#5017](https://github.com/aiidateam/aiida-core/pull/5017)
  - 👌 IMPROVE: Register `List` class with `to_aiida_type` dispatch by @sphuber in [#5142](https://github.com/aiidateam/aiida-core/pull/5142)
  - 👌 IMPROVE: Register `EnumData` class with `to_aiida_type` dispatch by @sphuber in [#5314](https://github.com/aiidateam/aiida-core/pull/5314)

- Processing:
  - ✨ NEW: `CalcJob.get_importer()` to import existing calculations, run outside of AiiDA by @sphuber in [#5086](https://github.com/aiidateam/aiida-core/pull/5086)
  - ✨ NEW: `ProcessBuilder._repr_pretty_` ipython representation by @mbercx in [#4970](https://github.com/aiidateam/aiida-core/pull/4970)
  - 👌 IMPROVE: Allow `Enum` types to be serialized on `ProcessNode.checkpoint` by @sphuber in [#5218](https://github.com/aiidateam/aiida-core/pull/5218)
  - 👌 IMPROVE: Allow numpy arrays to be serialized on `ProcessNode.checkpoint` by @greschd in [#4730](https://github.com/aiidateam/aiida-core/pull/4730)
  - 👌 IMPROVE: Add `Calcjob.spec.metadata.options.rerunnable` to requeue/rerun calculations by @greschd in [#4707](https://github.com/aiidateam/aiida-core/pull/4707)
  - 👌 IMPROVE: Add `Calcjob.spec.metadata.options.environment_variables_double_quotes` to escape environment variables by @unkcpz in [#5349](https://github.com/aiidateam/aiida-core/pull/5349)
  - 👌 IMPROVE: Allow directories in `CalcJob.local_copy_list` by @sphuber in [#5115](https://github.com/aiidateam/aiida-core/pull/5115)
  - 👌 IMPROVE: Add support for `.` namespacing in the keys for `WorkChain.to_context` by @dev-zero in [#4871](https://github.com/aiidateam/aiida-core/pull/4871)
  - 👌 IMPROVE: Handle namespaced outputs in `BaseRestartWorkChain` by @unkcpz in [#4961](https://github.com/aiidateam/aiida-core/pull/4961)
  - 🐛 FIX: Nested namespaces in `ProcessBuilderNamespace` by @sphuber in [#4983](https://github.com/aiidateam/aiida-core/pull/4983)
  - 🐛 FIX: Ensure `ProcessBuilder` instances do not interfere  by @sphuber in [#4984](https://github.com/aiidateam/aiida-core/pull/4984)
  - 🐛 FIX: Raise when `Process.exposed_outputs` gets non-existing `namespace` by @sphuber in [#5265](https://github.com/aiidateam/aiida-core/pull/5265)
  - 🐛 FIX: Catch `AttributeError` for unloadable identifier in `ProcessNode.is_valid_cache` by @sphuber in [#5222](https://github.com/aiidateam/aiida-core/pull/5222)
  - 🐛 FIX: Handle `CalcInfo.codes_run_mode` when `CalcInfo.codes_info` contains multiple codes by @unkcpz in [#4990](https://github.com/aiidateam/aiida-core/pull/4990)
  - 🐛 FIX: Check for recycled circus PID by @dev-zero in [#5086](https://github.com/aiidateam/aiida-core/pull/4858)

- Scheduler/Transport:
  - 👌 IMPROVE: Specify abstract methods on `Transport` by @chrisjsewell in [#5242](https://github.com/aiidateam/aiida-core/pull/5242)
  - ✨ NEW: Add support for SSH proxy_jump by @dev-zero in [#4951](https://github.com/aiidateam/aiida-core/pull/4951)
  - 🐛 FIX: Daemon hang when passing `None` as `job_id` by @ramirezfranciscof in [#4967](https://github.com/aiidateam/aiida-core/pull/4967)
  - 🐛 FIX: Avoid deadlocks when retrieving stdout/stderr via SSH by @giovannipizzi in [#3787](https://github.com/aiidateam/aiida-core/pull/3787)
  - 🐛 FIX: Use sanitised variable name in SGE scheduler job title by @mjclarke94 in [#4994](https://github.com/aiidateam/aiida-core/pull/4994)
  - 🐛 FIX: `listdir` method with pattern for SSH by @giovannipizzi in [#5252](https://github.com/aiidateam/aiida-core/pull/5252)
  - 👌 IMPROVE: `DirectScheduler`: use `num_cores_per_mpiproc` if defined in resources by @sphuber in [#5126](https://github.com/aiidateam/aiida-core/pull/5126)
  - 👌 IMPROVE: Add abstract generation of submit script env variables to `Scheduler` by @sphuber in [#5283](https://github.com/aiidateam/aiida-core/pull/5283)

- CLI:
  - ✨ NEW: Allow for CLI usage via `python -m aiida` by @chrisjsewell in [#5356](https://github.com/aiidateam/aiida-core/pull/5356)
  - ⬆️ UPDATE: `click==8.0` and remove `click-completion` by @sphuber in [#5111](https://github.com/aiidateam/aiida-core/pull/5111)
  - ♻️ REFACTOR: Replace `verdi database` commands with `verdi storage` by @ramirezfranciscof in [#5228](https://github.com/aiidateam/aiida-core/pull/5228)
  - ✨ NEW: Add verbosity control by @sphuber in [#5085](https://github.com/aiidateam/aiida-core/pull/5085)
  - ♻️ REFACTOR: Logging verbosity implementation by @sphuber in [#5119](https://github.com/aiidateam/aiida-core/pull/5119)
  - ✨ NEW: Add `verdi group move-nodes` command by @mbercx in [#4428](https://github.com/aiidateam/aiida-core/pull/4428)
  - 👌 IMPROVE: `verdi code setup`: validate the uniqueness of label for local codes by @sphuber in [#5215](https://github.com/aiidateam/aiida-core/pull/5215)
  - 👌 IMPROVE: `GroupParamType`: store group if created by @sphuber in [#5411](https://github.com/aiidateam/aiida-core/pull/5411)
  - 👌 IMPROVE: Show #procs/machine in `verdi computer show` by @dev-zero in [#4945](https://github.com/aiidateam/aiida-core/pull/4945)
  - 👌 IMPROVE: Notify users of runner usage in `verdi process list` by @ltalirz in [#4663](https://github.com/aiidateam/aiida-core/pull/4663)
  - 👌 IMPROVE: Set `localhost` as default for database hostname in `verdi setup` by @sphuber in [#4908](https://github.com/aiidateam/aiida-core/pull/4908)
  - 👌 IMPROVE: Make `verdi group` messages consistent by @CasperWA in [#4999](https://github.com/aiidateam/aiida-core/pull/4999)
  - 🐛 FIX: `verdi calcjob cleanworkdir` command by @zhubonan in [#5209](https://github.com/aiidateam/aiida-core/pull/5209)
  - 🔧 MAINTAIN: Add `verdi devel run-sql` by @chrisjsewell in [#5094](https://github.com/aiidateam/aiida-core/pull/5094)

- REST API:
  - ⬆️ UPDATE: Update to `flask~=2.0` for `rest` extra by @sphuber in [#5366](https://github.com/aiidateam/aiida-core/pull/5366)
  - 👌 IMPROVE: Error message when flask not installed by @ltalirz in [#5398](https://github.com/aiidateam/aiida-core/pull/5398)
  - 👌 IMPROVE: Allow serving of contents of `ArrayData` by @JPchico in [#5425](https://github.com/aiidateam/aiida-core/pull/5425)
  - 🐛 FIX: REST API date-time query by @NinadBhat in [#4959](https://github.com/aiidateam/aiida-core/pull/4959)

- Developers:
  - 🔧 MAINTAIN: Move to flit for PEP 621 compliant package build by @chrisjsewell in [#5312](https://github.com/aiidateam/aiida-core/pull/5312)
  - 🔧 MAINTAIN: Make `__all__` imports explicit by @chrisjsewell in [#5061](https://github.com/aiidateam/aiida-core/pull/5061)
  - 🔧 MAINTAIN: Add `pre-commit.ci` by @chrisjsewell in [#5062](https://github.com/aiidateam/aiida-core/pull/5062)
  - 🔧 MAINTAIN: Add isort pre-commit hook by @chrisjsewell in [#5151](https://github.com/aiidateam/aiida-core/pull/5151)
  - ⬆️ UPDATE: Drop support for Python 3.7 by @sphuber in [#5307](https://github.com/aiidateam/aiida-core/pull/5307)
  - ⬆️ UPDATE: Support Python 3.10 by @csadorf in [#5188](https://github.com/aiidateam/aiida-core/pull/5188)
  - ♻️ REFACTOR: Remove `reentry` requirement by @chrisjsewell in [#5058](https://github.com/aiidateam/aiida-core/pull/5058)
  - ♻️ REFACTOR: Remove `simplejson` by @sphuber in [#5391](https://github.com/aiidateam/aiida-core/pull/5391)
  - ♻️ REFACTOR: Remove `ete3` dependency by @ltalirz in [#4956](https://github.com/aiidateam/aiida-core/pull/4956)
  - 👌 IMPROVE: Replace deprecated imp with importlib by @DirectriX01 in [#4848](https://github.com/aiidateam/aiida-core/pull/4848)
  - ⬆️ UPDATE: `sphinx~=4.1` (+ sphinx extensions) by @chrisjsewell in [#5420](https://github.com/aiidateam/aiida-core/pull/5420)
  - 🧪 CI: Move time consuming tests to separate nightly workflow by @sphuber in [#5354](https://github.com/aiidateam/aiida-core/pull/5354)
  - 🧪 TESTS: Entirely remove `AiidaTestCase` by @chrisjsewell in [#5372](https://github.com/aiidateam/aiida-core/pull/5372)

### Contributors 🎉

Thanks to all contributors: [Contributor Graphs](https://github.com/aiidateam/aiida-core/graphs/contributors?from=2021-01-01&to=2022-15-03&type=c)

Including first-time contributors:

- @DirectriX01 made their first contribution in [[#4848]](https://github.com/aiidateam/aiida-core/pull/4848)
- @mjclarke94 made their first contribution in [[#4994]](https://github.com/aiidateam/aiida-core/pull/4994)
- @janssenhenning made their first contribution in [[#5064]](https://github.com/aiidateam/aiida-core/pull/5064)


## v1.6.7 - 2022-03-07

[full changelog](https://github.com/aiidateam/aiida-core/compare/v1.6.6...v1.6.7)

The `markupsafe` dependency specification was moved to `install_requires`


## v1.6.6 - 2022-03-07

[full changelog](https://github.com/aiidateam/aiida-core/compare/v1.6.5...v1.6.6)

### Bug fixes 🐛

- `DirectScheduler`: remove the `-e` option for bash invocation [[#5264]](https://github.com/aiidateam/aiida-core/pull/5264)
- Replace deprecated matplotlib config option 'text.latex.preview' [[#5233]](https://github.com/aiidateam/aiida-core/pull/5233)

### Dependencies

- Add upper limit `markupsafe<2.1` to fix the documentation build [[#5371]](https://github.com/aiidateam/aiida-core/pull/5371)
- Add upper limit `pytest-asyncio<0.17` [[#5309]](https://github.com/aiidateam/aiida-core/pull/5309)

### Devops 🔧

- CI: move Jenkins workflow to nightly GHA workflow [[#5277]](https://github.com/aiidateam/aiida-core/pull/5277)
- Docs: replace CircleCI build with ReadTheDocs [[#5279]](https://github.com/aiidateam/aiida-core/pull/5279)
- CI: run certain workflows only on main repo, not on forks [[#5091]](https://github.com/aiidateam/aiida-core/pull/5091)
- Revise Docker image build [[#4997]](https://github.com/aiidateam/aiida-core/pull/4997)


## v1.6.5 - 2021-08-13

[full changelog](https://github.com/aiidateam/aiida-core/compare/v1.6.4...v1.6.5)

This patch release contains a number of helpful bug fixes and improvements.

### Improvements 👌

- Add support for the `ProxyJump` SSH config option for seting up an arbitrary number of proxy jumps without additional processes by creating TCP channels over existing SSH connections.
  This provides improved control over the lifetime of the different connections.
  See [SSH configuration](docs/source/howto/ssh.rst) for further details. [[#4951]](https://github.com/aiidateam/aiida-core/pull/4951)
- Allow numpy arrays to be serialized to a process checkpoint. [[#4730)]](https://github.com/aiidateam/aiida-core/pull/4730))
- Add the `_merge` method to `ProcessBuilder`, to update the builder with a nested dictionary. [[#4983)]](https://github.com/aiidateam/aiida-core/pull/4983))
- `verdi setup`: Set the defaut database hostname as `localhost`. [[#4908]](https://github.com/aiidateam/aiida-core/pull/4908)
- Allow `Node.__init__` to be constructed with a specific `User` node. [[#4977]](https://github.com/aiidateam/aiida-core/pull/4977)
- Minimize database logs of failed schema version retrievals. [[#5056]](https://github.com/aiidateam/aiida-core/pull/5056)
- Remove duplicate call of normal `callback` for `InteractiveOption`. [[#5064]](https://github.com/aiidateam/aiida-core/pull/5064)
- Update requirement `pyyaml~=5.4`, which contains critical security fixes. [[#5060]](https://github.com/aiidateam/aiida-core/pull/5060)

### Bug Fixes 🐛

- Fix regression issue with `__contains__` operator in `LinkManager`, when using double underscores, e.g. for `'some__nested__namespace' in calc.inputs`. [#5067](https://github.com/aiidateam/aiida-core/pull/5067)
- Stop deprecation warning being shown when tab-completing incoming and outgoing node links. [[#5011]](https://github.com/aiidateam/aiida-core/pull/5011)
- Stop possible command hints being shown when attempting to tab complete `verdi` commands that do not exist. [[#5012]](https://github.com/aiidateam/aiida-core/pull/5012)
- Do not use `get_detailed_job_info` when retrieving a calculation job, if no job id is set. [[#4967]](https://github.com/aiidateam/aiida-core/pull/4967)
- Race condition when two processes try to create the same `Folder`/`SandboxFolder`, [[#4912]](https://github.com/aiidateam/aiida-core/pull/4912)
- Return the whole nested namespace when using `BaseRestartWorkChain.result`. [[#4961]](https://github.com/aiidateam/aiida-core/pull/4961)
- Use `numpy.nanmin` and `numpy.nanmax` for computing y-limits of `BandsData` matplotlib methods. [[#5024]](https://github.com/aiidateam/aiida-core/pull/5024)
- Use sanitized job title with `SgeScheduler` scheduler. [[#4994]](https://github.com/aiidateam/aiida-core/pull/4994)

## v1.6.4 - 2021-06-23

[full changelog](https://github.com/aiidateam/aiida-core/compare/v1.6.3...v1.6.4)

This is a patch release to pin `psycopg2-binary` to version 2.8.x, to avoid an issue with database creation in version 2.9 ([#4989](https://github.com/aiidateam/aiida-core/pull/4989)).

## v1.6.3 - 2021-04-28

[full changelog](https://github.com/aiidateam/aiida-core/compare/v1.6.2...v1.6.3) | [GitHub contributors page for this release](https://github.com/aiidateam/aiida-core/graphs/contributors?from=2021-04-281&to=2021-04-28&type=c)

This is a patch release to fix a bug that was introduced in `v1.6.2` that would cause a number of `verdi` commands to fail due to a bug in the `with_dbenv` decorator utility.

### Bug fixes
- Fix `aiida.cmdline.utils.decorators.load_backend_if_not_loaded` [[#4878]](https://github.com/aiidateam/aiida-core/pull/4878)


## v1.6.2 - 2021-04-28

[full changelog](https://github.com/aiidateam/aiida-core/compare/v1.6.1...v1.6.2) | [GitHub contributors page for this release](https://github.com/aiidateam/aiida-core/graphs/contributors?from=2021-03-31&to=2021-04-27&type=c)

### Bug fixes
- CLI: Use the proper proxy command for `verdi calcjob gotocomputer` if configured as such [[#4761]](https://github.com/aiidateam/aiida-core/pull/4761)
- Respect nested output namespaces in `Process.exposed_outputs` [[#4863]](https://github.com/aiidateam/aiida-core/pull/4863)
- `NodeLinkManager` now properly regenerates original nested namespaces from the flat link labels stored in the database. This means one can now do `node.outputs.some.nested.output` instead of having to do `node.outputs.some__nested__output`. The same goes for `node.inputs` [[#4625]](https://github.com/aiidateam/aiida-core/pull/4625)
- Fix `aiida.cmdline.utils.decorators.with_dbenv` always loading the database. Now it will only load the database if not already loaded, as intended [[#4865]](https://github.com/aiidateam/aiida-core/pull/4865)

### Features
- Add the `account` option to the `LsfScheduler` scheduler plugin [[#4832]](https://github.com/aiidateam/aiida-core/pull/4832)

### Documentation
- Update ssh proxycommand section with instructions on how to handle cases where the SSH key needs to be specified for the proxy server [[#4839]](https://github.com/aiidateam/aiida-core/pull/4839)
- Add the ["How to extend workflows"](https://aiida-core.readthedocs.io/en/latest/howto/write_workflows.html#extending-workflows) section, explaining the use of the `expose_inputs` and `expose_outputs` features, as well as nested namespaces [[#4562]](https://github.com/aiidateam/aiida-core/pull/4562)
- Add help in intro for when quicksetup fails due to problems autodetecting the PostgreSQL settings [[#4838]](https://github.com/aiidateam/aiida-core/pull/4838)


## v1.6.1 - 2021-03-31

[full changelog](https://github.com/aiidateam/aiida-core/compare/v1.6.0...v1.6.1) | [GitHub contributors page for this release](https://github.com/aiidateam/aiida-core/graphs/contributors?from=2021-03-15&to=2021-03-31&type=c)

This patch release is primarily intended to fix a regression in the `aiida_profile` test fixture, used by plugin developers, causing config validation errors ([#4831](https://github.com/aiidateam/aiida-core/pull/4831)).

Other additions:

- ✨ NEW: Added `structure.data.import` entry-point, allowing for plugins to define file-format specific sub-commands of `verdi data structure import` ([#4427](https://github.com/aiidateam/aiida-core/pull/4427)).
- ✨ NEW: Added `--label` and `--group` options to `verdi data structure import`, which apply a label/group to all structures being imported ([#4429](https://github.com/aiidateam/aiida-core/pull/4429)).
- ⬆️ UPDATE: `psgu` dependency increased to `v0.2.x`.
  This fixes a bug in `verdi quicksetup`, when used on the Windows Subsystem for Linux (WSL) platform ([#4834](https://github.com/aiidateam/aiida-core/pull/4834)).
- 🐛 FIX: `metadata.options.max_memory_kb` is now ignored when using the direct scheduler ([#4825](https://github.com/aiidateam/aiida-core/pull/4825)).
  This was previously imposing a a virtual memory limit with `ulimit -v`, which is very different to the physical memory limit that other scheduler plugins impose. No straightforward way exists to directly limit the physical memory usage for this scheduler.
- 🐛 FIX: Added `__str__` method to the `Orbital` class, fixing a recursion error ([#4829](https://github.com/aiidateam/aiida-core/pull/4829)).

## v1.6.0 - 2021-03-15

[full changelog](https://github.com/aiidateam/aiida-core/compare/v1.5.2...v1.6.0) | [GitHub contributors page for this release](https://github.com/aiidateam/aiida-core/graphs/contributors?from=2020-12-07&to=2021-03-15&type=c)

As well as introducing a number of improvements and new features listed below, this release marks the "under-the-hood" migration from the `tornado` package to the Python built-in module `asyncio`, for handling asynchronous processing within the AiiDA engine.
This removes a number of blocking dependency version clashes with other tools, in particular with the newest Jupyter shell and notebook environments.
The migration does not present any backward incompatible changes to AiiDA's public API.
A substantial effort has been made to test and debug the new implementation, and ensure it performs at least equivalent to the previous code (or improves it!), but please let us know if you uncover any additional issues.

This release also drops support for Python 3.6 (testing is carried out against `3.7`, `3.8` and `3.9`).

NOTE: `v1.6` is tentatively intended to be the final minor `v1.x` release before `v2.x`, that will include a new file repository implementation and remove all deprecated code.

### New calculation features ✨

The `additional_retrieve_list` metadata option has been added to `CalcJob` ([#4437](https://github.com/aiidateam/aiida-core/pull/4437)).
This new option allows one to specify additional files to be retrieved on a per-instance basis, in addition to the files that are already defined by the plugin to be retrieved.

A **new namespace `stash`** has bee added to the `metadata.options` input namespace of the `CalcJob` process ([#4424](https://github.com/aiidateam/aiida-core/pull/4424)).
This option namespace allows a user to specify certain files that are created by the calculation job to be stashed somewhere on the remote.
This can be useful if those files need to be stored for a longer time than the scratch space (where the job was run) is available for, but need to be kept on the remote machine and not retrieved.
Examples are files that are necessary to restart a calculation but are too big to be retrieved and stored permanently in the local file repository.

See [Stashing files on the remote](https://aiida.readthedocs.io/projects/aiida-core/en/v1.6.0/topics/calculations/usage.html#stashing-files-on-the-remote) for more details.

The **new `TransferCalcjob` plugin** ([#4194](https://github.com/aiidateam/aiida-core/pull/4194)) allows the user to copy files between a remote machine and the local machine running AiiDA.
More specifically, it can do any of the following:

- Take any number of files from any number of `RemoteData` folders in a remote machine and copy them in the local repository of a single newly created `FolderData` node.
- Take any number of files from any number of `FolderData` nodes in the local machine and copy them in a single newly created `RemoteData` folder in a given remote machine.

See the [Transferring data](https://aiida.readthedocs.io/projects/aiida-core/en/v1.6.0/howto/data.html#transferring-data) how-to for more details.

### Profile configuration improvements 👌

The way the global/profile configuration is accessed has undergone a number of distinct changes ([#4712](https://github.com/aiidateam/aiida-core/pull/4712)):

- When loaded, the `config.json` (found in the `.aiida` folder) is now validated against a [JSON Schema](https://json-schema.org/) that can be found in [`aiida/manage/configuration/schema`](https://github.com/aiidateam/aiida-core/tree/develop/aiida/manage/configuration/schema).
- The schema includes a number of new global/profile options, including: `transport.task_retry_initial_interval`, `transport.task_maximum_attempts`, `rmq.task_timeout` and `logging.aiopika_loglevel` ([#4583](https://github.com/aiidateam/aiida-core/pull/4583)).
- The `cache_config.yml` has now also been **deprecated** and merged into the `config.json`, as part of the profile options.
  This merge will be handled automatically, upon first load of the `config.json` using the new AiiDA version.

In-line with these changes, the `verdi config` command has been refactored into separate commands, including `verdi config list`, `verdi config set`, `verdi config unset` and `verdi config caching`.

See the [Configuring profile options](https://aiida.readthedocs.io/projects/aiida-core/en/v1.6.0/howto/installation.html#configuring-profile-options) and [Configuring caching](https://aiida.readthedocs.io/projects/aiida-core/en/v1.6.0/howto/run_codes.html#how-to-save-compute-time-with-caching) how-tos for more details.

### Command-line additions and improvements 👌

In addition to `verdi config`, numerous other new commands and options have been added to `verdi`:

- **Deprecated** `verdi export` and `verdi import` commands (replaced by new `verdi archive`) ([#4710](https://github.com/aiidateam/aiida-core/pull/4710))
- Added `verdi group delete --delete-nodes`, to also delete the nodes in a group during its removal ([#4578](https://github.com/aiidateam/aiida-core/pull/4578)).
- Improved `verdi group remove-nodes` command to warn when requested nodes are not in the specified group ([#4728](https://github.com/aiidateam/aiida-core/pull/4728)).
- Added `exception` to the projection mapping of `verdi process list`, for example to use in debugging as: `verdi process list -S excepted -P ctime pk exception` ([#4786](https://github.com/aiidateam/aiida-core/pull/4786)).
- Added `verdi database summary` ([#4737](https://github.com/aiidateam/aiida-core/pull/4737)):
  This prints a summary of the count of each entity and (optionally) the list of unique identifiers for some entities.
- Improved `verdi process play` performance, by only querying for active processes with the `--all` flag ([#4671](https://github.com/aiidateam/aiida-core/pull/4671))
- Added the `verdi database version` command ([#4613](https://github.com/aiidateam/aiida-core/pull/4613)):
  This shows the schema generation and version of the database of the given profile, useful mostly for developers when debugging.
- Improved `verdi node delete` performance ([#4575](https://github.com/aiidateam/aiida-core/pull/4575)):
  The logic has been re-written to greatly reduce the time to delete large amounts of nodes.
- Fixed `verdi quicksetup --non-interactive`, to ensure it does not include any user prompts ([#4573](https://github.com/aiidateam/aiida-core/pull/4573))
- Fixed `verdi --version` when used in editable mode ([#4576](https://github.com/aiidateam/aiida-core/pull/4576))

### API additions and improvements 👌

The base `Node` class now evaluates equality based on the node's UUID ([#4753](https://github.com/aiidateam/aiida-core/pull/4753)).
For example, loading the same node twice will always resolve as equivalent: `load_node(1) == load_node(1)`.
Note that existing, class specific, equality relationships will still override the base class behaviour, for example: `Int(99) == Int(99)`, even if the nodes have different UUIDs.
This behaviour for subclasses is still under discussion at: <https://github.com/aiidateam/aiida-core/issues/1917>

When hashing nodes for use with the caching features, `-0.` is now converted to `0.`, to reduce issues with differing hashes before/after node storage ([#4648](https://github.com/aiidateam/aiida-core/pull/4648)).
Known failure modes for hashing are now also raised with the `HashingError` exception ([#4778](https://github.com/aiidateam/aiida-core/pull/4778)).

Both `aiida.tools.delete_nodes` ([#4578](https://github.com/aiidateam/aiida-core/pull/4578)) and `aiida.orm.to_aiida_type` ([#4672](https://github.com/aiidateam/aiida-core/pull/4672)) have been exposed for use in the public API.

A `pathlib.Path` instance can now be used for the `file` argument of `SinglefileData` ([#3614](https://github.com/aiidateam/aiida-core/pull/3614))

Type annotations have been added to all inputs/outputs of functions and methods in `aiida.engine` ([#4669](https://github.com/aiidateam/aiida-core/pull/4669)) and `aiida/orm/nodes/processes` ([#4772](https://github.com/aiidateam/aiida-core/pull/4772)).
As outlined in [PEP 484](https://www.python.org/dev/peps/pep-0484/), this improves static code analysis and, for example, allows for better auto-completion and type checking in many code editors.

### New REST API Query endpoint ✨

The `/querybuilder` endpoint is the first POST method available for AiiDA's RESTful API ([#4337](https://github.com/aiidateam/aiida-core/pull/4337))

The POST endpoint returns what the QueryBuilder would return, when providing it with a proper `queryhelp` dictionary ([see the documentation here](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/database.html#the-queryhelp)).
Furthermore, it returns the entities/results in the "standard" REST API format - with the exception of `link_type` and `link_label` keys for links (these particular keys are still present as `type` and `label`, respectively).

For security, POST methods can be toggled on/off with the `verdi restapi --posting/--no-posting` options (it is on by default).
Although note that this option is not yet strictly public, since its naming may be changed in the future!

See [AiiDA REST API documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/reference/rest_api.html) for more details.

### Additional Changes

- Fixed the direct scheduler which, in combination with `SshTransport`, was hanging on submit command ([#4735](https://github.com/aiidateam/aiida-core/pull/4735)).
  In the ssh transport, to emulate 'chdir', the current directory is now kept in memory, and every command prepended with `cd FOLDER_NAME && ACTUALCOMMAND`.

- In `aiida.tools.ipython.ipython_magics`, `load_ipython_extension` has been **deprecated** in favour of `register_ipython_extension` ([#4548](https://github.com/aiidateam/aiida-core/pull/4548)).

- Refactored `.ci/` folder to make tests more portable and easier to understand ([#4565](https://github.com/aiidateam/aiida-core/pull/4565))
  The `ci/` folder had become cluttered, containing configuration and scripts for both the GitHub Actions and Jenkins CI.
  This change moved the GH actions specific scripts to `.github/system_tests`, and refactored the Jenkins setup/tests to use [molecule](https://molecule.readthedocs.io) in the `.molecule/` folder.

- For aiida-core development, the pytest `requires_rmq` marker and `config_with_profile` fixture have been added ([#4739](https://github.com/aiidateam/aiida-core/pull/4739) and [#4764](https://github.com/aiidateam/aiida-core/pull/4764))

## v1.5.2 - 2020-12-07

Note: release `v1.5.1` was skipped due to a problem with the uploaded files to PyPI.

### Bug fixes
- `Dict`: accessing an inexistent key now raises a `KeyError` (instead of `AttributeError`) [[#4577]](https://github.com/aiidateam/aiida-core/pull/4577)
- Config: make writing to disk as atomic as possible [[#4607]](https://github.com/aiidateam/aiida-core/pull/4607)
- Config: do not overwrite when loaded and not migrated [[#4605]](https://github.com/aiidateam/aiida-core/pull/4605)
- SqlAlchemy: fix bug in `Group` extras migration with revision `0edcdd5a30f0` [[#4602]](https://github.com/aiidateam/aiida-core/pull/4602)

### Developers
- SqlAlchemy: improve the alembic migration code [[#4602]](https://github.com/aiidateam/aiida-core/pull/4602)
4607
- CI: manually install `numpy` to prevent incompatible releases [[#4615]](https://github.com/aiidateam/aiida-core/pull/4615)


## v1.5.0 - 2020-11-13

In this minor version release, support for Python 3.9 is added [[#4301]](https://github.com/aiidateam/aiida-core/pull/4301), while support for Python 3.5 is dropped [[#4386]](https://github.com/aiidateam/aiida-core/pull/4386).
This version is compatible with all current Python versions that are not end-of-life:
 * 3.6
 * 3.7
 * 3.8
 * 3.9


### Features
- Process functions (`calcfunction` and `workfunction`) can now be submitted to the daemon just like `CalcJob`s and `WorkChain`s [[#4539]](https://github.com/aiidateam/aiida-core/pull/4539)
- REST API: list endpoints at base URL [[#4412]](https://github.com/aiidateam/aiida-core/pull/4412)
- REST API: new `full_types_count` endpoint that counts the number of nodes for each type of node [[#4277]](https://github.com/aiidateam/aiida-core/pull/4277)
- `ProcessBuilder`: allow unsetting of inputs through attribute deletion [[#4419]](https://github.com/aiidateam/aiida-core/pull/4419)
- `verdi migrate`: make `--in-place` work across different file systems [[#4393]](https://github.com/aiidateam/aiida-core/pull/4393)

### Improvements
- Added remaining original documentation that didn't make it into the first step of the recent major overhaul of v1.3.0
- `verdi process show`: order by ctime and print process label [[#4407]](https://github.com/aiidateam/aiida-core/pull/4407)
- `LinkManager`: fix inaccuracy in exception message for non-existent link [[#4388]](https://github.com/aiidateam/aiida-core/pull/4388)
- Add `reset` method to`ProgressReporterAbstract` [[#4522]](https://github.com/aiidateam/aiida-core/pull/4522)
- Improve the deprecation warning for `Node.open` outside context manager [[#4434]](https://github.com/aiidateam/aiida-core/pull/4434)

### Bug fixes
- `SlurmScheduler`: fix bug in validation of job resources [[#4555]](https://github.com/aiidateam/aiida-core/pull/4555)
- Fix `ZeroDivisionError` in worker slots check [[#4513]](https://github.com/aiidateam/aiida-core/pull/4513)
- `CalcJob`: only attempt to clean up the retrieve temporary folder after parsing if it is present [[#4379]](https://github.com/aiidateam/aiida-core/pull/4379)
- Add missing entry point groups to the mapping [[#4395]](https://github.com/aiidateam/aiida-core/pull/4395)
- REST API: the `process_type` can now identify pathological empty-stringed or null entries in the database [[#4277]](https://github.com/aiidateam/aiida-core/pull/4277)


### Developers
- `verdi group delete`: deprecate and ignore the `--clear` option [[#4357]](https://github.com/aiidateam/aiida-core/pull/4357)
- Replace old format string interpolation with f-strings [[#4400]](https://github.com/aiidateam/aiida-core/pull/4400)
- CI: move `pylint` configuration to `pyproject.toml` [[#4411]](https://github.com/aiidateam/aiida-core/pull/4411)
- CI: use `-e` install for tox + add docker-compose for isolated RabbitMQ [[#4375]](https://github.com/aiidateam/aiida-core/pull/4375)
- CI: add coverage patch threshold to prevent false positives [[#4413]](https://github.com/aiidateam/aiida-core/pull/4413)
- CI: Allow for mypy type checking of third-party imports [[#4553]](https://github.com/aiidateam/aiida-core/pull/4553)

### Dependencies
- Update requirement `pytest~=6.0` and use `pyproject.toml` [[#4410]](https://github.com/aiidateam/aiida-core/pull/4410)

### Archive (import/export) refactor
- The refactoring goal was to pave the way for the implementation of a new archive format in v2.0.0 ([ aiidateamAEP005](https://github.com/aiidateam/AEP/pull/21))
- Three abstract+concrete interface classes are defined; writer, reader, migrator, which are **independent of theinternal structure of the archive**. These classes are used within the export/import code.
- The code in `aiida/tools/importexport` has been largely re-written, in particular adding `aiida/toolsimportexport/archive`, which contains this code for interfacing with an archive, and **does not require connectionto an AiiDA profile**.
- The export logic has been re-written; to minimise required queries (faster), and to allow for "streaming" datainto the writer (minimise RAM requirement with new format). It is intended that a similiar PR will be made for the import code.
- A general progress bar implementation is now available in `aiida/common/progress_reporter.py`. All correspondingCLI commands now also have `--verbosity` option.
- Merged PRs:
    - Refactor export archive ([#4448](https://github.com/aiidateam/aiida-core/pull/4448) & [#4534](https://github.com/aiidateam/aiida-core/pull/4534))
    - Refactor import archive ([#4510](https://github.com/aiidateam/aiida-core/pull/4510))
    - Refactor migrate archive ([#4532](https://github.com/aiidateam/aiida-core/pull/4532))
    - Add group extras to archive ([#4521](https://github.com/aiidateam/aiida-core/pull/4521))
    - Refactor cmdline progress bar ([#4504](https://github.com/aiidateam/aiida-core/pull/4504) & [#4522](https://github.com/aiidateam/aiida-core/pull/4522))
- Updated archive version from `0.9` -> `0.10` ([#4561](https://github.com/aiidateam/aiida-core/pull/4561)
- Deprecations: `export_zip`, `export_tar`, `export_tree`, `extract_zip`, `extract_tar` and `extract_tree`functions. `silent` key-word in the `export` function
- Removed: `ZipFolder` class

## v1.4.4

This patch is a backport for 2 of the fixes in `v1.5.2`.

### Bug fixes
- `Dict`: accessing an inexistent key now raises a `KeyError` (instead of an `AttributeError`) [[#4616]](https://github.com/aiidateam/aiida-core/pull/4616)

### Developers
- CI: manually install `numpy` to prevent incompatible releases [[#4615]](https://github.com/aiidateam/aiida-core/pull/4615)


## v1.4.3

### Bug fixes
- RabbitMQ: update `topika` requirement to fix SSL connections and remove validation of `broker_parameters` from profile [[#4542]](https://github.com/aiidateam/aiida-core/pull/4542)
- Fix `UnboundLocalError` in `aiida.cmdline.utils.edit_multiline_template`, which affected `verdi code/computer setup` [[#4436]](https://github.com/aiidateam/aiida-core/pull/4436)


## v1.4.2

### Critical bug fixes
- `CalcJob`: make sure `local_copy_list` files do not end up in the node's repository folder [[#4415]](https://github.com/aiidateam/aiida-core/pull/4415)


## v1.4.1

### Improvements
- `verdi setup`: forward broker defaults to interactive mode [[#4405]](https://github.com/aiidateam/aiida-core/pull/4405)

### Bug fixes
- `verdi setup`: improve validation and help string of broker virtual host [[#4408]](https://github.com/aiidateam/aiida-core/pull/4408)
- Implement `next` and `iter` for the `Node.open` deprecation wrapper [[#4399]](https://github.com/aiidateam/aiida-core/pull/4399)
- Dependencies: increase minimum version requirement `plumpy~=0.15.1` to suppress noisy warning at end of interpreter that ran processes [[#4398]](https://github.com/aiidateam/aiida-core/pull/4398)


## v1.4.0

### Improvements
- Add defaults for configure options of the `SshTransport` plugin [[#4223]](https://github.com/aiidateam/aiida-core/pull/4223)
- `verdi status`: distinguish database schema version incompatible [[#4319]](https://github.com/aiidateam/aiida-core/pull/4319)
- `SlurmScheduler`: implement `parse_output` to detect OOM and OOW [[#3931]](https://github.com/aiidateam/aiida-core/pull/3931)

### Features
- Make the RabbitMQ connection parameters configurable [[#4341]](https://github.com/aiidateam/aiida-core/pull/4341)
- Add infrastructure to parse scheduler output for `CalcJobs` [[#3906]](https://github.com/aiidateam/aiida-core/pull/3906)
- Add support for "peer" authentication with PostgreSQL [[#4255]](https://github.com/aiidateam/aiida-core/pull/4255)
- Add the `--paused` flag to `verdi process list` [[#4213]](https://github.com/aiidateam/aiida-core/pull/4213)
- Make the loglevel of the daemonizer configurable [[#4276]](https://github.com/aiidateam/aiida-core/pull/4276)
- `Transport`: add option to not use a login shell for all commands [[#4271]](https://github.com/aiidateam/aiida-core/pull/4271)
- Implement `skip_orm` option for SqlAlchemy `Group.remove_nodes` [[#4214]](https://github.com/aiidateam/aiida-core/pull/4214)
- `Dict`: allow setting attributes through setitem and `AttributeManager` [[#4351]](https://github.com/aiidateam/aiida-core/pull/4351)
- `CalcJob`: allow nested target paths for `local_copy_list` [[#4373]](https://github.com/aiidateam/aiida-core/pull/4373)
- `verdi export migrate`: add `--in-place` flag to migrate archive in place [[#4220]](https://github.com/aiidateam/aiida-core/pull/4220)

### Bug fixes
- `verdi`: make `--prepend-text` and `--append-text` options properly interactive [[#4318]](https://github.com/aiidateam/aiida-core/pull/4318)
- `verdi computer test`: fix failing result in harmless `stderr` responses [[#4316]](https://github.com/aiidateam/aiida-core/pull/4316)
- `QueryBuilder`: Accept empty string for `entity_type` in `append` method [[#4299]](https://github.com/aiidateam/aiida-core/pull/4299)
- `verdi status`: do not except when no profile is configured [[#4253]](https://github.com/aiidateam/aiida-core/pull/4253)
- `ArithmeticAddParser`: attach output before checking for negative value [[#4267]](https://github.com/aiidateam/aiida-core/pull/4267)
- `CalcJob`: fix bug in `retrieve_list` affecting entries without wildcards [[#4275]](https://github.com/aiidateam/aiida-core/pull/4275)
- `TemplateReplacerCalculation`: make `files` namespace dynamic [[#4348]](https://github.com/aiidateam/aiida-core/pull/4348)

### Developers
- Rename folder `test.fixtures` to `test.static` [[#4219]](https://github.com/aiidateam/aiida-core/pull/4219)
- Remove all files from the pre-commit exclude list [[#4196]](https://github.com/aiidateam/aiida-core/pull/4196)
- ORM: move attributes/extras methods of frontend and backend nodes to mixins [[#4376]](https://github.com/aiidateam/aiida-core/pull/4376)

### Dependencies
- Dependencies: update minimum requirement `paramiko~=2.7` [[#4222]](https://github.com/aiidateam/aiida-core/pull/4222)
- Depedencies: remove upper limit and allow `numpy~=1.17` [[#4378]](https://github.com/aiidateam/aiida-core/pull/4378)

### Deprecations
- Deprecate getter and setter methods of `Computer` properties [[#4252]](https://github.com/aiidateam/aiida-core/pull/4252)
- Deprecate methods that refer to a computer's label as name [[#4309]](https://github.com/aiidateam/aiida-core/pull/4309)

### Changes
- `BaseRestartWorkChain`: do not run `process_handler` when `exit_codes=[]` [[#4380]](https://github.com/aiidateam/aiida-core/pull/4380)
- `SlurmScheduler`: always raise for non-zero exit code [[#4332]](https://github.com/aiidateam/aiida-core/pull/4332)
- Remove superfluous `ERROR_NO_RETRIEVED_FOLDER` from `CalcJob` subclasses [[#3906]](https://github.com/aiidateam/aiida-core/pull/3906)


## v1.3.1

### Bug fixes:
- Fix a file handle leak due to the `Runner` not closing the event loop if it created it itself [[#4307]](https://github.com/aiidateam/aiida-core/pull/4307)
- `ArithmeticAddParser`: attach output before checking for negative value [[#4267]](https://github.com/aiidateam/aiida-core/pull/4267)


## v1.3.0

### Improvements
- Comprehensive restructuring and revamp of the online documentation [[#4141]](https://github.com/aiidateam/aiida-core/pull/4141)
- Improve defaults for `verdi computer configure ssh` [[#4055]](https://github.com/aiidateam/aiida-core/pull/4055)
- Provenance graphs: enable highlighting specific node classes (and highlight root node by default) [[#4081]](https://github.com/aiidateam/aiida-core/pull/4081)

### Performance
- Enable event-based monitoring of work chain child processes (they were being polled every second) [[#4154]](https://github.com/aiidateam/aiida-core/pull/4154)
- Increase the default for `runner.poll.interval` config option from 1 to 60 seconds [[#4150]](https://github.com/aiidateam/aiida-core/pull/4150)
- Increase the efficiency of the `SqlaGroup.nodes` iterator [[#4094]](https://github.com/aiidateam/aiida-core/pull/4094)

### Features
- Add a progress bar for export and import related functionality [[#3599]](https://github.com/aiidateam/aiida-core/pull/3599)
- Enable loading config.yml files from URL in `verdi` commands with `--config` option [[#3977]](https://github.com/aiidateam/aiida-core/pull/3977)
- `QueryBuilder`: add the `flat` argument to the `.all()` method [[#3945]](https://github.com/aiidateam/aiida-core/pull/3945)
- `verdi status`: add `--no-rmq` flag to skip the RabbitMQ check [[#4181]](https://github.com/aiidateam/aiida-core/pull/4181)
- Add support for process functions in `verdi plugin list` [[#4117]](https://github.com/aiidateam/aiida-core/pull/4117)
- Allow profile selection in ipython magic `%aiida` [[#4071]](https://github.com/aiidateam/aiida-core/pull/4071)
- Support more complex formula formats in `aiida.orm.data.cif.parse_formula` [[#3954]](https://github.com/aiidateam/aiida-core/pull/3954)

### Bug fixes
- `BaseRestartWorkChain`: do not assume `metadata` exists in inputs in `run_process` [[#4210]](https://github.com/aiidateam/aiida-core/pull/4210)
- `BaseRestartWorkChain`: fix bug in `inspect_process` [[#4166]](https://github.com/aiidateam/aiida-core/pull/4166)
- `BaseRestartWorkChain`: fix the "unhandled failure mechanism" for dealing with failures of subprocesses [[#4155]](https://github.com/aiidateam/aiida-core/pull/4155)
- Fix exception handling in commands calling `list_repository_contents` [[#3968]](https://github.com/aiidateam/aiida-core/pull/3968)
- Fix bug in `Code.get_full_text_info` [[#4083]](https://github.com/aiidateam/aiida-core/pull/4083)
- Fix bug in `verdi daemon restart --reset` [[#3969]](https://github.com/aiidateam/aiida-core/pull/3969)
- Fix tab-completion for `LinkManager` and `AttributeManager` [[#3985]](https://github.com/aiidateam/aiida-core/pull/3985)
- `CalcJobResultManager`: fix bug that broke tab completion [[#4187]](https://github.com/aiidateam/aiida-core/pull/4187)
- `SshTransport.gettree`: allow non-existing nested target directories [[#4175]](https://github.com/aiidateam/aiida-core/pull/4175)
- `CalcJob`: move job resource validation to the `Scheduler` class fixing a problem for the SGE and LSF scheduler plugins [[#4192]](https://github.com/aiidateam/aiida-core/pull/4192)
- `WorkChain`: guarantee to maintain order of appended awaitables [[#4156]](https://github.com/aiidateam/aiida-core/pull/4156)
- Add support for binary files to the various `verdi` cat commands [[#4077]](https://github.com/aiidateam/aiida-core/pull/4077)
- Ensure `verdi group show --limit` respects limit even in raw mode [[#4092]](https://github.com/aiidateam/aiida-core/pull/4092)
- `QueryBuilder`: fix type string filter generation for `Group` subclasses [[#4144]](https://github.com/aiidateam/aiida-core/pull/4144)
- Raise when calling `Node.objects.delete` for node with incoming links [[#4168]](https://github.com/aiidateam/aiida-core/pull/4168)
- Properly handle multiple requests to threaded REST API [[#3974]](https://github.com/aiidateam/aiida-core/pull/3974)
- `NodeTranslator`: do not assume `get_export_formats` exists [[#4188]](https://github.com/aiidateam/aiida-core/pull/4188)
- Only color directories in `verdi node repo ls --color` [[#4195]](https://github.com/aiidateam/aiida-core/pull/4195)

### Developers
- Add arithmetic workflows and restructure calculation plugins [[#4124]](https://github.com/aiidateam/aiida-core/pull/4124)
- Add minimal `mypy` run to the pre-commit hooks. [[#4176]](https://github.com/aiidateam/aiida-core/pull/4176)
- Fix timeout in `tests.cmdline.commands.test_process:test_pause_play_kill` [[#4052]](https://github.com/aiidateam/aiida-core/pull/4052)
- Revise update-dependency flow to resolve issue #3930 [[#3957]](https://github.com/aiidateam/aiida-core/pull/3957)
- Add GitHub action for transifex upload [[#3958]](https://github.com/aiidateam/aiida-core/pull/3958)

### Deprecations
- The `get_valid_schedulers` class method of the `Scheduler` class has been deprecated in favor of `aiida.plugins.entry_point.get_entry_point_names` [[#4192]](https://github.com/aiidateam/aiida-core/pull/4192)


## v1.2.1

In the fixing of three bugs, three minor features have been added along the way.

### Features
- Add config option `daemon.worker_process_slots` to configure the maximum number of concurrent tasks each daemon worker can handle [[#3949]](https://github.com/aiidateam/aiida-core/pull/3949)
- Add config option `daemon.default_workers` to set the default number of workers to be started by `verdi daemon start` [[#3949]](https://github.com/aiidateam/aiida-core/pull/3949)
- `CalcJob`: make submit script filename configurable through the `metadata.options` [[#3948]](https://github.com/aiidateam/aiida-core/pull/3948)

### Bug fixes
- `CalcJob`: fix bug in idempotency check of upload transport task [[#3948]](https://github.com/aiidateam/aiida-core/pull/3948)
- REST API: reintroduce CORS headers, the lack of which was breaking the Materials Cloud provenance explorer [[#3951]](https://github.com/aiidateam/aiida-core/pull/3951)
- Remove the equality operator of `ExitCode` which caused the serialization of workchains to fail if put in the workchain context [[#3940]](https://github.com/aiidateam/aiida-core/pull/3940)

### Deprecations
- The `hookup` argument of `aiida.restapi.run_api` and the `--hookup` option of `verdi restapi` are deprecated [[#3951]](https://github.com/aiidateam/aiida-core/pull/3951)


## v1.2.0

### Features
- `ExitCode`: make the exit message parameterizable through templates [[#3824]](https://github.com/aiidateam/aiida-core/pull/3824)
- `GroupPath`: a utility to work with virtual `Group` hierarchies [[#3613]](https://github.com/aiidateam/aiida-core/pull/3613)
- Make `Group` sub classable through entry points [[#3882]](https://github.com/aiidateam/aiida-core/pull/3882)[[#3903]](https://github.com/aiidateam/aiida-core/pull/3903)[[#3926]](https://github.com/aiidateam/aiida-core/pull/3926)
- Add auto-complete support for `CodeParamType` and `GroupParamType` [[#3926]](https://github.com/aiidateam/aiida-core/pull/3926)
- Add export archive migration for `Group` type strings [[#3912]](https://github.com/aiidateam/aiida-core/pull/3912)
- Add the `-v/--version` option to `verdi export migrate` [[#3910]](https://github.com/aiidateam/aiida-core/pull/3910)
- Add the `-l/--limit` option to `verdi group show` [[#3857]](https://github.com/aiidateam/aiida-core/pull/3857)
- Add the `--order-by/--order-direction` options to `verdi group list` [[#3858]](https://github.com/aiidateam/aiida-core/pull/3858)
- Add `prepend_text` and `append_text` to `aiida_local_code_factory` pytest fixture [[#3831]](https://github.com/aiidateam/aiida-core/pull/3831)
- REST API: make it easier to call `run_api` in wsgi scripts [[#3875]](https://github.com/aiidateam/aiida-core/pull/3875)
- Plot bands with only one kpoint [[#3798]](https://github.com/aiidateam/aiida-core/pull/3798)

### Bug fixes
- Improved validation for CLI parameters [[#3894]](https://github.com/aiidateam/aiida-core/pull/3894)
- Ensure unicity when creating instances of `Autogroup` [[#3650]](https://github.com/aiidateam/aiida-core/pull/3650)
- Prevent nodes without registered entry points from being stored [[#3886]](https://github.com/aiidateam/aiida-core/pull/3886)
- Fix the `RotatingFileHandler` configuration of the daemon logger[[#3891]](https://github.com/aiidateam/aiida-core/pull/3891)
- Ensure log messages are not duplicated in daemon log file [[#3890]](https://github.com/aiidateam/aiida-core/pull/3890)
- Convert argument to `str` in `aiida.common.escaping.escape_for_bash` [[#3873]](https://github.com/aiidateam/aiida-core/pull/3873)
- Remove the return statement of `RemoteData.getfile()` [[#3742]](https://github.com/aiidateam/aiida-core/pull/3742)
- Support for `BandsData` nodes without `StructureData` ancestors [[#3817]](https://github.com/aiidateam/aiida-core/pull/3817)

### Deprecations
- Deprecate `--group-type` option in favor of `--type-string` for `verdi group list` [[#3926]](https://github.com/aiidateam/aiida-core/pull/3926)

### Documentation
- Docs: link to documentation of other libraries via `intersphinx` mapping [[#3876]](https://github.com/aiidateam/aiida-core/pull/3876)
- Docs: remove extra `advanced_plotting` from install instructions [[#3860]](https://github.com/aiidateam/aiida-core/pull/3860)
- Docs: consistent use of "plugin" vs "plugin package" terminology [[#3799]](https://github.com/aiidateam/aiida-core/pull/3799)

### Developers
- Deduplicate code for tests of archive migration code [[#3924]](https://github.com/aiidateam/aiida-core/pull/3924)
- CI: use GitHub Actions services for PostgreSQL and RabbitMQ [[#3901]](https://github.com/aiidateam/aiida-core/pull/3901)
- Move `aiida.manage.external.pgsu` to external package `pgsu` [[#3892]](https://github.com/aiidateam/aiida-core/pull/3892)
- Cleanup the top-level directory of the repository [[#3738]](https://github.com/aiidateam/aiida-core/pull/3738)
- Remove unused `orm.implementation.utils` module [[#3877]](https://github.com/aiidateam/aiida-core/pull/3877)
- Revise dependency management workflow [[#3771]](https://github.com/aiidateam/aiida-core/pull/3771)
- Re-add support for Coverage reports through codecov.io [[#3618]](https://github.com/aiidateam/aiida-core/pull/3618)


## v1.1.1

### Changes
- Emit a warning when input port specifies a node instance as default [[#3466]](https://github.com/aiidateam/aiida-core/pull/3466)
- `BaseRestartWorkChain`: require process handlers to be instance methods [[#3782]](https://github.com/aiidateam/aiida-core/pull/3782)
- `BaseRestartWorkChain`: add method to enable/disable process handlers [[#3786]](https://github.com/aiidateam/aiida-core/pull/3786)
- Docker container: remove conda activation from configure-aiida.sh script [[#3791]](https://github.com/aiidateam/aiida-core/pull/3791)
- Add fixtures to clear the database before or after tests [[#3783]](https://github.com/aiidateam/aiida-core/pull/3783)
- `verdi status`: add the configuration directory path to the output [[#3587]](https://github.com/aiidateam/aiida-core/pull/3587)
- `QueryBuilder`: add support for `datetime.date` objects in filters [[#3796]](https://github.com/aiidateam/aiida-core/pull/3796)

### Bug fixes
- Fix bugs in `Node._store_from_cache` and `Node.repository.erase` that could result in calculations not being reused [[#3777]](https://github.com/aiidateam/aiida-core/pull/3777)
- Caching: fix configuration spec and validation [[#3785]](https://github.com/aiidateam/aiida-core/pull/3785)
- Write migrated config to disk in `Config.from_file` [[#3797]](https://github.com/aiidateam/aiida-core/pull/3797)
- Validate label string at code setup stage [[#3793]](https://github.com/aiidateam/aiida-core/pull/3793)
- Reuse `prepend_text` and `append_text` in `verdi computer/code duplicate` [[#3788]](https://github.com/aiidateam/aiida-core/pull/3788)
- Fix broken imports of `urllib` in various locations including `verdi import` [[#3767]](https://github.com/aiidateam/aiida-core/pull/3767)
- Match headers with actual output for `verdi data structure list` [[#3756]](https://github.com/aiidateam/aiida-core/pull/3756)
- Disable caching for the `Data` node subclass (this should not affect usual caching behavior) [[#3807]](https://github.com/aiidateam/aiida-core/pull/3807)


## v1.1.0

**Nota Bene:** although this is a minor version release, the support for python 2 is dropped [(#3566)](https://github.com/aiidateam/aiida-core/pull/3566) following the reasoning outlined in the corresponding [AEP001](https://github.com/aiidateam/AEP/tree/master/001_drop_python2).
Critical bug fixes for python 2 will be supported until July 1 2020 on the `v1.0.*` release series.
With the addition of python 3.8 [(#3719)](https://github.com/aiidateam/aiida-core/pull/3719), this version is now compatible with all current python versions that are not end-of-life:
 * 3.5
 * 3.6
 * 3.7
 * 3.8

### Features
- Add the AiiDA Graph Explorer (AGE) a generic tool for traversing provenance graph [[#3686]](https://github.com/aiidateam/aiida-core/pull/3686)
- Add the `BaseRestartWorkChain` which makes it easier to write a simple work chain wrapper around another process with automated error handling [[#3748]](https://github.com/aiidateam/aiida-core/pull/3748)
- Add `provenance_exclude_list` attribute to `CalcInfo` data structure, allowing to prevent calculation input files from being permanently stored in the repository [[#3720]](https://github.com/aiidateam/aiida-core/pull/3720)
- Add the `verdi node repo dump` command [[#3623]](https://github.com/aiidateam/aiida-core/pull/3623)
- Add more methods to control cache invalidation of completed process node [[#3637]](https://github.com/aiidateam/aiida-core/pull/3637)
- Allow documentation to be build without installing and configuring AiiDA [[#3669]](https://github.com/aiidateam/aiida-core/pull/3669)
- Add option to expand namespaces in sphinx directive [[#3631]](https://github.com/aiidateam/aiida-core/pull/3631)

### Performance
- Add `node_type` to list of immutable model fields, preventing repeated database hits [[#3619]](https://github.com/aiidateam/aiida-core/pull/3619)
- Add cache for entry points in an entry point group [[#3622]](https://github.com/aiidateam/aiida-core/pull/3622)
- Improve the performance when exporting many groups [[#3681]](https://github.com/aiidateam/aiida-core/pull/3681)

### Changes
- `CalcJob`: move `presubmit` call from `CalcJob.run` to `Waiting.execute` [[#3666]](https://github.com/aiidateam/aiida-core/pull/3666)
- `CalcJob`: do not pause when exception thrown in the `presubmit` [[#3699]](https://github.com/aiidateam/aiida-core/pull/3699)
- Move `CalcJob` spec validator to corresponding namespaces [[#3702]](https://github.com/aiidateam/aiida-core/pull/3702)
- Move getting completed job accounting to `retrieve` transport task [[#3639]](https://github.com/aiidateam/aiida-core/pull/3639)
- Move `last_job_info` from JSON-serialized string to dictionary [[#3651]](https://github.com/aiidateam/aiida-core/pull/3651)
- Improve SqlAlchemy session handling for `QueryBuilder` [[#3708]](https://github.com/aiidateam/aiida-core/pull/3708)
- Use built-in `open` instead of `io.open`, which is possible now that python 2 is no longer supported [[#3615]](https://github.com/aiidateam/aiida-core/pull/3615)
- Add non-zero exit code for `verdi daemon status` [[#3729]](https://github.com/aiidateam/aiida-core/pull/3729)

### Bug fixes
- Deal with unreachable daemon worker in `get_daemon_status` [[#3683]](https://github.com/aiidateam/aiida-core/pull/3683)
- Django backend: limit batch size for `bulk_create` operations [[#3713]](https://github.com/aiidateam/aiida-core/pull/3713)
- Make sure that datetime conversions ignore `None` [[#3628]](https://github.com/aiidateam/aiida-core/pull/3628)
- Allow empty `key_filename` in `verdi computer configure ssh` and reuse cooldown time when reconfiguring [[#3636]](https://github.com/aiidateam/aiida-core/pull/3636)
- Update `pyyaml` to v5.1.2 to prevent arbitrary code execution [[#3675]](https://github.com/aiidateam/aiida-core/pull/3675)
- `QueryBuilder`: fix validation bug and improve message for `in` operator [[#3682]](https://github.com/aiidateam/aiida-core/pull/3682)
- Consider 'AIIDA_TEST_PROFILE' in 'get_test_backend_name' [[#3685]](https://github.com/aiidateam/aiida-core/pull/3685)
- Ensure correct types for `QueryBuilder().dict()` with multiple projections [[#3695]](https://github.com/aiidateam/aiida-core/pull/3695)
- Make local modules importable when running `verdi run` [[#3700]](https://github.com/aiidateam/aiida-core/pull/3700)
- Fix bug in `upload_calculation` for `CalcJobs` with local codes [[#3707]](https://github.com/aiidateam/aiida-core/pull/3707)
- Add imports from `urllib` to dbimporters [[#3704]](https://github.com/aiidateam/aiida-core/pull/3704)

### Developers
- Moved continuous integration from Travis to Github actions [[#3571]](https://github.com/aiidateam/aiida-core/pull/3571)
- Replace custom unit test framework for `pytest` and move all tests to `tests` top level directory [[#3653]](https://github.com/aiidateam/aiida-core/pull/3653)[[#3674]](https://github.com/aiidateam/aiida-core/pull/3674)[[#3715]](https://github.com/aiidateam/aiida-core/pull/3715)
- Cleaned up direct dependencies and relaxed requirements where possible [[#3597]](https://github.com/aiidateam/aiida-core/pull/3597)
- Set job poll interval to zero in localhost pytest fixture [[#3605]](https://github.com/aiidateam/aiida-core/pull/3605)
- Make command line deprecation warnings visible with test profile [[#3665]](https://github.com/aiidateam/aiida-core/pull/3665)
- Add docker image with minimal running AiiDA instance [[#3722]](https://github.com/aiidateam/aiida-core/pull/3722)


## v1.0.1

### Improvements
- Improve the backup mechanism of the configuration file: unique backup written at each update [[#3581]](https://github.com/aiidateam/aiida-core/pull/3581)
- Forward `verdi code delete` to `verdi node delete` [[#3546]](https://github.com/aiidateam/aiida-core/pull/3546)
- Homogenize and improve output of `verdi computer test` [[#3544]](https://github.com/aiidateam/aiida-core/pull/3544)
- Scheduler SLURM: support `UNLIMITED` and `NOT_SET` as values for requested walltimes [[#3586]](https://github.com/aiidateam/aiida-core/pull/3586)
- Set default for the `safe_interval` option of `verdi computer configure` [[#3590]](https://github.com/aiidateam/aiida-core/pull/3590)
- Create backup of configuration file before migrating [[#3568]](https://github.com/aiidateam/aiida-core/pull/3568)
- Add `python_requires` to `setup.json` necessary for future dropping of python 2 [[#3574]](https://github.com/aiidateam/aiida-core/pull/3574)
- Remove unused QB methods/functions [[#3526]](https://github.com/aiidateam/aiida-core/pull/3526)
- Move `pgtest` argument of `TemporaryProfileManager` to constructor [[#3486]](https://github.com/aiidateam/aiida-core/pull/3486)
- Add `filename` argument to `SinglefileData` constructor [[#3517]](https://github.com/aiidateam/aiida-core/pull/3517)
- Mention machine in SSH connection exception message [[#3536]](https://github.com/aiidateam/aiida-core/pull/3536)
- Docs: Expand on QB `order_by` information [[#3548]](https://github.com/aiidateam/aiida-core/pull/3548)
- Replace deprecated pymatgen `site.species_and_occu` with `site.species`  [[#3480]](https://github.com/aiidateam/aiida-core/pull/3480)
- `QueryBuilder`: add deepcopy implementation and `queryhelp` property [[#3524]](https://github.com/aiidateam/aiida-core/pull/3524)

### Bug fixes
- Fix `verdi calcjob gotocomputer` when `key_filename` is missing [[#3593]](https://github.com/aiidateam/aiida-core/pull/3593)
- Fix bug in database migrations where schema generation determination excepts for old databases [[#3582]](https://github.com/aiidateam/aiida-core/pull/3582)
- Fix false positive for `verdi database integrity detect-invalid-links` [[#3591]](https://github.com/aiidateam/aiida-core/pull/3591)
- Config migration: handle edge case where `daemon` key is missing from `daemon_profiles` [[#3585]](https://github.com/aiidateam/aiida-core/pull/3585)
- Raise when unable to detect name of local timezone [[#3576]](https://github.com/aiidateam/aiida-core/pull/3576)
- Fix bug for `CalcJob` dry runs with `store_provenance=False` [[#3513]](https://github.com/aiidateam/aiida-core/pull/3513)
- Migrations for legacy and now illegal default link label `_return`, export version upped to `0.8` [[#3561]](https://github.com/aiidateam/aiida-core/pull/3561)
- Fix REST API `attributes_filter` and `extras_filter` [[#3556]](https://github.com/aiidateam/aiida-core/pull/3556)
- Fix bug in plugin `Factory` classes for python 3.7 [[#3552]](https://github.com/aiidateam/aiida-core/pull/3552)
- Make `PolishWorkChains` checkpointable [[#3532]](https://github.com/aiidateam/aiida-core/pull/3532)
- REST API: fix generator of full node namespace [[#3516]](https://github.com/aiidateam/aiida-core/pull/3516)


## v1.0.0

### Overview of changes

The following is a summary of the major changes and improvements from `v0.12.*` to `v1.0.0`.

- Faster workflow engine: the new message-based engine powered by RabbitMQ supports tens of thousands of processes per hour and greatly speeds up workflow testing. You can now run one daemon per AiiDA profile.
- Faster database queries: the switch to JSONB for node attributes and extras greatly improves query speed and reduces storage size by orders of magnitude.
- Robust calculations: AiiDA now deals with network connection issues (automatic retries with backoff mechanism, connection pooling, ...) out of the box. Workflows and calculations are all Processes and can be "paused" and "played" anytime.
- Better verdi commands: the move to the `click` framework brings homogenous command line options across all commands (loading nodes, ...). You can easily add new commands through plugins.
- Easier workflow development: Input and output namespaces, reusing specs of sub-processes and less boilerplate code simplify writing WorkChains and CalcJobs, while also enabling powerful auto-documentation features.
- Mature provenance model: Clear separation between data provenance (Calculations, Data) and logical provenance (Workflows). Old databases can be migrated to the new model automatically.
- python3 compatible: AiiDA 1.0 is compatible with both python 2.7 and python 3.6 (and later). Python 2 support will be dropped in the coming months.

### Detailed list of changes

Below a (non-exhaustive) list of changes by category.
Changes between 1.0 alpha/beta releases are not included - for those see the changelog of the corresponding releases.

#### Engine and daemon
- Implement the concept of an "exit status" for all calculations, allowing a programmatic definition of success or failure for all processes [[#1189]](https://github.com/aiidateam/aiida-core/pull/1189)
- All calculations now go through the `Process` layer, homogenizing the state of work and job calculations [[#1125]](https://github.com/aiidateam/aiida-core/pull/1125)
- Allow `None` as default for arguments of process functions [[#2582]](https://github.com/aiidateam/aiida-core/pull/2582)
- Implement the new `calcfunction` decorator. [[#2203]](https://github.com/aiidateam/aiida-core/pull/2203)
- Each profile now has its own daemon that can be run completely independently in parallel [[#1217]](https://github.com/aiidateam/aiida-core/pull/1217)
- Polling based daemon has been replaced with a much faster event-based daemon [[#1067]](https://github.com/aiidateam/aiida-core/pull/1067)
- Replaced `Celery` with `Circus` as the daemonizer of the daemon [[#1213]](https://github.com/aiidateam/aiida-core/pull/1213)
- The daemon can now be stopped without loading the database, making it possible to stop it even if the database version does not match the code [[#1231]](https://github.com/aiidateam/aiida-core/pull/1231)
- Implement exponential backoff retry mechanism for transport tasks [[#1837]](https://github.com/aiidateam/aiida-core/pull/1837)
- Pause `CalcJob` when transport task falls through exponential backoff [[#1903]](https://github.com/aiidateam/aiida-core/pull/1903)
- Separate `CalcJob` submit task in folder upload and scheduler submit [[#1946]](https://github.com/aiidateam/aiida-core/pull/1946)
- Each daemon worker now respects an optional minimum scheduler polling interval [[#1929]](https://github.com/aiidateam/aiida-core/pull/1929)
- Make the `execmanager.retrieve_calculation` idempotent'ish [[#3142]](https://github.com/aiidateam/aiida-core/pull/3142)
- Make the `execmanager.upload_calculation` idempotent'ish [[#3146]](https://github.com/aiidateam/aiida-core/pull/3146)
- Make the `execmanager.submit_calculation` idempotent'ish [[#3188]](https://github.com/aiidateam/aiida-core/pull/3188)
- Implement a `PluginVersionProvider` for processes to automatically add versions of `aiida-core` and plugin to process nodes [[#3131]](https://github.com/aiidateam/aiida-core/pull/3131)

#### Processes
- Implement the `ProcessBuilder` which simplifies the definition of `Process` inputs and the launching of a `Process` [[#1116]](https://github.com/aiidateam/aiida-core/pull/1116)
- Namespaces added to the port containers of the `ProcessSpec` class [[#1099]](https://github.com/aiidateam/aiida-core/pull/1099)
- Convention of leading underscores for non-storable inputs is replaced with a proper `non_db` attribute of the `Port` class [[#1105]](https://github.com/aiidateam/aiida-core/pull/1105)
- Implement a Sphinx extension for the `WorkChain` class to automatically generate documentation from the workchain definition [[#1155]](https://github.com/aiidateam/aiida-core/pull/1155)
- `WorkChain`s can now expose the inputs and outputs of another `WorkChain`, which is great for writing modular workflows [[#1170]](https://github.com/aiidateam/aiida-core/pull/1170)
- Add built-in support and API for exit codes in `WorkChain`s [[#1640]](https://github.com/aiidateam/aiida-core/pull/1640), [[#1704]](https://github.com/aiidateam/aiida-core/pull/1704), [[#1681]](https://github.com/aiidateam/aiida-core/pull/1681)
- Implement method for `CalcJobNode` to create a restart builder  [[#1962]](https://github.com/aiidateam/aiida-core/pull/1962)
- Add `CalculationTools` base and entry point `aiida.tools.calculations` [[#2331]](https://github.com/aiidateam/aiida-core/pull/2331)
- Generalize Sphinx workchain extension to processes [[#3314]](https://github.com/aiidateam/aiida-core/pull/3314)
- Collapsible namespace in sphinxext [[#3441]](https://github.com/aiidateam/aiida-core/pull/3441)
- The `retrieve_singlefile_list` has been deprecated and is replaced by `retrieve_temporary_list` [[#3041]](https://github.com/aiidateam/aiida-core/pull/3041)
- Automatically set `CalcInfo.uuid` in `CalcJob.run` [[#2874]](https://github.com/aiidateam/aiida-core/pull/2874)
- Allow the usage of lambda functions for `InputPort` default values [[#3465]](https://github.com/aiidateam/aiida-core/pull/3465)

#### ORM
- Implementat `AuthInfo` class which allows custom configuration per configured computer [[#1184]](https://github.com/aiidateam/aiida-core/pull/1184)
- Add efficient `count` method for `aiida.orm.groups.Group` [[#2567]](https://github.com/aiidateam/aiida-core/pull/2567)
- Speed up creation of Nodes in the AiiDA ORM [[#2214]](https://github.com/aiidateam/aiida-core/pull/2214)
- Enable use of tuple in `QueryBuilder.append` for all ORM classes [[#1608]](https://github.com/aiidateam/aiida-core/pull/1608), [[#1607]](https://github.com/aiidateam/aiida-core/pull/1607)
- Refactor the ORM to have explicit front-end and back-end layers [[#2190]](https://github.com/aiidateam/aiida-core/pull/2190)[[#2210]](https://github.com/aiidateam/aiida-core/pull/2210)[[#2225]](https://github.com/aiidateam/aiida-core/pull/2225)[[#2227]](https://github.com/aiidateam/aiida-core/pull/2227)[[#2481]](https://github.com/aiidateam/aiida-core/pull/2481)
- Add support for indexing and slicing in `orm.Group.nodes` iterator [[#2371]](https://github.com/aiidateam/aiida-core/pull/2371)
- Add support for process classes to QueryBuilder.append [[#2421]](https://github.com/aiidateam/aiida-core/pull/2421)
- Change type of uuids returned by the QueryBuilder to unicode [[#2259]](https://github.com/aiidateam/aiida-core/pull/2259)
- The `AttributeDict` is now constructed recursively for nested dictionaries [[#3005]](https://github.com/aiidateam/aiida-core/pull/3005)
- Ensure immutability of `CalcJobNode` hash before and after storing [[#3130]](https://github.com/aiidateam/aiida-core/pull/3130)
- Fix bug in the `RemoteData._clean` method [[#1847]](https://github.com/aiidateam/aiida-core/pull/1847)
- Fix bug in `QueryBuilder.first()` for multiple projections [[#2824]](https://github.com/aiidateam/aiida-core/pull/2824)
- Fix bug in `delete_nodes` when passing pks of non-existing nodes [[#2440]](https://github.com/aiidateam/aiida-core/pull/2440)
- Remove unserializable data from metadata in `Log` records [[#2469]](https://github.com/aiidateam/aiida-core/pull/2469)

#### Data
- Fix bug in `parse_formula` for formulas with leading or trailing whitespace [[#2186]](https://github.com/aiidateam/aiida-core/pull/2186)
- Refactor `Orbital` code and fix some bugs [[#2737]](https://github.com/aiidateam/aiida-core/pull/2737)
- Fix bug in the `store` method of `CifData` which would raise an exception when called more than once [[#1136]](https://github.com/aiidateam/aiida-core/pull/1136)
- Allow passing directory path in `FolderData` constructor [[#3359]](https://github.com/aiidateam/aiida-core/pull/3359)
- Add element `X` to the elements list in order to support unknown species [[#1613]](https://github.com/aiidateam/aiida-core/pull/1613)
- Various bug and consistency fixes for `CifData` and `StructureData` [[#2374]](https://github.com/aiidateam/aiida-core/pull/2374)
- Changes to `Data` class attributes and `TrajectoryData` data storage [[#2310]](https://github.com/aiidateam/aiida-core/pull/2310)[[#2422]](https://github.com/aiidateam/aiida-core/pull/2422)
- Rename `ParameterData` to `Dict` [[#2530]](https://github.com/aiidateam/aiida-core/pull/2530)
- Remove the `FrozenDict` data sub class [[#2532]](https://github.com/aiidateam/aiida-core/pull/2532)
- Remove the `Error` data sub class [[#2529]](https://github.com/aiidateam/aiida-core/pull/2529)
- Make `Code` a real sub class of `Data` [[#2193]](https://github.com/aiidateam/aiida-core/pull/2193)
- Implement the `has_atomic_sites` and `has_unknown_species` properties for the `CifData` class [[#1257]](https://github.com/aiidateam/aiida-core/pull/1257)
- Change default library used in `_get_aiida_structure` (converting `CifData` to `StructureData`) from `ase` to `pymatgen` [[#1257]](https://github.com/aiidateam/aiida-core/pull/1257)
- Add converter for `UpfData` from UPF to JSON format [[#3308]](https://github.com/aiidateam/aiida-core/pull/3308)
- Fix potential inefficiency in `aiida.tools.data.cif` converters [[#3098]](https://github.com/aiidateam/aiida-core/pull/3098)
- Fix bug in `KpointsData.reciprocal_cell()` [[#2779]](https://github.com/aiidateam/aiida-core/pull/2779)
- Improve robustness of parsing versions and element names from UPF files [[#2296]](https://github.com/aiidateam/aiida-core/pull/2296)

#### Verdi command line interface
- Migrate `verdi` to the click infrastructure [[#1795]](https://github.com/aiidateam/aiida-core/pull/1795)
- Add a default user to AiiDA configuration, eliminating the need to retype user information for every new profile [[#2734]](https://github.com/aiidateam/aiida-core/pull/2734)
- Implement tab-completion for profile in the `-p` option of `verdi` [[#2345]](https://github.com/aiidateam/aiida-core/pull/2345)
- Homogenize the interface of `verdi quicksetup` and `verdi setup` [[#1797]](https://github.com/aiidateam/aiida-core/pull/1797)
- Add the option `--version` to `verdi` to display current version [[#1811]](https://github.com/aiidateam/aiida-core/pull/1811)
- `verdi computer configure` can now read inputs from a yaml file through the `--config` option [[#2951]](https://github.com/aiidateam/aiida-core/pull/2951)

#### External database importers
- Add importer class for the Materials Platform of Data Science API, which hosts the Pauling file data [[#1238]](https://github.com/aiidateam/aiida-core/pull/1238)
- Add an importer class for the Materials Project API [[#2097]](https://github.com/aiidateam/aiida-core/pull/2097)

#### Database
- Add an index to columns of `DbLink` for SqlAlchemy [[#2561]](https://github.com/aiidateam/aiida-core/pull/2561)
- Creating unique constraint and indexes at the `db_dbgroup_dbnodes` table for SqlAlchemy [[#1680]](https://github.com/aiidateam/aiida-core/pull/1680)
- Performance improvement for adding nodes to group [[#1677]](https://github.com/aiidateam/aiida-core/pull/1677)
- Make UUID columns unique in SqlAlchemy [[#2323]](https://github.com/aiidateam/aiida-core/pull/2323)
- Allow PostgreSQL connections via unix sockets [[#1721]](https://github.com/aiidateam/aiida-core/pull/1721)
- Drop the unused `nodeversion` and `public` columns from the node table [[#2937]](https://github.com/aiidateam/aiida-core/pull/2937)
- Drop various unused columns from the user table [[#2944]](https://github.com/aiidateam/aiida-core/pull/2944)
- Drop the unused `transport_params` column from the computer table [[#2946]](https://github.com/aiidateam/aiida-core/pull/2946)
- Drop the `DbCalcState` table [[#2198]](https://github.com/aiidateam/aiida-core/pull/2198)
- [Django]: migrate the node attribute and extra schema to use JSONB, greatly improving storage and querying efficiency [[#3090]](https://github.com/aiidateam/aiida-core/pull/3090)
- [SqlAlchemy]: Improve speed of node attribute and extra deserialization [[#3090]](https://github.com/aiidateam/aiida-core/pull/3090)

#### Export and Import
- Implement the exporting and importing of node extras [[#2416]](https://github.com/aiidateam/aiida-core/pull/2416)
- Implement the exporting and importing of comments [[#2413]](https://github.com/aiidateam/aiida-core/pull/2413)
- Implement the exporting and importing of logs [[#2393]](https://github.com/aiidateam/aiida-core/pull/2393)
- Add `export_parameters` to the `metadata.json` in archive files [[#3386]](https://github.com/aiidateam/aiida-core/pull/3386)
- Simplify the data format of export archives, greatly reducing file size [[#3090]](https://github.com/aiidateam/aiida-core/pull/3090)
- `verdi import` automatically migrates archive files of old formats [[#2820]](https://github.com/aiidateam/aiida-core/pull/2820)

#### Miscellaneous
- Refactor unit test managers and add basic fixtures for `pytest` [[#3319]](https://github.com/aiidateam/aiida-core/pull/3319)
- REST API v4: updates to conform with `aiida-core==1.0.0` [[#3429]](https://github.com/aiidateam/aiida-core/pull/3429)
- Improve decorators using the `wrapt` library such that function signatures are properly maintained [[#2991]](https://github.com/aiidateam/aiida-core/pull/2991)
- Allow empty `enabled` and `disabled` keys in caching configuration [[#3330]](https://github.com/aiidateam/aiida-core/pull/3330)
- AiiDA now enforces UTF-8 encoding for text output in its files and databases. [[#2107]](https://github.com/aiidateam/aiida-core/pull/2107)

#### Backwards-incompatible changes (only a sub-set)
- Remove `aiida.tests` and obsolete `aiida.storage.tests.test_parsers` entry point group [[#2778]](https://github.com/aiidateam/aiida-core/pull/2778)
- Implement new link types [[#2220]](https://github.com/aiidateam/aiida-core/pull/2220)
- Rename the type strings of `Groups` and change the attributes `name` and `type` to `label` and `type_string` [[#2329]](https://github.com/aiidateam/aiida-core/pull/2329)
- Make various protected `Node` methods public [[#2544]](https://github.com/aiidateam/aiida-core/pull/2544)
- Rename `DbNode.type` to `DbNode.node_type` [[#2552]](https://github.com/aiidateam/aiida-core/pull/2552)
- Rename the ORM classes for `Node` sub classes `JobCalculation`, `WorkCalculation`, `InlineCalculation` and `FunctionCalculation` [[#2184]](https://github.com/aiidateam/aiida-core/pull/2184)[[#2189]](https://github.com/aiidateam/aiida-core/pull/2189)[[#2192]](https://github.com/aiidateam/aiida-core/pull/2192)[[#2195]](https://github.com/aiidateam/aiida-core/pull/2195)[[#2201]](https://github.com/aiidateam/aiida-core/pull/2201)
- Do not allow the `copy` or `deepcopy` of `Node`, except for `Data` nodes  [[#1705]](https://github.com/aiidateam/aiida-core/pull/1705)
- Remove `aiida.control` and `aiida.utils` top-level modules; reorganize `aiida.common`, `aiida.manage` and `aiida.tools` [[#2357]](https://github.com/aiidateam/aiida-core/pull/2357)
- Make the node repository API backend agnostic [[#2506]](https://github.com/aiidateam/aiida-core/pull/2506)
- Redesign the Parser class [[#2397]](https://github.com/aiidateam/aiida-core/pull/2397)
- [Django]: Remove support for datetime objects from node attributes and extras [[#3090]](https://github.com/aiidateam/aiida-core/pull/3090)
- Enforce specific precision in `clean_value` for floats when computing a node's hash [[#3108]](https://github.com/aiidateam/aiida-core/pull/3108)
- Move physical constants from `aiida.common.constants` to external `qe-tools` package [[#3278]](https://github.com/aiidateam/aiida-core/pull/3278)
- Add type checks to all plugin factories [[#3456]](https://github.com/aiidateam/aiida-core/pull/3456)
- Disallow pickle when storing numpy array in `ArrayData` [[#3434]](https://github.com/aiidateam/aiida-core/pull/3434)
- Remove implementation of legacy workflows [[#2379]](https://github.com/aiidateam/aiida-core/pull/2379)
- Implement `CalcJob` process class that replaces the deprecated `JobCalculation` [[#2389]](https://github.com/aiidateam/aiida-core/pull/2389)
- Change the structure of the `CalcInfo.local_copy_list` [[#2581]](https://github.com/aiidateam/aiida-core/pull/2581)
- QueryBuilder: Change 'ancestor_of'/'descendant_of' to 'with_descendants'/'with_ancestors' [[#2278]](https://github.com/aiidateam/aiida-core/pull/2278)



## v0.12.4

### Improvements
- Added new endpoint in rest api to get list of distinct node types [[#2745]](https://github.com/aiidateam/aiida-core/pull/2745)
- Travis: port the deploy stage from the development branch [[#2816]](https://github.com/aiidateam/aiida-core/pull/2816)

### Minor bug fixes
- Corrected the graph export set expansion rules [[#2632]](https://github.com/aiidateam/aiida-core/pull/2632)

### Miscellaneous
- Backport streamlined quick install instructions from `provenance_redesign` [[#2555]](	https://github.com/aiidateam/aiida_core/pull/2555)
- Remove useless chainmap dependency [[#2799]](https://github.com/aiidateam/aiida-core/pull/2799)
- Add aiida-core version to docs home page [[#3058]](https://github.com/aiidateam/aiida-core/pull/3058)
- Docs: add note on increasing work_mem [[#2952]](https://github.com/aiidateam/aiida-core/pull/2952)


## v0.12.3

### Improvements
- Fast addition of nodes to groups with `skip_orm=True` [[#2471]](https://github.com/aiidateam/aiida-core/pull/2471)
- Add `environment.yml` for installing dependencies using conda; release of `aiida-core` on conda-forge channel [[#2081]](https://github.com/aiidateam/aiida-core/pull/2081)
- REST API: io tree response now includes link type and node label [[#2033]](https://github.com/aiidateam/aiida-core/pull/2033) [[#2511]](https://github.com/aiidateam/aiida-core/pull/2511)
- Backport postgres improvements for quicksetup [[#2433]](https://github.com/aiidateam/aiida-core/pull/2433)
- Backport `aiida.get_strict_version` (for plugin development) [[#2099]](https://github.com/aiidateam/aiida-core/pull/2099)

### Minor bug fixes
- Fix security vulnerability by upgrading `paramiko` to `2.4.2` [[#2043]](https://github.com/aiidateam/aiida-core/pull/2043)
- Disable caching for inline calculations (broken since move to ``workfunction``-based implementation) [[#1872]](https://github.com/aiidateam/aiida-core/pull/1872)
- Let `verdi help` return exit status 0 [[#2434]](https://github.com/aiidateam/aiida-core/pull/2434)
- Decode dict keys only if strings (backport) [[#2436]](https://github.com/aiidateam/aiida-core/pull/2436)
- Remove broken verdi-plug entry point [[#2356]](https://github.com/aiidateam/aiida-core/pull/2356)
- `verdi node delete` (without arguments) no longer tries to delete all nodes [[#2545]](https://github.com/aiidateam/aiida-core/pull/2545)
- Fix plotting of `BandsData` objects [[#2492]](https://github.com/aiidateam/aiida-core/pull/2492)

### Miscellaneous
- REST API: add tests for random sorting list entries of same type [[#2106]](https://github.com/aiidateam/aiida-core/pull/2106)
- Add various badges to README [[#1969]](https://github.com/aiidateam/aiida-core/pull/1969)
- Minor documentation improvements [[#1955]](https://github.com/aiidateam/aiida-core/pull/1955)
- Add license file to MANIFEST [[#2339]](https://github.com/aiidateam/aiida-core/pull/2339)
- Add instructions when `verdi import` fails [[#2420]](https://github.com/aiidateam/aiida-core/pull/2420)

## v0.12.2

### Improvements
- Support the hashing of `uuid.UUID` types by registering a hashing function  [[#1861]](https://github.com/aiidateam/aiida-core/pull/1861)
- Add documentation on plugin cutter [[#1904]](https://github.com/aiidateam/aiida-core/pull/1904)

### Minor bug fixes
- Make exported graphs consistent with the current node and link hierarchy definition [[#1764]](https://github.com/aiidateam/aiida-core/pull/1764)
- Fix link import problem under SQLA [[#1769]](https://github.com/aiidateam/aiida-core/pull/1769)
- Fix cache folder copying [[#1746]](https://github.com/aiidateam/aiida-core/pull/1746) [[1752]](https://github.com/aiidateam/aiida-core/pull/1752)
- Fix bug in mixins.py when copying node [[#1743]](https://github.com/aiidateam/aiida-core/pull/1743)
- Fix pgtest failures (release-branch) on travis [[#1736]](https://github.com/aiidateam/aiida-core/pull/1736)
- Fix plugin: return testrunner result to fail on travis, when tests don't pass [[#1676]](https://github.com/aiidateam/aiida-core/pull/1676)

### Miscellaneous
- Remove pycrypto dependency, as it was found to have sercurity flaws [[#1754]](https://github.com/aiidateam/aiida-core/pull/1754)
- Set xsf as default format for structures visualization [[#1756]](https://github.com/aiidateam/aiida-core/pull/1756)
- Delete unused `utils/create_requirements.py` file [[#1702]](https://github.com/aiidateam/aiida-core/pull/1702)


## v0.12.1

### Improvements
- Always use a bash login shell to execute all remote SSH commands, overriding any system default shell [[#1502]](https://github.com/aiidateam/aiida-core/pull/1502)
- Reduced the size of the distributed package by almost half by removing test fixtures and generating the data on the fly [[#1645]](https://github.com/aiidateam/aiida-core/pull/1645)
- Removed the explicit dependency upper limit for `scipy` [[#1492]](https://github.com/aiidateam/aiida-core/pull/1492)
- Resolved various dependency requirement conflicts [[#1488]](https://github.com/aiidateam/aiida-core/pull/1488)

### Minor bug fixes
- Fixed a bug in `verdi node delete` that would throw an exception for certain cases [[#1564]](https://github.com/aiidateam/aiida-core/pull/1564)
- Fixed a bug in the `cif` endpoint of the REST API [[#1490]](https://github.com/aiidateam/aiida-core/pull/1490)


## v0.12.0

### Improvements
- Hashing, caching and fast-forwarding [[#652]](https://github.com/aiidateam/aiida-core/pull/652)
- Calculation no longer stores full source file [[#1082]](https://github.com/aiidateam/aiida-core/pull/1082)
- Delete nodes via `verdi node delete` [[#1083]](https://github.com/aiidateam/aiida-core/pull/1083)
- Import structures using ASE [[#1085]](https://github.com/aiidateam/aiida-core/pull/1085)
- `StructureData` - `pymatgen` - `StructureData` roundtrip works for arbitrary kind names [[#1285]](https://github.com/aiidateam/aiida-core/pull/1285) [[#1306]](https://github.com/aiidateam/aiida-core/pull/1306) [[#1357]](https://github.com/aiidateam/aiida-core/pull/1357)
- Output format of archive file can now be defined for `verdi export migrate` [[#1383]](https://github.com/aiidateam/aiida-core/pull/1383)
- Automatic reporting of code coverage by unit tests has been added [[#1422]](https://github.com/aiidateam/aiida-core/pull/1422)

### Critical bug fixes
- Add `parser_name` `JobProcess` options [[#1118]](https://github.com/aiidateam/aiida-core/pull/1118)
- Node attribute reads were not always up to date across interpreters for SqlAlchemy [[#1379]](https://github.com/aiidateam/aiida-core/pull/1379)

### Minor bug fixes
- Cell vectors not printed correctly [[#1087]](https://github.com/aiidateam/aiida-core/pull/1087)
- Fix read-the-docs issues [[#1120]](https://github.com/aiidateam/aiida-core/pull/1120) [[#1143]](https://github.com/aiidateam/aiida-core/pull/1143)
- Fix structure/band visualization in REST API [[#1167]](https://github.com/aiidateam/aiida-core/pull/1167) [[#1182]](https://github.com/aiidateam/aiida-core/pull/1182)
- Fix `verdi work list` test [[#1286]](https://github.com/aiidateam/aiida-core/pull/1286)
- Fix `_inline_to_standalone_script` in `TCODExporter` [[#1351]](https://github.com/aiidateam/aiida-core/pull/1351)
- Updated `reentry` to fix various small bugs related to plugin registering [[#1440]](https://github.com/aiidateam/aiida-core/pull/1440)

### Miscellaneous
- Bump `qe-tools` version [[#1090]](https://github.com/aiidateam/aiida-core/pull/1090)
- Document link types [[#1174]](https://github.com/aiidateam/aiida-core/pull/1174)
- Switch to trusty + postgres 9.5 on Travis [[#1180]](https://github.com/aiidateam/aiida-core/pull/1180)
- Use raw SQL in sqlalchemy migration of `Code` [[#1291]](https://github.com/aiidateam/aiida-core/pull/1291)
- Document querying of list attributes [[#1326]](https://github.com/aiidateam/aiida-core/pull/1326)
- Document running `aiida` as a daemon service [[#1445]](https://github.com/aiidateam/aiida-core/pull/1445)
- Document that Torque and LoadLever schedulers are now fully supported [[#1447]](https://github.com/aiidateam/aiida-core/pull/1447)
- Cookbook: how to check the number of queued/running jobs in the scheduler [[#1349]](https://github.com/aiidateam/aiida-core/pull/1349)


## v0.11.4

### Improvements
- PyCifRW upgraded to 4.2.1 [[#1073]](https://github.com/aiidateam/aiida-core/pull/1073)

### Critical bug fixes
- Persist and load parsed workchain inputs and do not recreate to avoid creating duplicates for default inputs [[#1362]](https://github.com/aiidateam/aiida-core/pull/1362)
- Serialize `WorkChain` context before persisting [[#1354]](https://github.com/aiidateam/aiida-core/pull/1354)


## v0.11.3

### Improvements
- Documentation: AiiDA now has an automatically generated and complete API documentation (using `sphinx-apidoc`) [[#1330]](https://github.com/aiidateam/aiida-core/pull/1330)
- Add JSON schema for connection of REST API to Materials Cloud Explore interface  [[#1336]](https://github.com/aiidateam/aiida-core/pull/1336)

### Critical bug fixes
- `FINISHED_KEY` and `FAILED_KEY` variables were not known to `AbstractCalculation` [[#1314]](https://github.com/aiidateam/aiida-core/pull/1314)

### Minor bug fixes
- Make 'REST' extra lowercase, such that one can do `pip install aiida-core[rest]` [[#1328]](https://github.com/aiidateam/aiida-core/pull/1328)
- `CifData` `/visualization` endpoint was not returning data [[#1328]](https://github.com/aiidateam/aiida-core/pull/1328)

### Deprecations
- `QueryTool` (was deprecated in favor of `QueryBuilder` since v0.8.0) [[#1330]](https://github.com/aiidateam/aiida-core/pull/1330)

### Miscellaneous
- Add `gource` config for generating a video of development history [[#1337]](https://github.com/aiidateam/aiida-core/pull/1337)


## v0.11.2:

### Critical bug fixes
- Link types were not respected in `Node.get_inputs` for SqlAlchemy [[#1271]](https://github.com/aiidateam/aiida-core/pull/1271)


## v0.11.1:

### Improvements
- Support visualization of structures and cif files with VESTA [[#1093]](https://github.com/aiidateam/aiida-core/pull/1093)
- Better fallback when node class is not available [[#1185]](https://github.com/aiidateam/aiida-core/pull/1185)
- `CifData` now supports faster parsing and lazy loading [[#1190]](https://github.com/aiidateam/aiida-core/pull/1190)
- REST endpoint for `CifData`, API reports full list of available endpoints [[#1228]](https://github.com/aiidateam/aiida-core/pull/1228)
- Various smaller improvements [[#1100]](https://github.com/aiidateam/aiida-core/pull/1100) [[#1182]](https://github.com/aiidateam/aiida-core/pull/1182)

### Critical bug fixes
- Restore attribute immutability in nodes [[#1111]](https://github.com/aiidateam/aiida-core/pull/1111)
- Fix daemonization issue that could cause aiida daemon to be killed [[#1246]](https://github.com/aiidateam/aiida-core/pull/1246)

### Minor bug fixes
- Fix type column in `verdi calculation list` [[#960]](https://github.com/aiidateam/aiida-core/pull/960) [[#1053]](https://github.com/aiidateam/aiida-core/pull/1053)
- Fix `verdi import` from URLs [[#1139]](https://github.com/aiidateam/aiida-core/pull/1139)


## v0.11.0:

### Improvements

### Core entities
- `Computer`: the shebang line is now customizable [[#940]](https://github.com/aiidateam/aiida-core/pull/940)
- `KpointsData`: deprecate buggy legacy implementation of k-point generation in favor of Seekpath [[#1015]](https://github.com/aiidateam/aiida-core/pull/1015)
- `Dict`: `to_aiida_type` used on dictionaries now automatically converted to `Dict` [[#947]](https://github.com/aiidateam/aiida-core/pull/947)
- `JobCalculation`: parsers can now specify files that are retrieved locally for parsing, but only temporarily, as they are deleted after parsing is completed [[#886]](https://github.com/aiidateam/aiida-core/pull/886) [[#894]](https://github.com/aiidateam/aiida-core/pull/894)

### Plugins
- Plugin data hooks: plugins can now add custom commands to `verdi data` [[#993]](https://github.com/aiidateam/aiida-core/pull/993)
- Plugin fixtures: simple-to-use decorators for writing tests of plugins [[#716]](https://github.com/aiidateam/aiida-core/pull/716) [[#865]](https://github.com/aiidateam/aiida-core/pull/865)
- Plugin development: no longer swallow `ImportError` exception during import of plugins [[#1029]](https://github.com/aiidateam/aiida-core/pull/1029)

### Verdi
- `verdi shell`: improve tab completion of imports in  [[#1008]](https://github.com/aiidateam/aiida-core/pull/1008)
- `verdi work list`: projections for verdi work list [[#847]](https://github.com/aiidateam/aiida-core/pull/847)

### Miscellaneous
- Supervisor removal: dependency on unix-only supervisor package removed [[#790]](https://github.com/aiidateam/aiida-core/pull/790)
- REST API: add server info endpoint, structure endpoint can return different file formats [[#878]](https://github.com/aiidateam/aiida-core/pull/878)
- REST API: update endpoints for structure visualization, calculation (includes retrieved input & output list), add endpoints for `UpfData` and more [[#977]](https://github.com/aiidateam/aiida-core/pull/977) [[#991]](https://github.com/aiidateam/aiida-core/pull/991)
- Tests using daemon run faster [[#870]](https://github.com/aiidateam/aiida-core/pull/870)
- Documentation: updated outdated workflow examples [[#948]](https://github.com/aiidateam/aiida-core/pull/948)
- Documentation: updated import/export [[#994]](https://github.com/aiidateam/aiida-core/pull/994),
- Documentation: plugin quickstart [[#996]](https://github.com/aiidateam/aiida-core/pull/996),
- Documentation: parser example [[#1003]](https://github.com/aiidateam/aiida-core/pull/1003)

### Minor bug fixes
- Fix bug with repository on external hard drive [[#982]](https://github.com/aiidateam/aiida-core/pull/982)
- Fix bug in configuration of pre-commit hooks [[#863]](https://github.com/aiidateam/aiida-core/pull/863)
- Fix and improve plugin loader tests [[#1025]](https://github.com/aiidateam/aiida-core/pull/1025)
- Fix broken celery logging [[#1033]](https://github.com/aiidateam/aiida-core/pull/1033)

### Deprecations
- async from aiida.work.run has been deprecated because it can lead to race conditions and thereby unexpected behavior [[#1040]](https://github.com/aiidateam/aiida-core/pull/1040)


## v0.10.1:

### Improvements
- Improved exception handling for loading db tests [[#968]](https://github.com/aiidateam/aiida-core/pull/968)
- `verdi work kill` on workchains: skip calculation if it cannot be killed, rather than stopping [[#980]](https://github.com/aiidateam/aiida-core/pull/980)
- Remove unnecessary INFO messages of Alembic for SQLAlchemy backend [[#1012]](https://github.com/aiidateam/aiida-core/pull/1012)
- Add filter to suppress unnecessary log messages during testing [[#1014]](https://github.com/aiidateam/aiida-core/pull/1014)

### Critical bug fixes
- Fix bug in `verdi quicksetup` on Ubuntu 16.04 and add regression tests to catch similar problems in the future [[#976]](https://github.com/aiidateam/aiida-core/pull/976)
- Fix bug in `verdi data` list commands for SQLAlchemy backend [[#1007]](https://github.com/aiidateam/aiida-core/pull/1007)

### Minor bug fixes
- Various bug fixes related to workflows for the SQLAlchemy backend [[#952]](https://github.com/aiidateam/aiida-core/pull/952) [[#960]](https://github.com/aiidateam/aiida-core/pull/960)


## v0.10.0:

### Major changes
- The `DbPath` table has been removed and replaced with a dynamic transitive closure, because, among others, nested workchains could lead to the `DbPath` table exploding in size
- Code plugins have been removed from `aiida-core` and have been migrated to their own respective plugin repositories and can be found here:
    * [Quantum ESPRESSO](https://github.com/aiidateam/aiida-quantumespresso)
    * [ASE](https://github.com/aiidateam/aiida-ase)
    * [COD tools](https://github.com/aiidateam/aiida-codtools)
    * [NWChem](https://github.com/aiidateam/aiida-nwchem)

    Each can be installed from `pip` using e.g. `pip install aiida-quantumespresso`.
    Existing installations will require a migration (see [update instructions in the documentation](https://aiida-core.readthedocs.io/en/v0.10.0/installation/updating.html#plugin-migration)).
    For a complete overview of available plugins you can visit [the registry](https://aiidateam.github.io/aiida-registry/).

### Improvements
- A new entry `retrieve_temporary_list` in `CalcInfo` allows to retrieve files temporarily for parsing, while not having to store them permanently in the repository [[#903]](https://github.com/aiidateam/aiida-core/pull/903)
- New verdi command: `verdi work kill` to kill running workchains [[#821]](https://github.com/aiidateam/aiida-core/pull/821)
- New verdi command: `verdi data remote [ls,cat,show]` to inspect the contents of `RemoteData` objects [[#743]](https://github.com/aiidateam/aiida-core/pull/743)
- New verdi command: `verdi export migrate` allows the migration of existing export archives to new formats [[#781]](https://github.com/aiidateam/aiida-core/pull/781)
- New verdi command: `verdi profile delete` [[#606]](https://github.com/aiidateam/aiida-core/pull/606)
- Implemented a new option `-m` for the `verdi work report` command to limit the number of nested levels to be printed [[#888]](https://github.com/aiidateam/aiida-core/pull/888)
- Added a `running` field to the output of `verdi work list` to give the current state of the workchains [[#888]](https://github.com/aiidateam/aiida-core/pull/888)
- Implemented faster query to obtain database statistics [[#738]](https://github.com/aiidateam/aiida-core/pull/738)
- Added testing for automatic SqlAlchemy database migrations through alembic [[#834]](https://github.com/aiidateam/aiida-core/pull/834)
- Exceptions that are triggered in steps of a `WorkChain` are now properly logged to the `Node` making them visible through `verdi work report` [[#908]](https://github.com/aiidateam/aiida-core/pull/908)

### Critical bug fixes
- Export will now write the link types to the archive and import will properly recreate the link [[#760]](https://github.com/aiidateam/aiida-core/pull/760)
- Fix bug in workchain persistence that would lead to crashed workchains under certain conditions being resubmitted [[#728]](https://github.com/aiidateam/aiida-core/pull/728)
- Fix bug in the pickling of `WorkChain` instances containing an `_if` logical block in the outline [[#904]](https://github.com/aiidateam/aiida-core/pull/904)

### Minor bug fixes
- The logger for subclasses of `AbstractNode` is now properly namespaced to `aiida.` such that it works in plugins outside of the `aiida-core` source tree [[#897]](https://github.com/aiidateam/aiida-core/pull/897)
- Fixed a problem with the states of the direct scheduler that was causing the daemon process to hang during submission [[#879]](https://github.com/aiidateam/aiida-core/pull/879)
- Various bug fixes related to the old workflows in combination with the SqlAlchemy backend [[#889]](https://github.com/aiidateam/aiida-core/pull/889) [[#898]](https://github.com/aiidateam/aiida-core/pull/898)
- Fixed bug in `TCODexporter` [[#761]](https://github.com/aiidateam/aiida-core/pull/761)
- `verdi profile delete` now respects the configured `dbport` setting [[#713]](https://github.com/aiidateam/aiida-core/pull/713)
- Restore correct help text for `verdi --help` [[#704]](https://github.com/aiidateam/aiida-core/pull/704)
- Fixed query in the ICSD importer element that caused certain structures to be erroneously skipped [[#690]](https://github.com/aiidateam/aiida-core/pull/690)

### Miscellaneous
- Added a "quickstart" to plugin development in the [documentation](http://aiida-core.readthedocs.io/en/v0.10.0/developer_guide/plugins/quickstart.html),
  structured around the new [plugintemplate](https://github.com/aiidateam/aiida-plugin-template) [[#818]](https://github.com/aiidateam/aiida-core/pull/818)
- Improved and restructured the developer documentation [[#818]](https://github.com/aiidateam/aiida-core/pull/818)


## v0.9.1:

### Critical bug fixes
- Workchain steps will no longer be executed multiple times due to process pickles not being locked

### Minor bug fixes
- Fix arithmetic operations for basic numeric types
- Fixed `verdi calculation cleanworkdir` after changes in `QueryBuilder` syntax
- Fixed `verdi calculation logshow` exception when called for `WorkCalculation` nodes
- Fixed `verdi import` for SQLAlchemy profiles
- Fixed bug in `reentry` and update dependency requirement to `v1.0.2`
- Made octal literal string compatible with python 3
- Fixed broken import in the ASE plugin

### Improvements
- `verdi calculation show` now properly distinguishes between `WorkCalculation` and `JobCalculation` nodes
- Improved error handling in `verdi setup --non-interactive`
- Disable unnecessary console logging for tests


## v0.9.0

### Data export functionality
- A number of new functionalities have been added to export band structures to a number of formats, including: gnuplot, matplotlib (both to export a python file, and directly PNG or PDF; both with support of LaTeX typesetting and not); JSON; improved agr (xmgrace) output. Also support for two-color bands for collinear magnetic systems. Added also possibility to specify export-format-specific parameters.
- Added method get_export_formats() to know available export formats for a given data subclass
- Added label prettifiers to properly typeset high-symmetry k-point labels for different formats (simple/old format, seekpath, ...) into a number of plotting codes (xmgrace, gnuplot, latex, ...)
- Improvement of command-line export functionality (more options, possibility to write directly to file, possibility to pass custom options to exporter, by removing its DbPath dependency)

### Workchains
- Crucial bug fix: workchains can now be run through the daemon, i.e. by using `aiida.work.submit`
- Enhancement: added an `abort` and `abort_nowait` method to `WorkChain` which allows to abort the workchain at the earliest possible moment
- Enhancement: added the `report` method to `WorkChain`, which allows a workchain developer to log messages to the database
- Enhancement: added command `verdi work report` which for a given `pk` returns the messages logged for a `WorkChain` through the `report` method
- Enhancement: workchain inputs ports with a valid default specified no longer require to explicitly set `required=False` but is overriden automatically

### New plugin system
- New plugin system implemented, allowing to load aiida entrypoints, and working in parallel with old system (still experimental, though - command line entry points are not fully implemented yet)
- Support for the plugin registry

### Code refactoring
- Refactoring of `Node` to move as much as possible of the caching code into the abstract class
- Refactoring of `Data` nodes to have the export code in the topmost class, and to make it more general also for formats exporting more than one file
- Refactoring of a number of `Data` subclasses to support the new export API
- Refactoring of `BandsData` to have export code not specific to xmgrace or a given format, and to make it more general

### Documentation
- General improvements to documentation
- Added documentation to upgrade AiiDA from v0.8.0 to v0.9.0
- Added documentation of new plugin system and tutorial
- Added more in-depth documentation on how to export data nodes to various formats
- Added explanation on how to export band structures and available formats
- Added documentation on how to run tests in developer's guide
- Documented Latex requirements
- Updated WorkChain documentation for `WaitingEquationOfState` example
- Updated AiiDA installation documentation for installing virtual environment
- Updated documentation to use Jupyter

### Enhancements
- Speedups the travis builds process by caching pip files between runs
- Node can be loaded by passing the start of its UUID
- Handled invalid verdi command line arguments; added help texts for same
- upgraded `Paramiko` to 2.1.2 and avoided to create empty file when remote connection is failed
- `verdi calculation kill` command is now available for `SGE plugin`
- Updated `Plum` from 0.7.8 to 0.7.9 to create a workchain inputs that had default value and evaluated to false
- Now QueryBuilder will be imported by default for all verdi commands

### Bug Fixes
- Bug fixes in QE input parser
- Code.get() method accepts the pk in integer or string format whereas Code.get_from_string() method accepts pk only in string format
- `verdi code show` command now shows the description of the code
- Bug fix to check if computer is properly configured before submitting the calculation

### Miscellaneous
- Replacing dependency from old unmantained `pyspglib` to new `spglib`
- Accept BaseTypes as attributes/extras, and convert them automatically to their value. In this way, for instance, it is now possible to pass a `Int`, `Float`, `Str`, ... as value of a dictionary, and store all into a `Dict`.
- Switch from `pkg_resources` to reentry to allow for much faster loading of modules when possible, and therefore allowing for good speed for bash completion
- Removed obsolete code for Sqlite
- Removed `mayavi2` package from dependencies


## v0.8.1

### Exporters
- Upgraded the TCODExporter to produce CIF files, conforming to the newest (as of 2017-04-26) version of cif_tcod.dic.

### General
- Added dependency on six to properly re-raise exceptions


## v0.8.0

### Installation and setup
- Simplified installation procedure by adopting standard python package installation method through
setuptools and pip
- Verdi install replaced by verdi setup
- New verdi command `quicksetup` to simplify the setup procedure
- Significantly updated and improved the installation documentation

### General
- Significantly increased test coverage and implemented for both backends
- Activated continuous integration through Travis CI
- Application-wide logging is now abstracted and implemented for all backends
- Added a REST API layer with hook through verdi cli: `verdi restapi`
- Improved `QueryBuilder`
    * Composition model instead of inheritance removing the requirement of determining the
    implementation on import
    * Added keyword `with_dbpath` that makes `QueryBuilder` switch between using the `DbPath`and not
    using it.
    * Updated and improved documentation
- The QueryTool as well as the `class Node.query()` method are now deprecated in favor of the
`QueryBuilder`
- Migration of verdi cli to use the `QueryBuilder` in order to support both database backends
- Added option `--project` to `verdi calculation list` to specify which attributes to print

### Documentation
- Documentation is restructured to improve navigability
- Added pseudopotential tutorial

### Database
- Dropped support for MySQL and SQLite to fully support efficient features in Postgres like JSONB
fields
- Database efficiency improvements with orders of magnitude speedup for large databases
[added indices for daemon queries and node UUID queries]
- Replace deprecated `commit_on_success` with atomic for Django transactions
- Change of how SQLAlchemy internally uses the session and the engine to work also with forks (e.g. in celery)

### Workflows
- Finalized the naming for the new workflow system from `workflows2` to `work`
    * `FragmentedWorkFunction` is replaced by `WorkChain`
    * `InlineCalculation` is replaced by `Workfunction`
    * `ProcessCalculation` is replaced by `WorkCalculation`
- Old style Workflows can still be called and run from a new style `WorkChain`
- Major improvements to the `WorkChain` and `Workfunction` implementation
- Improvements to `WorkChain`
    * Implemented a `return` statement for `WorkChain` specification
    * Logging to the database implemented through `WorkChain.report()` for debugging
- Improved kill command for old-style workflows to avoid steps to remaing in running state

### Plugins
- Added finer granularity for parsing PW timers in output
- New Quantum ESPRESSO and scheduler plugins contributed from EPFL
    * ASE/GPAW plugins: Andrea Cepellotti (EPFL and Berkeley)
    * Quantum ESPRESSO DOS, Projwfc: Daniel Marchand (EPFL and McGill)
    * Quantum ESPRESSO phonon, matdyn, q2r, force constants plugins: Giovanni Pizzi,
    Nicolas Mounet (EPFL); Andrea Cepellotti (EPFL and Berkeley)
    * Quantum ESPRESSO cp.x plugin: Giovanni Pizzi (EPFL)
    * Quantum ESPRESSO neb.x plugin: Marco Gibertini (EPFL)
    * LSF scheduler: Nicolas Mounet (EPFL)
- Implemented functionality to export and visualize molecular dynamics trajectories
(using e.g. matplotlib, mayavi)
- Improved the TCODExporter (some fixes to adapt to changes of external libraries, added some
additional TCOD CIF tags, various bugfixes)

### Various fixes and improvements
- Fix for the direct scheduler on Mac OS X
- Fix for the import of computers with name collisions
- Generated backup scripts are now made profile specific and saved as `start_backup_<profile>.py`
- Fix for the vary_rounds warning


## v0.7.1

### Functionalities
- Implemented support for Kerberos authentication in the ssh transport plugin.
- Added `_get_submit_script_footer` to scheduler base class.
- Improvements of the SLURM scheduler plugin.
- Fully functional parsers for Quantumespresso CP and PW.
- Better parsing of atomic species from PW output.
- Array classes for projection & xy, and changes in kpoints class.
- Added codespecific tools for Quantumespresso.
- `verdi code list`now shows local codes too.
- `verdi export` can now export non user-defined groups (from their pk).

### Fixes
- Fixed bugs in (old) workflow manager and daemon.
- Improvements of the efficiency of the (old) workflow manager.
- Fixed JobCalculation text prepend with multiple codes.


## v0.7.0

This release introduces a lot and significant changes & enhancements.

We worked on our new backend and now AiiDA can be installed using SQLAlchemy too. Many of the verdi
commands and functionalities have been tested and are working with this backend. The full JSON
support provided by SQLAlchemy and the latest versions of PostgreSQL enable significant speed
increase in attribute related queries. SQLAlchemy backend choice is a beta option since some last
functionalities and commands need to be implemented or improved for this backend. Scripts are
provided for the transition of databases from Django backend to SQLAlchemy backend.

In this release we have included a new querying tool called `QueryBuilder`. It is a powerfull tool
allowing users to write complex graph queries to explore the AiiDA graph database. It provides
various features like selection of entity properties, filtering of results, combination of entities
on specific properties as well as various ways to obtain the final result. It also provides the
users an abstract way to query their data without enforcing them to write backend dependent queries.

Last but not least we have included a new workflow engine (in beta version) which is available
through the `verdi workflow2` command. The new workflows are easier to write (it is as close as
writing python as possible), there is seamless mixing of short running tasks with long running
(remote) tasks and they encourage users to write reusable workflows. Moreover, debugging of
workflows has been made easier and it is possible both in-IDE and through logging.

### List of changes:
- Installation procedure works with SQLAlchemy backend too (SQLAlchemy option is still in beta).
- Most of the verdi commands work with SQLAlchemy backend.
- Transition script from Django schema of version 0.7.0 to SQLAlchemy schema of version 0.7.0.
- AiiDA daemon redesigned and working with both backends (Django & SQLAlchemy).
- Introducing new workflow engine that allows better debugging and easier to write workflows. It is
available under the `verdi workflows2` command. Examples are also added.
- Old workflows are still supported and available under the "verdi workflow" command.
- Introducing new querying tool (called `QueryBuilder`). It allows to easily write complex graph
queries that will be executed on the AiiDA graph database. Extensive documentation also added.
- Unifying behaviour of verdi commands in both backends.
- Upped to version 0.4.2 of plum (needed for workflows2)
- Implemented the validator and input helper for Quantum ESPRESSO pw.x.
- Improved the documentation for the pw (and cp) input plugins (for all the flags in the Settings
node).
- Fixed a wrong behavior in the QE pw/cp plugins when checking for the parser options and checking
if there were further unknown flags in the Settings node. However, this does not solve yet
completely the problem (see issue #219).
- Implemented validator and input helper for Quantum ESPRESSO pw.x.
- Added elements with Z=104-112, 114 and 116, in `aiida.common.constants`.
- Added method `set_kpoints_mesh_from_density` in `KpointsData` class.
- Improved incremental backup documentation.
- Added backup related tests.
- Added an option to `test_pw.py` to run also in serial.
- SSH transport, to connect to remote computers via SSH/SFTP.
- Support for the SGE and SLURM schedulers.
- Support for Quantum ESPRESSO Car-Parrinello calculations.
- Support for data nodes to store electronic bands, phonon dispersion and generally arrays defined
over the Brillouin zone.


## v0.6.0

We performed a lot of changes to introduce in one of our following releases a second
object-relational mapper (we will refer to it as back-end) for the management of the used DBMSs and
more specifically of PostgreSQL. SQLAlchemy and the latest version of PostgreSQL allows AiiDA to
store JSON documents directly to the database and also to query them. Moreover the JSON query
optimization is left to the database including also the use of the JSON specific indexes. There was
major code restructuring to accommodate the new back-end resulting to abstracting many classes of
the orm package of AiiDA.

Even if most of the needed restructuring & code addition has been finished, a bit of more work is
needed. Therefore even in this version, Django is the only available back-end for the end user.

However, the users have to update their AiiDA configuration files by executing the migration file
that can be found at `YOUR_AIIDA_DIR/aiida/common/additions/migration.py` as the Linux user that
installed AiiDA in your system.
(e.g. `python YOUR_AIIDA_DIR/aiida/common/additions/migration.py`)

### List of changes:
- Back-end selection (Added backend selection). SQLAlchemy selection is disabled for the moment.
- Migration scripts for the configuration files of AiiDA (SQLAlchemy support).
- Enriched link description in the database (to enrich the provenance model).
- Corrections for numpy array and cell. List will be used with cell.
- Fixed backend import. Verdi commands load as late as possible the needed backend.
- Abstraction of the basic AiiDA orm classes (like node, computer, data etc). This is needed to
support different backends (e.g. Django and SQLAlchemy).
- Fixes on the structure import from QE-input files.
- SQLAlchemy and Django benchmarks.
- UltraJSON support.
- requirements.txt now also include SQLAlchemy and its dependencies.
- Recursive way of loading JSON for SQLAlchemy.
- Improved way of accessing calculations and workflows attached to a workflow step.
- Added methods to programmatically create new codes and computers.


## v0.5.0

### General
- Final paper published, ref: G. Pizzi, A. Cepellotti, R. Sabatini, N. Marzari, and B. Kozinsky,
AiiDA: automated interactive infrastructure and database for computational science,
Comp. Mat. Sci 111, 218-230 (2016)
- Core, concrete, requirements kept in `requirements.txt` and optionals moved to
`optional_requirements.txt`
- Schema change to v1.0.2: got rid of `calc_states.UNDETERMINED`

### Import/export, backup and code interaction
- [non-back-compatible] Now supporting multiple codes execution in the same submission script.
Plugin interface changed, requires adaptation of the code plugins.
- Added import support for XYZ files
- Added support for van der Waals table in QE input
- Restart QE calculations avoiding using scratch using copy of parent calc
- Adding database importer for NNIN/C Pseudopotential Virtual Vault
- Implemented conversion of pymatgen Molecule lists to AiiDA's TrajectoryData
- Adding a converter from pymatgen Molecule to AiiDA StructureData
- Queries now much faster when exporting
- Added an option to export a zip file
- Added backup scripts for efficient incremental backup of large AiiDA repositories

### API
- Added the possibility to add any kind of Django query in Group.query
- Added TCOD (Theoretical Crystallography Open Database) importer and exporter
- Added option to sort by a field in the query tool
- Implemented selection of data nodes and calculations by group
- Added NWChem plugin
- Change default behaviour of symbolic link copy in the transport plugins: "put"/"get"
methods -> symbolic links are followed before copy; "copy" methods -> symbolic links are not
followed (copied "as is").

### Schedulers
- Explicit Torque support (some slightly different flags)
- Improved PBSPro scheduler
- Added new `num_cores_per_machine` and `num_cores_per_mpiproc fields` for pbs and torque schedulers
 (giving full support for MPI+OpenMP hybrid codes)
- Direct scheduler added, allowing calculations to be run without batch system
(i.e. directly call executable)

### verdi
- Support for profiles added: it allows user to switch between database configurations using the `verdi profile` command
- Added `verdi data structure import --file file.xyz` for importing XYZ
- Added a `verdi data upf exportfamily` command (to export an upf pseudopotential family into a folder)
- Added new functionalities to the `verdi group` command (show list of nodes, add and remove nodes
from the command line)
- Allowing verdi export command to take group PKs
- Added ASE as a possible format for visualizing structures from command line
- Added possibility to export trajectory data in xsf format
- Added possibility to show trajectory data with xcrysden
- Added filters on group name in `verdi group list`
- Added possibility to load custom modules in the verdi shell (additional property
verdishell.modules created; can be set with `verdi devel setproperty verdishell.modules`)
- Added `verdi data array show` command, using `json_date` serialization to display the contents of `ArrayData`
- Added `verdi data trajectory deposit` command line command
- Added command options `--computer` and `--code` to `verdi data * deposit`
- Added a command line option `--all-users` for `verdi data * list` to list objects, owned by all users
