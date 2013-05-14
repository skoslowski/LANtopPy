# -*- coding: utf-8 -*-
"""Google Calendar connector for lantop package"""

from . event_importer import GCalEventImporter
from . cli import main

__all__ = ['GCalEventImporter', 'main']
__author__ = "Sebastian Koslowski"
__license__ = "GPL"
__copyright__ = "Copyright 2013 Sebastian Koslowski"

try:
    from _version import __version__
except ImportError:
    __version__ = "Unknown"