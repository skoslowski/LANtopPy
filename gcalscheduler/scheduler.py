# -*- coding: utf-8 -*-
"""Crond like scheduler"""

import time
import sched
import sys
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import logging
import logging.handlers

from lantop import Lantop, utils
from lantop.lock_counts import LockCounts

from ._config import CONFIG
from .client import GCalEventImporter
from .parser import get_combined_actions


def update_jobs(scheduler):
    logger = logging.getLogger(__name__ + '.updater')

    start = scheduler.timefunc() + timedelta(seconds=30)
    end = start + timedelta(days=CONFIG["time_span"])

    events = GCalEventImporter(CONFIG["calendar_name"]).get_events(start, end)
    logger.info("Imported %d events from Google Calendar", len(events))

    actions = [a for a in get_combined_actions(events) if start < a.time < end]
    logger.info("Scheduling %d actions from event data", len(actions))

    for event in scheduler.queue:
        scheduler.cancel(event)

    scheduler.enter(timedelta(minutes=5), 0, update_jobs, (scheduler,))

    for action in actions:
        scheduler.enterabs(action.time, 1, run_lantop,
                           (action.args, action.label))
        logger.debug(('Adding {0.label!r:50}'
                      ' at {0.time} with {0.args}').format(action))


def run_lantop(change_list, label, retries=5):
    logger = logging.getLogger(__name__ + '.executor')
    logger.info('Setting %r for event %r', change_list, label)

    device = Lantop(*utils.get_dev_addr(), retries=retries)
    with device, LockCounts() as with_counters:
        for channel, state in change_list.items():
            with_counters.apply(device.set_state, channel, state)


def main():
    logging.basicConfig(
        stream=sys.stdout,
        style='{',
        format='{asctime:10} {levelname:7} {name:35} {message}',
        level=logging.INFO,
        # filename=os.path.expanduser('~/gcal_scheduler.log')
    )
    logger = logging.getLogger(__name__)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)

    def sleep_with_timedelta(duration):
        if hasattr(duration, 'total_seconds'):
            duration = duration.total_seconds()
        time.sleep(duration)

    scheduler = sched.scheduler(
        timefunc=lambda: datetime.now(tzlocal()),
        delayfunc=sleep_with_timedelta
    )
    update_jobs(scheduler)

    while True:
        try:
            scheduler.run()

        except Exception as e:
            logger.exception(e)

        except KeyboardInterrupt:
            break
