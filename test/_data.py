# -*- coding: utf-8 -*-
"""Test data for LANtop2 emulator"""

from datetime import datetime, date

# holds request and response codes and the respective decoded data
TEST_DATA = {
    # dummy command
    'xxxxxx0': ('787838',),
    # dummy command
    'xxxxxx1': ('787802',),
    # dummy command
    'xxxxxx2': ('7878UIJK',),
    # get info
    'T02624C': ('626C0690502F082D',
                ('TR 644 top2 RC', 110121007)),
    # get name
    'K024E47': ('6B4E746573745445535431323300',
                'testTEST123'),
    # set name
    'K174E53': ('6B4E31',
                'K174E536162636465666768696A6B6C6D6E6F707172737400'),
    # get pin
    'T026250': ('6270123401E1',
                ('1234', True)),
    #set pin
    'T046150': ('6170002B',
                'T0461501234'),
    # get sw version
    'K0156': ('6B56302E3133203230303830373236',
              (0.13, date(2008, 7, 26))),
    # get time
    'T02625A': ('627A150B0C0E0E00D3',
                datetime(2012, 11, 21, 14, 14, 0, 211)),
    # set time
    'T08615A': ('617A0021',
                'T08615A0B0C0D0E0F10'),
    # get states
    'T02624B': ('626B8C0209020202020200000015',
                [{'active': True, 'reason': 'Dauer int', 'index': 0},
                 {'active': False, 'reason': 'Auto', 'index': 1},
                 {'active': False, 'reason': 'Timer int', 'index': 2},
                 {'active': False, 'reason': 'Auto', 'index': 3}]),
    # set state
    'T04614B': ('616B0030',
                'T04614B'),
    # get channel name
    'T03624E': ('626E004C35434754554F44205351416C1B0760',
                  'L5Cgtuod Sqal'),
    # get channel stats
    'T036242': ('626200331A0000004000001B010100050207DAE3',
                (670.7, 1638.4, 65819, date(2010, 2, 5))),
    # reset channel stats
    'T046142': ('61620039',
                'T046142'),
    # set timed state
    'T08614B': ('616B0030',
                'T08614B030400011C01'),
    # extra info
    'T036249': ({'00': '626900383532315D',
                 '01': '6269017B7700003A',
                 '02': '626902E8AE020093',
                 '03': '6269031D0407DB27'},''),
}