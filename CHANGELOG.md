# Changelog

## v2.2.1 - 2022-12-22

### Fixes
- Critical bug fix: Revert the changes of PR [#5804](https://github.com/aiidateam/aiida-core/pull/5804) released with v2.2.0, which addressed a bug when mutating nodes during `QueryBuilder.iterall`. Unfortunately, the change caused changes performed by `verdi` commands (as well as changes made in `verdi shell`) to not be persisted to the database. [[#5851]](https://github.com/aiidateam/aiida-core/pull/5851)


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

See the [Basic Tutorial](docs/source/intro/tutorial.md) for example usage.

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

See the [Basic Tutorial](docs/source/intro/tutorial.md) for example usage.

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
