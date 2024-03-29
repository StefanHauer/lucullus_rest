# Importing the package in the conf.py file seems to be necessary
# for autodoc.
# Source: https://stackoverflow.com/questions/63261090/github-sphinx-action-cant-find-target-python-modules-and-builds-an-empty-sphinx
import lucullus_rest

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'lucullus_rest'
copyright = '2024, Stefan F. Hauer'
author = 'Stefan F. Hauer'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.githubpages']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'classic'
html_static_path = ['_static']