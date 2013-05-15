# -*- coding: utf-8 -*-
"""A Class to represent and format a entry in a crontab file"""

import re
from datetime import timedelta

from ._config import CONFIG


class CronAction(object):
    """Representation of a crontab entry"""

    def __init__(self, start, command, user='root', comment=None):
        """Set entry data"""
        self.start = start
        self.command = command
        self.user = user
        self.comment = comment

    def __repr__(self):
        return ('{}(start={}, command="{command}", '
                'user="{user}", comment="{comment}")').format(
                    self.__class__.__name__, repr(self.start), **self.__dict__)

    def __unicode__(self):
        """Format entry for crontab"""
        output = u"{start:%M %H %d %m *}\t{user}\t{command}"
        if self.comment:
            output += u"\t# {comment}"

        return output.format(**self.__dict__)

    def __eq__(self, other):
        """Compare with other Actions, for unit tests"""
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)


class LantopCronAction(CronAction):
    """A crontab entry for lantop commands"""

    def __init__(self, channel, start, duration, comment):
        """Set parameters and format args for CronEvent"""
        super(LantopCronAction, self).__init__(start, '', comment=comment)
        self.channel = None
        self.duration = None
        self.build_command(channel, duration)

    def build_command(self, channel, duration):
        """Build command string"""
        self.channel = channel
        self.duration = duration
        self.command = CONFIG['cron']['cmd'] + u" " + \
            CONFIG['cron']['args'].format(**self.__dict__)

    def __repr__(self):
        return ('{}(channel={channel}, start={}, '
                'duration={}, comment="{comment}")').format(
                    self.__class__.__name__, repr(self.start),
                    repr(self.duration), **self.__dict__)


def extract_actions_from_desc(event, channels):
    """Get triggers from event description

    Mentioning a channel label in the description will turn this channel on for
    the duration of the event. Optionally start and end time offsets can be
    specified by appending them to the label: LABEL[S_OFF[E_OFF]], where S_OFF
    and E_OFF are the offsets in minutes including their sign (+-xxx)

    :param event: event dict to examine
    :param channels: mapping of channel label to their respective index

    """
    prog = re.compile(u'(' + u'|'.join(channels.keys()) + u')' +  # channels
                      u'([+-][0-9]+)?([+-][0-9]+)?',              # offsets
                      re.I | re.U)

    for match in prog.findall(event['description']):
        name = match[0].lower()
        index = channels[name]
        offset_start = int(match[1]) \
            if len(match) > 1 and len(match[1]) > 0 else 0
        offset_end = int(match[2]) \
            if len(match) > 2 and len(match[2]) > 0 else 0

        start = event['start'] + timedelta(minutes=offset_start)
        duration = (event['end'] - event['start'] +
                    timedelta(minutes=offset_end - offset_start))
        if duration <= timedelta(0):
            continue
        yield LantopCronAction(index, start, duration, event['summary'])


def extract_actions(events, channels):
    """Extract actions from events based on the summary

    Yields a LantopCronAction object for extracted action. Each event summary
    is searched for the channel labels (one action per event). If none are
    found the event description is parsed (can contain multiple action per
    event)

    :param events: list of event dicts return by Google API
    :param channels: mapping of channel label to their respective index

    """
    for event in events:
        for name, index in channels.iteritems():
            # Check if the channel name is in the event title
            if name in event['summary'].lower():
                yield LantopCronAction(index, event['start'],
                                       event['end'] - event['start'],
                                       event['summary'])
                break  # only one channel trigger per event
        else:
            # if no channel names in event title, try to parse its description
            for action in extract_actions_from_desc(event, channels):
                yield action
            # yield from