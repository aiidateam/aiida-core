:sd_hide_title:

#################################
Welcome to AiiDA's documentation!
#################################

.. grid::
   :reverse:
   :gutter: 2 3 3 3
   :margin: 1 2 1 2

   .. grid-item::
      :columns: 12 4 4 4

      .. image:: images/aiida-icon.svg
         :width: 200px
         :class: sd-m-auto

   .. grid-item::
      :columns: 12 8 8 8
      :child-align: justify
      :class: sd-fs-5

      .. rubric:: AiiDA

      An open-source Python infrastructure to help researchers with automating, managing, persisting, sharing and reproducing the complex workflows associated with modern computational science and all associated data (see :ref:`features<intro:about>`).

      **aiida-core version:** |release|

------------------------------

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`rocket;mr-1` Getting Started
      :text-align: center
      :shadow: md

      AiiDA installation, configuration and troubleshooting.

      +++++++++++++++++++++++++++++++++++++++++++++

      .. button-ref:: intro/get_started
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         To the installation guides

   .. grid-item-card:: :fa:`info-circle;mr-1` Tutorial
      :text-align: center
      :shadow: md

      First time users: Get your feet wet with AiiDA basics!

      +++++++++++++++++++++++++++++++++++++++++++++

      .. button-ref:: intro/tutorial
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         To the tutorials

   .. grid-item-card:: :fa:`question-circle;mr-1` How-To Guides
      :text-align: center
      :shadow: md

      Learn how to use AiiDA to power your own work.

      +++++++++++++++++++++++++++++++++++++++++++++

      .. button-ref:: howto/index
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         To the how-to guides

   .. grid-item-card:: :fa:`bookmark;mr-1` Topics
      :text-align: center
      :shadow: md

      Background information on AiiDA's underlying concepts.

      +++++++++++++++++++++++++++++++++++++++++++++

      .. button-ref:: topics/index
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         To the topics

   .. grid-item-card:: :fa:`cogs;mr-1` API Reference
      :text-align: center
      :shadow: md

      Comprehensive documentation of AiiDA components: command-line interface, Python interface, and RESTful API.

      +++++++++++++++++++++++++++++++++++++++++++++

      .. button-ref:: reference/index
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         To the reference guide

   .. grid-item-card:: :fa:`sitemap;mr-1` Internal Architecture
      :text-align: center
      :shadow: md

      Notes on AiiDA's design and architecture aimed at core developers.

      +++++++++++++++++++++++++++++++++++++++++++++

      .. button-ref:: internals/index
         :ref-type: doc
         :click-parent:
         :expand:
         :color: primary
         :outline:

         To the architecture guide

------------------------------

.. admonition:: Need support?
   :class: title-icon-code-fork

   For any questions, discussions and requests for support, please visit the `Discourse forum <https://aiida.discourse.group>`__.


.. admonition:: Development Contributions
   :class: title-icon-code-fork

   Saw a typo in the documentation? Want to improve the code?
   Help is always welcome, get started with the `contributing guidelines <https://github.com/aiidateam/aiida-core/wiki>`__.


.. toctree::
   :maxdepth: 2
   :hidden:

   intro/index
   howto/index
   topics/index
   reference/index
   internals/index

***********
How to cite
***********

If you use AiiDA for your research, please cite the following work:

.. highlights:: **AiiDA >= 1.0:** Sebastiaan. P. Huber, Spyros Zoupanos, Martin Uhrin, Leopold Talirz, Leonid Kahle, Rico Häuselmann, Dominik Gresch, Tiziano Müller, Aliaksandr V. Yakutovich, Casper W. Andersen, Francisco F. Ramirez, Carl S. Adorf, Fernando Gargiulo, Snehal Kumbhar, Elsa Passaro, Conrad Johnston, Andrius Merkys, Andrea Cepellotti, Nicolas Mounet, Nicola Marzari, Boris Kozinsky, and Giovanni Pizzi, *AiiDA 1.0, a scalable computational infrastructure for automated reproducible workflows and data provenance*, Scientific Data **7**, 300 (2020); DOI: `10.1038/s41597-020-00638-4 <https://doi.org/10.1038/s41597-020-00638-4>`_

.. highlights:: **AiiDA >= 1.0:** Martin Uhrin, Sebastiaan. P. Huber, Jusong Yu, Nicola Marzari, and Giovanni Pizzi, *Workflows in AiiDA: Engineering a high-throughput, event-based engine for robust and modular computational workflows*, Computational Materials Science **187**, 110086 (2021); DOI: `10.1016/j.commatsci.2020.110086 <https://doi.org/10.1016/j.commatsci.2020.110086>`_

.. highlights:: **AiiDA < 1.0:** Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky, *AiiDA: automated interactive infrastructure and database for computational science*, Computational Materials Science **111**, 218-230 (2016); DOI: `10.1016/j.commatsci.2015.09.013 <https://doi.org/10.1016/j.commatsci.2015.09.013>`_


****************
Acknowledgements
****************

AiiDA is supported by the `MARVEL National Centre of Competence in Research`_, the `MaX European Centre of Excellence`_ and by a number of other supporting projects, partners and institutions, whose complete list is available on the `AiiDA website acknowledgements page`_.

AiiDA is a NumFOCUS Affiliated Project. Visit `numfocus.org`_ for more information.


.. _AiiDA: http://www.aiida.net
.. _MARVEL National Centre of Competence in Research: http://www.marvel-nccr.ch
.. _MaX European Centre of Excellence: http://www.max-centre.eu
.. _AiiDA website acknowledgements page: http://www.aiida.net/acknowledgements/
.. _numfocus.org: https://www.numfocus.org
