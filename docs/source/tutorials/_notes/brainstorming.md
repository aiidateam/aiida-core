# AiiDA tutorial 2026 planning

[toc]

183 g + 245 g diabolo


## 2026-02-06: Brainstorming

* No invitation sent out until all the material is ready.
    * [Ali]: maybe one could still send a "save the date" message without announcing the content. Otherwise it's gonna be too much of a short notice, and poeple may not be able to attend

## Introduction

* Sexify introduction
* Examples also there: Things that people have done; not executable from our docs page
* Then, get started as next section

## Get started / quick start

* link back to installation
* we can `git clone` a repository there
* we set up that repository, and they can just run something from there
* birds eye view / guided stroll through executing a workflow and interacting with it
* EOS with ASE
* [GP]: Simple tutorial could be multiple steps, not just one page. storyline, adding features. submodules. Mention full story / end goal at the beginning.
* [MBx]: Should this still have some advertisement there?
* [GP]: Argument against running the full workflow: too high complexity (though, other docs, e.g., docker, provide complex setups; already)
* [EB]: Showcase at landing page with panels main features of aiida (compare with react); let people fill in with their imagination, what they can do with that.
* [BM]: Keep it very general at the beginning (e.g., React docs, just mentions button); in the end, it's all just math. E.g., very
*

**what to show/explain (superficially)/showcasing**
* simple profile creation
* run basic workflow and provide simple inputs to it
* interact with running workflow
* check the output
* show provenance graph (and, possibly, plot EOS - part of workflow or external)
* [GP]: 1) run executable without AiiDA, 2) run two things, 3) run things remotely
* [JG]: Alternative approach (what MBx and I discussed before): top-down approach, runnnig a first workfow
* Quickstart categorized: workflow users, workflow creators (probably we should not have two paths; instead, linear, but people can skip it)
* `verdi presto` should also set up a `Code` (`verdi presto --tutorial` that sets everything up required for the tutorial)
* `git clone` over `pip install aiida-core[tutorials]`, as with the latter, the workflow we expose them to, cannot be changed (not editable installed, within `.venv` lib)
* Inside, `aiida-core`, add entries, e.g. `core.tutorial.<something>`, to get things similar like `MultiplyAdddWorkChain`, but less artifial, and slightly more complex


## Conclusions

* "Teaser": move to introduction: external stuff, not runnable
* "Quick Start":
    * Materials science agnostic, simple workflow.
    * Focus on running, don't expose internals.
    * Learn:
        *
*

## Running python


## Running external codes

* first, `aiida-shell`, then CalcJob
*


## Running workflows


## Interacting with your AiiDA data


## Writing workflows

***

## Practical

**Tentative dates**: 27 - 29 April

(30th is CSD science day, so we'll limit the tutorial to three days)

Previous Google drive:

https://drive.google.com/drive/folders/14xWqtcrfO71lyRYP-noMFEpRTRteRgCk

## Content

The content of the tutorial will be split up into "modules", each of which focus on a particular topic.

General comments:

* The modules should be written to be a part of the AiiDA documentation and usable outside of the scope of an event.
* Every tutorial module should start "what you will learn", and redirects to what they will learn next and where.

>[!NOTE]
> The modules below are still a rough sketch, and very much a work in progress. So far the below list is in no particular order (except for introduction, we start with that).

### Introduction / Teaser

Installation
Teaser that shows executing a more complex workflow, to show the power of AiiDA
Then, for the participants: Run a basic workflow (EOS):
* Avoid using codes you have to compile (e.g. QE) -> Use ASE instead
* No RMQ (or, no-RMQ broker, if available)
* Possibly use conda, in general (though, services still need to be started)

Should we run a `CalcJob`?
Top-level architecture? Concepts?
1-hour kickoff event where everybody can join, or record it

### Running external code(s)

* Setting up a computer/code
* Using Plugins
* `aiida-shell`
* `aiida-pythonjob`

### Running workflows (?)

* How to customize inputs
* How to run remotely

### Working with/Accessing/Organising data

* `verdi calcjob gotocomputer`
* `verdi process dump`
* Querying
* Groups
* Exporting

### Writing workflows

To WorkGraph or not to Workgraph (probably yes)
-> Simple linear example at least
-> Basic branching would be nice

### Other

* Provenance
* Error inspection
* Error handler
* General: how to debug
* Submit high-throughput

## Meeting notes

### Brainstorming MBx & JG

* Masterclass -> we decide to take real research problems and help them with those
* Start with a teaser
* Show AiiDAlab-QE?
* Start with a band structure workflow: get a structure, calculate something from it
* Alternative: EOS, one could use also ase calculator, as they are quick
* Include aiida-tutorials content in aiida-core docs. we should not have a separate repo for this
    * Time from timetable to actual tutorial should be minimal
    * Tutorials should be integrated here
    * ![{E20F44D3-4C49-41EF-BDA3-C46B5E3C78B7}](https://hackmd.io/_uploads/ByI0Rx-IWe.png)
* 3 days, 6 "Tutorials", gather.town or similar social event going on
* rather than talks that only exist for the tutorial, videos
* `pip install aiida-core[tutorials]` that installs the required additional packages
* https://github.com/superstar54/workgraph-collections/blob/main/workgraph_collections/ase/common/eos.py
* aiida-quantumespresso specific stuff we should just point to the docs of this package
* We could send out instructions before (just installation section from docs), then have half a day, before, be on gather.town, and make sure that things work for people on their local machines, and fix issues.
* "Submitting to the daemon" (that should point to the complete installation guide)
* Don't link things directly from other documentation pages, but in "See Also" / footnotes at the end, to not interrupt the general flow

### Brainstorming MSD GM (29 Jan 2026)

* AiiDAlab teaser, one short slot
* live doing everything and talking over it preferred by NM, but not good for long sessions
* have live sessions / recordings, build personal relationships

#### Installation

Install on own machine or use kubernetes/QM?
Provide slot beforehand to help with installation.

#### Other

Start on Zoom (easier to connect/use): demo -> move to Gather.town (keep some people in Zoom to help them use Gather).
Also slot for AiiDAlab, even for people who don't know any programming
Main focus on users, **not** workflow developers
* Possibly one last advanced session with a real plugin (aiida-qe)
    * run actual workflow with real code
* Provenance aside the QueryBuilder
* Add to form: what are you intending to use aiida for?
    * complex things a few times, or a simple thing 10k times, not quite well-defined
* Which are the aiida features people will be exposed to
    * setting up computer & code
    * managing data: groups & querying, dump & export
    * introducing error codes, how to debug, etc. (calcjob inputcat, report)
    * high-throughput: running multiple things
    * creating simple (linear) workflows (WorkGraph)
    * how to run in practice (aiidalab?); how to configure workflows, nested, etc.
    * PR for aiida ecosystem (when people write complex workflow, they can go all the way to aiidalab, gui, etc.)
    * introduction to data types, and the advantages they provide:
        * specific provenance for these values, querying, exporting to custom outputs (e.g., pdf of band structure for BandsData)
        * could again be story of gradually building up capabilities
    * List of things we haven't covered: how to write calcjob/workchain, how to write a plugin, etc.

* heading, with subheadings "what you will learn", "what we have not learned yet"

#### Desired outcomes

1. Better tutorial material
2. ~5 proper AiiDA developers
3. More employees for Gio to hire.

Targeted audience:

1. Python experience?
2. Experimentalists / Computational peeps:


Prerequisites: some terminal knowledge, some programming in some language, basic python scripting

Targeted at people that want to _use_ AiiDA

Quantum ESPRESSO or no?


#### Open questions

* Registration? Google form in the past
* Communicate announcement?


#### Story: gradually building up things?

* run simple calculation ("code" / executable)
* run remotely on HPC
* parse / use QB


#### Module 1

* running a pre-prepared script
* using verdi to explore what's going on


## Word vomit section

> Just write whatever thought comes in your mind

* Ideas by Wednesday
    * chess as a game example
    * Giuseppe as a cook that makes a pizza, that's the workflow (maybe not :( )
        * ingredients are the inputs
        * and parameters, e.g., temperature of the oven, time
        * steps: kneading, toppings, cooking

Comment From Pietro:

As an experimentalist and a potential new AiiDA user with a decent programming background, the first thing I would like to understand is what AiiDA can actually do for me. In other words, I would suggest starting the tutorial from a “wishlist” made by the experimentalist or interested researcher: What would I like to achieve? After that I think could be useful from the teacher prospective to answer with: "which of these things can AiiDA help you with or not?"

Beginning with this mapping between new user needs and AiiDA’s capabilities would make it much easier for newcomers to understand where AiiDA fits into their workflow and what realistic expectations they should have.

## AI slop

### List of concepts/features

> [MBx] I wanted to try to get a more or less comprehensive list of features to present in the tutorial.

Based on the AiiDA tutorials and planning notes, here's a comprehensive list of basic features that should be covered in an AiiDA tutorial:

#### Core Concepts & Setup

* **Installation & environment setup** - Getting AiiDA running (possibly with conda)
* **Basic architecture** - Understanding computers, codes, data nodes, process nodes
* **Provenance fundamentals** - Understanding the directed acyclic graph (DAG) and how AiiDA tracks everything
* **Data types** - Working with basic data types (Int, Float, Str, Dict, StructureData, etc.) and their advantages

#### Working with Data

* **Creating and storing data nodes** - Using PK vs UUID identifiers
* **Querying the database** - Using QueryBuilder to search and filter nodes
* **Groups** - Organizing data into groups for easier management
* **Exporting & importing** - Moving data between databases (verdi export/import)
* **Loading data** - Retrieving existing nodes from the database

#### Running External Codes

* **Setting up computers** - Configuring localhost and remote computers
* **Setting up codes** - Registering code installations (verdi code create)
* **Understanding plugins** - The role of calculation plugins (CalcJob plugins)
* **Simple execution tools** - Using aiida-shell and aiida-pythonjob for lightweight jobs
* **Running CalcJobs** - Executing single calculations with proper input preparation
* **Providing inputs** - Understanding required vs optional inputs, using builder pattern

#### Remote Execution & Daemon

* **AiiDA daemon** - Submitting calculations to the daemon for asynchronous execution
* **Monitoring processes** - Using verdi process list, verdi process show
* **Remote data access** - Using verdi calcjob gotocomputer to inspect files on remote machines
* **Process status** - Understanding process states (running, finished, failed, etc.)

#### Executing Workflows

* **Running pre-built workflows** - Using existing WorkChains (e.g., PwBandsWorkChain)
* **Protocol-based setup** - Using get_builder_from_protocol() for quick workflow configuration
* **Customizing workflow inputs** - Modifying builder inputs for different scenarios
* **Submitting workflows** - Using submit() vs run()
* **Following workflow execution** - Monitoring multi-step processes

#### Writing Simple Workflows

* **Calculation functions** - Simple Python functions wrapped as AiiDA processes
* **Work functions** - Basic workflows that call other processes
* **WorkChains (basics)** - Linear workflows with define(), steps, and return
* **Basic branching** - Conditional logic in workflows
* **WorkGraph** - Modern workflow tool (alternative/complement to WorkChains)

#### Debugging & Error Handling

* **Inspecting calculations** - Using verdi calcjob inputcat, outputcat, res
* **Process reports** - Understanding error messages and logs (verdi process report)
* **Dumping process data** - Using verdi process dump for detailed inspection
* **Common errors** - Recognizing typical issues and how to fix them
* **Error handlers** - Automatic recovery from calculation failures

#### Advanced Querying & Analysis

* **QueryBuilder advanced** - Complex queries with filters, joins, projections
* **Provenance exploration** - Navigating input/output relationships
* **Provenance visualization** - Generating and viewing provenance graphs (verdi node graph)
* **REST API** - Accessing data through the web interface
* **Provenance browser** - Using the Materials Cloud provenance browser

#### High-Throughput Computing

* **Submitting multiple calculations** - Running many calculations efficiently
* **Managing large datasets** - Using groups and smart querying

#### Practical Output Handling

* **Parsing outputs** - Understanding how parsers extract data from raw output files
* **Output nodes** - Working with structured output data (RemoteData, retrieved files, parsed data)
* **Data visualization** - Basic plotting and analysis of results

#### Best Practices

* **Input validation** - Checking inputs before submission
* **Workflow modularity** - Writing reusable components
* **Documentation** - Understanding where to find help (docs, forums)
