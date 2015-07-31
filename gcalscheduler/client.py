# -*- coding: utf-8 -*-
"""Handles Google API client stuff"""

import os
import httplib2

from apiclient import discovery
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow

from dateutil.parser import parse as dateutil_parse

from . _config import CONFIG


API_TOKEN_STORAGE = os.path.expanduser(os.path.join(
    CONFIG["credentials_storage_path"], "api_token.json"))


class GCalEventError(Exception):
    """Exceptions thrown by GCalEventImporter"""
    pass


class GCalAuthorizationMissing(GCalEventError):
    """Exceptions thrown by GCalEventImporter"""
    pass


class GCalEventImporter(object):
    """Class for retrieving a list of calendar entries from Google"""

    def __init__(self, calendar_came=None):
        """Connect to and authenticate with Google API"""
        self._calendar_id = ""

        credentials = Storage(API_TOKEN_STORAGE).get()
        if credentials is None or credentials.invalid:
            raise GCalAuthorizationMissing('Missing or invalid credentials')

        self.service = discovery.build(
            serviceName="calendar",
            version="v3",
            http=credentials.authorize(httplib2.Http()),
            developerKey=CONFIG["dev_key"]
        )

        if calendar_came:
            self.select_calendar(calendar_came)

    def select_calendar(self, calendar_came):
        """Select a calendar to be used for entry retrieval"""
        response = self.service.calendarList().list().execute()
        for calendar_list_entry in response["items"]:
            if calendar_list_entry["summary"] == calendar_came:
                self._calendar_id = calendar_list_entry["id"]
                break
        else:
            raise GCalEventError("Calendar not found")

    def get_events(self, start, end):
        """Retrieve a list of event in the time between start and stop"""
        if not self._calendar_id:
            raise GCalEventError("No calendar has been selected")

        response = self.service.events().list(
            calendarId=self._calendar_id,
            orderBy="startTime",
            singleEvents=True,
            timeMin=start.isoformat(),
            timeMax=end.isoformat()
        ).execute()

        events = response["items"]
        for event in events:
            for what in ('start', 'end'):
                event[what] = dateutil_parse(event[what]["dateTime"])

        # check if there were more results
        if response.get("nextPageToken"):
            raise GCalEventError("There were more")

        return events


def authorize():
    flow = OAuth2WebServerFlow(**CONFIG["api_params"])

    authorize_url = flow.step1_get_authorize_url()

    print('Go to the following link in your browser:')
    print()
    print('    ' + authorize_url)
    print()

    code = input('Enter verification code: ').strip()
    credential = flow.step2_exchange(code)

    Storage(API_TOKEN_STORAGE).put(credential)
