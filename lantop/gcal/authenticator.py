from datetime import datetime

from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

from pushbullet import PushBullet


class Flow:
    def __init__(self, googleapi, api_key, email, **_):
        if api_key == 'YOUR_API_KEY_HERE':
            raise ValueError('Missing api key in settings')

        self.email = email
        self.pb = PushBullet(api_key)

        self.credentials_storage_path = googleapi.credentials_storage_path
        self.flow = flow_from_clientsecrets(
            filename=googleapi.client_secrets_path,
            scope='https://www.googleapis.com/auth/calendar.readonly',
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')

        self.last_check = None
        self.callback = lambda: None

    def run(self, callback):
        self.callback = callback

        authorize_url = self.flow.step1_get_authorize_url()
        self.pb.push_link('Google Auth Request', authorize_url, email=self.email)
        self.last_check = datetime.now()

    def iter_received_codes(self):
        pushes = self.pb.get_pushes(modified_after=self.last_check.timestamp())
        self.last_check = datetime.now()
        for push in pushes:
            if push['type'] == 'note' and push['sender_email'] == self.email:
                self.pb.dismiss_push(push['iden'])
                yield push['body'].strip()

    def check_response(self):
        if self.last_check is None:
            return

        for code in self.iter_received_codes():
            try:
                credential = self.flow.step2_exchange(code)
                Storage(self.credentials_storage_path).put(credential)
                break
            except (ValueError, FlowExchangeError) as error:
                self.pb.push_note('', 'Error: ' + str(error), email=self.email)
        else:
            return

        self.last_check = None
        self.callback()
        self.pb.push_note('', 'Authentication complete', email=self.email)
