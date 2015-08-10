# -*- coding: utf-8 -*-
"""Get/set the default dev addr, setup logging, pushbullet logging handler"""

import os
import sys
import json
import logging
import logging.config

from pushbullet import Pushbullet

from . import LANTOP_CONF_PATH
from .lantop import LantopError

CONFIG_FILE = os.path.join(LANTOP_CONF_PATH, "dev_addr.json")


def get_dev_addr():
    try:
        with open(CONFIG_FILE, "r") as fp:
            dev_addr = json.load(fp)
    except (IOError, ValueError):
        raise LantopError("Can't load default device address")
    return dev_addr


def set_dev_addr(value):
    directory = os.path.dirname(CONFIG_FILE)
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        with open(CONFIG_FILE, "w") as fp:
            json.dump(value, fp)
    except IOError:
        print("Failed to set default address", file=sys.stderr)


def setup_logging():
    """Load logging settings from file"""
    logging_config_file = os.path.join(LANTOP_CONF_PATH, "logging.json")
    if os.path.exists(logging_config_file):
        with open(logging_config_file) as fp:
            logging.config.dictConfig(json.load(fp))
    root = logging.getLogger()
    root.addHandler(logging.NullHandler())


class PushBulletHandler(logging.Handler):

    def __init__(self, api_key, title='', email=None, level=logging.WARNING):
        super().__init__(level)
        self.client = Pushbullet(api_key)
        self.title = title
        self.email = email

    def emit(self, record):
        try:
            self.client.push_note(
                title=self.title, body=self.format(record), email=self.email
            )
        except Exception:
            self.handleError(record)
