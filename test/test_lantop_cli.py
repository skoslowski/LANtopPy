#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for lantop CLI"""

import unittest
from datetime import timedelta
import argparse
from helpers import LantopEmulator, nostdout

import lantop.cli

from _data import TEST_DATA


class CLITest(unittest.TestCase):
    """Tests for lantop cli"""

    def test_parse_dev_addr(self):
        options = lantop.cli.parse_args(['dummy_host'])
        self.assertEqual(['dummy_host'], options.dev_addr)

        options = lantop.cli.parse_args(['dummy_host:123'])
        self.assertEqual(['dummy_host', 123], options.dev_addr)

    def test_parse_dev_addr_wrong(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.dev_addr_type('dummy_host:asf')

    def test_parse_set_states(self):
        options = lantop.cli.parse_args(['dummy_host', '-s', '0:on'])
        self.assertEqual([(0, 'on')], options.set_states)

    def test_parse_set_states_wrong(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.set_state_type('0:foo')

        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.set_state_type('8:on')

        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.set_state_type('aaaa')

    def test_parse_timer(self):
        duration = lantop.cli.duration_type('12:34:56')
        self.assertEqual(timedelta(hours=12, minutes=34, seconds=56), duration)

        duration = lantop.cli.duration_type('12:34')
        self.assertEqual(timedelta(hours=12, minutes=34), duration)

        duration = lantop.cli.duration_type('48')
        self.assertEqual(timedelta(hours=48), duration)

    def test_parse_timer_wrong(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.duration_type('12,74:56')

    def test_main(self):
        server = LantopEmulator(resp_dict=TEST_DATA)
        server.start()
        dev_addr = "{}:{}".format(*server.server_address)

        with nostdout():
            lantop.cli.main([dev_addr, '--extra'])

        server.stop()

if __name__ == "__main__":
    unittest.main()
