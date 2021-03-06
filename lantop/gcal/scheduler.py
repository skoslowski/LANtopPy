"""Crond like scheduler"""

import time
import sched
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import logging
import logging.config
import functools

from . import parser, client, authenticator, __version__

from .. import Lantop, utils
from ..lock_counts import LockCounts


class NeedAuthError(Exception):
    """Missing authentication error"""

logger = logging.getLogger(__name__)


class JobUpdater:
    def __init__(self, googleapi, calendar_name, time_span, **_):
        self.event_importer_kwargs = googleapi
        self.calendar_name = calendar_name
        self.time_span = timedelta(**time_span)

        self.logger = logger.getChild('update_jobs')

        self.wait_for_auth = False

    def run(self, scheduler, lantop_updater):
        if self.wait_for_auth:
            return
        try:
            self.update(scheduler, lantop_updater)
        except client.Error as error:
            self.logger.error(error)
            raise NeedAuthError()

    def update(self, scheduler, lantop_updater):
        gcal = client.EventImporter(**self.event_importer_kwargs)
        gcal.select_calendar(self.calendar_name)

        start = scheduler.timefunc()
        end = start + self.time_span
        events = gcal.get_events(start, end)
        actions = [action for action in parser.get_combined_actions(events)
                   if start < action.time < end]

        self.logger.info("Scheduling %d actions from %d Google Calender events",
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
            self.logger.debug('Adding {0.label!r:50} '
                              'at {0.time} with {0.args}'.format(action))


class LantopStateChanger:
    def __init__(self, address, channel_names, retries=5, **_):
        if not address:
            raise ValueError('Missing device address setting')
        self.lantop_args = address + [retries]
        self.channel_names = channel_names

    def update_states(self, change_list, label):
        logger.getChild('update_states').info(
            'Setting %r for event %r', change_list, label)

        device = Lantop(*self.lantop_args)
        with device, LockCounts() as with_locks:
            for channel, state in change_list.items():
                with_locks.apply(device.set_state, channel, state)

            time.sleep(5.0)  # else, the reported states can be outdated
            new_states = ['{active:d}'.format(**ch) for ch in device.get_states()]
            logger.getChild('monitor').info(
                'Event: %r\n%s\nStates: %s', label or '(no label)',
                '\n'.join('{}: {}'.format(self.channel_names[ch], state)
                          for ch, state in sorted(change_list.items())),
                ' '.join(new_states))

    def sync_time(self):
        with Lantop(*self.lantop_args) as device:
            device.set_time()
        logger.getChild('sync_time').info('Updated time on device')


class Scheduler(sched.scheduler):

    def enter_per(self, delay, priority, action, argument=(), kwargs=None):
        """Enter an action to be executed now and then periodically"""
        kwargs = kwargs or {}

        @functools.wraps(action)
        def action_wrapped(*argument_, **kwargs_):
            event = self.enter(delay, priority, action_wrapped, argument, kwargs)
            result = action(*argument_, **kwargs_)
            if result == 'cancel':
                self.cancel(event)
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

    job_updater = JobUpdater(config.googleapi, **config.scheduler)
    lantop_worker = LantopStateChanger(**config.device)
    try:
        auth_flow = authenticator.Flow(config.googleapi, **config.pb_authenticator)
    except ValueError:
        auth_flow = None
        logger.debug('Authenticator disabled')

    scheduler = Scheduler(
        timefunc=lambda: datetime.now(tzlocal()),
        delayfunc=Scheduler.sleep_with_timedelta
    )
    scheduler.enter_per(
        delay=timedelta(**config.scheduler.poll_interval),
        priority=1,
        action=job_updater.run,
        argument=(scheduler, lantop_worker.update_states),
    )
    if config.device.time_sync_interval:
        scheduler.enter_per(
            delay=timedelta(**config.device.time_sync_interval),
            priority=2,
            action=lantop_worker.sync_time
        )
    if auth_flow:
        scheduler.enter_per(
            delay=timedelta(**config.pb_authenticator.poll_interval),
            action=auth_flow.check_response,
            priority=0
        )

    logger.warning("Scheduler started (%s)", __version__)
    while True:
        try:
            scheduler.run()

        except NeedAuthError:
            if auth_flow:
                job_updater.wait_for_auth = True

                def end_auth(): job_updater.wait_for_auth = False
                auth_flow.run(callback=end_auth)

        except Exception as e:
            print(e)
            logger.exception(e)

        except KeyboardInterrupt:
            break
