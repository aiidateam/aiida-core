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

`AiiDA`_ is an open-source framework implemented in Python that aims to help researchers with managing simple to complex workflows and making them fully reproducible.

.. _AiiDA: https://www.aiida.net

.. panels::
   :column: col-lg-6 col-md-6 col-sm-12 col-xs-12 p-2
   :body: text-center

   **Getting Started**

   First time user or are looking for installation instructions? Start here!

   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   .. container:: link-box bottom

      :ref:`To the getting started guides <intro/get_started>`

   ........................................................

   **Tutorial**

   Get your feet wet with a brief introduction to the basics of AiiDA.

   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   .. container:: link-box bottom

      :ref:`To the tutorials <tutorials>`

   ........................................................

   **How-To Guides**

   Learn how to use AiiDA to power your own work.

   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   .. container:: link-box bottom

      :ref:`To the how-to guides <how-to>`

   ........................................................

   **Topics**

   Comprehensive background information for those who want to learn more about AiiDA's underlying concepts.

   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   .. container:: link-box bottom

      :ref:`To the topics <topics>`

   ........................................................

   **API Reference**

   Comprehensive description of all AiiDA components and APIs, including the command-line-interface, the Python interface, and the RESTful API.

   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   .. container:: link-box bottom

      :ref:`To the reference guide <api>`

   ........................................................

   **Development**

   Saw a typo in the documentation? Want to improve existing functionalities? The contributing guidelines will guide you through the process of improving AiiDA.

   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   .. container:: link-box bottom

      :ref:`To the development guide <development>`


.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   intro/about
   intro/get_started
   intro/installation
   intro/troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Tutorial
   :hidden:

   tutorial/basic

.. toctree::
   :maxdepth: 1
   :caption: How-To Guides
   :hidden:

   howto/codes
   howto/workflows
   howto/data
   howto/installation
   howto/plugins

.. toctree::
   :maxdepth: 1
   :caption: Topics
   :hidden:

   topics/cli
   topics/daemon
   topics/provenance
   topics/database
   topics/repository
   topics/processes
   topics/plugins

.. toctree::
   :maxdepth: 2
   :caption: Reference
   :hidden:

   reference/command_line
   reference/apidoc/aiida.rst
   reference/rest_api

.. toctree::
   :maxdepth: 2
   :caption: Internal architecture

   internals/global_design
   internals/orm
   internals/data_storage
   internals/engine
   internals/plugin_system
   internals/rest_api

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
