# -*- coding: utf-8 -*-
"""Config values for gcal package"""

import datetime
import os

from lantop import LANTOP_CONF_PATH


def _full_path(name):
    return os.path.expanduser(os.path.join(LANTOP_CONF_PATH, name))


CONFIG = {
    ############################################################
    # Event importer
    ############################################################
    # Calendar to import events from
    'calendar_name': 'CZK',
    # how many days to get events in advantage
    'time_span': datetime.timedelta(days=7),  # days
    # mapping of channel labels to their indexes
    'channels': {
        'lüftung': 0,
        'mutterkind': 1,
        'heizung': 2,
        'spare': 3
    },
    # how often to check to changes events
    'poll_interval': datetime.timedelta(minutes=20),

    ############################################################
    # Push Bullet API
    ############################################################
    'PB_API_KEY': _full_path('pushbullet_logger.json'),

    ############################################################
    # Google Calendar API
    ############################################################
    'credentials_storage_path': _full_path('api_token.json'),
    'client_secrets': _full_path('client_secret.json'),
    'scope': 'https://www.googleapis.com/auth/calendar.readonly',
    'dev_key': _full_path('google_dev_key.json'),

    ############################################################
    # Cron settings
    ############################################################
    # crontab file path to save output
    'cron_file': '/etc/cron.d/lantop_set_state',
    # user for cron jobs
    'cron_user': 'root',
    # lantop cli command line
    'cron_cmd': '/usr/local/bin/lantop --state {args} --retries 5 --quiet',
    # argument template to the above command
    'cron_arg': '{channel:d}:{state:4s}'
}
