#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for lantop client API"""

import unittest
from datetime import datetime, timedelta

from lantop.lantop import Lantop, Transport, LantopError

from .helpers import LantopEmulator
from .data import TEST_DATA


class LantopTransportTest(unittest.TestCase):

    def setUp(self):
        self.server = LantopEmulator(resp_dict=TEST_DATA)
        self.server.start()
        self.tp = Transport(*self.server.server_address)

    def tearDown(self):
        self.tp.close()
        self.server.stop()

    def test_command_error_code(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.command("xxxxxx0", "xx")
        self.assertEqual("Got unknown error code", str(cm.exception))

    def test_request_channel_wrong(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.request("xxxxxx0", "xx", channel=9)
        self.assertEqual("Invalid channel index given", str(cm.exception))

    def test_command_error_code2(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.command("xxxxxx1", "xx")
        self.assertEqual("Got UNGUELTIGER BEFEHL", str(cm.exception))

    def test_command_decode(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.command("xxxxxx2", "xx")
        self.assertEqual("Message can not be decoded", str(cm.exception))

    def test_command_resp_code(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.command("xxxxxx0", "xy")
        self.assertEqual("Wrong response code", str(cm.exception))


class LantopTest(unittest.TestCase):

    def setUp(self):
        self.server = LantopEmulator(resp_dict=TEST_DATA)
        self.server.start()
        self.lt = Lantop(*self.server.server_address)

    def tearDown(self):
        self.lt.close()
        self.server.stop()

    def test_get_name(self):
        name = self.lt.get_name()
        self.assertEqual(TEST_DATA[b'K024E47'][1], name)

    def test_set_name(self):
        self.lt.set_name('abcdefghijklmnopqrst')  # max length
        self.assertEqual(TEST_DATA[b'K174E53'][1], self.server.last_msg)

    def test_get_pin(self):
        pin = self.lt.get_pin()
        self.assertEqual(TEST_DATA[b'T026250'][1], pin)

    def test_set_pin(self):
        self.lt.set_pin('1234')
        self.assertEqual(TEST_DATA[b'T046150'][1], self.server.last_msg)

    def test_set_pin_wrong1(self):
        with self.assertRaises(LantopError) as cm:
            self.lt.set_pin('12345')
        self.assertEqual('PIN must be exactly 4 numbers', str(cm.exception))

    def test_set_pin_wrong2(self):
        with self.assertRaises(LantopError) as cm:
            self.lt.set_pin('abcd')
        self.assertEqual('Only numeric pin allowed', str(cm.exception))

    def test_set_name_too_long(self):
        with self.assertRaises(LantopError) as cm:
            self.lt.set_name(' ' * 21)
        self.assertEqual('Name too long', str(cm.exception))

    def test_get_info(self):
        dev_type, serial = self.lt.get_info()
        self.assertEqual(TEST_DATA[b'T02624C'][1][0], dev_type)
        self.assertEqual(TEST_DATA[b'T02624C'][1][1], serial)

    def test_get_swv_ersion(self):
        res = self.lt.get_sw_version()
        self.assertEqual(TEST_DATA[b'K0156'][1], res)

    def test_get_time(self):
        time = self.lt.get_time()
        self.assertEqual(TEST_DATA[b'T02625A'][1], time)

    def test_set_time(self):
        self.lt.set_time(datetime(2011, 12, 13, 14, 15, 16))
        self.assertEqual(TEST_DATA[b'T08615A'][1], self.server.last_msg)

    def test_get_states(self):
        states = self.lt.get_states()
        self.assertEqual(TEST_DATA[b'T02624B'][1], states)

    def test_set_state_on(self):
        self.lt.set_state(3, 'on')
        self.assertEqual(TEST_DATA[b'T04614B'][1] + b'0302',
                         self.server.last_msg)

    def test_set_state_off(self):
        self.lt.set_state(2, 'off')
        self.assertEqual(TEST_DATA[b'T04614B'][1] + b'0201',
                         self.server.last_msg)

    def test_set_state_auto(self):
        self.lt.set_state(0, 'auto')
        self.assertEqual(TEST_DATA[b'T04614B'][1] + b'0003',
                         self.server.last_msg)

    def test_set_state_wrong(self):
        with self.assertRaises(LantopError) as cm:
            self.lt.set_state(3, 'foo')
        self.assertEqual('Cannot parse state', str(cm.exception))

    def test_set_state_duration_on(self):
        self.lt.set_state(3, 'on', duration=timedelta(minutes=1, seconds=28))
        self.assertEqual(TEST_DATA[b'T08614B'][1], self.server.last_msg)

    def test_get_channel_name(self):
        name = self.lt.get_channel_name(0)
        self.assertEqual(b'T03624E00', self.server.last_msg)
        self.assertEqual(TEST_DATA[b'T03624E'][1], name)

    def test_get_channel_stats(self):
        name = self.lt.get_channel_stats(2)
        self.assertEqual(b'T03624202', self.server.last_msg)
        self.assertEqual(TEST_DATA[b'T036242'][1], name)

    def test_reset_channel_stats(self):
        self.lt.reset_channel_stats(3)
        self.assertEqual(TEST_DATA[b'T046142'][1] + b'0300',
                         self.server.last_msg)


if __name__ == '__main__':
    unittest.main()
