# -*- coding: utf-8 -*-
"""Get triggers from Google Calendar and format them for cron"""

import os
import json
import logging
from datetime import datetime, timedelta
from dateutil.tz import tzlocal

from . client import GCalEventImporter, GCalEventError
from . parser import get_combined_actions

from . config import CONFIG
from lantop import LANTOP_CONF_PATH
from lantop.cli import setup_logging


def load_config():
    """Define and parse command line options"""
    config_file = os.path.expanduser(
        os.path.join(LANTOP_CONF_PATH, "gcal_import.json"))
    try:
        with open(config_file, "r") as fp:
            CONFIG.update(json.load(fp))
    except (IOError, ValueError):
        pass


def main():
    """get event and generate crontab"""
    setup_logging()
    logger = logging.getLogger(__name__)
    load_config()

    # get events from Google Calendar
    now = datetime.now(tzlocal())
    try:
        gcal = GCalEventImporter(CONFIG["calendar_name"])
        events = gcal.get_events(now - timedelta(days=1),
                                 now + CONFIG["time_span"])
    except GCalEventError as err:
        logger.exception(err)
        return -1

    # build cron file with data found in events
    try:
        entries = [str(action).encode("UTF-8")
                   for action in get_combined_actions(events)
                   if action.time > now]
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
        return -1
