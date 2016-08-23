#!/usr/bin/env python3
"""Tests for lantop CLI"""

import argparse
from datetime import timedelta
import os
import types
import unittest

import lantop.cli

from .helpers import LantopEmulator, nostdout
from .data import TEST_DATA


class CLITest(unittest.TestCase):
    """Tests for lantop cli"""

    @classmethod
    def setUpClass(cls):
        os.environ['LANTOPPY_CONFIG'] = ''

    def test_parse_set_states(self):
        config = types.SimpleNamespace(device=types.SimpleNamespace(address=None, retries=0))
        options = lantop.cli.parse_args(["dummy_host", "-s", "0:on"], config)
        self.assertEqual([(0, "on")], options.set_states)

    def test_parse_set_states_wrong(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.set_state_type("0:foo")

        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.set_state_type("8:on")

        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.set_state_type("aaaa")

    def test_parse_timer(self):
        duration = lantop.cli.duration_type("12:34:56")
        self.assertEqual(timedelta(hours=12, minutes=34, seconds=56), duration)

        duration = lantop.cli.duration_type("12:34")
        self.assertEqual(timedelta(hours=12, minutes=34), duration)

        duration = lantop.cli.duration_type("48")
        self.assertEqual(timedelta(hours=48), duration)

    def test_parse_timer_wrong(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            lantop.cli.duration_type("12,74:56")

    def test_main(self):
        server = LantopEmulator(resp_dict=TEST_DATA)
        server.start()
        dev_addr = "{}:{}".format(*server.server_address)

        with nostdout():
            lantop.cli.main([dev_addr, "--extra"])

        server.stop()

if __name__ == "__main__":
    unittest.main()
