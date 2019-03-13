## v1.0.0

### General

- Code has been made python 3 compatible. [[#804]](https://github.com/aiidateam/aiida_core/pull/804)[[#2136]](https://github.com/aiidateam/aiida_core/pull/2136)[[#2125]](https://github.com/aiidateam/aiida_core/pull/2125)[[#2117]](https://github.com/aiidateam/aiida_core/pull/2117)[[#2110]](https://github.com/aiidateam/aiida_core/pull/2110)[[#2100]](https://github.com/aiidateam/aiida_core/pull/2100)[[#2094]](https://github.com/aiidateam/aiida_core/pull/2094)[[#2092]](https://github.com/aiidateam/aiida_core/pull/2092)
- AiiDA now enforces UTF-8 encoding for text output in its files and databases. [[#2107]](https://github.com/aiidateam/aiida_core/pull/2107)
- Drop the `DbCalcState` table [[#2198]](https://github.com/aiidateam/aiida_core/pull/2198)
- All calculations now go through the `Process` layer, homogenizing the state of work and job calculations [[#1125]](https://github.com/aiidateam/aiida_core/pull/1125)
- Bump version of Django to `1.11.16` for py3 support [[#2206]](https://github.com/aiidateam/aiida_core/pull/2206)
- Implement new link types [[#2220]](https://github.com/aiidateam/aiida_core/pull/2220)
- Make the node repository API backend agnostic [[#2506]](https://github.com/aiidateam/aiida_core/pull/2506)
- Move the definition and import location of plugin factories [[#2498]](https://github.com/aiidateam/aiida_core/pull/2498)
- Redesign the Parser class [[#2397]](https://github.com/aiidateam/aiida_core/pull/2397)
- Remove implementation of legacy workflows [[#2379]](https://github.com/aiidateam/aiida_core/pull/2379)
- Reorganization of some top level modules [[#2357]](https://github.com/aiidateam/aiida_core/pull/2357)

### Engine and daemon
- Allow the definition of `None` as default in process functions [[#2582]](https://github.com/aiidateam/aiida_core/pull/2582)
- Implement the new `calcfunction` decorator. [[#2203]](https://github.com/aiidateam/aiida_core/pull/2203)
- Engine stability and communications improvements [[#2158]](https://github.com/aiidateam/aiida_core/pull/2158)
- Each profile now has its own daemon that can be run completely independently in parallel [[#1217]](https://github.com/aiidateam/aiida_core/pull/1217)
- Polling based daemon has been replaced with a much faster event-based daemon [[#1067]](https://github.com/aiidateam/aiida_core/pull/1067)
- Replaced `Celery` with `Circus` as the daemonizer of the daemon [[#1213]](https://github.com/aiidateam/aiida_core/pull/1213)
- The daemon can now be stopped without loading the database, making it possible to stop it even if the database version does not match the code [[#1231]](https://github.com/aiidateam/aiida_core/pull/1231)
- Ported calculation jobs to use coroutines for transport tasks [[#1827]](https://github.com/aiidateam/aiida_core/pull/1827)
- Implement exponential backoff retry mechanism for transport tasks [[#1837]](https://github.com/aiidateam/aiida_core/pull/1837)
- Pause `CalcJob` when transport task falls through exponential backoff [[#1903]](https://github.com/aiidateam/aiida_core/pull/1903)
- Separate `CalcJob` submit task in folder upload and scheduler submit [[#1946]](https://github.com/aiidateam/aiida_core/pull/1946)
- Each daemon worker now respects an optional minimum scheduler polling interval [[#1929]](https://github.com/aiidateam/aiida_core/pull/1929)
- Prevent launching or construction of `WorkChain` and `CalcJob` base class [[#2564]](https://github.com/aiidateam/aiida_core/pull/2564)
- Process queues are now properly removed and cleaned when a process terminates [[#2324]](https://github.com/aiidateam/aiida_core/pull/2324)
- Implement the concept of an "exit status" for all calculations, allowing a programmatic definition of success or failure for all processes [[#1189]](https://github.com/aiidateam/aiida_core/pull/1189)

### Workflows
- Implemented the `ProcessBuilder` which simplifies the definition of `Process` inputs and the launching of a `Process` [[#1116]](https://github.com/aiidateam/aiida_core/pull/1116)
- Namespaces have been added to the port containers of the `ProcessSpec` class [[#1099]](https://github.com/aiidateam/aiida_core/pull/1099)
- Convention of leading underscores for non-storable inputs has been replaced with a proper `non_db` attribute of the `Port` class [[#1105]](https://github.com/aiidateam/aiida_core/pull/1105)
- Implemented a Sphinx extension for the `WorkChain` class to automatically generate documentation from the workchain definition [[#1155]](https://github.com/aiidateam/aiida_core/pull/1155)
- Added new feature for a `WorkChain` to expose the inputs and outputs of another `WorkChain`, which is perfect for writing modular workflows [[#1170]](https://github.com/aiidateam/aiida_core/pull/1170)
- Add built-in support and API for exit codes in `WorkChains` [[#1640]](https://github.com/aiidateam/aiida_core/pull/1640), [[#1704]](https://github.com/aiidateam/aiida_core/pull/1704), [[#1681]](https://github.com/aiidateam/aiida_core/pull/1681)
- Overload `PortNamespace` mutable properties upon exposing [[#1635]](https://github.com/aiidateam/aiida_core/pull/1635)

### CalcJob
- Implement `CalcJob` process class that replaces the deprecated `JobCalculation` [[#2389]](https://github.com/aiidateam/aiida_core/pull/2389)
- Implement method for `CalcJobNode` to create a restart builder  [[#1962]](https://github.com/aiidateam/aiida_core/pull/1962)
- Implement the `get_options` method for `CalcJobNode` [[#1961]](https://github.com/aiidateam/aiida_core/pull/1961)
- Redefine the structure of the `CalcInfo.local_copy_list` [[#2581]](https://github.com/aiidateam/aiida_core/pull/2581)
- Add `CalculationTools` base and entry point `aiida.tools.calculations` [[#2331]](https://github.com/aiidateam/aiida_core/pull/2331)

### ORM
- Implementation of the `AuthInfo` class which will allow custom configuration per configured computer [[#1184]](https://github.com/aiidateam/aiida_core/pull/1184)
- Rename the ORM classes for `Node` sub classes `JobCalculation`, `WorkCalculation`, `InlineCalculation` and `FunctionCalculation` [[#2184]](https://github.com/aiidateam/aiida_core/pull/2184)[[#2189]](https://github.com/aiidateam/aiida_core/pull/2189)[[#2192]](https://github.com/aiidateam/aiida_core/pull/2192)[[#2195]](https://github.com/aiidateam/aiida_core/pull/2195)[[#2201]](https://github.com/aiidateam/aiida_core/pull/2201)
- Implement the new `QueryBuilder` relationship indicators [[#2224]](https://github.com/aiidateam/aiida_core/pull/2224)
- Change 'ancestor_of'/'descendant_of' to 'with_descendants'/'with_ancestors' [[#2278]](https://github.com/aiidateam/aiida_core/pull/2278)
- Add efficient `count` method for `aiida.orm.groups.Group` [[#2567]](https://github.com/aiidateam/aiida_core/pull/2567)
- Implement the new generic link traversal methods for the `Node` class [[#2236]](https://github.com/aiidateam/aiida_core/pull/2236)[[#2569]](https://github.com/aiidateam/aiida_core/pull/2569)
- Speed up creation of Nodes in the AiiDA ORM [[#2214]](https://github.com/aiidateam/aiida_core/pull/2214)
- Enable use of tuple in `QueryBuilder.append` for all ORM classes [[#1608]](https://github.com/aiidateam/aiida_core/pull/1608), [[#1607]](https://github.com/aiidateam/aiida_core/pull/1607)
- Do not allow the `copy` or `deepcopy` of `Node`, except for `Data`  [[#1705]](https://github.com/aiidateam/aiida_core/pull/1705)
- Refactored the ORM to have explicit front-end and back-end layers [[#2190]](https://github.com/aiidateam/aiida_core/pull/2190)[[#2210]](https://github.com/aiidateam/aiida_core/pull/2210)[[#2225]](https://github.com/aiidateam/aiida_core/pull/2225)[[#2227]](https://github.com/aiidateam/aiida_core/pull/2227)[[#2481]](https://github.com/aiidateam/aiida_core/pull/2481)
- Add support for indexing and slicing in `orm.Group.nodes` iterator [[#2371]](https://github.com/aiidateam/aiida_core/pull/2371)
- Implement the exporting and importing of node extras [[#2416]](https://github.com/aiidateam/aiida_core/pull/2416)
- Implement the exporting and importing of comments [[#2413]](https://github.com/aiidateam/aiida_core/pull/2413)
- Implement the exporting and importing of logs [[#2393]](https://github.com/aiidateam/aiida_core/pull/2393)
- Add support for process classes to QueryBuilder.append [[#2421]](https://github.com/aiidateam/aiida_core/pull/2421)
- Renaming `DbNode.type` to `DbNode.node_type` [[#2552]](https://github.com/aiidateam/aiida_core/pull/2552)
- Make various protected `Node` methods public [[#2544]](https://github.com/aiidateam/aiida_core/pull/2544)
- Add option to add nodes to a group through the backend interface by directly generating an `INSERT` SQL statement for SqlAlchemy [[#2518]](https://github.com/aiidateam/aiida_core/pull/2518)
- Rename the type strings of `Groups` and change the attributes `name` and `type` to `label` and `type_string` [[#2329]](https://github.com/aiidateam/aiida_core/pull/2329)
- Changed type of uuids returned by the QueryBuilder to be unicode [[#2259]](https://github.com/aiidateam/aiida_core/pull/2259)
- Prevent to store base `Node` and `ProcessNode` instances in the database but only their subclasses [[#2301]](https://github.com/aiidateam/aiida_core/pull/2301)

### Data
- Added element `X` to the elements list in order to support unknown species [[#1613]](https://github.com/aiidateam/aiida_core/pull/1613)
- Various bug and consistency fixes for `CifData` and `StructureData` [[#2374]](https://github.com/aiidateam/aiida_core/pull/2374)
- Changes to `Data` class attributes and `TrajectoryData` data storage [[#2310]](https://github.com/aiidateam/aiida_core/pull/2310)[[#2422]](https://github.com/aiidateam/aiida_core/pull/2422)
- Rename `ParameterData` to `Dict` [[#2530]](https://github.com/aiidateam/aiida_core/pull/2530)
- Remove the `FrozenDict` data sub class [[#2532]](https://github.com/aiidateam/aiida_core/pull/2532)
- Remove the `Error` data sub class [[#2529]](https://github.com/aiidateam/aiida_core/pull/2529)
- Make `Code` a real sub class of `Data` [[#2193]](https://github.com/aiidateam/aiida_core/pull/2193)
- Implement the `has_atomic_sites` and `has_unknown_species` properties for the `CifData` class [[#1257]](https://github.com/aiidateam/aiida_core/pull/1257)
- Default library used in `_get_aiida_structure` to convert the `CifData` to `StructureData` has been changed from `ase` to `pymatgen` [[#1257]](https://github.com/aiidateam/aiida_core/pull/1257)

### Verdi
- Update `verdi export` and `verdi import` to the new export archive version `v0.4` [[#2554]](https://github.com/aiidateam/aiida_core/pull/2554)
- Implement tab-completion for profile in the `-p` option of `verdi` [[#2345]](https://github.com/aiidateam/aiida_core/pull/2345)
- Migrate `verdi` to the click infrastructure [[#1795]](https://github.com/aiidateam/aiida_core/pull/1795)
- Allow existing profile to be overriden in `verdi setup` [[#2244]](https://github.com/aiidateam/aiida_core/pull/2244)
- Added new command `verdi config` that supercedes the `verdi devel *property*` family of commands  [[#2354]](https://github.com/aiidateam/aiida_core/pull/2354)
- Added new command `verdi data upf content` [[#2468]](https://github.com/aiidateam/aiida_core/pull/2468)
- Added new command `verdi status` to give an overview of the status of required external components [[#2487]](https://github.com/aiidateam/aiida_core/pull/2487)
- Added new command `verdi process` to interact with running processes [[#1855]](https://github.com/aiidateam/aiida_core/pull/1855)
- Added new command `verdi group rename` [[#1224]](https://github.com/aiidateam/aiida_core/pull/1224)
- Added new command `verdi code duplicate` [[#1737]](https://github.com/aiidateam/aiida_core/pull/1737)
- Added new command `verdi computer duplicate` [[#1937]](https://github.com/aiidateam/aiida_core/pull/1937)
- Added new command `verdi profile show` [[#2028]](https://github.com/aiidateam/aiida_core/pull/2028)
- Added new command `verdi work show` [[#1816]](https://github.com/aiidateam/aiida_core/pull/1816)
- Added new command `verdi export inspect` [[#2128]](https://github.com/aiidateam/aiida_core/pull/2128)
- Added new command `verdi database migrate` [[#2334]](https://github.com/aiidateam/aiida_core/pull/2334)
- Added new command `verdi database integrity` with endpoints for links and nodes [[#2343]](https://github.com/aiidateam/aiida_core/pull/2343)
- Add `--group` option to `verdi process list` [[#2254]](https://github.com/aiidateam/aiida_core/pull/2254)
- Homogenize the interface of `verdi quicksetup` and `verdi setup` [[#1797]](https://github.com/aiidateam/aiida_core/pull/1797)
- Add the option `--version` to `verdi` to display current version [[#1811]](https://github.com/aiidateam/aiida_core/pull/1811)
- `verdi work tree` has been removed in favor of `verdi process status` [[#1299]](https://github.com/aiidateam/aiida_core/pull/1299)
- `verdi code show` no longer shows number of calculations by default to improve performance, with `--verbose` flag to restore old behavior [[#1428]](https://github.com/aiidateam/aiida_core/pull/1428)
- `verdi export create` set `allowZip64=True` as the default when exporting as zip file [[#1619]](https://github.com/aiidateam/aiida_core/pull/1619)
- Improve error message for `verdi import` when archive version is incompatible [[#1960]](https://github.com/aiidateam/aiida_core/pull/1960)
- Modularize `verdi profile delete` [[#2151]](https://github.com/aiidateam/aiida_core/pull/2151)
- Bug fix for `verdi node delete` [[#2545]](https://github.com/aiidateam/aiida_core/pull/2545)

### Database
- Add an index to columns of `DbLink` for SqlAlchemy [[#2561]](https://github.com/aiidateam/aiida_core/pull/2561)
- Creating unique constraint and indexes at the `db_dbgroup_dbnodes` table for SqlAlchemy [[#1680]](https://github.com/aiidateam/aiida_core/pull/1680)
- Performance improvement for adding nodes to group [[#1677]](https://github.com/aiidateam/aiida_core/pull/1677)
- Make UUID columns unique in SqlAlchemy [[#2323]](https://github.com/aiidateam/aiida_core/pull/2323)
- Allow PostgreSQL connections via unix sockets [[#1721]](https://github.com/aiidateam/aiida_core/pull/1721)

### Schedulers
- Renamed `aiida.daemon.execmanager.job_states` to `JOB_STATES`, conforming to python conventions [[#1799]](https://github.com/aiidateam/aiida_core/pull/1799)
- Abstract method `aiida.scheduler.Scheduler._get_detailed_jobinfo_command()` raises `aiida.common.exceptions.FeatureNotAvailable` (was `NotImplemented`).

### Importers
- Added an importer class for the Materials Platform of Data Science API, which exposed the content of the Pauling file [[#1238]](https://github.com/aiidateam/aiida_core/pull/1238)
- Added an importer class for the Materials Project API [[#2097]](https://github.com/aiidateam/aiida_core/pull/2097)

### REST API
- Added node label in the tree end point response [[#2511]](https://github.com/aiidateam/aiida_core/pull/2511)
- Added an IOtree limit [[#2458]](https://github.com/aiidateam/aiida_core/pull/2458)

### Documentation
- Document optional graphviz dependency and removed use of os.system() in draw_graph [[#2287]](https://github.com/aiidateam/aiida_core/pull/2287)
- Document the Windows Subsystem for Linux [[#2319]](https://github.com/aiidateam/aiida_core/pull/2319)
- Add documentation for plugin fixtures [[#2314]](https://github.com/aiidateam/aiida_core/pull/2314)
- Big reorganization of the documentation structure [[#1299]](https://github.com/aiidateam/aiida_core/pull/1299)
- Added section on the basics of workchains and workfunctions [[#1384]](https://github.com/aiidateam/aiida_core/pull/1384)
- Added section on how to launch workchains and workfunctions [[#1385]](https://github.com/aiidateam/aiida_core/pull/1385)
- Added section on how to monitor workchains and workfunctions[[#1387]](https://github.com/aiidateam/aiida_core/pull/1387)
- Added section on the concept of the `Process` [[#1395]](https://github.com/aiidateam/aiida_core/pull/1395)
- Added section on advance concepts of the `WorkChain` class, as well as best-practices on designing/writing workchains [[#1459]](https://github.com/aiidateam/aiida_core/pull/1459)
- Remove outdated or duplicated docs for legacy and new workflow system [[#1718]](https://github.com/aiidateam/aiida_core/pull/1718)
- Added entry of potential issues for transports that enter bash login shells that write spurious output [[#2132]](https://github.com/aiidateam/aiida_core/pull/2132)

### Bug fixes
- Escape newline chars in strings used to label nodes in visual provenance graphs [[#2275]](https://github.com/aiidateam/aiida_core/pull/2275)
- Enforced the behavior of queries to ressemble backend, by disallowing deduplication of results by SQLAlchemy [[#2281]](https://github.com/aiidateam/aiida_core/pull/2281)
- Improve robustness of parsing versions and element names from UPF files [[#2296]](https://github.com/aiidateam/aiida_core/pull/2296)
- Prevent `verdi` from failing on empty profile list [[#2425]](https://github.com/aiidateam/aiida_core/pull/2425)
- Fix bug in `delete_nodes` when passing pks of non-existing nodes [[#2440]](https://github.com/aiidateam/aiida_core/pull/2440)
- Catch `UnroutableError` for orphaned processes in `verdi process` calls [[#2445]](https://github.com/aiidateam/aiida_core/pull/2445)
- Remove unserializable data from metadata in `Log` records [[#2469]](https://github.com/aiidateam/aiida_core/pull/2469)
- Fix bug in `verdi quicksetup` where check for existing profile was done too late [[#2473]](https://github.com/aiidateam/aiida_core/pull/2473)
- Fix BandsData issue related to the k-points labels [[#2492]](https://github.com/aiidateam/aiida_core/pull/2492)
- Fix bug in `TemplatereplacerCalculation` input check [[#2583]](https://github.com/aiidateam/aiida_core/pull/2583)
- Fix bug in `parse_formula` for formula's with leading or trailing whitespace [[#2186]](https://github.com/aiidateam/aiida_core/pull/2186)
- Fix leaking of SSH processes when using a proxy command for a computer using SSH transport [[#2019]](https://github.com/aiidateam/aiida_core/pull/2019)
- Fixed a problem with the temporary folder containing the files of the `retrieve_temporary_list` that could be cleaned before parsing finished [[#1168]](https://github.com/aiidateam/aiida_core/pull/1168)
- Fixed a bug in the `store` method of `CifData` which would raise and exception when called more than once [[#1136]](https://github.com/aiidateam/aiida_core/pull/1136)
- Restored a proper implementation of mutability for `Node` attributes [[#1181]](https://github.com/aiidateam/aiida_core/pull/1181)
- Restore the correct plugin type string based on the module path of the base `Data` types [[#1192]](https://github.com/aiidateam/aiida_core/pull/1192)
- Fix bug in `verdi export create` when only exporting computers [[#1448]](https://github.com/aiidateam/aiida_core/pull/1448)
- Fix copying of the calculation raw input folder in caching [[#1745]](https://github.com/aiidateam/aiida_core/pull/1745)
- Fix sphinxext command by allowing whitespace in argument [[#1644]](https://github.com/aiidateam/aiida_core/pull/1644)
- Check for `test_` keyword in repo path only on last directory during profile setup [[#1812]](https://github.com/aiidateam/aiida_core/pull/1812)
- Fix bug in the `RemoteData._clean` method [[#1847]](https://github.com/aiidateam/aiida_core/pull/1847)
- Fix the formatting of `verdi calculation logshow` [[#1850]](https://github.com/aiidateam/aiida_core/pull/1850)
- Differentiate `quicksetup` profile settings based on project folder [[#1901]](https://github.com/aiidateam/aiida_core/pull/1901)
- Ensure `WorkChain` does not exit unless stepper returns non-zero value [[#1945]](https://github.com/aiidateam/aiida_core/pull/1945)
- Fix variable `virtual_memory_kb` in direct scheduler. [[#2050]](https://github.com/aiidateam/aiida_core/pull/2050)
- Compile the scripts before calling exec in `verdi run` to keep introspection functional [[#2166]](https://github.com/aiidateam/aiida_core/pull/2166)

### Developers
- Move requirements from setup_requirements.py to setup.json [[#2307]](https://github.com/aiidateam/aiida_core/pull/2307)
- Refactor the management of the configuration file [[#2349]](https://github.com/aiidateam/aiida_core/pull/2349)
- Add a transaction context manager to backend [[#2387]](https://github.com/aiidateam/aiida_core/pull/2387)
- Enable tab-completion for `verdi devel tests` [[#1809]](https://github.com/aiidateam/aiida_core/pull/1809)
- Add `-v/--verbose` flag to `verdi devel tests` [[#1807]](https://github.com/aiidateam/aiida_core/pull/1807)

## v0.12.3
### Improvements
- Fast addition of nodes to groups with `skip_orm=True` [[#2471]](https://github.com/aiidateam/aiida_core/pull/2471)
- Add `environment.yml` for installing dependencies using conda; release of `aiida-core` on conda-forge channel [[#2081]](https://github.com/aiidateam/aiida_core/pull/2081)
- REST API: io tree response now includes link type and node label [[#2033]](https://github.com/aiidateam/aiida_core/pull/2033) [[#2511]](https://github.com/aiidateam/aiida_core/pull/2511)
- Backport postgres improvements for quicksetup [[#2433]](https://github.com/aiidateam/aiida_core/pull/2433)
- Backport `aiida.get_strict_version` (for plugin development) [[#2099]](https://github.com/aiidateam/aiida_core/pull/2099)

### Minor bug fixes
- Fix security vulnerability by upgrading `paramiko` to `2.4.2` [[#2043]](https://github.com/aiidateam/aiida_core/pull/2043)
- Disable caching for inline calculations (broken since move to ``workfunction``-based implementation) [[#1872]](https://github.com/aiidateam/aiida_core/pull/1872)
- Let `verdi help` return exit status 0 [[#2434]](https://github.com/aiidateam/aiida_core/pull/2434)
- Decode dict keys only if strings (backport) [[#2436]](https://github.com/aiidateam/aiida_core/pull/2436)
- Remove broken verdi-plug entry point [[#2356]](https://github.com/aiidateam/aiida_core/pull/2356)
- `verdi node delete` (without arguments) no longer tries to delete all nodes [[#2545]](https://github.com/aiidateam/aiida_core/pull/2545)
- Fix plotting of `BandsData` objects [[#2492]](https://github.com/aiidateam/aiida_core/pull/2492)

### Miscellaneous
- REST API: add tests for random sorting list entries of same type [[#2106]](https://github.com/aiidateam/aiida_core/pull/2106)
- Add various badges to README [[#1969]](https://github.com/aiidateam/aiida_core/pull/1969)
- Minor documentation improvements [[#1955]](https://github.com/aiidateam/aiida_core/pull/1955)
- Add license file to MANIFEST [[#2339]](https://github.com/aiidateam/aiida_core/pull/2339)
- Add instructions when `verdi import` fails [[#2420]](https://github.com/aiidateam/aiida_core/pull/2420)

## v0.12.2

### Improvements
- Support the hashing of `uuid.UUID` types by registering a hashing function  [[#1861]](https://github.com/aiidateam/aiida_core/pull/1861)
- Add documentation on plugin cutter [[#1904]](https://github.com/aiidateam/aiida_core/pull/1904)

### Minor bug fixes
- Make exported graphs consistent with the current node and link hierarchy definition [[#1764]](https://github.com/aiidateam/aiida_core/pull/1764)
- Fix link import problem under SQLA [[#1769]](https://github.com/aiidateam/aiida_core/pull/1769)
- Fix cache folder copying [[#1746]](https://github.com/aiidateam/aiida_core/pull/1746) [[1752]](https://github.com/aiidateam/aiida_core/pull/1752)
- Fix bug in mixins.py when copying node [[#1743]](https://github.com/aiidateam/aiida_core/pull/1743)
- Fix pgtest failures (release-branch) on travis [[#1736]](https://github.com/aiidateam/aiida_core/pull/1736)
- Fix plugin: return testrunner result to fail on travis, when tests don't pass [[#1676]](https://github.com/aiidateam/aiida_core/pull/1676)

### Miscellaneous
- Remove pycrypto dependency, as it was found to have sercurity flaws [[#1754]](https://github.com/aiidateam/aiida_core/pull/1754)
- Set xsf as default format for structures visualization [[#1756]](https//github.com/aiidateam/aiida_core/pull/1756)
- Delete unused `utils/create_requirements.py` file [[#1702]](https//github.com/aiidateam/aiida_core/pull/1702)


## v0.12.1

### Improvements
- Always use a bash login shell to execute all remote SSH commands, overriding any system default shell [[#1502]](https://github.com/aiidateam/aiida_core/pull/1502)
- Reduced the size of the distributed package by almost half by removing test fixtures and generating the data on the fly [[#1645]](https://github.com/aiidateam/aiida_core/pull/1645)
- Removed the explicit dependency upper limit for `scipy` [[#1492]](https://github.com/aiidateam/aiida_core/pull/1492)
- Resolved various dependency requirement conflicts [[#1488]](https://github.com/aiidateam/aiida_core/pull/1488)

### Minor bug fixes
- Fixed a bug in `verdi node delete` that would throw an exception for certain cases [[#1564]](https://github.com/aiidateam/aiida_core/pull/1564)
- Fixed a bug in the `cif` endpoint of the REST API [[#1490]](https://github.com/aiidateam/aiida_core/pull/1490)


## v0.12.0

### Improvements
- Hashing, caching and fast-forwarding [[#652]](https://github.com/aiidateam/aiida_core/pull/652)
- Calculation no longer stores full source file [[#1082]](https://github.com/aiidateam/aiida_core/pull/1082)
- Delete nodes via `verdi node delete` [[#1083]](https://github.com/aiidateam/aiida_core/pull/1083)
- Import structures using ASE [[#1085]](https://github.com/aiidateam/aiida_core/pull/1085)
- `StructureData` - `pymatgen` - `StructureData` roundtrip works for arbitrary kind names [[#1285]](https://github.com/aiidateam/aiida_core/pull/1285) [[#1306]](https://github.com/aiidateam/aiida_core/pull/1306) [[#1357]](https://github.com/aiidateam/aiida_core/pull/1357)
- Output format of export file can now be defined for `verdi export migrate` [[#1383]](https://github.com/aiidateam/aiida_core/pull/1383)
- Automatic reporting of code coverage by unit tests has been added [[#1422]](https://github.com/aiidateam/aiida_core/pull/1422)

### Critical bug fixes
- Add `parser_name` `JobProcess` options [[#1118]](https://github.com/aiidateam/aiida_core/pull/1118)
- Node attribute reads were not always up to date across interpreters for SqlAlchemy [[#1379]](https://github.com/aiidateam/aiida_core/pull/1379)

### Minor bug fixes
- Cell vectors not printed correctly [[#1087]](https://github.com/aiidateam/aiida_core/pull/1087)
- Fix read-the-docs issues [[#1120]](https://github.com/aiidateam/aiida_core/pull/1120) [[#1143]](https://github.com/aiidateam/aiida_core/pull/1143)
- Fix structure/band visualization in REST API [[#1167]](https://github.com/aiidateam/aiida_core/pull/1167) [[#1182]](https://github.com/aiidateam/aiida_core/pull/1182)
- Fix `verdi work list` test [[#1286]](https://github.com/aiidateam/aiida_core/pull/1286)
- Fix `_inline_to_standalone_script` in `TCODExporter` [[#1351]](https://github.com/aiidateam/aiida_core/pull/1351)
- Updated `reentry` to fix various small bugs related to plugin registering [[#1440]](https://github.com/aiidateam/aiida_core/pull/1440)

### Miscellaneous
- Bump `qe-tools` version [[#1090]](https://github.com/aiidateam/aiida_core/pull/1090)
- Document link types [[#1174]](https://github.com/aiidateam/aiida_core/pull/1174)
- Switch to trusty + postgres 9.5 on Travis [[#1180]](https://github.com/aiidateam/aiida_core/pull/1180)
- Use raw SQL in sqlalchemy migration of `Code` [[#1291]](https://github.com/aiidateam/aiida_core/pull/1291)
- Document querying of list attributes [[#1326]](https://github.com/aiidateam/aiida_core/pull/1326)
- Document running `aiida` as a daemon service [[#1445]](https://github.com/aiidateam/aiida_core/pull/1445)
- Document that Torque and LoadLever schedulers are now fully supported [[#1447]](https://github.com/aiidateam/aiida_core/pull/1447)
- Cookbook: how to check the number of queued/running jobs in the scheduler [[#1349]](https://github.com/aiidateam/aiida_core/pull/1349)


## v0.11.4

### Improvements
- PyCifRW upgraded to 4.2.1 [[#1073]](https://github.com/aiidateam/aiida_core/pull/1073)

### Critical bug fixes
- Persist and load parsed workchain inputs and do not recreate to avoid creating duplicates for default inputs [[#1362]](https://github.com/aiidateam/aiida_core/pull/1362)
- Serialize `WorkChain` context before persisting [[#1354]](https://github.com/aiidateam/aiida_core/pull/1354)


## v0.11.3

### Improvements
- Documentation: AiiDA now has an automatically generated and complete API documentation (using `sphinx-apidoc`) [[#1330]](https://github.com/aiidateam/aiida_core/pull/1330)
- Add JSON schema for connection of REST API to Materials Cloud Explore interface  [[#1336]](https://github.com/aiidateam/aiida_core/pull/1336)

### Critical bug fixes
- `FINISHED_KEY` and `FAILED_KEY` variables were not known to `AbstractCalculation` [[#1314]](https://github.com/aiidateam/aiida_core/pull/1314)

### Minor bug fixes
- Make 'REST' extra lowercase, such that one can do `pip install aiida-core[rest]` [[#1328]](https://github.com/aiidateam/aiida_core/pull/1328)
- `CifData` `/visualization` endpoint was not returning data [[#1328]](https://github.com/aiidateam/aiida_core/pull/1328)

### Deprecations
- `QueryTool` (was deprecated in favor of `QueryBuilder` since v0.8.0) [[#1330]](https://github.com/aiidateam/aiida_core/pull/1330)

### Miscellaneous
- Add `gource` config for generating a video of development history [[#1337]](https://github.com/aiidateam/aiida_core/pull/1337)


## v0.11.2:

### Critical bug fixes
- Link types were not respected in `Node.get_inputs` for SqlAlchemy [[#1271]](https://github.com/aiidateam/aiida_core/pull/1271)


## v0.11.1:

### Improvements
- Support visualization of structures and cif files with VESTA [[#1093]](https://github.com/aiidateam/aiida_core/pull/1093)
- Better fallback when node class is not available [[#1185]](https://github.com/aiidateam/aiida_core/pull/1185)
- `CifData` now supports faster parsing and lazy loading [[#1190]](https://github.com/aiidateam/aiida_core/pull/1190)
- REST endpoint for `CifData`, API reports full list of available endpoints [[#1228]](https://github.com/aiidateam/aiida_core/pull/1228)
- Various smaller improvements [[#1100]](https://github.com/aiidateam/aiida_core/pull/1100) [[#1182]](https://github.com/aiidateam/aiida_core/pull/1182)

### Critical bug fixes
- Restore attribute immutability in nodes [[#1111]](https://github.com/aiidateam/aiida_core/pull/1111)
- Fix daemonization issue that could cause aiida daemon to be killed [[#1246]](https://github.com/aiidateam/aiida_core/pull/1246)

### Minor bug fixes
- Fix type column in `verdi calculation list` [[#960]](https://github.com/aiidateam/aiida_core/pull/960) [[#1053]](https://github.com/aiidateam/aiida_core/pull/1053)
- Fix `verdi import` from URLs [[#1139]](https://github.com/aiidateam/aiida_core/pull/1139)


## v0.11.0:

### Improvements

#### Core entities
- `Computer`: the shebang line is now customizable [[#940]](https://github.com/aiidateam/aiida_core/pull/940)
- `KpointsData`: deprecate buggy legacy implementation of k-point generation in favor of Seekpath [[#1015]](https://github.com/aiidateam/aiida_core/pull/1015)
- `Dict`: `to_aiida_type` used on dictionaries now automatically converted to `Dict` [[#947]](https://github.com/aiidateam/aiida_core/pull/947)
- `JobCalculation`: parsers can now specify files that are retrieved locally for parsing, but only temporarily, as they are deleted after parsing is completed [[#886]](https://github.com/aiidateam/aiida_core/pull/886) [[#894]](https://github.com/aiidateam/aiida_core/pull/894)

#### Plugins
- Plugin data hooks: plugins can now add custom commands to `verdi data` [[#993]](https://github.com/aiidateam/aiida_core/pull/993)
- Plugin fixtures: simple-to-use decorators for writing tests of plugins [[#716]](https://github.com/aiidateam/aiida_core/pull/716) [[#865]](https://github.com/aiidateam/aiida_core/pull/865)
- Plugin development: no longer swallow `ImportError` exception during import of plugins [[#1029]](https://github.com/aiidateam/aiida_core/pull/1029)

#### Verdi
- `verdi shell`: improve tab completion of imports in  [[#1008]](https://github.com/aiidateam/aiida_core/pull/1008)
- `verdi work list`: projections for verdi work list [[#847]](https://github.com/aiidateam/aiida_core/pull/847)

#### Miscellaneous
- Supervisor removal: dependency on unix-only supervisor package removed [[#790]](https://github.com/aiidateam/aiida_core/pull/790)
- REST API: add server info endpoint, structure endpoint can return different file formats [[#878]](https://github.com/aiidateam/aiida_core/pull/878)
- REST API: update endpoints for structure visualization, calculation (includes retrieved input & output list), add endpoints for `UpfData` and more [[#977]](https://github.com/aiidateam/aiida_core/pull/977) [[#991]](https://github.com/aiidateam/aiida_core/pull/991)
- Tests using daemon run faster [[#870]](https://github.com/aiidateam/aiida_core/pull/870)
- Documentation: updated outdated workflow examples [[#948]](https://github.com/aiidateam/aiida_core/pull/948)
- Documentation: updated import/export [[#994]](https://github.com/aiidateam/aiida_core/pull/994), 
- Documentation: plugin quickstart [[#996]](https://github.com/aiidateam/aiida_core/pull/996), 
- Documentation: parser example [[#1003]](https://github.com/aiidateam/aiida_core/pull/1003) 

### Minor bug fixes
- Fix bug with repository on external hard drive [[#982]](https://github.com/aiidateam/aiida_core/pull/982)
- Fix bug in configuration of pre-commit hooks [[#863]](https://github.com/aiidateam/aiida_core/pull/863)
- Fix and improve plugin loader tests [[#1025]](https://github.com/aiidateam/aiida_core/pull/1025)
- Fix broken celery logging [[#1033]](https://github.com/aiidateam/aiida_core/pull/1033)

### Deprecations
- async from aiida.work.run has been deprecated because it can lead to race conditions and thereby unexpected behavior [[#1040]](https://github.com/aiidateam/aiida_core/pull/1040)


## v0.10.1:

### Improvements
- Improved exception handling for loading db tests [[#968]](https://github.com/aiidateam/aiida_core/pull/968)
- `verdi work kill` on workchains: skip calculation if it cannot be killed, rather than stopping [[#980]](https://github.com/aiidateam/aiida_core/pull/980)
- Remove unnecessary INFO messages of Alembic for SQLAlchemy backend [[#1012]](https://github.com/aiidateam/aiida_core/pull/1012)
- Add filter to suppress unnecessary log messages during testing [[#1014]](https://github.com/aiidateam/aiida_core/pull/1014)

### Critical bug fixes
- Fix bug in `verdi quicksetup` on Ubuntu 16.04 and add regression tests to catch similar problems in the future [[#976]](https://github.com/aiidateam/aiida_core/pull/976)
- Fix bug in `verdi data` list commands for SQLAlchemy backend [[#1007]](https://github.com/aiidateam/aiida_core/pull/1007)

### Minor bug fixes
- Various bug fixes related to workflows for the SQLAlchemy backend [[#952]](https://github.com/aiidateam/aiida_core/pull/952) [[#960]](https://github.com/aiidateam/aiida_core/pull/960)


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
- Added a "quickstart" to plugin development in the [documentation](http://aiida-core.readthedocs.io/en/v0.10.0/developer_guide/plugins/quickstart.html),
  structured around the new [plugintemplate](https://github.com/aiidateam/aiida-plugin-template) [[#818]](https://github.com/aiidateam/aiida_core/pull/818)
- Improved and restructured the developer documentation [[#818]](https://github.com/aiidateam/aiida_core/pull/818)


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
