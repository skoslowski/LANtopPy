#!/usr/bin/env python3
"""Setup script for LANtopPy"""

from setuptools import setup, find_packages
import versioneer

setup(
    name="LANtopPy",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    license="GPL",
    author="Sebastian Koslowski",
    author_email="sebastian.koslowski@gmail.com",

    description="A client API and CLI to control/manage Theben digital "
                "time switches with a yearly program "
                "(TR 64* top2 connected using a EM LAN top2 module)",
    long_description=open("README.md").read(),

    url="https://github.com/skoslowski/LANtopPy",
    download_url="https://github.com/skoslowski/LANtopPy/archive/master.zip",

    packages=find_packages(exclude=['tests']),
    package_data={'lantop': ['default.yml']},

    install_requires=[
        'python-dateutil',
        'google-api-python-client',
        'pushbullet.py',
        'yamlsettings',
    ],

    entry_points={
        "console_scripts": [
            "lantop = lantop.cli:main",
            "gcal_cron = lantop.gcal.cron:main",
            "gcal_scheduler = lantop.gcal.scheduler:main",
            "gcal_auth = lantop.gcal.client:authorize",
        ]
    },
    test_suite="tests",
)
