# -*- coding: utf-8 -*-
"""Get triggers from Google Calendar and format them for cron"""

import os
import logging
import logging.config
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import json

from . event_importer import GCalEventImporter, GCalEventError
from . event_parser import get_combined_actions

from . _config import CONFIG
from .. _config import LANTOP_CONF_PATH


def load_config():
    """Define and parse command line options"""
    config_file = os.path.expanduser(
        os.path.join(LANTOP_CONF_PATH, 'gcal_import.json'))

    try:
        with open(config_file, 'r') as fp:
            CONFIG.update(json.load(fp))
    except (IOError, ValueError):
        pass


def main():
    """get event and generate crontab"""
    load_config()

    # get logger
    logging_config_file = os.path.expanduser(
        os.path.join(LANTOP_CONF_PATH, 'logging.json'))
    if os.path.exists(logging_config_file):
        with open(logging_config_file, 'r') as fp:
            logging.config.dictConfig(json.load(fp))
    logger = logging.getLogger('lantop.gcal_import')
    logger.addHandler(logging.NullHandler())

    # get events from Google Calendar
    now = datetime.now(tzlocal())
    try:
        gcal = GCalEventImporter()
        gcal.select_calendar(CONFIG['calendar_name'])
        events = gcal.get_events(now - timedelta(days=1),
                                 now + timedelta(days=CONFIG['time_span']))
    except GCalEventError as err:
        logger.exception(err)
        return 1

    # build cron file with data found in events
    try:
        entries = [unicode(action).encode("UTF-8")
                   for action in get_combined_actions(events)
                   if action.time > now]
        logger.info("Imported %d actions from google calendar", len(entries))

    except Exception as e:
        logger.exception(e)
        #logger.error("Could not parse event data: %s", str(e))
        return 1

    # all good till here? Write triggers to file
    try:
        with open(CONFIG['cron_file'], 'w') as fp:
            fp.write("# LANtopPy actions - generated from google calendar\n")
            fp.write("\n".join(entries))
    except IOError:
        logger.error("Could not write to crontab file")
        return 1