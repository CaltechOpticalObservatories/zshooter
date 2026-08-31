# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ZShooter'
copyright = '2026, Caltech Optical Observatories (COO)'
author = 'Caltech Optical Observatories (COO)'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinxcontrib.mermaid",
]
templates_path = ['_templates']

# The requirements section is hidden for now: the L1/L2/L3 baseline has not
# been ingested, so the pages are placeholders. Remove this entry and restore
# `requirements/index` to the toctree in index.rst to bring it back.
exclude_patterns = ['requirements/**']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'shibuya'
html_static_path = ['_static']
