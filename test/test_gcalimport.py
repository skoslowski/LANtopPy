#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from datetime import datetime, timedelta
from dateutil.tz import tzlocal

from lantop.gcalimport.event_parser import LantopCronAction, extract_actions, \
    extract_actions_from_desc

CHANNELS = {'ch' + str(i): i for i in range(4)}
NOW = datetime.now(tzlocal())


def Event(summary='', start=None, end=None, description=''):
    """Get event dict like google API does"""
    return {'summary': summary or u"summary",
            'start': start or NOW,
            'end': end or NOW + timedelta(hours=2),
            'description': description}


class EventParserTest(unittest.TestCase):
    def test_parse_events(self):
        events = [Event(summary=u"x ch0 adsf"), Event(summary=u"ch1")]
        actions = list(extract_actions(events, CHANNELS))
        exp = [LantopCronAction(0, NOW, timedelta(minutes=120), u"x ch0 adsf"),
               LantopCronAction(1, NOW, timedelta(minutes=120), u"ch1")]
        self.assertEqual(exp, actions)

    def test_parse_empty_event(self):
        self.assertEqual([], list(extract_actions([Event()], CHANNELS)))

    def test_parse_desc(self):
        events = [Event(description=u"j ch0 adsf ch2")]
        actions = list(extract_actions(events, CHANNELS))
        exp = [LantopCronAction(0, NOW, timedelta(minutes=120), u"summary"),
               LantopCronAction(2, NOW, timedelta(minutes=120), u"summary")]
        self.assertEqual(exp, actions)

    def test_parse_desc_offset(self):
        events = [Event(description=u"ch1+60")]
        actions = list(extract_actions(events, CHANNELS))
        actions2 = list(extract_actions_from_desc(events[0], CHANNELS))
        self.assertEqual(actions, actions2)
        exp = [LantopCronAction(1, NOW + timedelta(minutes=60),
                                timedelta(minutes=60), u"summary")]
        self.assertEqual(exp, actions)

    def test_parse_desc_offsets(self):
        events = [Event(description=u"ch1+30-60")]
        actions = list(extract_actions(events, CHANNELS))
        exp = [LantopCronAction(1, NOW + timedelta(minutes=30),
                                timedelta(minutes=30), u"summary")]
        self.assertEqual(exp, actions)

    def test_parse_desc_offsets(self):
        events = [Event(description=u"ch1+30-60")]
        actions = list(extract_actions(events, CHANNELS))
        exp = [LantopCronAction(1, NOW + timedelta(minutes=30),
                                timedelta(minutes=30), u"summary")]
        self.assertEqual(exp, actions)

    def test_parse_desc_offsets_neg_duration(self):
        events = [Event(description=u"ch1+60-90")]
        actions = list(extract_actions(events, CHANNELS))
        self.assertEqual([], actions)

if __name__ == "__main__":
    unittest.main()