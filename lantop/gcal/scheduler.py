# -*- coding: utf-8 -*-
"""Crond like scheduler"""

import time
import sched
import sys
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import logging

from .. import utils, Lantop, __version__ as version
from ..lock_counts import LockCounts

from ._config import CONFIG
from .client import GCalEventImporter
from .parser import get_combined_actions
from .utils import PushBulletHandler


def update_jobs(scheduler):
    scheduler.enter(timedelta(minutes=5), 0, update_jobs, (scheduler,))
    logger = logging.getLogger(__name__ + '.updater')

    start = scheduler.timefunc() + timedelta(seconds=30)
    end = start + timedelta(days=CONFIG["time_span"])

    events = GCalEventImporter(CONFIG["calendar_name"]).get_events(start, end)
    logger.info("Imported %d events from Google Calendar", len(events))

    actions = [a for a in get_combined_actions(events) if start < a.time < end]
    logger.info("Scheduling %d actions from event data", len(actions))

    for event in scheduler.queue:
        if event.action == run_lantop:
            scheduler.cancel(event)
    for action in actions:
        scheduler.enterabs(action.time, 1, run_lantop,
                           (action.args, action.label))
        logger.debug(('Adding {0.label!r:50}'
                      ' at {0.time} with {0.args}').format(action))


def run_lantop(change_list, label, retries=5):
    logger = logging.getLogger(__name__ + '.executor')
    logger.warning('Setting %r for event %r', change_list, label)

    device = Lantop(*utils.get_dev_addr(), retries=retries)
    with device, LockCounts() as with_locks:
        for channel, state in change_list.items():
            with_locks.apply(device.set_state, channel, state)


def sync_lantop_time(scheduler, retries=5):
    scheduler.enter(timedelta(days=7), 0, update_jobs, (scheduler,))
    logger = logging.getLogger(__name__ + '.time_sync')

    with Lantop(*utils.get_dev_addr(), retries=retries) as device:
        device.set_time()
    logger.info('Updated time on device')


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(
        fmt='{asctime:10} {levelname:7} {name:35} {message}', style='{'
    ))
    stream_handler.setLevel(logging.INFO)
    root.addHandler(stream_handler)

    pb_handler = PushBulletHandler(
        api_key=CONFIG['PB_API_KEY'], title="CZK Heizung")
    pb_handler.setFormatter(logging.Formatter(
        fmt='{message}\n\n{levelname:7}\n{name:35}', style='{'
    ))
    root.addHandler(pb_handler)

    for name in ('requests', 'googleapiclient'):
        logging.getLogger(name).setLevel(logging.WARNING)


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.warning("Scheduler started (%s)", version)

    def sleep_with_timedelta(duration):
        if hasattr(duration, 'total_seconds'):
            duration = duration.total_seconds()
        time.sleep(duration)

    scheduler = sched.scheduler(
        timefunc=lambda: datetime.now(tzlocal()),
        delayfunc=sleep_with_timedelta
    )
    sync_lantop_time(scheduler)
    update_jobs(scheduler)

    while True:
        try:
            scheduler.run()

        except Exception as e:
            logger.exception(e)

        except KeyboardInterrupt:
            break
