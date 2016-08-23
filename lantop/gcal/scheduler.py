"""Crond like scheduler"""

import time
import sched
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import logging
import logging.config
import functools

from . import parser, client, __version__

from .. import Lantop, utils
from ..lock_counts import LockCounts


def update_jobs(scheduler, lantop_updater, calendar_name, time_span, googleapi, **_):
    logger = logging.getLogger(__name__ + '.update_jobs')

    start = scheduler.timefunc()
    end = start + timedelta(**time_span)

    try:
        gcal = client.EventImporter(**googleapi)
        gcal.select_calendar(calendar_name)
        events = gcal.get_events(start, end)
    except client.Error as error:
        logger.error(error)
        return

    actions = [a for a in parser.get_combined_actions(events)
               if start < a.time < end]

    logger.info("Scheduling %d actions from %d Google Calender events",
                len(actions), len(events))

    for event in scheduler.queue:
        if event.action == lantop_updater:
            scheduler.cancel(event)
    for action in actions:
        scheduler.enterabs(
            time=action.time,
            priority=1,
            action=lantop_updater,
            argument=(action.args, parser.simplify_label(action))
        )
        logger.debug('Adding {0.label!r:50} at {0.time} with {0.args}'
                     ''.format(action))


class LantopStateChanger:

    def __init__(self, address, channel_names, retries=5):
        self.lantop_args = address + [retries]
        self.channel_names = channel_names

    def update_states(self, change_list, label):
        logger = logging.getLogger(__name__ + '.update_states')
        logger.info('Setting %r for event %r', change_list, label)

        device = Lantop(*self.lantop_args)
        with device, LockCounts() as with_locks:
            for channel, state in change_list.items():
                with_locks.apply(device.set_state, channel, state)

            time.sleep(5.0)  # else, the reported states can be outdated
            new_states = ['{active:d}'.format(**ch) for ch in device.get_states()]
            logging.getLogger(__name__ + '.monitor').info(
                'Event: %r\n%s\nStates: %s', label or '(no label)',
                '\n'.join('{}: {}'.format(self.channel_names[ch], state)
                          for ch, state in sorted(change_list.items())),
                ' '.join(new_states))

    def sync_time(self):
        logger = logging.getLogger(__name__ + '.sync_time')
        with Lantop(*self.lantop_args) as device:
            device.set_time()
        logger.info('Updated time on device')


class Scheduler(sched.scheduler):

    def enter_per(self, delay, priority, action, argument=(), kwargs=None):
        """Enter an action to be executed now and then periodically"""
        kwargs = kwargs or {}

        @functools.wraps(action)
        def action_wrapped(*argument_, **kwargs_):
            self.enter(delay, priority, action_wrapped, argument, kwargs)
            action(*argument_, **kwargs_)
        self.enter(timedelta(), priority, action_wrapped, argument, kwargs)

    @staticmethod
    def sleep_with_timedelta(duration):
        if hasattr(duration, 'total_seconds'):
            duration = duration.total_seconds()
        time.sleep(duration)


def main():
    config = utils.load_config()
    logging.config.dictConfig(config.get('logging', {}))
    parser.Action.set_defaults(config.device.channel_names, **config.cron)
    logger = logging.getLogger(__name__)

    lantop_worker = LantopStateChanger(**config.device)

    logger.warning("Scheduler started (%s)", __version__)
    scheduler = Scheduler(
        timefunc=lambda: datetime.now(tzlocal()),
        delayfunc=Scheduler.sleep_with_timedelta
    )
    scheduler.enter_per(
        delay=timedelta(**config.scheduler.poll_interval),
        priority=0,
        action=update_jobs,
        argument=(scheduler, lantop_worker.update_states),
        kwargs=config.scheduler
    )
    scheduler.enter_per(
        delay=timedelta(days=7),
        priority=2,
        action=lantop_worker.sync_time
    )

    while True:
        try:
            scheduler.run()

        except Exception as e:
            print(e)
            logger.exception(e)

        except KeyboardInterrupt:
            break
