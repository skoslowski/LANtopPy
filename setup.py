#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for LANtopPy"""

import codecs
import os
import subprocess
import re
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from distutils.core import Command
from distutils.command.sdist import sdist


HERE = os.path.abspath(os.path.dirname(__file__))

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
        version = Version.update_version_py()
        print("Version is now {}".format(version))

    @staticmethod
    def update_version_py():
        """Get version string from git and save it to _version.py"""
        if not os.path.isdir(".git"):
            print("Version: This does not appear to be a Git repository.")
            return "0.0"
        try:
            p = subprocess.Popen(["git", "describe", "--tags"],
                                 stdout=subprocess.PIPE)
            version = p.communicate()[0].strip()
            if p.returncode != 0:
                raise EnvironmentError()

            # adapt git-describe version to be in line with PEP 386
            parts = version.split('-')
            if parts[0][0] == 'v':
                parts[0] = parts[0][1:]
            parts[-2] = 'post'+parts[-2]
            version  = '.'.join(parts[:-1])

            with open("lantop/_version.py", "w") as fp:
                fp.write(VERSION_PY_TEMPLATE.format(version).encode('UTF-8'))
            return version

        except (EnvironmentError, IndexError):
            print("Version: Unable to run git, leaving _version.py alone")
            return "0.0"

    @staticmethod
    def get_version():
        """Read version from _version.py"""
        try:
            for line in open("lantop/_version.py"):
                mo = re.match("__version__ = \"([^']+)\"", line)
                if mo:
                    version = mo.group(1)
                    return version
        except EnvironmentError:
            pass

        return "0.0"


class SDistWithVersion(sdist):
    """Extension of sdist command with version update"""
    def run(self):
        version = Version.update_version_py()
        self.distribution.metadata.version = version
        return super(self, SDistWithVersion).run()


def read(*parts):
    """Utility function to read the README file"""
    return codecs.open(os.path.join(HERE, *parts), 'r').read()


setup(
    name = "LANtopPy",
    version = Version.get_version(),
    license = "GPL",
    author =  "Sebastian Koslowski",
    author_email = "sebastian.koslowski@gmail.com",

    description = "A client API and CLI to control/manage Theben digital "
                  "time switches with a yearly program "
                  "(TR 64* top2 connected using a EM LAN top2 module)",
    long_description = read('README.md'),

    url = "https://github.com/skoslowski/LANtopPy",
    download_url = "https://github.com/skoslowski/LANtopPy/archive/master.zip",

    packages = ["lantop"],
    install_requires = [line.strip() for line in open("requirements.txt",'r')],

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
        "version": Version,
        "sdist": SDistWithVersion
    }
)