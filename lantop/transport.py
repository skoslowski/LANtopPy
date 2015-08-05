# -*- coding: utf-8 -*-
"""lantop client API"""

import socket
import logging
import base64

from ._config import ERROR_NAMES, DEFAULT_PORT
from .errors import LantopTransportError


class Transport(object):
    """Connection to LANtop2 and basic protocol"""

    def __init__(self, host=None, port=DEFAULT_PORT):
        """Connect to LANtop2 module

        :param host: host name or ip
        :param port: port

        """
        self.logger = logging.getLogger("lantop.transport")
        self._socket = None

        try:
            # name resolution
            addr_info = socket.getaddrinfo(host, port,
                                           socket.AF_INET, 0, socket.SOL_TCP)
            if len(addr_info) == 0:
                raise LantopTransportError("Could not find LANtop2")

            family, socktype, proto, canonname, sockaddr = addr_info[0]

            self._socket = socket.socket(family, socktype, proto)
            self._socket.settimeout(4.0)  # same as Theben software
            self._socket.connect(sockaddr)
            self.logger.debug("Connected to %s:%d", host, port)
        except:
            raise LantopTransportError("Could not connect to LANtop2")

    def close(self):
        """Disconnect from LANtop2"""
        if self._socket:
            self._socket.close()
            self._socket = None

    def _send(self, req_code, channel=None, args=b''):
        """Generic send method to send a command to LANtop

        :param req_code: request/command header code
        :param channel: zero-based channel index (or None)
        :param args: custom request payload

        """
        # Command structure: req_code [channel] args
        command = bytearray(req_code, encoding='UTF-8')
        if channel is not None:
            command += hex(channel)[2:].upper().rjust(2, "0").encode('UTF-8')
        command += args
        self.logger.debug("Sending command %s", command)
        self._socket.sendall(command)

    def _receive(self):
        """Receive msg from LANtop (length followed by data)

        :throws LantopException: If a message cannot be received
        :returns: the received message

        """
        try:
            length = self._socket.recv(1)[0] - 32
            buffer = memoryview(bytearray(length))
            received = 0
            while received < length:
                received += self._socket.recv_into(buffer[received:])
            self.logger.debug("Got response %s", buffer)
            return buffer.obj
        except Exception:
            raise LantopTransportError("Could not read from LANtop2")

    def request(self, req_code, resp_code, channel=None, args=b''):
        """Combined send and receive (decode) method

        :param req_code: request/command header code
        :param resp_code: excepted response header code
        :param channel: zero-based channel index (or None)
        :param args: custom request payload

        :returns: response payload

        """
        if channel is not None and not 0 <= channel < 8:
            raise LantopTransportError("Invalid channel index given")

        # issue command
        self._send(req_code, channel, args)
        # get and check response
        data = self._receive()
        if len(data) < len(resp_code):
            raise LantopTransportError("Invalid message")
        try:
            data = base64.b16decode(data)
        except:
            raise LantopTransportError("Message can not be decoded")
        if not resp_code.encode('UTF-8') == data[:len(resp_code)]:
            raise LantopTransportError("Wrong response code")
        payload = data[len(resp_code):]
        return payload

    def command(self, req_code, resp_code, channel=None, args=b''):
        """Issue command and check resulting error code

        :param req_code: request/command header code
        :param resp_code: excepted response header code
        :param channel: zero-based channel index (or None)
        :param args: custom request payload

        """
        msg = self.request(req_code, resp_code, channel, args)
        code = msg[0]
        if code != 0:
            try:
                raise LantopTransportError("Got " + ERROR_NAMES[code])
            except IndexError:
                raise LantopTransportError("Got unknown error code")

    def __del__(self):
        self.close()
