# -*- coding: utf-8 -*-
"""Test data for LANtop2 emulator"""

from datetime import datetime, date

# holds request and response codes and the respective decoded data
TEST_DATA = {
    # dummy command
    b'xxxxxx0': (b'787838',),
    # dummy command
    b'xxxxxx1': (b'787802',),
    # dummy command
    b'xxxxxx2': (b'7878UIJK',),
    # get info
    b'T02624C': (b'626C0690502F082D',
                 ('TR 644 top2 RC', 110121007)),
    # get name
    b'K024E47': (b'6B4E746573745445535431323300',
                 'testTEST123'),
    # set name
    b'K174E53': (b'6B4E31',
                 b'K174E536162636465666768696A6B6C6D6E6F707172737400'),
    # get pin
    b'T026250': (b'6270123401E1',
                 ('1234', True)),
    #set pin
    b'T046150': (b'6170002B',
                 b'T0461501234'),
    # get sw version
    b'K0156': (b'6B56302E3133203230303830373236',
               (0.13, date(2008, 7, 26))),
    # get time
    b'T02625A': (b'627A150B0C0E0E00D3',
                 datetime(2012, 11, 21, 14, 14, 0, 211)),
    # set time
    b'T08615A': (b'617A0021',
                 b'T08615A0B0C0D0E0F10'),
    # get states
    b'T02624B': (b'626B8C0209020202020200000015',
                 [{'active': True, 'reason': 'Dauer int', 'index': 0},
                  {'active': False, 'reason': 'Auto', 'index': 1},
                  {'active': False, 'reason': 'Timer int', 'index': 2},
                  {'active': False, 'reason': 'Auto', 'index': 3}]),
    # set state
    b'T04614B': (b'616B0030',
                b'T04614B'),
    # get channel name
    b'T03624E': (b'626E004C35434754554F44205351416C1B0760',
                 'L5Cgtuod Sqal'),
    # get channel stats
    b'T036242': (b'626200331A0000004000001B010100050207DAE3',
                 (670.7, 1638.4, 65819, date(2010, 2, 5))),
    # reset channel stats
    b'T046142': (b'61620039',
                 b'T046142'),
    # set timed state
    b'T08614B': (b'616B0030',
                 b'T08614B030400011C01'),
    # extra info
    b'T036249': ({b'00': b'626900383532315D',
                  b'01': b'6269017B7700003A',
                  b'02': b'626902E8AE020093',
                  b'03': b'6269031D0407DB27'}, b''),
}
