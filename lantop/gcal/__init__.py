# -*- coding: utf-8 -*-
"""Google Calendar connector for lantop package"""

from . client import EventImporter, EventImporterError
from . cli import main
from . config import CONFIG

__all__ = ["EventImporter", "EventImporterError"]
__author__ = "Sebastian Koslowski"
__license__ = "GPL"
__copyright__ = "Copyright 2013 Sebastian Koslowski"

try:
    from _version import __version__
except ImportError:
    __version__ = "Unknown"
