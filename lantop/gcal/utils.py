# -*- coding: utf-8 -*-
"""PushBullet logging handler"""

import logging

from pushbullet import Pushbullet


class PushBulletHandler(logging.Handler):

    def __init__(self, api_key, title='', email=None, level=logging.WARNING):
        super().__init__(level)
        self.api_key = api_key
        self.title = title
        self.email = email

    def emit(self, record):
        try:
            Pushbullet(self.api_key).push_note(
                title=self.title,
                body=self.format(record),
                email=self.email
            )
        except:
            pass
