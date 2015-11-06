# -*- coding: utf-8 -*-
"""Get triggers from Google Calendar and format them for cron"""

import logging
from datetime import datetime, timedelta
from dateutil.tz import tzlocal

from .. import utils

from . client import EventImporter, EventImporterError
from . parser import get_combined_actions, remove_duplicate_comments
from . config import CONFIG, load_user_config


def main():
    """get event and generate crontab"""
    utils.setup_logging()
    logger = logging.getLogger(__name__)
    try:
        load_user_config()
    except Exception as err:
        logger.exception(err)
        exit(err)

    # get events from Google Calendar
    now = datetime.now(tzlocal())
    try:
        gcal = EventImporter(CONFIG["calendar_name"])
        events = gcal.get_events(now - timedelta(days=1),
                                 now + CONFIG["time_span"])
    except EventImporterError as err:
        logger.exception(err)
        return 1

    # build cron file with data found in events
    try:
        actions = remove_duplicate_comments(get_combined_actions(events))
        entries = [str(action) for action in actions if action.time > now]
        logger.info("Imported %d actions from Google Calendar", len(entries))

    except Exception as err:
        logger.exception(err)
        return 1

    # all good till here? Write triggers to file
    try:
        with open(CONFIG["cron_file"], "w") as fp:
            fp.write("# LANtopPy actions - generated from google calendar\n")
            fp.write("\n".join(entries) + "\n")
    except IOError:
        logger.error("Could not write to crontab file")
        return 1
