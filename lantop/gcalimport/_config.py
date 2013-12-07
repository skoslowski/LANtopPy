# -*- coding: utf-8 -*-
"""Config values for gcalimport package"""

CONFIG = {
    ############################################################
    # Event importer
    ############################################################
    # Calendar to import events from
    'calendar_name': 'CZK',
    # how many days to get events in advantage
    'time_span': 7,  # days
    # mapping of channel labels to their indexes
    'channels': {
        u'lüftung': 0,
        u'mutterkind': 1,
        u'heizung': 2,
        u'spare': 3
    },

    ############################################################
    # Google Calendar API
    ############################################################
    'api_params': {
        'client_id': '',
        'client_secret': '',
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'scope': 'https://www.googleapis.com/auth/calendar.readonly',
        'user_agent': 'CZK-Heizungsteuerung/v1.0'
    },
    'dev_key': '',

    ############################################################
    # Cron settings
    ############################################################
    # crontab file path to save output
    'cron_file': '/etc/cron.d/lantop_set_state',
    # user for cron jobs
    'cron_user': 'root',
    # lantop cli command line
    'cron_cmd': '/usr/local/bin/lantop {args} --retries 5 --quiet',
    # argument template to the above command
    'cron_arg': u'--state {channel:d}:{state:s}'
}