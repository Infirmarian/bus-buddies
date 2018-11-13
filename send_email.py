from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from email.mime.text import MIMEText
import base64


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly https://www.googleapis.com/auth/gmail.send'
store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('gmail', 'v1', http=creds.authorize(Http()))


def send_email(sender, receiver, subject, message):
    msg = create_message(sender, receiver, subject, message)
    send_message(service, sender, msg)


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