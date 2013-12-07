#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for LANtopPy"""

import os
import subprocess
import re
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.core import Command
from distutils.command.sdist import sdist as _sdist


VERSION_PY_TEMPLATE = u"""# -*- coding: utf-8 -*-
# This file is originally generated from Git information by running 'setup.py
# version'. Distribution tarballs contain a pre-generated copy of this file.

__version__ = '{}'
"""


def update_version_py():
    """Get version string from git and save it to _version.py"""
    if not os.path.isdir(".git"):
        print "This does not appear to be a Git repository."
        return
    try:
        cmd = ["git", "describe", "--tags", "--dirty", "--always"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        if p.returncode != 0:
            print "Unable to run git, leaving _version.py alone"
            return
    except EnvironmentError:
        print "Unable to run git, leaving _version.py alone"
        return

    # get extract version from tag and save it to file
    version = stdout.strip()
    if version[0] != "v":
        return
    with open("lantop/_version.py", "w") as fp:
        fp.write(VERSION_PY_TEMPLATE.format(version[1:]).encode("UTF-8"))
    return version[1:]


def get_version():
    """Read version from _version.py"""
    try:
        for line in open("lantop/_version.py"):
            mo = re.match("__version__ = '([^']+)'", line)
            if mo:
                version = mo.group(1)
                return version
        else:
            return
    except EnvironmentError:
        return


class Version(Command):
    """setup command to update _version.py"""
    description = "update _version.py from Git repo info"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        version = update_version_py()
        print "Version is now", version


class sdist(_sdist):
    def run(self):
        version = update_version_py()
        self.distribution.metadata.version = version
        return super(self, sdist).run()


setup(
    name = 'LANtopPy',
    version = get_version() or update_version_py() or "Unknown",
    license = 'GPL',

    author = 'Sebastian Koslowski',
    author_email = 'sebastian.koslowski@gmail.com',

    description = "A client API and CLI to control/manage Theben digital "
                  "time switches with a yearly program "
                  "(TR 64* top2 connected using a EM LAN top2 module)",
    long_description = open('README.md').read(),

    url = "https://github.com/skoslowski/LANtopPy",
    download_url = "https://github.com/skoslowski/LANtopPy/archive/master.zip",

    packages = ["lantop"],

    install_requires = [line.strip() for line in open("requirements.txt",'r')],

    entry_points = {
        "console_scripts": [
            "lantop=lantop.cli:main",
            "lantop_state=lantop.setstatesafe:main",
            "gcal_import=lantop.gcalimport.cli:main"
        ]
    },

    data_files = [
        ("~/.config/lantop", ["config/logging.json",
                              "config/gcal_import.json"])
    ],
    package_data = {
        "": ["README.md", "LICENSE.txt"]
    },

    test_suite = "test",

    # zip_safe = False,
    cmdclass = {"version": Version, "sdist": sdist}
)