# -*- coding: utf-8 -*-
"""A Class to represent and format a entry in a crontab file"""

from ._config import CONFIG


class CronAction(object):
    """Representation of a crontab entry"""

    def __init__(self, start, command, user='root', comment=None):
        """Set entry data"""
        self.start = start
        self.command = command
        self.user = user
        self.comment = comment

    def __str__(self):
        """Format entry for crontab"""
        output = u"{start:%M %H %d %m *}\t{user}\t{command}"
        if self.comment:
            output += u"\t# {comment}"

        return output.format(**self.__dict__)


class LantopCronAction(CronAction):
    """A crontab entry for lantop commands"""

    def __init__(self, channel, start, duration, comment):
        """Set parameters and format args for CronEvent"""
        super(LantopCronAction, self).__init__(start, '', comment=comment)
        self.build_command(channel, duration)

    def build_command(self, channel, duration):
        """Build command string"""
        self.command = CONFIG['cron']['cmd'] + u" " + \
            CONFIG['cron']['args'].format(channel=channel, duration=duration,
                                          **self.__dict__)
