# -*- coding: utf-8 -*-
"""Handles Google API client stuff"""

import json
import httplib2

from apiclient import discovery
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets

from dateutil.parser import parse as dateutil_parse

from . config import CONFIG


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

        try:
            dev_key = json.load(open(CONFIG["dev_key"]))
        except IOError:
            raise GCalAuthorizationMissing('Missing developer key file')

        credentials = Storage(CONFIG['credentials_storage_path']).get()
        if credentials is None or credentials.invalid:
            raise GCalAuthorizationMissing('Missing or invalid credentials')

        self.service = discovery.build(
            serviceName="calendar",
            version="v3",
            http=credentials.authorize(httplib2.Http()),
            developerKey=dev_key
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
            event['start'] = dateutil_parse(event['start']["dateTime"])
            event['end'] = dateutil_parse(event['end']["dateTime"])
            event['created'] = dateutil_parse(event['created'])
            event['updated'] = dateutil_parse(event['updated'])

        # check if there were more results
        if response.get("nextPageToken"):
            raise GCalEventError("There were more")

        return events


def authorize():
    flow = flow_from_clientsecrets(CONFIG['client_secrets'], CONFIG['scope'],
                                   redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    authorize_url = flow.step1_get_authorize_url()

    print('Go to the following link in your browser:')
    print()
    print('    ' + authorize_url)
    print()

    code = input('Enter verification code: ').strip()
    credential = flow.step2_exchange(code)

    Storage(CONFIG['credentials_storage_path']).put(credential)
