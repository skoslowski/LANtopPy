# -*- coding: utf-8 -*-
"""PushBullet logging handler"""

import logging

from pushbullet import Pushbullet


class PushBulletHandler(logging.Handler):

    def __init__(self, api_key, title='', level=logging.WARNING):
        super().__init__(level)
        self.name = title
        self.api_key = api_key

    def emit(self, record):
        try:
            Pushbullet(self.api_key).push_note(
                title=self.name,
                body=self.format(record)
            )
        except:
            pass
