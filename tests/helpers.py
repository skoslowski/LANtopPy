# -*- coding: utf-8 -*-
"""Contains test helper class(es)"""

import threading
import socket
import struct
import sys
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

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(address or ("localhost", 0))
        self.socket.listen(1)

        self.server_address = self.socket.getsockname()
        self.resp_dict = resp_dict or {}
        self.last_msg = ""

    def start(self):
        """Start server thread"""
        self.running = True
        threading.Thread.start(self)

    def run(self):
        """Accept connections. Send reply according to DATA dict variable"""
        client_socket, caddr = self.socket.accept()
        while self.running:
            data = client_socket.recv(1024)
            if not data:
                break

            self.last_msg = data
            header, args = data[:7], data[7:]
            try:
                resp = self.resp_dict[header][0]
                if not isinstance(resp, bytes):
                    resp = resp[args]
                client_socket.sendall(bytes([32 + len(resp)]) + resp)

            except KeyError:
                # Unknown message...
                print('Unhandled message:', data)

        client_socket.close()
        self.socket.close()
        self.running = False

    def stop(self):
        """Shutdown server thread"""
        self.running = False
        self.join()
