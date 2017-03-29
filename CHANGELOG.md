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
