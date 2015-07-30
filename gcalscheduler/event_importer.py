# -*- coding: utf-8 -*-
"""Handles Google API client stuff"""

import os
import httplib2

from apiclient import discovery
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow, SignedJwtAssertionCredentials
from oauth2client import tools

from dateutil.parser import parse as dateutil_parse

from . _config import CONFIG


class GCalEventError(Exception):
    """Exceptions thrown by GCalEventImporter"""
    pass


class GCalEventImporter(object):
    """Class for retrieving a list of calendar entries from Google"""

    def __init__(self):
        """Connect to and authenticate with Google API"""
        self._calendar_id = ""

        flow = OAuth2WebServerFlow(**CONFIG["api_params"])
        flags = tools.argparser.parse_args(())

        storage = Storage(os.path.expanduser(os.path.join(
            CONFIG["credentials_storage_path"], "api_token.json")))
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow, storage, flags)

        http = credentials.authorize(httplib2.Http())
        credentials.refresh(http)

        self.service = discovery.build(
            serviceName="calendar", version="v3", http=http,
            developerKey=CONFIG["dev_key"]
        )

    def select_calendar(self, calendar_came):
        """Select a calendar to be used for entry retrieval"""
        calendar_list = self.service.calendarList().list().execute()
        for calendar_list_entry in calendar_list["items"]:
            if calendar_list_entry["summary"] == calendar_came:
                self._calendar_id = calendar_list_entry["id"]
                break

        if not self._calendar_id:
            raise GCalEventError("Calendar not found")

    def get_events(self, start, end):
        """Retrieve a list of event in the time between start and stop"""
        if not self._calendar_id:
            raise GCalEventError("No calendar selected")

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
