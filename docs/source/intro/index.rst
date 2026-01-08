.. _intro:

.. toctree::
   :maxdepth: 1
   :hidden:

============
Introduction
============

AiiDA is an open-source Python infrastructure to help researchers with automating, managing, persisting, sharing and reproducing the complex workflows associated with modern computational science and all associated data.

AiiDA is built to support and streamline the four core pillars of the ADES model: Automation, Data, Environment, and Sharing (described `here <https://arxiv.org/abs/1504.01163>`__, `doi <https://doi.org/10.1016/j.commatsci.2015.09.013>`__). Some of the key features of AiiDA include:

*  **Workflows:** AiiDA allows to build and execute complex, auto-documenting workflows linked to multiple codes on local and remote computers.
*  **High-throughput:** AiiDA's event-based workflow engine supports tens of thousands of processes per hour with full check-pointing.
*  **Data provenance:** AiiDA automatically tracks and records inputs, outputs and metadata of all calculations and workflows in extensive provenance graphs that preserve the full lineage of all data.
*  **Advanced queries:** AiiDA's query language enables fast graph queries on millions of nodes.
*  **Plugin interface:** AiiDA can support via plugins any computational code and data analytics tool, data type, scheduler, connection mode, etc. (see `public plugin repository <https://aiidateam.github.io/aiida-registry/>`__).
*  **HPC interface:** AiiDA can seamlessly deal with heterogeneous and remote computing resources; it works with many schedulers out of the box (`SLURM <https://slurm.schedmd.com>`__, `PBS Pro <https://www.pbspro.org/>`__, `torque <https://docs.adaptivecomputing.com/torque/5-0-0/help.htm>`__, `SGE <http://gridscheduler.sourceforge.net/>`__ or `LSF <https://www.ibm.com/docs/en/spectrum-lsf>`__).
*  **Open science:** AiiDA allows to export both full databases and selected subsets, to be shared with collaborators or made available and browsable online on the `Archive <https://archive.materialscloud.org/>`__ and `Explore <https://www.materialscloud.org/explore>`__ sections of `Materials Cloud <https://www.materialscloud.org>`__.
*  **Open source:** AiiDA is released under the `MIT open-source license <https://github.com/aiidateam/aiida-core/blob/main/LICENSE.txt>`__.

See also the `list of AiiDA-powered scientific publications <http://www.aiida.net/science/>`__ and `testimonials from AiiDA users <http://www.aiida.net/testimonials/>`__.
