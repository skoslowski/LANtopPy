# -*- coding: utf-8 -*-
"""A Class to represent and format a entry in a crontab file"""

import re
from datetime import timedelta

from ._config import CONFIG


class LantopCronAction(object):
    """A crontab entry for lantop commands"""

    def __init__(self, time, args, comment, user=None):
        """Set parameters and format args for CronEvent"""
        self.time = time
        self.comment = comment
        self.args = args
        self.user = user or CONFIG['cron']['user']

    def __unicode__(self):
        """Format entry for crontab"""
        command = CONFIG['cron']['cmd'] + u" " + u" ".join(
            CONFIG['cron']['args'].format(channel=ch, state=st)
            for ch, st in self.args.iteritems()
        )
        output = u"{:%M %H %d %m *}\t{}\t{}".format(
            self.time, self.user, command, self.comment)
        if self.comment:
            output += u"\t# {}".format(self.comment)
        return output

    def __repr__(self):
        return '{}(time={}, args={}, comment="{}")'.format(
            self.__class__.__name__, repr(self.time),
            repr(self.args), self.comment)

    def __iadd__(self, other):
        """Append others args and combine comment"""
        self.args.update(other.args)
        self.comment = u"{} + {}".format(self.comment, other.comment)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and \
            self.time == other.time and self.comment == other.comment and \
            self.args == other.args and self.user == other.user


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
        end = event['end'] + timedelta(minutes=offset_end)
        if start < end:
            yield LantopCronAction(start, {index: u'on'}, event['summary'])
            yield LantopCronAction(end, {index: u'auto'}, event['summary'])


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
                yield LantopCronAction(event['start'], {index: u'on'},
                                       event['summary'])
                yield LantopCronAction(event['end'], {index: u'auto'},
                                       event['summary'])
                break  # only one channel per event
        else:
            # if no channel names in event title, try to parse its description
            for action in extract_actions_from_desc(event, channels):
                yield action
            # yield from


def get_combined_actions(events):
    actions = {}
    for action in extract_actions(events, CONFIG['channels']):
        try:
            actions[action.time] += action
        except KeyError:
            actions[action.time] = action
    return actions.values()