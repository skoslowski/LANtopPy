# -*- coding: utf-8 -*-
"""Get/set the default dev addr"""

import os
import sys
import json

from . import LANTOP_CONF_PATH
from .lantop import LantopError

config_file = os.path.expanduser(
    os.path.join(LANTOP_CONF_PATH, "dev_addr.json"))


def get_dev_addr():
    try:
        with open(config_file, "r") as fp:
            dev_addr = json.load(fp)
    except (IOError, ValueError):
        raise LantopError("Can't load default device address")
    return dev_addr


def set_dev_addr(value):
    directory = os.path.dirname(config_file)
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        with open(config_file, "w") as fp:
            json.dump(value, fp)
    except IOError:
        print("Failed to set default address", file=sys.stderr)
