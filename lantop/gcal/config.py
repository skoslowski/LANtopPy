# -*- coding: utf-8 -*-
"""Config values for gcal package"""

import json
import datetime
from collections import Mapping

from lantop import LANTOP_CONF_PATH, LANTOP_CONF_FILE


CONFIG = {
    # "device": ["127.0.0.1", 10001],  # set by lantop command

    # Google Calendar API
    "google_dev_key": "TO_BE_SET_BY_USER",
    "client_secrets": "{conf_path}/client_secret.json",
    "credentials_storage_path": "{conf_path}/api_token.json",

    # Calendar to import events from
    "calendar_name": "TO_BE_SET_BY_USER",
    # how far to get events in advance
    "time_span": {"days": 7},  # datetime.timedelta kwargs
    # list of channel labels
    "channels": [
        "ch0",
        "ch1",
        "ch2",
        "ch3"
    ],
    # how often to check to changes events
    "poll_interval": {"minutes": 20},  # datetime.timedelta kwargs

    # cron settings
    "cron_file": "/etc/cron.d/lantop_set_state",
    "cron_user": "root",
    "cron_cmd": "lantop --state {args} --retries 5 --quiet",
    "cron_arg": "{channel:d}:{state:4s}"
}


def load_user_config():
    def make_timedelta(d):
        return datetime.timedelta(**d) if isinstance(d, Mapping) else d

    def expand_config_path(filepath):
        return filepath.format(conf_path=LANTOP_CONF_PATH)

    transforms = {
        "time_span": make_timedelta,
        "poll_interval": make_timedelta,
        "client_secrets": expand_config_path,
        "credentials_storage_path": expand_config_path,
    }

    try:
        with open(LANTOP_CONF_FILE, encoding='utf-8') as fp:
            user_config = json.load(fp)
            CONFIG.update(user_config)
    except FileNotFoundError:
        pass

    for key, transform in transforms.items():
        CONFIG[key] = transform(CONFIG[key])
