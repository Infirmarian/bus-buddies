from googleapiclient.discovery import build
from httplib2 import Http
from email.mime.text import MIMEText
import base64
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/gmail.send']

print('Loading Google API credentials')
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

print('Building mailservice for sending email')
mailservice = build('gmail', 'v1', credentials=creds)
print('Building sheet service to access Google Sheets')
sheetservice = build('sheets', 'v4', credentials=creds)

def send_email(sender, receiver, subject, message):
    msg = create_message(sender, receiver, subject, message)
    send_message(mailservice, sender, msg)

def create_message(sender, to, subject, message_text):
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  x = message.as_string().encode()
  z = base64.urlsafe_b64encode(x)
  return {"raw":z.decode()}

def send_message(service, user_id, message):
    message = (service.users().messages().send(userId=user_id, body=message)
                .execute())
    print ('Message Id: %s' % message['id'])
    return message

def get_google_sheets(sheet_id, sheet_range):
    # Call the Sheets API
    print('Fetching Google Sheet id=%s' % sheet_id)
    sheet = sheetservice.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id,
                                range=sheet_range).execute()
    values = result.get('values', [])
    if not values:
        raise Exception('No data found.')
    print('Successfully fetched Google Sheet data')
    return values
