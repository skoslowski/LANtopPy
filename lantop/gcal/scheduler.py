# -*- coding: utf-8 -*-
"""Crond like scheduler"""

import time
import sched
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import logging

from .. import utils, Lantop, __version__
from ..lock_counts import LockCounts

from .config import CONFIG
from .client import GCalEventImporter, GCalEventError
from .parser import get_combined_actions


def update_jobs(scheduler):
    scheduler.enter(CONFIG['poll_interval'], 0, update_jobs, (scheduler,))
    logger = logging.getLogger(__name__ + '.updater')

    start = scheduler.timefunc() + timedelta(seconds=30)
    end = start + CONFIG["time_span"]

    try:
        gcal = GCalEventImporter(CONFIG["calendar_name"])
        events = gcal.get_events(start, end)
    except GCalEventError:
        logger.error("Can't fetch events from Google Calender")
        return

    actions = [a for a in get_combined_actions(events) if start < a.time < end]

    logger.info("Scheduling %d actions from %d Google Calender events",
                len(actions), len(events))

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
    logger.info('Setting %r for event %r', change_list, label)

    device = Lantop(*utils.get_dev_addr(), retries=retries)
    with device, LockCounts() as with_locks:
        for channel, state in change_list.items():
            with_locks.apply(device.set_state, channel, state)

        logger.warning(
            'Event: %r\nStates:%s', label,
            ' '.join('{active:d}'.format(**ch) for ch in device.get_states())
        )


def sync_lantop_time(scheduler, retries=5):
    scheduler.enter(timedelta(days=7), 2, update_jobs, (scheduler,))
    logger = logging.getLogger(__name__ + '.time_sync')

    with Lantop(*utils.get_dev_addr(), retries=retries) as device:
        device.set_time()
    logger.info('Updated time on device')


def main():
    utils.setup_logging()
    logger = logging.getLogger(__name__)
    logger.warning("Scheduler started (%s)", __version__)

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
