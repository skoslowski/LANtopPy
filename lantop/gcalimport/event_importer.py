# -*- coding: utf-8 -*-
"""Handles Google API client stuff"""

import os
import gflags
import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

from dateutil.parser import parse

from . _config import CONFIG
from .. _config import LANTOP_CONF_PATH


class GCalEventError(Exception):
    """Exceptions thrown by GCalEventImporter"""
    pass


class GCalEventImporter(object):
    """Class for retrieving a list of calendar entries from Google"""
    
    def __init__(self):
        """Connect to and authenticate with Google API"""
        self.cal_id = ''     
        
        FLAGS = gflags.FLAGS
        FLOW = OAuth2WebServerFlow(**CONFIG['api_params'])
        FLAGS.auth_local_webserver = False

        storage_file = os.path.expanduser(
            os.path.join(LANTOP_CONF_PATH, 'api_token.json'))
        storage = Storage(storage_file)
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = run(FLOW, storage)
        
        http = httplib2.Http()
        http = credentials.authorize(http)
        
        credentials.refresh(http)

        self.service = build(serviceName='calendar', version='v3', http=http,
                             developerKey=CONFIG['dev_key'])
       
    def select_calendar(self, calendar_came):
        """Select a calendar to be used for entry retrieval"""
        calendar_list = self.service.calendarList().list().execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary'] == calendar_came:
                self.cal_id = calendar_list_entry['id']
                break
        
        if not self.cal_id:
            raise GCalEventError('Calendar not found')
    
    def get_events(self, start, end):
        """Retrieve a list of event in the time between start and stop"""
        if not self.cal_id:
            raise GCalEventError('No calendar selected')
        
        events = self.service.events().list(
            calendarId=self.cal_id,
            orderBy="startTime",
            singleEvents=True,
            timeMin=start.isoformat(),
            timeMax=end.isoformat()
        ).execute()
        
        for i, event in enumerate(events['items']):
            events['items'][i]['start'] = parse(event['start']['dateTime'])
            events['items'][i]['end'] = parse(event['end']['dateTime'])
                        
        # check if there were more results
        if events.get('nextPageToken'):
            raise GCalEventError('There were more')
            
        return events['items']
