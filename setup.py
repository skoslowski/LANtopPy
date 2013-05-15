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


VERSION_PY = u"""# -*- coding: utf-8 -*-
# This file is originally generated from Git information by running 'setup.py
# version'. Distribution tarballs contain a pre-generated copy of this file.

__version__ = '{}'
"""


def update_version_py():
    if not os.path.isdir(".git"):
        print "This does not appear to be a Git repository."
        return
    try:
        cmd = ["git", "describe", "--tags", "--dirty", "--always"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    except EnvironmentError:
        print "Unable to run git, leaving _version.py alone"
        return
    stdout = p.communicate()[0]
    if p.returncode != 0:
        print "Unable to run git, leaving _version.py alone"
        return
    ver = stdout.strip()
    ver = ver[1:] if ver[0] == 'v' else 'Unknown'

    with open("lantop/_version.py", "w") as fp:
        fp.write(VERSION_PY.format(ver).encode('UTF-8'))


def get_version():
    try:
        f = open("lantop/_version.py")
    except EnvironmentError:
        return None
    for line in f.readlines():
        mo = re.match("__version__ = '([^']+)'", line)
        if mo:
            ver = mo.group(1)
            return ver
    return "Unknown"


class Version(Command):
    description = "update _version.py from Git repo"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        update_version_py()
        print "Version is now", get_version()


class sdist(_sdist):
    def run(self):
        update_version_py()
        # unless we update this, the sdist command will keep using the old
        # version
        self.distribution.metadata.version = get_version()
        return _sdist.run(self)


setup(
    name = 'LANtopPy',
    version = get_version(),
    license = 'GPL',

    author = 'Sebastian Koslowski',
    author_email = 'sebastian.koslowski@gmail.com',

    description = "A client API and CLI to control/manage Theben digital "
                  "time switches with a yearly program "
                  "(TR 64* top2 connected using a EM LAN top2 module)",
    long_description = open('README.md').read(),

    url = "https://github.com/skoslowski/LANtopPy",
    download_url = "https://github.com/skoslowski/LANtopPy/archive/master.zip",

    packages = ['lantop'],

    install_requires = [
        "python-dateutil",
        "oauth2client",
        "apiclient",
        "httplib2"
    ],

    entry_points = {
        "console_scripts": [
            "lantop = lantop.cli:main"
            "gcal_import = lantop.gcalimport.cli:main"
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