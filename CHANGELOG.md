## v0.10.0:

### Major changes
- The `DbPath` table has been removed and replaced with a dynamic transitive closure, because, among others, nested workchains could lead to the `DbPath` table exploding in size
- Code plugins have been removed from `aiida_core` and have been migrated to their own respective plugin repositories and can be found here:
    * [Quantum ESPRESSO](https://github.com/aiidateam/aiida-quantumespresso)
    * [ASE](https://github.com/aiidateam/aiida-ase)
    * [COD tools](https://github.com/aiidateam/aiida-codtools)
    * [NWChem](https://github.com/aiidateam/aiida-nwchem)

    Each can be installed from `pip` using e.g. `pip install aiida-quantumespresso`.
    Existing installations will require a migration (see [update instructions in the documentation](https://aiida-core.readthedocs.io/en/v0.10.0/installation/updating.html#plugin-migration)).
    For a complete overview of available plugins you can visit [the registry](https://aiidateam.github.io/aiida-registry/).

### Improvements
- A new entry `retrieve_temporary_list` in `CalcInfo` allows to retrieve files temporarily for parsing, while not having to store them permanently in the repository [[#903]](https://github.com/aiidateam/aiida_core/pull/903)
- New verdi command: `verdi work kill` to kill running workchains [[#821]](https://github.com/aiidateam/aiida_core/pull/821)
- New verdi command: `verdi data remote [ls,cat,show]` to inspect the contents of `RemoteData` objects [[#743]](https://github.com/aiidateam/aiida_core/pull/743)
- New verdi command: `verdi export migrate` allows the migration of existing export archives to new formats [[#781]](https://github.com/aiidateam/aiida_core/pull/781)
- New verdi command: `verdi profile delete` [[#606]](https://github.com/aiidateam/aiida_core/pull/606)
- Implemented a new option `-m` for the `verdi work report` command to limit the number of nested levels to be printed [[#888]](https://github.com/aiidateam/aiida_core/pull/888)
- Added a `running` field to the output of `verdi work list` to give the current state of the workchains [[#888]](https://github.com/aiidateam/aiida_core/pull/888)
- Implemented faster query to obtain database statistics [[#738]](https://github.com/aiidateam/aiida_core/pull/738)
- Added testing for automatic SqlAlchemy database migrations through alembic [[#834]](https://github.com/aiidateam/aiida_core/pull/834)
- Exceptions that are triggered in steps of a `WorkChain` are now properly logged to the `Node` making them visible through `verdi work report` [[#908]](https://github.com/aiidateam/aiida_core/pull/908)

### Critical bug fixes
- Export will now write the link types to the archive and import will properly recreate the link [[#760]](https://github.com/aiidateam/aiida_core/pull/760)
- Fix bug in workchain persistence that would lead to crashed workchains under certain conditions being resubmitted [[#728]](https://github.com/aiidateam/aiida_core/pull/728)
- Fix bug in the pickling of `WorkChain` instances containing an `_if` logical block in the outline [[#904]](https://github.com/aiidateam/aiida_core/pull/904)

### Minor bug fixes
- The logger for subclasses of `AbstractNode` is now properly namespaced to `aiida.` such that it works in plugins outside of the `aiida-core` source tree [[#897]](https://github.com/aiidateam/aiida_core/pull/897)
- Fixed a problem with the states of the direct scheduler that was causing the daemon process to hang during submission [[#879]](https://github.com/aiidateam/aiida_core/pull/879)
- Various bug fixes related to the old workflows in combination with the SqlAlchemy backend [[#889]](https://github.com/aiidateam/aiida_core/pull/889) [[#898]](https://github.com/aiidateam/aiida_core/pull/898)
- Fixed bug in `TCODexporter` [[#761]](https://github.com/aiidateam/aiida_core/pull/761)
- `verdi profile delete` now respects the configured `dbport` setting [[#713]](https://github.com/aiidateam/aiida_core/pull/713)
- Restore correct help text for `verdi --help` [[#704]](https://github.com/aiidateam/aiida_core/pull/704)
- Fixed query in the ICSD importer element that caused certain structures to be erroneously skipped [[#690]](https://github.com/aiidateam/aiida_core/pull/690)

### Miscellaneous
- Added a "quickstart" to plugin development in the [documentation](http://aiida-core.readthedocs.io/en/v0.10.0/developer_guide/plugins/quickstart.html), structured around the new [plugin template](https://github.com/aiidateam/aiida-plugin-template)
- Improved and restructured the documentation


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
- Accept BaseTypes as attributes/extras, and convert them automatically to their value. In this way, for instance, it is now possible to pass a `Int`, `Float`, `Str`, ... as value of a dictionary, and store all into a `ParameterData`.
- Switch from `pkg_resources` to reentry to allow for much faster loading of modules when possible, and therefore allowing for good speed for bash completion
- Removed obsolete code for Sqlite
- Removed `mayavi2` package from dependencies


## v0.8.1

### Exporters
- Upgraded the TCODExporter to produce CIF files, conforming to the newest (as of 2017-04-26) version of cif_tcod.dic.

## General
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
- Support for profiles added: it allows user to switch between database configurations using the  
`verdi profile` command
- Added `verdi data structure import --file file.xyz` for importing XYZ
- Added a `verdi data upf exportfamily` command (to export an upf pseudopotential family into a  
folder)
- Added new functionalities to the `verdi group` command (show list of nodes, add and remove nodes  
from the command line)
- Allowing verdi export command to take group PKs
- Added ASE as a possible format for visualizing structures from command line
- Added possibility to export trajectory data in xsf format
- Added possibility to show trajectory data with xcrysden
- Added filters on group name in `verdi group list`
- Added possibility to load custom modules in the verdi shell (additional property  
verdishell.modules created; can be set with `verdi devel setproperty verdishell.modules`)
- Added `verdi data array show` command, using `json_date` serialization to display the contents  
of `ArrayData`
- Added `verdi data trajectory deposit` command line command
- Added command options `--computer` and `--code` to `verdi data * deposit`
- Added a command line option `--all-users` for `verdi data * list` to list objects, owned by all  
users
