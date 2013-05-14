# -*- coding: utf-8 -*-
"""Get triggers from Google Calendar and format them for cron"""

import os
import logging
import logging.config
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import json

from . event_importer import GCalEventImporter, GCalEventError, extract_actions
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
        os.path.join(LANTOP_CONF_PATH, 'logging.conf'))
    if os.path.exists(logging_config_file):
        logging.config.fileConfig(logging_config_file)
    logger = logging.getLogger('lantop.google_importer')
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
    output = u''
    action_counter = 0
    try:
        output += u"# LANtopPy file - auto generated from google calendar\n"
        last_day = None

        for action in extract_actions(events, CONFIG['channels']):
            # skip past events
            if action['start'] <= now:
                continue
            # emtpy line between events of different days
            if last_day is None or last_day < action['start'].date():
                last_day = action['start'].date()
                output += "\n"
            # generate crontab line
            output += (u"{start:%M %H %d %m *}\t{user}\t"
                       u"{cmd} " + CONFIG['cron']['args'] + u"\t"
                       u"# {comment}\n").format(user=CONFIG['cron']['user'],
                                                cmd=CONFIG['cron']['cmd'],
                                                **action)
            action_counter += 1
    #except Exception as e:
    #    logger.exception(e)
    #    #logger.error("Could not parse event data: %s", str(e))
    #    return 1
    finally:
        pass
    # log import, warn if no event at least every other day
    logger.info('Imported %d actions from google calendar', action_counter)

    print output

    # all good till here? Write triggers to file
    try:
        with open(CONFIG['cron']['file'], 'w') as fp:
            fp.write(output.encode('utf8'))
    except IOError:
        logger.error("Could not write to cron file")
        return 1