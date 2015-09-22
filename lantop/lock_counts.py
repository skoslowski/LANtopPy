# -*- coding: utf-8 -*-
"""Alternative, simplified CLI with a state counter (3 on, 2 off = on)"""

import os
import json
import logging
from datetime import datetime, timedelta

from . consts import LOCK_COUNTERS_FILE


class LockCounts(object):
    """Read/write the channel state counters from/to file"""
    max_channels = 8

    def __init__(self, filename=None, logger=None):
        self.filename = filename or LOCK_COUNTERS_FILE
        self.logger = logger or logging.getLogger(__name__)

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

    def load(self):
        """Load counts from file"""
        try:
            # check mod time
            mod_time = datetime.fromtimestamp(os.path.getmtime(self.filename))
            mod_time_max = 7
            if mod_time_max > 0 and \
               datetime.now() - mod_time > timedelta(days=mod_time_max):
                self.logger.warning(
                    "State file was not modified in the last %d days.",
                    mod_time_max)
            # load counts
            with open(self.filename, "r") as fp:
                counts = json.load(fp)
            # check consistency
            if len(counts) < self.max_channels:
                counts = (counts + [0] * self.max_channels)[:self.max_channels]
                self.logger.warning("States file did not contain %d entries",
                               self.max_channels)

        except (os.error, TypeError, ValueError, IOError):
            self.logger.warning(
                "Could not access or open state file, using all zeros")
            counts = [0] * self.max_channels

        self._counts = counts

    def save(self, force=False):
        """Store updated channel state counts to file"""
        if not (force or self.modified):
            return
        directory = os.path.dirname(self.filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(self.filename, "w") as fp:
            json.dump(self._counts, fp)
        self.modified = False

    def apply(self, func, channel, state):
        logger = self.logger

        def apply():
            func(channel, state)
            logger.info("Set channel {} to state {!r}.".format(channel, state))

        self[channel] += 1 if state == "on" else -1

        if self[channel] == 1 and state == "on":
            apply()
        elif self[channel] <= 0 and state == "auto":
            apply()
        elif state == "off":
            apply()
            self[channel] = 0
        else:
            logger.info("Channel {} unchanged (locked).".format(channel))

        if self[channel] < 0:
            self[channel] = 0
            logger.warning("Negative count on channel %d", channel)

        logger.debug("Lock counters changed to {}".format(self))
