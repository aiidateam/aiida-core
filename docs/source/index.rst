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


.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   intro/about
   intro/get_started
   intro/installation
   intro/troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Tutorial

   tutorial/placeholder

.. toctree::
   :maxdepth: 2
   :caption: How-To Guides

   howto/placeholder

.. toctree::
   :maxdepth: 2
   :caption: Topics

   topics/placeholder

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/placeholder

.. toctree::
   :maxdepth: 2
   :caption: Plugins

   plugins/placeholder

.. toctree::
   :maxdepth: 2
   :caption: Development

   development/placeholder

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

This work is supported by:
* the `MARVEL National Centre for Competency in Research`_ funded by the `Swiss National Science Foundation`_;
* the `MaX European Centre of Excellence`_ funded by the Horizon 2020 EINFRA-5 program, Grant No. 676598;
* the `swissuniversities P-5 project "Materials Cloud"`_.

AiiDA is a NumFOCUS Affiliated Project. Visit `numfocus.org`_ for more information.

.. image:: images/MARVEL.png
   :height: 100px
   :target: `MARVEL National Centre for Competency in Research`_

.. image:: images/MaX.png
   :height: 80px
   :target: `MaX European Centre of Excellence`_

.. image:: images/swissuniversities.png
   :height: 35px
   :target: `swissuniversities P-5 project "Materials Cloud"`_

.. _MARVEL National Centre for Competency in Research: http://www.marvel-nccr.ch
.. _Swiss National Science Foundation: http://www.snf.ch/en
.. _MaX European Centre of Excellence: http://www.max-centre.eu
.. _swissuniversities P-5 project "Materials Cloud": https://www.materialscloud.org/swissuniversities
.. _numfocus.org: https://www.numfocus.org
