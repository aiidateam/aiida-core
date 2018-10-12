.. aiida documentation master file, created by
       sphinx-quickstart on Wed Oct 24 11:33:37 2012.
       You can adapt this file completely to your liking, but it should at least
       contain the root `toctree` directive.

.. figure:: images/AiiDA_transparent_logo.png
    :width: 250px
    :align: center

    Automated Interactive Infrastructure and Database for Computational Science

#################################
Welcome to AiiDA's documentation!
#################################

AiiDA is a sophisticated framework designed from scratch to be a flexible and scalable infrastructure for computational science.
Being able to store the full data provenance of each simulation, and based on a tailored database solution built for efficient data mining implementations, AiiDA gives the user the ability to interact seamlessly with any number of HPC machines and codes thanks to its flexible plugin interface, together with a powerful workflow engine for the automation of simulations.

The software is available at http://www.aiida.net.

If you use AiiDA for your research, please cite the following work:
  
.. highlights:: Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari,
    and Boris Kozinsky, *AiiDA: automated interactive infrastructure and database 
    for computational science*, Comp. Mat. Sci 111, 218-230 (2016);
    http://dx.doi.org/10.1016/j.commatsci.2015.09.013; http://www.aiida.net.

This is the documentation of the AiiDA framework.
To install AiiDA follow the instructions in the :ref:`installation section<installation>`.
After you have successfully installed AiiDA, you can find some tips in the :ref:`get started section<get_started>` to help you on your way.

For advanced users and developers we point you to the developers section :doc:`developer's guide<developer_guide/index>`.


.. toctree::
    :maxdepth: 1
    :caption: Install

    install/quick_installation
    install/installation
    install/updating_installation
    install/details


.. toctree::
    :maxdepth: 1
    :caption: Get started

    get_started/index
    get_started/daemon
    get_started/computers
    get_started/codes
    get_started/plugins
    working_with_aiida/index


.. toctree::
    :maxdepth: 1
    :caption: Concepts

    concepts/calculations
    concepts/workflows
    concepts/processes
    concepts/provenance
    concepts/caching
    import_export/index


.. toctree::
    :maxdepth: 1
    :caption: Tutorials

    tutorial/index


.. toctree::
    :maxdepth: 1
    :caption: Developers

    developer_guide/index


.. toctree::
    :maxdepth: 1
    :caption: Advanced

    advanced_guide/index


.. toctree::
    :maxdepth: 1
    :caption: API reference

    apidoc/aiida


******************
Indices and tables
******************

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

****************
Acknowledgements
****************

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
