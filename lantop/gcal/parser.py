"""A Class to represent and format a entry in a crontab file"""

import re
from datetime import timedelta
from operator import attrgetter
from itertools import groupby


class Action(object):
    """A crontab entry for lantop commands"""
    channel_names = []
    cron_user = cron_cmd = cron_arg = ''

    @classmethod
    def set_defaults(cls, channel_names, user='root', cmd='', arg='', **_):
        cls.channel_names = channel_names
        cls.cron_user = user
        cls.cron_cmd = cmd
        cls.cron_arg = arg

    NONE = object()  # sentinel value to seed sum of Actions

    def __init__(self, time, args, label=""):
        """Set parameters and format args for CronEvent"""
        self.time = time
        self.label = label
        self.args = args

    def __str__(self):
        """Format entry for crontab"""
        command = self.cron_cmd.format(args=" ".join(
            self.cron_arg.format(channel=ch, state=st)
            for ch, st in self.args.items()
        ))
        output = "{:%M %H %d %m *}\t{}\t{}".format(
            self.time, self.cron_user, command, self.label)
        if self.label:
            output = "# {}\n{}".format(self.label, output)
        return output

    def __repr__(self):
        return "{}(time={}, args={}, comment=\"{}\")".format(
            self.__class__.__name__, repr(self.time),
            repr(self.args), self.label)

    def __add__(self, other):
        """Append others args and combine comment"""
        if self.time != other.time or self.cron_user != other.cron_user:
            return NotImplemented
        args, label = self.args.copy(), self.label

        args.update(other.args)
        if label != other.label:
            label += " + " + other.label
        return type(self)(self.time, args, label)

    def __radd__(self, other):
        """Radd to NoAction returns self"""
        return self if other is self.NONE else NotImplemented

    def __eq__(self, other):
        return self.__class__ == other.__class__ and \
            self.time == other.time and self.label == other.label and \
            self.args == other.args and self.cron_user == other.cron_user


def extract_actions_from_desc(event):
    """Get triggers from event description

    Mentioning a channel label in the description will turn this channel on for
    the duration of the event. Optionally start and end time offsets can be
    specified by appending them to the label: LABEL[S_OFF[E_OFF]], where S_OFF
    and E_OFF are the offsets in minutes including their sign (+-xxx)

    :param event: event dict to examine

    """
    prog = re.compile("(" + "|".join(list(Action.channel_names)) + ")" +
                      "([+-][0-9]+)?([+-][0-9]+)?",           # offsets
                      re.I | re.U)

    for match in prog.findall(event.get("description", '')):
        name = match[0].lower()
        index = Action.channel_names.index(name)
        offset_start = int(match[1]) \
            if len(match) > 1 and len(match[1]) > 0 else 0
        offset_end = int(match[2]) \
            if len(match) > 2 and len(match[2]) > 0 else 0

        start = event["start"] + timedelta(minutes=offset_start)
        end = event["end"] + timedelta(minutes=offset_end)
        if start < end:
            yield Action(start, {index: "on"}, event["summary"])
            yield Action(end, {index: "auto"}, event["summary"])


def extract_actions(events):
    """Extract actions from events based on the summary

    Yields a LantopCronAction object for extracted action. Each event summary
    is searched for the channel labels (one action per event). If none are
    found the event description is parsed (can contain multiple action per
    event)

    :param events: list of event dicts return by Google API

    """
    for event in events:
        for index, name in enumerate(Action.channel_names):
            # Check if the channel name is in the event title
            if name.lower() in event["summary"].lower():
                yield Action(event["start"], {index: "on"}, event["summary"])
                yield Action(event["end"], {index: "auto"}, event["summary"])
                break  # only one channel per event
        else:
            yield from extract_actions_from_desc(event)


def get_combined_actions(events):
    """Combine actions triggered at the same time"""
    actions = sorted(extract_actions(events), key=attrgetter('time'))
    return [sum(action_group, Action.NONE)
            for _, action_group in groupby(actions, key=attrgetter('time'))]


def remove_duplicate_comments(actions):
    """Remove same comments in consecutive actions to get nicer crontab file"""
    last_comment = None
    for action in actions:
        if action.comment == last_comment:
            action.comment = None
        else:
            last_comment = action.comment
    return actions


def simplify_label(action):
    """Get a nice title of an action"""
    names = re.compile('(' + '|'.join(action.channel_names) + ')', re.I)
    labels = {names.sub('', label).strip(' :(),-')
              for label in action.label.split(' + ')}
    labels.discard('')
    return ' + '.join(labels) or action.label
