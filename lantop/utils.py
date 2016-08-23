"""Get/set the default dev addr, setup logging, pushbullet logging handler"""

import os
import logging
import logging.config
import pkgutil

import yamlsettings
from pushbullet import Pushbullet

from . import LANTOP_CONF_PATHS


def load_config():
    config = yamlsettings.yamldict.load(pkgutil.get_data(__package__, 'default.yml'))

    try:
        overwrite = os.environ.get('LANTOP_CONFIG', '')
        yamlsettings.update_from_file(
            config, LANTOP_CONF_PATHS if not overwrite else [overwrite])
    except OSError:
        pass

    yamlsettings.update_from_env(config, prefix='LANTOP')
    return config


class PushBulletHandler(logging.Handler):

    def __init__(self, api_key, title='', email=None, level=logging.WARNING):
        super().__init__(level)
        self.client = Pushbullet(api_key)
        self.title = title
        self.email = email

    def emit(self, record):
        try:
            self.client.push_note(
                title=self.title, body=self.format(record), email=self.email
            )
        except Exception:
            self.handleError(record)


class IndentFilter(logging.Filter):
    """Indent extra lines of record messages"""

    def __init__(self, name='', indent=0):
        super().__init__(name)
        self.indent = indent

    def filter(self, record):
        if not super().filter(record):
            return False
        newline = '\n' + ' ' * self.indent
        record.msg = newline.join(str(record.msg).strip().split('\n'))
        return True


class ContentFilter(logging.Filter):
    """Pass only tagged messages (or only not tagged)"""

    def __init__(self, name='', tag='', mode='match'):
        super().__init__(name)
        self.tag = tag
        self.mode = mode

    def filter(self, record):
        if not super().filter(record):
            return False
        if not self.tag:
            return True
        response = self.mode != 'match'
        if self.tag in record.msg:
            record.msg = record.msg.replace(self.tag, '')
            response = not response
        return self.mode == 'clear' or response
