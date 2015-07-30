# -*- coding: utf-8 -*-
"""Contains test helper class(es)"""

import threading
import socket
import struct
import sys
import select
from contextlib import contextmanager


@contextmanager
def nostdout():
    """Suppress output from print function"""
    class DummyFile(object):
        """Dummy class to dump output"""
        def write(self, x):
            pass

        def flush(self):
            pass

    orig_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = orig_stdout


class LantopEmulator(threading.Thread):
    """Emulation of the a LANtop2 device for unit tests"""

    def __init__(self, address=None, resp_dict=None):
        """Set-up socket, start thread for listening to requests"""
        threading.Thread.__init__(self)
        self.running = False

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(address or ("localhost", 0))
        self._socket.listen(1)

        self.server_address = self._socket.getsockname()
        self.resp_dict = resp_dict or {}
        self.last_msg = ""

    def start(self):
        """Start server thread"""
        self.running = True
        threading.Thread.start(self)

    def run(self):
        """Accept connections. Send reply according to DATA dict variable"""
        csocket, caddr = self._socket.accept()
        while self.running:
            data = csocket.recv(1024)
            if not data:
                break

            self.last_msg = data
            try:
                msg = self.resp_dict[data[:7]][0]
                if type(msg) is dict:
                    msg = msg[data[7:]]
                csocket.sendall(
                    struct.pack("B%ds" % (len(msg),), len(msg) + 32, msg))

            except KeyError:
                # Unknown message...
                print(data)

        self._socket.close()
        self.running = False

    def stop(self):
        """Shutdown server thread"""
        self.running = False
        self.join()
