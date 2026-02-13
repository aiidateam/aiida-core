# Design evolution

This document records the evolution of the design and architecture of AiiDA, including the underlying reasoning.

## Version 1.0.0

(design-changes-1-0-0-provenance-redesign)=
### The provenance redesign

In the early stages of AiiDA, the concept of its provenance graph was simple.
Data is used as input for calculations, that in turn create new data as output.
The data and calculations, produced and ran by AiiDA, were stored as nodes in a graph.
Due to the causality principle, the resulting graph was naturally acyclic, as no piece of data could possibly also have been an input to its own creation.
The directed acyclic graph that stored the data provenance in AiiDA was well defined and all was good.

However, as AiiDA matured, its use cases became more complex and soon there was a need to be able to define and run workflows.
Workflows allow the user to define a sequence of calculations, that ultimately produce a result.
In order to be able to retrieve the final result directly from the workflow, it needed to be able to return the data created by the calculations that it ran.
"Easy peasy: we simply add a `return` link from the workflow node in the graph to the created data node".
But what seemed like an easy solution brought a host of unforeseen problems with it.
By introducing the concept of a `return` link, the acyclicity of the graph was broken, and with it, much of AiiDA's graph traversal API that assumed this property.

After more than a year of discussion, AiiDA developers and users concluded that the concept of the `return` link was absolutely crucial.
Without it, the results of complicated and heavily nested workflows will be buried deep within their call stack and difficult to retrieve.
The alternative was to redesign the provenance graph architecture such that acyclicity would be returned to part of the provenance graph, while keeping the utility of the `return` link.
The AiiDA development team, in close collaboration with advanced users, spent a year and a half, redesigning the provenance architecture and implementing the changes into AiiDA's API.
As always, we have tried our best to allow early adopters of AiiDA to migrate their existing databases to newer versions as easy as possible, by providing automatic migration.
This time around is no different, except for the fact that the migration was a lot more complicated and unfortunately this time some backwards-incompatible changes had to be introduced in the API.

A more detailed explanation of the new provenance design and the motivation can be found {ref}`here <topics:provenance>`.

(design-changes-1-0-0-calcjob-redesign)=
### The calculation job redesign

The calculation job has been one of the most used and important components of AiiDA as it represents a calculation that is submitted to a scheduler, often on a remote cluster.
From its earliest conception, the class that implemented this feature, the `JobCalculation`, fulfilled two major but very distinct tasks.
On one side, it provided the means to the user to specify what inputs the calculation required, how the actual input files should be constructed, and what files should be retrieved after completion.
In addition to that, since it was a sub class of the `Node` class, it also functioned as a record in the provenance graph of an actual calculation that was executed.
This double role was leading to problems with the `Node` class becoming too complicated as well as inconsistent.
For example, an instance representing an already completed calculation would also still have the methods on how to run it again.

This problem was solved with the introduction of the `WorkChain` in `aiida-core` version `0.7.0`.
Like the `JobCalculation`, the `WorkChain` was a process that takes certain inputs and then performs operations on those in order to produce outputs.
However, unlike the `JobCalculation`, the `WorkChain` class was only concerned with knowledge of *how* the process should be run.
To represent the execution of the `WorkChain` in the provenance graph, a different class was used, namely the `WorkChainNode`.
This separation of responsibilities leads to two entities with a clearer interface and behavior.

For quite a few versions, the old and new way of defining and running processes were kept functional alongside one another, but slowly the old way was adapted to use the new mechanism.
In `aiida-core` version `1.0.0` we fully deprecated the old way and all calculations now use the process/node duality.
As a result the `JobCalculation` class has disappeared.
Now, instead, a `CalcJobNode` is created in the provenance graph to represent the execution of a calculation through a scheduler.
Moreover, to implement the plugin for a calculation job, one now subclasses the `Process` subclass `CalcJob`, whose interface is the same as that of the `WorkChain`.

Inputs, outputs and potentially exit codes are simply implemented in the `define` class method, just as you would for the `WorkChain`.
Unlike the `WorkChain`, however, the `CalcJob` does not have an outline, but instead just has a single method that should be implemented, namely `prepare_for_submission`.
This method takes a single argument `folder` which will point to a temporary folder to which the required input files for the calculation can be written.
From a plugin developer standpoint, the rest works exactly as before, and the `prepare_for_submission` method should return a `CalcInfo` object, containing information for the engine on what files to copy over and to retrieve.

A more detailed explanation about the new `CalcJob` and best practices for writing `Parser` implementations can be found {ref}`here <topics:calculations:usage:calcjobs>`.

(design-changes-1-0-0-module-hierarchy)=
### The module hierarchy and importing

AiiDA has been developed and used since 2013 and in the past years we have tried, as much as possible, to reduce the changes to the Python API over time to a minimum.
At the same time, a lot of new functionality has been added to the code, with a potentially complex submodule structure for the AiiDA Python package, that had started to become too complex even just to remember where to find a given function or class.

With `aiida-core` version `1.0.0`, we decided to restructure the package module hierarchy, moving functions and classes to more intuitive locations, and exposing functionality that is commonly used by users at higher levels (e.g., now one can do `from aiida.orm import CalcJobNode` in addition to `from aiida.orm.nodes.process.calculation.calcjob import CalcJobNode`).

Albeit this change was essential to increase usability, we want to guarantee a high degree of stability for users for the components that are intended to be public.
To facilitate this, we explain here first the module hierarchy of `aiida-core`, what parts of its API are intended to be public and how those should be preferentially imported.

The first level of the package hierarchy is the `aiida` module.
It contains many other packages within it, such as `orm` and `engine`, which we will refer to as second-level packages, each of which can have a much deeper hierarchy within it.
Since this internal structure is mostly to simplify development and for organizational purposes, the components of the `aiida` package that should be usable are exposed on the second-level packages at most.
Practically this means that anything that is intended to be used should be importable from a second-level package, for example:

```python
from aiida.engine import WorkChain, calcfunction
from aiida.orm import load_node, CalcJobNode
```

With the definition of public components of the `aiida-core` package in place, from `1.0.0` we maintain a standard deprecation policy to minimize the amount of breaking changes for plugins and users.
In particular we strive to:

- Not change the API of public components as much as possible
- If we are forced to change it anyway, deprecate a significant amount of time in advance
- For backwards incompatible changes, increase the major version

For better clarity, we are {ref}`curating a list of classes and functions<reference:api:public>` (exposed at the second level) that are intended to be public and for which the above policy will be enforced.

## Version 0.9.0

### The plugin system

The plugin system was designed with the following goals in mind:

* **Sharing of calculations, workflows and data types**: plugins are bundled in a Python package, distributed as a zip source archive, Python egg, or PyPI package. There is extensive documentation available for how to [distribute Python packages](https://packaging.python.org/en/latest/).

* **Ease of use**: plugins are listed on the [AiiDA plugin registry](https://aiidateam.github.io/aiida-registry/) and can be installed with one simple command. This process is familiar to every regular Python user.

* **Decouple development and update cycles of AiiDA and plugins**: since plugins are separate Python packages, they can be developed in a separate code repository and updated when the developer sees fit without a need to update AiiDA. Similarly, if AiiDA is updated, plugins may not need to release a new version.

* **Promote modular design in AiiDA development**: separating plugins into their own Python packages ensures that plugins cannot (easily) access parts of the AiiDA code which are not part of the public API, enabling AiiDA development to stay agile. The same applies to plugins relying on other plugins.

* **Low overhead for developers**: plugin developers can write their extensions the same way they would write any Python code meant for distribution.

* **Automatic AiiDA setup and testing of plugins**: installation of complete Python environments consisting of many packages can be automated, provided all packages use `setuptools` as a distribution tool. This enables use of AiiDA in a service-based way using, e.g., Docker images. At the same time it becomes possible to create automated tests for any combination of plugins, as long as the plugins provide test entry points.

The chosen approach to plugins has some limitations:

* The interface for entry point objects is enforced implicitly by the way the object is used. It is the responsibility of the plugin developer to test for compliance, especially if the object is not derived from the recommended base classes provided by AiiDA.
* The freedom of the plugin developer to name and rename classes ends where the information in question is stored in the database as, e.g., node attributes.
* The system is designed with the possibility of plugin versioning in mind, however this is not implemented yet.
* In principle, two different plugins can give the same name to an entry point, creating ambiguity when trying to load the associated objects. Plugin development guidelines in the documentation advise on how to avoid this problem, and this is addressed via the use of a centralized registry of known AiiDA plugins.
* Plugins can potentially contain malicious or otherwise dangerous code. In the registry of AiiDA plugins, we try to flag plugins that we know are safe to use.
