#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for LANtopPy"""

from __future__ import print_function
import sys
import os
import re
import codecs
from subprocess import Popen, PIPE
from setuptools import setup, Command

HERE = os.path.abspath(os.path.dirname(__file__))

VERSION_PY = "lantop/_version.py"
VERSION_PY_TEMPLATE = u"""# -*- coding: utf-8 -*-
# This file is originally generated from Git information by running 'setup.py
# version'. Distribution tarballs contain a pre-generated copy of this file.

__version__ = "{}"
"""


class Version(Command):
    """setup command to update _version.py"""
    description = "update _version.py from 'git describe'"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            version = Version.from_file()
            version_new = Version.call_git_describe()
            if version is not None:
                print("version: current is '{}'.".format(version))
            if version == version_new:
                print("version: unchanged.")
            else:
                Version.to_file(version_new)
                print("version: new is '{}'.".format(version_new))
        except (EnvironmentError, IndexError):
            print("version failed.", file=sys.stderr)

    @staticmethod
    def call_git_describe():
        """Get version string from git"""
        p = Popen(["git", "describe", "--tags"], stdout=PIPE)
        version = p.communicate()[0].strip()
        if p.returncode != 0:
            raise EnvironmentError()

        # adapt git-describe version to be in line with PEP 386
        parts = version.split("-")
        if parts[0][0] == "v":
            parts[0] = parts[0][1:]
        parts[-2] = "post"+parts[-2]
        return ".".join(parts[:-1])

    @staticmethod
    def to_file(version):
        """Write version to _version.py"""
        with open(os.path.join(HERE, VERSION_PY), "w") as fp:
            fp.write(VERSION_PY_TEMPLATE.format(version).encode("UTF-8"))

    @staticmethod
    def from_file():
        """Read version from _version.py"""
        try:
            for line in open(os.path.join(HERE, VERSION_PY), "r"):
                mo = re.match("__version__ = \"([^']+)\"", line)
                if mo:
                    return mo.group(1)
        except EnvironmentError:
            print("version: could not read from file.")
        return None


def read(*parts):
    """Utility function to read the README file"""
    return codecs.open(os.path.join(HERE, *parts), "r").read()


setup(
    name = "LANtopPy",
    version = Version.from_file() or "0.0",
    license = "GPL",
    author =  "Sebastian Koslowski",
    author_email = "sebastian.koslowski@gmail.com",

    description = "A client API and CLI to control/manage Theben digital "
                  "time switches with a yearly program "
                  "(TR 64* top2 connected using a EM LAN top2 module)",
    long_description = read("README.md"),

    url = "https://github.com/skoslowski/LANtopPy",
    download_url = "https://github.com/skoslowski/LANtopPy/archive/master.zip",

    packages = ["lantop"],
    install_requires = [line.strip() for line in open("requirements.txt","r")],

    entry_points = {
        "console_scripts": [
            "lantop = lantop.cli:main",
            "gcal_import = lantop.gcalimport.cli:main"
        ]
    },
    data_files = [
        ("/etc/lantop", [
            "config/logging.json",
            "config/gcal_import.json"
        ])
    ],
    package_data = {
        "": [
            "README.md",
            "LICENSE.txt"
        ]
    },
    test_suite = "test",

    # zip_safe = False,
    cmdclass = {
        "version": Version
    }
)