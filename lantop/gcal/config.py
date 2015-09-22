# -*- coding: utf-8 -*-
"""Config values for gcal package"""

import datetime
import os

from lantop import LANTOP_CONF_PATH


CONFIG = {
    ############################################################
    # Event importer
    ############################################################
    # Calendar to import events from
    'calendar_name': 'CZK',
    # how many days to get events in advantage
    'time_span': datetime.timedelta(days=7),
    # list of channel labels
    'channels': [
        'Lüftung',
        'Mutterkind',
        'Heizung',
        'Spare',
    ],
    # how often to check to changes events
    'poll_interval': datetime.timedelta(minutes=20),

    ############################################################
    # Google Calendar API
    ############################################################
    'client_secrets': os.path.join(LANTOP_CONF_PATH, 'client_secret.json'),
    'scope': 'https://www.googleapis.com/auth/calendar.readonly',
    'dev_key': os.path.join(LANTOP_CONF_PATH, 'google_dev_key.json'),
    'credentials_storage_path': os.path.join(LANTOP_CONF_PATH, 'api_token.json'),

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
