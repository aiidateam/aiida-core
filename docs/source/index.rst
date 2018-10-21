.. aiida documentation master file, created by
   sphinx-quickstart on Wed Oct 24 11:33:37 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. figure:: images/AiiDA_transparent_logo.png
    :width: 250px
    :align: center

    Automated Interactive Infrastructure and Database for Computational Science

Welcome to AiiDA's documentation!
=================================

AiiDA is a sophisticated framework designed from scratch to be a flexible and scalable infrastructure for computational science. Being able to store the full data provenance of each simulation, and based on a tailored database solution built for efficient data mining implementations, AiiDA gives the user the ability to interact seamlessly with any number of HPC machines and codes thanks to its flexible plugin interface, together with a powerful workflow engine for the automation of simulations.

The software is available at http://www.aiida.net.

If you use AiiDA for your research, please cite the following work:
  
.. highlights:: Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari,
  and Boris Kozinsky, *AiiDA: automated interactive infrastructure and database 
  for computational science*, Comp. Mat. Sci 111, 218-230 (2016);
  http://dx.doi.org/10.1016/j.commatsci.2015.09.013; http://www.aiida.net.

This is the documentation of the AiiDA framework. For the first setup, configuration and
usage, refer to the :doc:`user's guide<user_guide/index>` below.

If, instead, you plan to add new plugins, or you simply want to understand
AiiDA internals, refer to the :doc:`developer's guide<developer_guide/index>`.

User's guide
++++++++++++

.. toctree::
   :maxdepth: 4

   user_guide/index

Other guide resources
+++++++++++++++++++++

.. toctree::
   :maxdepth: 3
    
   other_guide/index


Developer's guide
+++++++++++++++++

.. toctree::
    :maxdepth: 3

    developer_guide/index

API reference
+++++++++++++

.. toctree::
   :maxdepth: 4

   API reference <apidoc/aiida>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Acknowledgements
================

This work is supported by the `MARVEL National Centre for Competency in Research`_ 
funded by the `Swiss National Science Foundation`_, as well as by the 
`MaX European Centre of Excellence`_ funded by the Horizon 2020 EINFRA-5 program, Grant No. 676598.

.. figure:: images/MARVEL.png
    :height: 100px
    :align: center
.. figure:: images/MaX.png
    :height: 80px
    :align: center

.. _MARVEL National Centre for Competency in Research: http://www.marvel-nccr.ch
.. _Swiss National Science Foundation: http://www.snf.ch/en
.. _MaX European Centre of Excellence: http://www.max-centre.eu
