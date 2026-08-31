# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also from the
# environment. SPHINXBUILD invokes Sphinx through the *active* Python rather
# than a bare `sphinx-build` on PATH, so an activated virtualenv is always the
# one used -- a bare `sphinx-build` silently falls through to a system-wide
# install when the venv has no Sphinx.
PYTHON        ?= python3
SPHINXOPTS    ?=
SPHINXBUILD   ?= $(PYTHON) -m sphinx
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile check-deps

# Fail with an actionable message instead of a Sphinx extension traceback when
# the docs dependencies are missing from the active environment.
check-deps:
	@$(PYTHON) -c "import sphinx, sphinxcontrib.mermaid, shibuya" 2>/dev/null || { \
		echo ""; \
		echo "Documentation dependencies are missing from:"; \
		echo "    $$($(PYTHON) -c 'import sys; print(sys.prefix)')"; \
		echo ""; \
		echo "Install them into the active environment with:"; \
		echo "    pip install -e \".[docs]\""; \
		echo ""; \
		exit 1; \
	}

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile check-deps
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
