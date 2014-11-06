cod-tools
---------

Description
^^^^^^^^^^^
**cod-tools** is an open-source collection of command line scripts for
handling of `Crystallographic Information Framework (CIF) files`_. The
package is developed by the team of `Crystallography Open Database`_ (COD)
developers. Detailed information for the usage of each individual script
from the package can be obtained by invoking commands with ``--help`` and
``--usage`` command line options. For example::

    cif_filter --help
    cif_filter --usage

.. _Crystallographic Information Framework (CIF) files: http://www.iucr.org/resources/cif
.. _Crystallography Open Database: http://www.crystallography.net

* cif_cod_check
    Parse a CIF file, check if certain data values match COD
    requirements and IUCr data validation criteria (Version: 2000.06.09,
    ftp://ftp.iucr.ac.uk/pub/dvntests or ftp://ftp.iucr.org/pub/dvntests)

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

* cif_molecule
    Restores molecules from a CIF file.

* cif_split_primitive
    Split CIF files into separate files with one data\_ section each.

    This is a very naive and primitive version of the splitter, which
    expects each data\_... section to start on a new line. It may fail on
    some CIF files that do not follow such convention. For splitting of
    any correctly formatted CIF files, one must do full CIF parsing
    using CIF grammar and tokenisation of the file.


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

  .. note:: as the source of `Inline::C`_ is not nicely portable, some
    tests may fail. In that case the C CIF parser will not be available and
    some scripts that allow the user to choose between C and Perl CIF
    parsers have to be invoked with ``--use-perl-parser`` command line
    option.

* Prepare the environment:
    As the layout of the scripts and libraries is somewhat non-standard,
    more than a single path has to be added to ``${PATH}`` and
    ``${PERL5LIB}``. Attached below is a `modulefile`_, setting environment
    for **cod-tools** as of source revision 2930::

        #%Module1.0#####################################################################
        module-whatis    loads the cod-tools environment
        
        set             CODTOOLS_SRC    ~/src/cod-tools
        prepend-path    PATH            ${CODTOOLS_SRC}/perl-scripts
        prepend-path    PERL5LIB        ${CODTOOLS_SRC}
        prepend-path    PERL5LIB        ${CODTOOLS_SRC}/CCIFParser
        prepend-path    PERL5LIB        ${CODTOOLS_SRC}/CIFData
        prepend-path    PERL5LIB        ${CODTOOLS_SRC}/CIFParser
        prepend-path    PERL5LIB        ${CODTOOLS_SRC}/CIFTags
        prepend-path    PERL5LIB        ${CODTOOLS_SRC}/Spacegroups
        prepend-path    PERL5LIB        ${CODTOOLS_SRC}/lib/perl5

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
   cifsplitprimitive
