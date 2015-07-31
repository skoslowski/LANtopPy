# -*- coding: utf-8 -*-
"""CLI for lantop client API"""

import os
import sys
import json
from datetime import datetime, timedelta

from time import sleep
import random  # uniform

import logging
import logging.config

import argparse

from . import __version__, utils
from . lantop import Lantop, LantopError, CONTROL_MODES, TIMED_STATE_LABELS
from . _config import LANTOP_CONF_PATH, LOCK_COUNTERS_FILE
from . lock_counts import LockCounts


def set_state_type(value):
    """Parse arg of state option (channel:new_state)"""
    try:
        channel, state = value.split(':', 1)
        channel = int(channel)
        state = state.lower()
    except:
        raise argparse.ArgumentTypeError("Unexpected parameter format")

    if not state in CONTROL_MODES:
        raise argparse.ArgumentTypeError("Invalid control mode")

    if not 0 <= channel < 8:
        raise argparse.ArgumentTypeError("Invalid channel index")

    return channel, state


def duration_type(value):
    """ Parse arg of timer option (HH:MM:SS)"""
    try:
        td = ([int(v) for v in value.split(":", 2)] + [0, 0, 0])
        return timedelta(hours=td[0], minutes=td[1], seconds=td[2])
    except:
        raise argparse.ArgumentTypeError("Error parsing timer argument")


def dev_addr_type(value):
    """ Parse device address host[:port]"""
    try:
        dev_addr = value.rsplit(":", 1)
        if len(dev_addr) > 1:
            dev_addr[-1] = int(dev_addr[-1])

        return dev_addr

    except:
        raise argparse.ArgumentTypeError("Error parsing device address")


def parse_args(args):
    """Define and parse command line options"""
    try:
        dev_addr = utils.get_dev_addr()
    except LantopError:
        dev_addr = None

    parser = argparse.ArgumentParser(description="Get and set LANtop2 state, "
                                                 "settings and statistics")

    extra_args = {"nargs": "?", "default": dev_addr} if dev_addr else {}
    parser.add_argument(metavar="host[:port]", dest="dev_addr",
                        type=dev_addr_type,
                        help="Device host name or IP (and port)", **extra_args)

    parser.add_argument("-t", "--time", dest="set_time", action="store_true",
                        help="Set the time on device")
    parser.add_argument("-r", "--reset", dest="reset_ch", action="store",
                        type=int, metavar="CH",
                        help="Reset stats on channel CH")
    parser.add_argument("-p", "--pin", dest="set_pin", action="store",
                        type=str, metavar="PIN",
                        help="Set PIN (length 4 numeric, set 0000 to disable)")
    parser.add_argument("-s", "--state", metavar="CH:ST", dest="set_states",
                        type=set_state_type, nargs="+",
                        help="Set a channel CH (0, 1, ...) to a new state ST" +
                             "(" + ", ".join(list(CONTROL_MODES.keys())) + ")")
    parser.add_argument("-d", "--duration", metavar="HH[:MM[:SS]]",
                        dest="duration", type=duration_type,
                        help="Turn off after or turn on for a defined time")
    parser.add_argument("-e", "--extra", dest="extra_info",
                        action="store_true", help="Show extra info")
    parser.add_argument("-y", "--retries", dest="retries", action="store",
                        type=int, metavar="COUNT", default=0,
                        help="How often to retry connecting (random delay)")
    parser.add_argument("--set-default", dest="set_default_addr",
                        action="store_true", help="Set default IP (and port)")
    parser.add_argument("-q", "--quiet", dest="be_quiet", action="store_true",
                        help="Suppress output")
    parser.add_argument("-v", "--version", dest="show_version",
                        action="store_true", help="Show version string.")

    options = parser.parse_args(args)

    if options.duration and not options.set_states:
        parser.error("Need -s when -d is given.")

    # get/set default ip:port if available
    if options.set_default_addr:
        utils.set_dev_addr(options.dev_addr)

    return options


def change_device_states_or_time(device, options, locks, logger):
    """Change the state of a channel, the time, ... if requested"""
    add_spacer = False

    # set time
    if options.set_time:
        device.set_time()
        if not options.be_quiet:
            add_spacer = True
            print("Action: Updated clock on device.")
        logger.info("Updated clock in device.")

    # reset stats
    if options.reset_ch is not None:
        device.reset_channel_stats(options.reset_ch)
        if not options.be_quiet:
            add_spacer = True
            print("Action: Reset statistics.")
        logger.info("Reset statistics on channel %d", options.reset_ch)

    # set pin
    if options.set_pin is not None:
        device.set_pin(options.set_pin)
        if not options.be_quiet:
            add_spacer = True
            print("Action: Updated PIN on device.")
        logger.info("Set PIN to %s.", options.set_pin)

    # set state
    if options.set_states:
        for channel, state in options.set_states:
            # handle temporary states (finite duration)
            duration = options.duration if state in TIMED_STATE_LABELS \
                else None

            if duration is not None:
                device.set_state(channel. state, duration)
                log_str = "Set channel {} to state {} for {}".format(
                    channel, state, str(duration))
            else:
                # indefinite state changes with locks
                # ...flat is better than nested...ups...
                locks[channel] += 1 if state == "on" else -1

                if locks[channel] == 1 and state == "on":
                    device.set_state(channel, "on")
                    log_str = "Set channel {} to state on.".format(channel)
                elif locks[channel] <= 0 and state == "auto":
                    device.set_state(channel, "auto")
                    log_str = "Set channel {} to state auto.".format(channel)
                elif state == "off":
                    device.set_state(channel, "off")
                    locks[channel] = 0
                    log_str = "Set channel {} to state off.".format(channel)
                else:
                    log_str = "Channel {} unchanged due to locks.".format(channel)

                if locks[channel] < 0:
                    locks[channel] = 0
                    logger.warning("Negative count on channel %d", channel)

                logger.info("Lock counters changed {}".format(locks))

            logger.info(log_str)
            if not options.be_quiet:
                add_spacer = True
                print(log_str)

    if add_spacer:
        print("")


def get_and_print_device_info(device, options):
    """Request general device parameters and print them"""
    dev_name = device.get_name()
    dev_type, serial = device.get_info()
    print("Device: {:s} ({:s})".format(str(dev_name), str(dev_type)))

    dev_time = device.get_time()
    diff = int((dev_time - datetime.now()).total_seconds())
    if abs(diff) < 2:
        diff = 0  # account for network latency
    print("Time:   {:%d.%m.%Y %H:%M:%S} (diff: {:d}s)".format(dev_time, diff))

    if options.extra_info:
        print("Extra:  #{:d}, v{:4.2f} ({:%d.%m.%Y})".format(
            serial, *device.get_sw_version()))
        print("        v{:4.2f}, battery {:.1f}h, "
              "power-on {:.1f}h ({:%d.%m.%Y})".format(*device.get_extra_info()))


def get_and_print_overview(device, options, locks):
    """Request channel specific data and arrange it in a table"""
    states = device.get_states()
    # table header
    header = "CH Name          State Locks Reason      Active Service Switches"
    if options.extra_info:
        header += "    (since)"
    print(header)
    # table entries
    for channel in range(len(states)):
        name = device.get_channel_name(channel)
        state = "On" if states[channel]["active"] else "Off"
        stats = device.get_channel_stats(channel)
        fmt = "{index:1d}  {:13} {:5s} {:5d} {reason:10s} {:6.1f}h {:6.1f}h {:8d}"
        if options.extra_info:
            fmt += " {:%d.%m.%Y}"
        print(fmt.format(name, state, locks[channel], *stats, **states[channel]))


def get_logger(name):
    """Load logging settings from file"""
    logging_config_file = os.path.join(LANTOP_CONF_PATH, "logging.json")
    if os.path.exists(logging_config_file):
        with open(logging_config_file, "r") as fp:
            logging.config.dictConfig(json.load(fp))
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    return logger


def main(args=None):
    """main function for the CLI"""
    logger = get_logger("lantop.cli")
    options = parse_args(args or sys.argv[1:])

    if options.show_version:
        print("Version: {}".format(__version__))
        return 0

    device = None
    try:
        device = Lantop(*options.dev_addr, retries=options.retries)
        locks = LockCounts(LOCK_COUNTERS_FILE, logger)

        if not options.be_quiet:
            get_and_print_device_info(device, options)
            print("")

        # set stuff
        change_device_states_or_time(device, options, locks, logger)

        # print overview
        if not options.be_quiet:
            get_and_print_overview(device, options, locks)

    except LantopError as err:
        logger.error(err)
        if not options.be_quiet:
            print(err, file=sys.stderr)
        return 1

    finally:
        # disconnect
        del device
