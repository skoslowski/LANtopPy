#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Alternative, simplified CLI with a state counter (3 on, 2 off = on)"""

import os
import sys
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

from random import randint
from time import sleep

import argparse

from . cli import set_state_type, dev_addr_type, get_logger
from . lantop import Lantop, LantopException, CONTROL_MODES
from . _config import LANTOP_CONF_PATH, CONFIG


def parse_args(args):
    """Define and parse command line options"""

    config_file = os.path.expanduser(
        os.path.join(LANTOP_CONF_PATH, 'dev_addr.json'))
    try:
        with open(config_file, 'r') as fp:
            dev_addr = json.load(fp)
    except (IOError, ValueError):
        dev_addr = None

    extra_args = {'nargs': '?', 'default': dev_addr} if dev_addr else {}
    parser = argparse.ArgumentParser(description='Get and set LANtop2 state, '
                                                 'settings and statistics')

    parser.add_argument(metavar="host[:port]", dest="dev_addr",
                        type=dev_addr_type,
                        help="Device host name or IP (and port)", **extra_args)
    parser.add_argument("-c", "--count", dest='print_counts',
                        action='store_true',
                        help="print the current channel counts")
    parser.add_argument("-s", "--state", metavar='CH:ST', dest='set_states',
                        type=set_state_type, nargs='+',
                        help="Set a channel CH (0, 1, ...) to a new state ST" +
                             "(" + ", ".join(CONTROL_MODES.keys()) + ")")

    return parser.parse_args(args)


class StateCounts(object):
    """Read/write the channel state counters from/to file"""
    max_channels = CONFIG['num_channels']

    def __init__(self, filename, logger):
        self.filename = filename
        self.logger = logger

        self._counts = None
        self.modified = False
        self.load()

    def __getitem__(self, item):
        return self._counts[item]

    def __setitem__(self, key, value):
        self._counts[key] = value
        self.modified = True

    def __del__(self):
        self.save()

    def __str__(self):
        return str(self._counts)

    def load(self):
        """Load counts from file"""
        try:
            # check mod time
            mod_time = datetime.fromtimestamp(os.path.getmtime(self.filename))
            mod_time_max = CONFIG['mod_time_warning']
            if mod_time_max > 0 and \
               datetime.now() - mod_time > timedelta(days=mod_time_max):
                self.logger.warning(
                    'State file was not modified in the last %d days.',
                    mod_time_max)
            # load counts
            with open(self.filename, 'r') as fp:
                counts = json.load(fp)
            # check consistency
            if len(counts) < self.max_channels:
                counts = (counts + [0] * self.max_channels)[:self.max_channels]
                self.logger.warning('States file did not contain %d entries',
                               self.max_channels)

        except (os.error, TypeError, ValueError, IOError):
            self.logger.warning(
                'Could not access or open state file, using all zeros')
            counts = [0] * self.max_channels

        self._counts = counts

    def save(self, force=False):
        """Store updated channel state counts to file"""
        if force or self.modified:
            try:
                with open(self.filename, 'w') as fp:
                    json.dump(self._counts, fp)
                self.modified = False
            except IOError:
                raise RuntimeError('Could not write states file')

@contextmanager
def delayed_connect(address, logger):
    """Context manager to connect to a LANtop2 with a random delay"""
    try:
        device = Lantop(*address)
    except LantopException:
        logger.warning("First attempt to connect to LANtop failed.")
        device = None

    try:  # if some else is connected wait and try again
        if device is None:
            sleep(randint(5, 30))
            device = Lantop(*address)

        yield device

    except LantopException as err:
        raise RuntimeError('LANtop2: ' + err.message)

    finally:
        del device


def main(args):
    """main function for CLI"""
    logger = get_logger('lantop.state_tracking')

    try:
        options = parse_args(args or sys.argv[1:])

        # read state file and get previous counts
        counts = StateCounts(CONFIG['state_counts_file'], logger)

        if options.print_counts:
            print("Current channel counts: {}".format(str(counts)))

        if not options.set_states:
            return

        # delay connection attempt if a channel is going to be set to auto
        # if events "touch" the on command gets executed first
        if 'auto' in [state for channel, state in options.set_states]:
            sleep(randint(2, 5))

        with delayed_connect(options.dev_addr, logger) as device:
            # read state file and get previous counts
            counts.load()

            for channel, state in options.set_states:
                # ...flat is better than nested...ups...
                if state == 'on':
                    if counts[channel] == 0:
                        device.set_state(channel, state)
                    counts[channel] += 1

                elif state == 'auto':
                    counts[channel] -= 1
                    if counts[channel] <= 0:
                        device.set_state(channel, state)
                    if counts[channel] < 0:
                        counts[channel] = 0
                        logger.warning('Negative count on channel %d', channel)

                elif state == 'off':
                    counts[channel] = 0
                    device.set_state(channel, state)

                logger.info('Set channel %d to state %s %s',
                            channel, state, counts)

        if options.print_counts:
            print "New channel counts:", counts

    except Exception as err:
        logger.exception(err)
        # logger.error(err.message)
        return 1
