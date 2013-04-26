# -*- coding: utf-8 -*-
"""A client API and CLI to control/manage Theben digital time switches
with a yearly programm (TR 64* top2 connected using a EM LAN top2 module)
"""

from . lantop import Lantop, LantopException

__all__ = ["Lantop", "LantopException"]
__author__ = "Sebastian Koslowski"
__license__ = "GPL"
__copyright__ = "Copyright 2013 Sebastian Koslowski"

try:
    from _version import __version__
except ImportError:
    __version__ = "Unknown"