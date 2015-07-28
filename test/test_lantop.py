#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for lantop client API"""

import unittest
from datetime import datetime, timedelta
from helpers import LantopEmulator

from lantop.lantop import Lantop, LantopSocketTransport, LantopError

from _data import TEST_DATA


class LantopTransportTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server = LantopEmulator(resp_dict=TEST_DATA)
        self.server.start()
        self.tp = LantopSocketTransport(*self.server.server_address)

    def tearDown(self):
        self.tp.close()
        self.server.stop()
        del self.server

    def test_command_error_code(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.command("xxxxxx0", "xx")
        self.assertEqual("Got unknown error code", cm.exception.message)

    def test_request_channel_wrong(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.request("xxxxxx0", "xx", channel=9)
        self.assertEqual("Invalid channel index given", cm.exception.message)

    def test_command_error_code2(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.command("xxxxxx1", "xx")
        self.assertEqual("Got UNGUELTIGER BEFEHL", cm.exception.message)

    def test_command_decode(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.command("xxxxxx2", "xx")
        self.assertEqual("Message can not be decoded", cm.exception.message)

    def test_command_resp_code(self):
        with self.assertRaises(LantopError) as cm:
            self.tp.command("xxxxxx0", "xy")
        self.assertEqual("Wrong response code", cm.exception.message)


class LantopTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server = LantopEmulator(resp_dict=TEST_DATA)
        self.server.start()
        self.lt = Lantop(*self.server.server_address)

    def tearDown(self):
        del self.lt
        self.server.stop()
        del self.server

    def test_get_name(self):
        name = self.lt.get_name()
        self.assertEqual(TEST_DATA["K024E47"][1], name)

    def test_set_name(self):
        self.lt.set_name("abcdefghijklmnopqrst")  # max length
        self.assertEqual(TEST_DATA["K174E53"][1], self.server.last_msg)

    def test_get_pin(self):
        name = self.lt.get_pin()
        self.assertEqual(TEST_DATA["T026250"][1], name)

    def test_set_pin(self):
        self.lt.set_pin("1234")
        self.assertEqual(TEST_DATA["T046150"][1], self.server.last_msg)

    def test_set_pin_wrong1(self):
        with self.assertRaises(LantopError) as cm:
            self.lt.set_pin("12345")
        self.assertEqual("PIN must be exactly 4 numbers", cm.exception.message)

    def test_set_pin_wrong2(self):
        with self.assertRaises(LantopError) as cm:
            self.lt.set_pin("abcd")
        self.assertEqual("Only numeric pin allowed", cm.exception.message)

    def test_set_name_too_long(self):
        with self.assertRaises(LantopError) as cm:
            self.lt.set_name(" " * 21)
        self.assertEqual("Name too long", cm.exception.message)

    def test_get_info(self):
        dev_type, serial = self.lt.get_info()
        self.assertEqual(TEST_DATA["T02624C"][1][0], dev_type)
        self.assertEqual(TEST_DATA["T02624C"][1][1], serial)

    def test_get_swv_ersion(self):
        res = self.lt.get_sw_version()
        self.assertEqual(TEST_DATA["K0156"][1], res)

    def test_get_time(self):
        time = self.lt.get_time()
        self.assertEqual(TEST_DATA["T02625A"][1], time)

    def test_set_time(self):
        self.lt.set_time(datetime(2011, 12, 13, 14, 15, 16))
        self.assertEqual(TEST_DATA["T08615A"][1], self.server.last_msg)

    def test_get_states(self):
        states = self.lt.get_states()
        self.assertEqual(TEST_DATA["T02624B"][1], states)

    def test_set_state_on(self):
        self.lt.set_state(3, "on")
        self.assertEqual(TEST_DATA["T04614B"][1] + "0302",
                         self.server.last_msg)

    def test_set_state_off(self):
        self.lt.set_state(2, "off")
        self.assertEqual(TEST_DATA["T04614B"][1] + "0201",
                         self.server.last_msg)

    def test_set_state_auto(self):
        self.lt.set_state(0, "auto")
        self.assertEqual(TEST_DATA["T04614B"][1] + "0003",
                         self.server.last_msg)

    def test_set_state_wrong(self):
        with self.assertRaises(LantopError) as cm:
            self.lt.set_state(3, "foo")
        self.assertEqual("Cannot parse state", cm.exception.message)

    def test_set_state_duration_on(self):
        self.lt.set_state(3, "on", duration=timedelta(minutes=1, seconds=28))
        self.assertEqual(TEST_DATA["T08614B"][1], self.server.last_msg)

    def test_get_channel_name(self):
        name = self.lt.get_channel_name(0)
        self.assertEqual("T03624E00", self.server.last_msg)
        self.assertEqual(TEST_DATA["T03624E"][1], name)

    def test_get_channel_stats(self):
        name = self.lt.get_channel_stats(2)
        self.assertEqual("T03624202", self.server.last_msg)
        self.assertEqual(TEST_DATA["T036242"][1], name)

    def test_reset_channel_stats(self):
        self.lt.reset_channel_stats(3)
        self.assertEqual(TEST_DATA["T046142"][1] + "0300",
                         self.server.last_msg)


if __name__ == "__main__":
    unittest.main()
