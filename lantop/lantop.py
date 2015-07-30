# -*- coding: utf-8 -*-
"""lantop client API"""

import struct
import base64
from datetime import datetime, date

from . _config import (
    DEVICE_TYPES, CONTROL_MODES, TIMED_STATE_LABELS,
    STATE_REASONS
)
from .transport import Transport
from .errors import LantopError


class Lantop(object):
    """Client API for Theben LANtop2 module"""

    Transport = Transport

    def __init__(self, *args, **kwargs):
        self._dev_type = None  # will be set by get_info
        self.tp = None
        if args or kwargs:
            self.connect(*args, **kwargs)

    def connect(self, *args, **kwargs):
        self.tp = self.Transport(*args, **kwargs)

    def close(self):
        if self.tp:
            self.tp.close()

    def get_info(self):
        """Get device Info (type, serial number)

        :returns: device type name and serial number

        """
        msg = self.tp.request("T02624C", "bl")

        (serial, dev_type) = struct.unpack(">IB", msg[:5])
        try:
            dev_type_name = DEVICE_TYPES[dev_type][0]
            self._dev_type = dev_type
        except KeyError:
            dev_type_name = "Unknown device type"

        return dev_type_name, serial

    def get_name(self):
        """Get device name"""
        msg = self.tp.request("K024E47", "kN")
        return msg[:-1].decode().strip()

    def set_name(self, name):
        """Set name of device

        :param name: new device name (max. 20 characters)

        """
        name = name.encode()
        if len(name) > 20:
            raise LantopError("Name too long")
        args = base64.b16encode(name.ljust(21, b'\0'))
        self.tp.request("K174E53", "kN", args=args)

    def get_pin(self):
        """Get device PIN

        :returns: the current PIN and whether it is required

        """
        msg = self.tp.request("T026250", "bp")
        pin = base64.b16encode(msg[:2]).decode()
        active = (msg[2] == 1)
        return pin, active

    def set_pin(self, pin="0000"):
        """Set device PIN (0000 disables PIN)

        :param pin: new PIN (length 4, numeric)

        """
        try:
            int(pin)
        except ValueError:
            raise LantopError("Only numeric pin allowed")
        if not len(pin) == 4:
            raise LantopError("PIN must be exactly 4 numbers")
        self.tp.command("T046150", "ap", args=pin.encode())

    def get_extra_info(self):
        """Get metadata from device

        :returns: swVersion, battery time, power-on time and power-on date

        """
        def extra_request(req_code, resp_code, param):
            """Special request function with support sub command codes"""
            msg = self.tp.request(req_code, resp_code, args=param)
            code, msg = base64.b16encode(msg[:1]), msg[1:]
            if not param == code:
                raise LantopError("Wrong return code")
            return msg
        # Get Software version
        msg = extra_request("T036249", "bi", b"00")
        full, frac = int(msg[:2]), int(msg[2:4])
        sw_version = full + frac / 100.0

        # Get battery time
        msg = extra_request("T036249", "bi", b"01")
        (bat_time,) = struct.unpack("<I", msg[:4])
        bat_time /= 10.0

        # Get power on time
        msg = extra_request("T036249", "bi", b"02")
        (pwr_on_time,) = struct.unpack("<I", msg[:4])
        pwr_on_time /= 10.0

        # Get power on time
        msg = extra_request("T036249", "bi", b"03")
        day, month = struct.unpack("BB", msg[:2])
        (year,) = struct.unpack(">H", msg[2:4])
        pwr_on_date = date(year, month, day)

        return sw_version, bat_time, pwr_on_time, pwr_on_date

    def get_sw_version(self):
        """Get software version from device

        :returns: version number and date

        """
        msg = self.tp.request("K0156", "kV").decode()
        try:
            version = float(msg[:4])
            vdate = datetime.strptime(msg[5:13], "%Y%m%d").date()
        except:
            raise LantopError("Cannot parse respone")

        return version, vdate

    def get_time(self):
        """Get current time on device"""
        msg = self.tp.request("T02625A", "bz")
        try:
            time_struct = list(struct.unpack("BBBBBBB", msg))
            # Swap day and year
            time_struct[0], time_struct[2] = \
                2000 + time_struct[2], time_struct[0]
            dev_time = datetime(*time_struct)
        except:
            raise LantopError("Cannot parse respone")

        return dev_time

    def set_time(self, new_time=None):
        """Set time on device

        :param new_time: the new time (default: None, means now)

        """
        if not new_time:
            new_time = datetime.now()
        args = (new_time.year - 2000, new_time.month, new_time.day,
                new_time.hour, new_time.minute, new_time.second)
        args = b''.join((base64.b16encode(bytes([c])) for c in args))
        self.tp.command("T08615A", "a\x7A", args=args)

    def get_states(self):
        """Get current channel states and reasons

        :returns: a list of dicts. Each channel has a active and reason entry

        """
        # dev_type tells the number of channels on device
        if self._dev_type is None:
            self.get_info()
        num_channels = DEVICE_TYPES[self._dev_type][1]
        # now, get the state
        msg = self.tp.request("T02624B", "bk")
        try:
            channels = struct.unpack_from("B" * 8, msg)
            has_extension_module = ord(msg[8:9]) == 1

            states = [{"active": bool(ch & 0x80),
                       "reason": STATE_REASONS[ch & 0x7F],
                       "index": i}
                      for i, ch in enumerate(channels)
                      if i < num_channels or has_extension_module and i >= 4]
        except:
            raise LantopError("Cannot parse channel state response")

        return states

    def set_state(self, channel, state, duration=None):
        """Set state of a channel

        :param channel: zero-based channel index
        :param state: new state (on, off, auto, manual)
        :param duration: how long to keep the new setting (None for indefinite)
        :type duration: datetime.timedelta

        """
        if duration is None:  # set state indefinitely
            try:
                state_code = CONTROL_MODES[state]
            except:
                raise LantopError("Cannot parse state")
            args = base64.b16encode(bytes([state_code]))
            self.tp.command("T04614B", "ak", channel, args)

        else:  # keep new state only for a certain time
            try:
                state_code = TIMED_STATE_LABELS[state]
            except:
                raise LantopError("Cannot parse state")

            hours = 24 * duration.days + duration.seconds // 3600
            minutes = (duration.seconds // 60) % 60
            seconds = duration.seconds % 60

            args = (4, hours, minutes, seconds, state_code)
            args = b''.join((base64.b16encode(bytes([c])) for c in args))
            self.tp.command("T08614B", "ak", channel, args)

    def get_channel_name(self, channel):
        """Get name of a certain channel

        :param channel: zero-based channel index

        """
        msg = self.tp.request("T03624E", "bn", channel=channel)
        name = msg[1:14].decode('UTF-8').strip().title()
        return name

    def get_channel_stats(self, channel):
        """Get usage statistics of a channel

        :param channel: zero-based channel index

        """
        msg = self.tp.request("T036242", "bb", channel=channel)
        (active, service, switches, day, month) = \
            struct.unpack("<IIIBB", msg[1:15])
        (year,) = struct.unpack(">H", msg[15:17])
        last_reset = date(year, month, day)

        return active / 10.0, service / 10.0, switches, last_reset

    def reset_channel_stats(self, channel):
        """Reset usage statistics of a certain channel

        :param channel: zero-based channel index

        """
        self.tp.command("T046142", "ab", channel=channel, args=b'00')
