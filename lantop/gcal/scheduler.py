# -*- coding: utf-8 -*-
"""Crond like scheduler"""

import time
import sched
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import logging
import functools

from .. import utils, Lantop, __version__
from ..lock_counts import LockCounts

from . import parser, client
from .config import CONFIG, load_user_config


def update_jobs(scheduler):
    logger = logging.getLogger(__name__ + '.updater')

    start = scheduler.timefunc()
    end = start + CONFIG["time_span"]

    try:
        gcal = client.EventImporter(CONFIG["calendar_name"])
        events = gcal.get_events(start, end)
    except client.EventImporterError:
        logger.error("Can't fetch events from Google Calender")
        return

    actions = [a for a in parser.get_combined_actions(events)
               if start < a.time < end]

    logger.info("Scheduling %d actions from %d Google Calender events",
                len(actions), len(events))

    for event in scheduler.queue:
        if event.action == run_lantop:
            scheduler.cancel(event)
    for action in actions:
        scheduler.enterabs(action.time, 1, run_lantop,
                           (action.args, parser.simplify_label(action)))
        logger.debug(('Adding {0.label!r:50}'
                      ' at {0.time} with {0.args}').format(action))


def run_lantop(change_list, label, retries=5):
    logger = logging.getLogger(__name__ + '.executor')
    logger.info('Setting %r for event %r', change_list, label)

    device = Lantop(*utils.get_dev_addr(), retries=retries)
    with device, LockCounts() as with_locks:
        for channel, state in change_list.items():
            with_locks.apply(device.set_state, channel, state)
        time.sleep(5.0)  # else, the reported states can be outdated
        new_states = ['{active:d}'.format(**ch) for ch in device.get_states()]
        logger.warning(
            'Event: %r\n%s\nStates: %s', label or '(no label)',
            '\n'.join('{}: {}'.format(CONFIG['channels'][ch], state)
                      for ch, state in sorted(change_list.items())),
            ' '.join(new_states)
        )


def sync_lantop_time(retries=5):
    logger = logging.getLogger(__name__ + '.time_sync')

    with Lantop(*utils.get_dev_addr(), retries=retries) as device:
        device.set_time()
    logger.info('Updated time on device')


class Scheduler(sched.scheduler):

    def enter_per(self, delay, priority, action, argument=(), kwargs=None):
        """Enter an action to be executed now and then periodically"""
        kwargs = kwargs or {}

        @functools.wraps(action)
        def action_wrapped(*args_, **kwargs_):
            self.enter(delay, priority, action_wrapped, argument, kwargs)
            action(*args_, **kwargs_)
        self.enter(timedelta(), priority, action_wrapped, argument, kwargs)

    @staticmethod
    def sleep_with_timedelta(duration):
        if hasattr(duration, 'total_seconds'):
            duration = duration.total_seconds()
        time.sleep(duration)


def main():
    utils.setup_logging()
    logger = logging.getLogger(__name__)

    try:
        load_user_config()
    except Exception as e:
        logger.exception(e)
        exit(e)

    logger.warning("Scheduler started (%s)", __version__)
    scheduler = Scheduler(
        timefunc=lambda: datetime.now(tzlocal()),
        delayfunc=Scheduler.sleep_with_timedelta
    )
    scheduler.enter_per(CONFIG['poll_interval'], 0, update_jobs, (scheduler,))
    scheduler.enter_per(timedelta(days=7), 2, sync_lantop_time)

    while True:
        try:
            scheduler.run()

        except Exception as e:
            print(e)
            logger.exception(e)

        except KeyboardInterrupt:
            break
