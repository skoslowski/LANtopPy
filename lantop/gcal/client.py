"""Handles Google API client stuff"""

import logging.config

import httplib2

import apiclient
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets

from dateutil.parser import parse as dateutil_parse

from .. import utils

Error = apiclient.errors.Error


class EventImporterError(Error):
    """Exceptions thrown by GCalEventImporter"""


class AuthorizationMissing(EventImporterError):
    """Missing or outdated authorization token"""


class EventImporter(object):
    """Class for retrieving a list of calendar entries from Google"""

    calendar_name_id_cache = {}

    def __init__(self, credentials_storage_path, dev_key, calendar_name=None, **_):
        """Connect to and authenticate with Google API"""
        self._calendar_id = ""

        if dev_key == 'YOUR_DEV_KEY_HERE':
            raise ValueError('Missing developer key in settings')

        credentials = Storage(credentials_storage_path).get()
        if credentials is None or credentials.invalid:
            raise AuthorizationMissing('Missing or invalid credentials')

        try:
            self.service = apiclient.discovery.build(
                serviceName="calendar",
                version="v3",
                http=credentials.authorize(httplib2.Http()),
                developerKey=dev_key
            )
        except httplib2.HttpLib2Error:
            raise EventImporterError("Can't connect to Google API")

        if calendar_name:
            self.select_calendar(calendar_name)

    def select_calendar(self, name, use_cache=True):
        """Select a calendar to be used for entry retrieval"""
        if use_cache and name in self.calendar_name_id_cache:
            self._calendar_id = self.calendar_name_id_cache[name]
            return

        response = self.service.calendarList().list().execute()
        for calendar_list_entry in response["items"]:
            if calendar_list_entry["summary"] == name:
                id_ = calendar_list_entry["id"]
                self._calendar_id = id_
                self.calendar_name_id_cache[name] = id_
                break
        else:
            raise EventImporterError("Calendar {!r} not found"
                                     "".format(name))

    def get_events(self, start, end):
        """Retrieve a list of event in the time between start and stop"""
        if not self._calendar_id:
            raise EventImporterError("No calendar has been selected")

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
            raise EventImporterError("There were more")

        return events


def authorize():
    config = utils.load_config()
    logging.config.dictConfig(config.get('logging', {}))

    flow = flow_from_clientsecrets(
        filename=config.scheduler.google.client_secrets_path,
        scope='https://www.googleapis.com/auth/calendar.readonly',
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    authorize_url = flow.step1_get_authorize_url()

    print('Go to the following link in your browser:')
    print()
    print('    ' + authorize_url)
    print()

    code = input('Enter verification code: ').strip()
    credential = flow.step2_exchange(code)

    Storage(config.scheduler.google.credentials_storage_path).put(credential)
