# -*- coding: utf-8 -*-
"""A client API and CLI to control/manage Theben digital time switches
with a yearly program (TR 64* top2 connected using a EM LAN top2 module)
"""


import os.path

from .lantop import Lantop, LantopError
from .consts import (
    DEFAULT_LANTOP_CONF_PATH, LOCK_COUNTERS_FILE, DEFAULT_PORT, DEVICE_TYPES,
    STATE_REASONS, CONTROL_MODES, TIMED_STATE_LABELS, ERROR_NAMES
)


__all__ = ["Lantop", "LantopError"]
__author__ = "Sebastian Koslowski"
__license__ = "GPL"
__copyright__ = "Copyright 2013 Sebastian Koslowski"


LANTOP_CONF_PATH = os.path.abspath(os.path.expanduser(
    os.environ.get('LANTOP_CONF_PATH', DEFAULT_LANTOP_CONF_PATH)))

LANTOP_CONF_FILE = os.path.join(LANTOP_CONF_PATH, "lantop.json")


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
