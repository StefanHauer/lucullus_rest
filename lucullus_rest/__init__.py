#

"""
lucullus_rest
=============

lucullus_rest is a Python package to access information via the
REST-API of the Lucullus Process and Information Management
System (PIMS) of Securecell. It is meant to make retrieval of
information as easy as possible and to also provide a simple
framework for creating process control loops for bioprocesses.

Documentation
----------------------------

Documentation is available as docstrings.
Use the built-in ``help`` function to view a function's docstring::

  >>> help(lucullus_rest.export_to_df)
"""

__version__ = "0.0.1"
__author__ = ["Stefan F. Hauer"]
__license__ = "MIT"

from .core import *
from . import utils
