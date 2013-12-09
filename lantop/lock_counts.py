#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Alternative, simplified CLI with a state counter (3 on, 2 off = on)"""

import os
import json
from datetime import datetime, timedelta


class LockCounts(object):
    """Read/write the channel state counters from/to file"""
    max_channels = 8

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
            mod_time_max = 7
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
