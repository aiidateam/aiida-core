cod-tools
---------

Description
^^^^^^^^^^^
**cod-tools** (`more info here`_) is an open-source collection of command 
line scripts for
handling of Crystallographic Information Framework `(CIF) files`_. The
package is developed by the team of `Crystallography Open Database`_ (COD)
developers. Detailed information for the usage of each individual script
from the package can be obtained by invoking commands with ``--help`` and
``--usage`` command line options. For example::

    cif_filter --help
    cif_filter --usage

.. _more info here: http://wiki.crystallography.net/cod-tools
.. _(CIF) files: http://www.iucr.org/resources/cif
.. _Crystallography Open Database: http://www.crystallography.net

* cif_cod_check
    Parse a CIF file, check if certain data values match COD
    requirements and IUCr data validation criteria (Version: 2000.06.09,
    ftp://ftp.iucr.ac.uk/pub/dvntests or ftp://ftp.iucr.org/pub/dvntests)

* cif_cod_deposit
    Deposit CIFs into COD database using CGI deposition interface.

* cif_cod_numbers
    Find COD numbers for the .cif files in given directories of file lists.

* cif_correct_tags
    Correct misspelled tags in a CIF file.

* cif_filter
    Parse a CIF file and print out essential data values in the CIF
    format, the COD CIF style.

    This script has also many capabilities -- it can restore spacegroup
    symbols from symmetry operators (consulting pre-defined tables),
    parse and tidy-up ``_chemical_formula_sum``, compute cell volume,
    exclude unknown or "empty" tags, and add specified bibliography data.

* cif_fix_values
    Correct temperature values which have units specified or convert
    between Celsius degrees and Kelvins. Changes 'room/ambiante
    temperature' to the appropriate numeric value.
    Fixes other undefined values (no, not measured, etc.) to '?' symbol.
    Determine a report about changes made into standart I/O streams.

    Fixes enumeration values in CIF file against CIF dictionaries.

* cif_mark_disorder
    Marks disorder in CIF files judging by distance and occupancy.

* cif_molecule
    Restores molecules from a CIF file.

* cif_select
    Read CIFs and print out selected tags with their values.

* cif_split
    Split CIF files into separate files with one data\_ section each.

    This script parses given CIF files to separate the datablocks, so is
    capable of splitting non-correctly formatted and nested CIF files.

* cif_split_primitive
    Split CIF files into separate files with one data\_ section each.

    This is a very naive and primitive version of the splitter, which
    expects each data\_... section to start on a new line. It may fail on
    some CIF files that do not follow such convention. For splitting of
    any correctly formatted CIF files, one must do full CIF parsing
    using CIF grammar and tokenisation of the file.

.. _codtools_installation:

Installation
^^^^^^^^^^^^
Currently **cod-tools** package is distributed via source code only. To
prepare the package for usage (as of source revision 2930) one has to
follow these steps:

* Retrieve the source from the `Subversion`_ repository::

    svn co svn://www.crystallography.net/cod-tools/trunk cod-tools

* Install the dependencies::

    bash -e cod-tools/dependencies/Ubuntu-12.04/install.sh

  .. note:: the dependency installer is written for Ubuntu 12.04, but
    works fine on some older or newer Ubuntu as well as Debian
    distributions.

* Build and test::

    make -C cod-tools

* Prepare the environment:
    Described below are two methods of setting the environment for
    **cod-tools** as of source revision 3393:

    * Using Bash::

        CODTOOLS_SRC=~/src/cod-tools

        export PATH=${CODTOOLS_SRC}/scripts:${PATH}
        export PERL5LIB=${CODTOOLS_SRC}/src/lib/perl5:${PERL5LIB}

      These commands can be pasted to ``~/.bashrc`` file, which is sourced
      automatically by the AiiDA before each calculation.

      .. note:: Be sure to restart the AiiDA daemon after modifying the
        ``~/.bashrc``.

    * Using `modulefile`_::

        #%Module1.0#####################################################################
        module-whatis    loads the cod-tools environment
        
        set             CODTOOLS_SRC    ~/src/cod-tools
        prepend-path    PATH            ${CODTOOLS_SRC}/scripts
        prepend-path    PERL5LIB        ${CODTOOLS_SRC}/src/lib/perl5

Examples
^^^^^^^^

* Fix a syntactically incorrect structure:

  Some simple common CIF syntax errors can be fixed automatically using
  cif_filter with ``--fix-syntax`` option. In example, such structure::

        data_broken
        _publ_section_title "Runaway quote
        loop_
        _atom_site_label
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        C 0 0 0

  can be fixed (provided it's stored in ``test.cif``)::

        cif_filter --fix test.cif

  Obtained structure::

        data_broken
        _publ_section_title              'Runaway quote'
        loop_
        _atom_site_label
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        C 0 0 0

  A warning message tells what was done::

        cif_filter: test.cif(2) data_broken: warning, double-quoted string is missing a closing quote -- fixed

  where:
    * ``cif_filter`` is the name of the used script;
    * ``test.cif`` is the name of the CIF file;
    * ``2`` is the number of a line in the file;
    * ``data_broken`` is the CIF datablock name;
    * ``warning`` is the level of severity;
    * rest is the message text.

* Fetch a structure from Web, filter and fix it, restore the crystal
  contents and calculate summary formulae per each compound in a crystal::

        curl --silent http://www.crystallography.net/cod/2231955.cif \
            | cif_filter \
            | cif_fix_values \
            | cif_molecule \
            | cif_cell_contents --use-attached-hydrogens

  Obtained result::

        C9 H14 N
        C10 H6 O6 S2
        H2 O

  As well as a warning message::

        cif_molecule: - data_2231955: WARNING, multiplicity ratios are given instead of multiplicities for 39 atoms -- taking calculated values.

* Fetch a structure from Web and mark alternative atoms sharing same site::

        curl --silent http://www.crystallography.net/2018107.cif \
            | cif_mark_disorder \
            | cif_select --cif --tag _atom_site_label

  Obtained result::

        data_2018107
        loop_
        _atom_site_type_symbol
        _atom_site_label
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        _atom_site_u_iso_or_equiv
        _atom_site_adp_type
        _atom_site_calc_flag
        _atom_site_refinement_flags
        _atom_site_occupancy
        _atom_site_symmetry_multiplicity
        _atom_site_disorder_assembly
        _atom_site_disorder_group
        Pb Pb1 0.5000 0.0000 0.2500 0.0213(13) Uani d S 1 4 . .
        Mo Mo2 0.0000 0.0000 0.0000 0.022(4) Uani d S 1 4 . .
        Pb Pb3 0.5000 0.5000 0.0000 0.025(2) Uani d SP 0.881(8) 4 A 1
        Mo Mo3 0.5000 0.5000 0.0000 0.025(2) Uani d SP 0.119(8) 4 A 2
        Mo Mo1 0.0000 0.5000 0.2500 0.018(3) Uani d S 1 4 . .
        O O1 0.2344(13) -0.1372(14) 0.0806(6) 0.0302(17) Uani d . 1 1 . .
        O O2 0.2338(14) 0.3648(14) 0.1697(6) 0.0307(17) Uani d . 1 1 . .

  As well as output messages::

        cif_mark_disorder: - data_2018107: NOTE, atoms 'Mo3', 'Pb3' were marked as alternatives.
        cif_mark_disorder: - data_2018107: NOTE, 1 site(s) were marked as disorder assemblies.

  .. note:: atoms ``Mo3`` and ``Pb3`` share the same site, as can be
    found out by checking their coordinates. Moreover, sum of their
    occupancies are close to 1. In the original CIF file these sites have
    both ``_atom_site_disorder_assembly`` and ``_atom_site_disorder_group``
    set to '``.``'.

.. _Inline::C: http://search.cpan.org/~etj/Inline-C-0.65/lib/Inline/C.pod
.. _modulefile: http://linux.die.net/man/4/modulefile
.. _Subversion: https://subversion.apache.org

Plugins
^^^^^^^

.. toctree::
   :maxdepth: 4

   ciffilter
   cifcellcontents
   cifcodcheck
   cifcoddeposit
   cifcodnumbers
   cifsplitprimitive
