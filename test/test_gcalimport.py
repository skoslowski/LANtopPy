#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from lantop.gcalimport.event_importer import extract_actions, parse_event_desc

CHANNELS = {'ch' + str(i): i for i in range(4)}


class EventParserTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_events(self):
        for name, i in CHANNELS.iteritems():
            desc = u'Random foo' + name + u' bar'
            result = ({0: [i]},  # trigger_start: offset 0
                      {0: [i]})  # trigger_end: offset 0
            self.assertEqual(result, parse_event_desc(desc, CHANNELS))

    def test_parse_events_lueftung_wrong(self):
        desc = r"asfsaf Lüftung alskdfj"
        result = 2 * ({},)
        self.assertEqual(result, parse_event_desc(desc, CHANNELS))

    def test_parse_events_offset(self):
        desc = "asfsaf MUTTERKIND+10 alskdfj"
        i = CHANNELS[u'mutterkind']
        result = ({10: [i]}, {0: [i]})
        self.assertEqual(result, parse_event_desc(desc, CHANNELS))

    def test_parse_events_offset2(self):
        desc = "asfsaf MUTTERKIND-10+100 alskdfj"
        i = CHANNELS[u'mutterkind']
        result = ({-10: [i]}, {100: [i]})
        self.assertEqual(result, parse_event_desc(desc, CHANNELS))

    def test_parse_events_combine(self):
        desc = u"asfsaf LÜFTUNG-10+100 alskdfj heizung-10-2"
        il = CHANNELS[u'lüftung']
        ih = CHANNELS[u'heizung']
        result = ({-10: [il, ih]}, {100: [il], -2: [ih]})
        self.assertEqual(result, parse_event_desc(desc))

    def test_parse_event_summary(self):
        for name, i in CHANNELS.iteritems():
            event = {'summary': u'Random foo' + name + u' bar'}
            result = ({0: [i]}, {0: [i]})
            self.assertEqual(result, parse_event(event))

    def test_parse_event_summary(self):
        for name, i in CHANNELS.iteritems():
            event = {'summary': u'Random foo' + name.upper() + u' bar'}
            result = ({0: [i]}, {0: [i]})
            self.assertEqual(result, parse_event(event))

    def test_parse_events_all_in_one(self):
        event = {'summary': 'Tolles Event',
                 'description': u"asfsaf LÜFTUNG-10+100heizung-10-2"
                                u"mutterkind+9spare-2-2"}
        il = CHANNELS[u'lüftung']
        im = CHANNELS[u'mutterkind']
        ih = CHANNELS[u'heizung']
        ip = CHANNELS[u'spare']
        result = ({9: [im], -2: [ip], -10: [il, ih]},
                  {0: [im], 100: [il], -2: [ih, ip]})
        self.assertEqual(result, parse_event(event))


if __name__ == "__main__":
    unittest.main()