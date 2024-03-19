# MIT License
# Copyright \(c\) 2023-2024 ZHAW (Institute of Embedded Systems at Zurich University of Applied Sciences) & Securecell AG
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# https://mit-license.org/

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
