# Makefile for Sphinx documentation
#

SPHINXBUILD  = sphinx-build
BUILDDIR     = build
HTMLBUILDDIR = build/html
SOURCEDIR    = workchain_source

# User-friendly check for sphinx-build
ifeq ($(shell which $(SPHINXBUILD) >/dev/null 2>&1; echo $$?), 1)
$(error The '$(SPHINXBUILD)' command was not found. Make sure you have Sphinx installed, then set the SPHINXBUILD environment variable to point to the full path of the '$(SPHINXBUILD)' executable. Alternatively you can add the directory with the executable to your PATH. If you don't have Sphinx installed, grab it from http://sphinx-doc.org/)
endif

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -n -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) $(SOURCEDIR)
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) $(SOURCEDIR)

.PHONY: all help clean html dirhtml singlehtml pickle json htmlhelp qthelp devhelp epub latex latexpdf text man changes linkcheck doctest coverage gettext

all: html

clean:
	@rm -r $(BUILDDIR) || true
	@rm -r $(HTMLBUILDDIR) || true

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(HTMLBUILDDIR)
	@echo
	@echo "Build finished. The HTML pages are in $(HTMLBUILDDIR)."


view:
	xdg-open $(HTMLBUILDDIR)/index.html
