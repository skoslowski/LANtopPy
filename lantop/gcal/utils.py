# -*- coding: utf-8 -*-
"""PushBullet logging handler"""

import logging

from pushbullet import Pushbullet


class PushBulletHandler(logging.Handler):

    def __init__(self, api_key, title='', level=logging.WARNING):
        super().__init__(level)
        self.name = title
        self.pb = Pushbullet(api_key)

    def emit(self, record):
        self.pb.push_note(
            title=self.name,
            body=self.format(record)
        )
