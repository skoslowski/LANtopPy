# -*- coding: utf-8 -*-
"""lantop client API"""

import socket
import struct
from datetime import datetime, date
import logging

from . _config import DEVICE_TYPES, CONTROL_MODES, TIMED_STATE_LABELS, \
    ERROR_NAMES, STATE_REASONS


class LantopException(Exception):
    """Exception thrown by Lantop objects"""
    pass


class LantopBase(object):
    """Connection to LANtop2 and basic protocol"""

    def __init__(self, host, port=10001):
        """Connect to LANtop2 module

        :param host: host name or ip
        :param port: port

        """
        self.logger = logging.getLogger("lantop.client")

        try:
            # name resolution
            addr_info = socket.getaddrinfo(host, port,
                                           socket.AF_INET, 0, socket.SOL_TCP)
            if len(addr_info) == 0:
                raise LantopException("Could not find LANtop2")

            family, socktype, proto, canonname, sockaddr = addr_info[0]

            self._socket = socket.socket(family, socktype, proto)
            self._socket.settimeout(4.0)  # same as Theben software
            self._socket.connect(sockaddr)
            self.logger.debug("Connected to %s:%d", host, port)
        except:
            raise LantopException("Could not connect to LANtop2")

        self._dev_type = None  # will be set by get_info

    def __del__(self):
        """Disconnect from LANtop2"""
        if hasattr(self, "_socket") and self._socket:
            self._socket.close()

    def _send(self, req_code, channel=None, args=""):
        """Generic send method to send a command to LANtop

        :param req_code: request/command header code
        :param channel: zero-based channel index (or None)
        :param args: custom request payload

        """
        # Command structure: req_code [channel] args
        command = req_code
        if channel is not None:
            command += hex(channel)[2:].upper().rjust(2, "0")
        command += args
        self.logger.debug("Sending command %s", command)
        self._socket.sendall(command)

    def _receive(self):
        """Receive msg from LANtop (length followed by data)

        :throws LantopException: If a message cannot be received
        :returns: the received message

        """
        try:
            data = self._socket.recv(1024)
            # get msg length
            msg_len = ord(data[0]) - 32
            rest = msg_len - (len(data) - 1)
            # get first part of message
            message = data[1:] if rest >= 0 else ""
            # get rest of message
            more = 4  # max number of message parts (should be enough)
            while more > 0 and rest > 0:
                message += self._socket.recv(1024)
                rest -= len(message)
                more -= 1
            if not more:
                raise LantopException("Could receive message")
            message = message[:msg_len]

            self.logger.debug("Got response %s", message)
            return message

        except:
            raise LantopException("Could not read from LANtop2")

    def _request(self, req_code, resp_code, channel=None, args=""):
        """Combined send and receive (decode) method

        :param req_code: request/command header code
        :param resp_code: excepted response header code
        :param channel: zero-based channel index (or None)
        :param args: custom request payload

        :returns: response payload

        """
        if not channel is None and not 0 <= channel < 8:
            raise LantopException("Invalid channel index given")

        # issue command
        self._send(req_code, channel, args)
        # get and check response
        data = self._receive()
        if len(data) < len(resp_code):
            raise LantopException("Invalid message")
        try:
            data = data.decode("hex")
        except TypeError:
            raise LantopException("Message can not be decoded")
        if not resp_code == data[:len(resp_code)]:
            raise LantopException("Wrong response code")
        payload = data[len(resp_code):]
        return payload

    def _command(self, req_code, resp_code, channel=None, args=""):
        """Issue command and check resulting error code

        :param req_code: request/command header code
        :param resp_code: excepted response header code
        :param channel: zero-based channel index (or None)
        :param args: custom request payload

        """
        msg = self._request(req_code, resp_code, channel, args)
        code = ord(msg[0])
        if code != 0:
            try:
                raise LantopException("Device returned " + ERROR_NAMES[code])
            except IndexError:
                raise LantopException("Device returned an unknown error code")


class Lantop(LantopBase):
    """Client API for Theben LANtop2 module"""

    def get_info(self):
        """Get device Info (type, serial number)

        :returns: device type name and serial number

        """
        msg = self._request("T02624C", "bl")

        (serial, dev_type) = struct.unpack(">IB", msg[:5])
        try:
            dev_type_name = DEVICE_TYPES[dev_type][0]
            self._dev_type = dev_type
        except KeyError:
            dev_type_name = "Unknown device type"

        return dev_type_name, serial

    def get_name(self):
        """Get device name"""
        msg = self._request("K024E47", "kN")
        return msg[:-1].strip()

    def set_name(self, name):
        """Set name of device

        :param name: new device name (max. 20 characters)

        """
        if len(name) > 20:
            raise LantopException("Name too long")
        name = name.encode("hex").upper() + "00" * (21 - len(name))
        self._request("K174E53", "kN", args=name)  # not _command!

    def get_pin(self):
        """Get device PIN

        :returns: the current PIN and whether it is required

        """
        msg = self._request("T026250", "bp")
        pin = msg[:2].encode("hex")
        active = (msg[2] == "\x01")
        return pin, active

    def set_pin(self, pin="0000"):
        """Set device PIN (0000 disables PIN)

        :param pin: new PIN (length 4, numeric)

        """
        try:
            int(pin)
        except ValueError:
            raise LantopException("Only numeric pin allowed")
        if not len(pin) == 4:
            raise LantopException("PIN must be exactly 4 numbers")
        self._command("T046150", "ap", args=pin)

    def get_extra_info(self):
        """Get metadata from device

        :returns: swVersion, battery time, power-on time and power-on date

        """
        def extra_request(req_code, resp_code, param):
            """Special request function with support sub command codes"""
            msg = self._request(req_code, resp_code, args=param)
            code, msg = msg[:1].encode("hex"), msg[1:]
            if not param == code:
                raise LantopException("Wrong return code")
            return msg
        # Get Software version
        msg = extra_request("T036249", "bi", "00")
        full, frac = int(msg[:2]), int(msg[2:4])
        sw_version = full + frac / 100.0

        # Get battery time
        msg = extra_request("T036249", "bi", "01")
        (bat_time,) = struct.unpack("<I", msg[:4])
        bat_time /= 10.0

        # Get power on time
        msg = extra_request("T036249", "bi", "02")
        (pwr_on_time,) = struct.unpack("<I", msg[:4])
        pwr_on_time /= 10.0

        # Get power on time
        msg = extra_request("T036249", "bi", "03")
        day, month = struct.unpack("BB", msg[:2])
        (year,) = struct.unpack(">H", msg[2:4])
        pwr_on_date = date(year, month, day)

        return sw_version, bat_time, pwr_on_time, pwr_on_date

    def get_sw_version(self):
        """Get software version from device

        :returns: version number and date

        """
        msg = self._request("K0156", "kV")
        try:
            version = float(msg[:4])
            vdate = datetime.strptime(msg[5:13], "%Y%m%d").date()
        except:
            raise LantopException("Cannot parse respone")

        return version, vdate

    def get_time(self):
        """Get current time on device"""
        msg = self._request("T02625A", "bz")
        try:
            time_struct = list(struct.unpack("BBBBBBB", msg))
            # Swap day and year
            time_struct[0], time_struct[2] = \
                2000 + time_struct[2], time_struct[0]
            dev_time = datetime(*time_struct)
        except:
            raise LantopException("Cannot parse respone")

        return dev_time

    def set_time(self, new_time=None):
        """Set time on device

        :param new_time: the new time (default: None, means now)

        """
        if not new_time:
            new_time = datetime.now()
        args = (new_time.year - 2000, new_time.month, new_time.day,
                new_time.hour, new_time.minute, new_time.second)
        args = "".join((hex(c)[2:].upper().rjust(2, "0") for c in args))
        self._command("T08615A", "a\x7A", args=args)

    def get_states(self):
        """Get current channel states and reasons

        :returns: a list of dicts. Each channel has a active and reason entry

        """
        # dev_type tells the number of channels on device
        if self._dev_type is None:
            self.get_info()
        num_channels = DEVICE_TYPES[self._dev_type][1]
        # now, get the state
        msg = self._request("T02624B", "bk")
        try:
            channels = struct.unpack_from("B" * 8, msg)
            has_extension_module = ord(msg[8:9]) == 1

            states = [{"active": bool(ch & 0x80),
                       "reason": STATE_REASONS[ch & 0x7F],
                       "index": i}
                      for i, ch in enumerate(channels)
                      if i < num_channels or has_extension_module and i >= 4]
        except:
            raise LantopException("Cannot parse channel state response")

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
                raise LantopException("Cannot parse state")
            args = hex(state_code)[2:].upper().rjust(2, "0")
            self._command("T04614B", "ak", channel, args)

        else:  # keep new state only for a certain time
            try:
                state_code = TIMED_STATE_LABELS[state]
            except:
                raise LantopException("Cannot parse state")

            hours = 24 * duration.days + duration.seconds // 3600
            minutes = (duration.seconds // 60) % 60
            seconds = duration.seconds % 60

            args = (4, hours, minutes, seconds, state_code)
            args = "".join((hex(c)[2:].upper().rjust(2, "0") for c in args))
            self._command("T08614B", "ak", channel, args)

    def get_channel_name(self, channel):
        """Get name of a certain channel

        :param channel: zero-based channel index

        """
        msg = self._request("T03624E", "bn", channel=channel)
        name = msg[1:14].strip().title()
        return name

    def get_channel_stats(self, channel):
        """Get usage statistics of a channel

        :param channel: zero-based channel index

        """
        msg = self._request("T036242", "bb", channel=channel)
        (active, service, switches, day, month) = \
            struct.unpack("<IIIBB", msg[1:15])
        (year,) = struct.unpack(">H", msg[15:17])
        last_reset = date(year, month, day)

        return active / 10.0, service / 10.0, switches, last_reset

    def reset_channel_stats(self, channel):
        """Reset usage statistics of a certain channel

        :param channel: zero-based channel index

        """
        self._command("T046142", "ab", channel=channel, args="00")
