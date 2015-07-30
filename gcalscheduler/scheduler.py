# -*- coding: utf-8 -*-
"""Crond like scheduler"""

import time
import sched
import random
from datetime import datetime, timedelta
from dateutil.tz import tzlocal

import logging
import logging.handlers

from lantop import Lantop, LantopError, utils
from lantop.lock_counts import LockCounts

from gcalscheduler import GCalEventImporter, get_combined_actions, CONFIG


logger = logging.getLogger(__name__)


def update_jobs(scheduler):
    try:
        start = scheduler.timefunc() + timedelta(seconds=30)
        end = start + timedelta(days=CONFIG["time_span"])

        gcal = GCalEventImporter()
        gcal.select_calendar(CONFIG["calendar_name"])
        events = gcal.get_events(start, end)
        actions = get_combined_actions(events)

        for event in scheduler.queue:
            scheduler.cancel(event)

        scheduler.enter(timedelta(minutes=5), 0, update_jobs, (scheduler,))

        for action in actions:
            scheduler.enterabs(action.time, 1, run_lantop,
                               (action.args, action.label))

        logger.info("Imported %d actions from google calendar", len(events))

    except Exception as e:
        logger.exception(e)


def run_lantop(change_list, comment, retries=5):
    logger.info('Starting job %r, args: %r', comment, change_list)

    dev_addr = utils.get_dev_addr()
    device = None
    try:
        # robust connect
        for _ in range(retries):
            try:
                device = Lantop(*dev_addr)
                break
            except LantopError:
                time.sleep(random.uniform(1, 5))
        else:
            raise LantopError("Could not connect to LANtop2")

        with LockCounts(logger=logger) as locks:
            for channel, state in change_list.items():
                locks.apply_new_state(device.set_state, channel, state)

    except LantopError as err:
        logger.error(err.message)

    finally:
        if device:
            device.close()


def main():
    logging.basicConfig(format='%(asctime)-15s %(message)s')
    utils.set_dev_addr(('127.0.0.1', 10001))

    def sleep_with_timedelta(duration):
        if hasattr(duration, 'total_seconds'):
            duration = duration.total_seconds()
        time.sleep(duration)

    scheduler = sched.scheduler(
        timefunc=lambda: datetime.now(tzlocal()),
        delayfunc=sleep_with_timedelta
    )
    update_jobs(scheduler)

    for event in scheduler.queue:
        print(event)

    while True:
        try:
            scheduler.run()
        except Exception as e:
            logger.exception(e)

        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
