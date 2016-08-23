# -*- coding: utf-8 -*-
"""A client API and CLI to control/manage Theben digital time switches
with a yearly program (TR 64* top2 connected using a EM LAN top2 module)
"""


from .lantop import Lantop, LantopError
from .consts import (
    LANTOP_CONF_PATHS, LOCK_COUNTERS_FILE, DEFAULT_PORT, DEVICE_TYPES,
    STATE_REASONS, CONTROL_MODES, TIMED_STATE_LABELS, ERROR_NAMES
)

__author__ = "Sebastian Koslowski"
__license__ = "GPL"
__copyright__ = "Copyright 2013 Sebastian Koslowski"
__version__ = '4.2.dev'

__all__ = ["Lantop", "LantopError"]

from ._version import get_versions
version_info = get_versions()

if not version_info['error']:
    __version__ = version_info['version']

del get_versions
del version_info
