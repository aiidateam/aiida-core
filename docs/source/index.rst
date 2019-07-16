.. aiida documentation master file, created by
       sphinx-quickstart on Wed Oct 24 11:33:37 2012.
       You can adapt this file completely to your liking, but it should at least
       contain the root `toctree` directive.

**aiida-core version:** |release|

.. figure:: images/AiiDA_transparent_logo.png
    :width: 250px
    :align: center

    Automated Interactive Infrastructure and Database for Computational Science

#################################
Welcome to AiiDA's documentation!
#################################

`AiiDA`_ is a python framework that aims to help researchers with managing complex workflows and making them fully reproducible.

.. _AiiDA: http://www.aiida.net


************
Features
************

 * **Workflows:** Write complex, auto-documenting workflows in python, linked to arbitrary executables on local and remote computers. The event-based workflow engine supports tens of thousands of processes per hour with full checkpointing.
 * **Data provenance:** Automatically track inputs, outpus & metadata of all calculations in a provenance graph for full reproducibility. Perform fast queries on graphs containing millions of nodes.
 * **HPC interface:** Move your calculations to a different computer by changing one line of code. AiiDA is compatible with schedulers like `SLURM <https://slurm.schedmd.com>`_, `PBS Pro <https://www.pbspro.org/>`_, `torque <http://www.adaptivecomputing.com/products/torque/>`_, `SGE <http://gridscheduler.sourceforge.net/>`_ or `LSF <https://www.ibm.com/support/knowledgecenter/SSETD4/product_welcome_platform_lsf.html>`_ out of the box.
 * **Plugin interface:** Extend AiiDA with `plugins <https://aiidateam.github.io/aiida-registry/>`_ for new simulation codes (input generation & parsing), data types, schedulers, transport modes and more.
 * **Open Science:** Export subsets of your provenance graph and share them with peers or make them available online for everyone on the `Materials Cloud <https://www.materialscloud.org>`_.
 * **Open source:** AiiDA is released under the `MIT open source license <https://github.com/aiidateam/aiida-core/blob/develop/LICENSE.txt>`_.

See also the `AiiDA home page`_.

.. _AiiDA home page: http://www.aiida.net

***************
Getting started
***************

 * The `AiiDA tutorials <https://aiida-tutorials.readthedocs.io/en/latest/>`_ are a good place to get started with using AiiDA.
 * Afterwards, you might want to :ref:`install AiiDA<installation>` on your machine.
 * For setting up a production environment, you may find the :ref:`configuration <configure_aiida>` section helpful.
 * For the advanced, there is the complete :doc:`AiiDA API reference<apidoc/aiida>` (including a :ref:`modindex`), and of course you can always peek into the code on the `AiiDA git repository <https://github.com/aiidateam/aiida-core>`_.

.. toctree::
    :maxdepth: 1
    :caption: Installation
    :hidden:

    install/quick_installation
    install/prerequisites
    install/installation
    install/configuration
    install/updating_installation
    install/troubleshooting


.. toctree::
    :maxdepth: 1
    :caption: Getting started
    :hidden:

    get_started/index
    get_started/computers
    get_started/codes


.. toctree::
    :maxdepth: 1
    :caption: Concepts
    :hidden:

    concepts/provenance
    concepts/processes
    concepts/calculations
    concepts/workflows


.. toctree::
    :maxdepth: 1
    :caption: Working with
    :hidden:

    working/processes
    working/functions
    working/calculations
    working/workflows

.. toctree::
    :maxdepth: 1
    :caption: Working with AiiDA
    :hidden:

    working_with_aiida/index
    import_export/index


.. toctree::
    :maxdepth: 1
    :caption: For AiiDA developers
    :hidden:

    developer_guide/index

.. toctree::
    :maxdepth: 1
    :caption: Tutorials
    :hidden:

    tutorial/index


.. toctree::
    :maxdepth: 1
    :caption: API reference
    :hidden:

    apidoc/aiida

.. toctree::
   :maxdepth: 1
   :caption: aiida-plugins [Section to be moved]
   :hidden:


   developer_guide/plugins/index
   developer_guide/devel_tutorial/code_plugin_float_sum
   developer_guide/devel_tutorial/plugin_tests
   developer_guide/devel_tutorial/cmdline_plugin
   developer_guide/devel_tutorial/parser_warnings_policy
   developer_guide/aiida_sphinxext


***********
How to cite
***********

If you use AiiDA for your research, please cite the following work:
  
.. highlights:: Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari,
    and Boris Kozinsky, *AiiDA: automated interactive infrastructure and database 
    for computational science*, Comp. Mat. Sci 111, 218-230 (2016);
    https://doi.org/10.1016/j.commatsci.2015.09.013; http://www.aiida.net.


****************
Acknowledgements
****************

This work is supported by the `MARVEL National Centre for Competency in Research`_ 
funded by the `Swiss National Science Foundation`_, as well as by the 
`MaX European Centre of Excellence`_ funded by the Horizon 2020 EINFRA-5 program, Grant No. 676598.

.. image:: images/MARVEL.png
   :height: 100px
   :target: `MARVEL National Centre for Competency in Research`_

.. image:: images/MaX.png
   :height: 80px
   :target: `MaX European Centre of Excellence`_

.. _MARVEL National Centre for Competency in Research: http://www.marvel-nccr.ch
.. _Swiss National Science Foundation: http://www.snf.ch/en
.. _MaX European Centre of Excellence: http://www.max-centre.eu
