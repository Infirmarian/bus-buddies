from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import json
import os
import random
import sms
import send_email
import time
import config
import sqlite3

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/gmail.send']
SPREADSHEET_ID = config.SPREADSHEET_ID
RANGE_NAME = config.RANGE_NAME

class Clarinet():
    def __init__(self, name, likes, dislikes, allergies, number, email):
        self.name = name
        self.likes = likes
        self.dislikes = dislikes
        self.allergies = allergies
        self.number = ''.join(n if n.isdigit() else '' for n in number)
        self.email = email
        self.buddy = None
        self.history = {}
    def serializeFormat(self):
        return {
            'name': self.name,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'allergies': self.allergies,
            'number': self.number,
            'email': self.email,
            'history': self.history
        }
    def __eq__(self, other):
        if isinstance(other, Clarinet):
            return other.name == self.name
        if isinstance(other, str):
            return other == self.name
        return False
    def __hash__(self):
        return hash(self.name)

def get_google_sheets():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
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

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    nets = set()

    if not values:
        print('No data found.')
    else:
        for row in values[1:]:
            if len(row) > 5 and row[5] != "":
                print("%s opted out" % row[0])
                continue
            nets.add(Clarinet(row[0], row[1], row[2], row[3], row[4], row[6]))
    return nets


def generate_messages(nets, send_message=False):
    game = "GAME"
    for net in nets:
        name = net
        number = nets[net]['number']
        email = nets[net]['email']
        buddy_obj = nets[nets[net]['buddy']]
        buddy_name = nets[net]['buddy']
        likes = buddy_obj['likes']
        dislikes = buddy_obj['dislikes']
        allergies = buddy_obj['allergies']
        msg = "Hello {name}, your bus buddy for the {game} game is {buddy}.\nLikes: {likes}\nDislikes: {dislikes}\nAllergies: {allergies}\n\nGo Bruins!".format(
            name=name, 
            buddy=buddy_name, 
            likes=likes, 
            dislikes=dislikes, 
            allergies=allergies,
            game=game
        )
        print(email)
        print(number)
        if send_message:
            time.sleep(2.5)
            if email is not None:
                send_email.send_email(sender = conf.EMAIL, receiver=email, subject="{} Bus Buddy".format(game), message=msg)
            if number is not None:
                sms.send_sms(number=number, message=msg)
        else:
            print(msg)


def gen_bus_buddies(nets):
    net_list = list(nets)
    for net in nets:
        potential_buddies = set(net_list.copy())
        if net in potential_buddies:
            potential_buddies.remove(net)  # Cannot be a buddy with yourself!
        for done_bud in nets[net]['already-had']:
            if done_bud in potential_buddies:
                potential_buddies.remove(done_bud)
        if len(potential_buddies) == 0:
            print("WARNING! No possible buddies for {}".format(net))
            return None  # Error was encountered, need to reselect
        buddy = random.sample(potential_buddies, 1)[0]
        nets[net]['buddy'] = buddy
        net_list.remove(buddy)
    return 0

def send_main_buddies(m = False):
    nets = get_google_sheets()
    if gen_bus_buddies(nets) is None:
        print("Failed")
        return
    i = input("Press enter to continue, q to quit: ")
    if i == 'Q' or i == 'q':
        return
    generate_messages(nets, send_message=m)
    update_bus_buddies(nets)

def resend_buddies(m = False):
    nets = get_google_sheets()
    load_old_bus_buddies(nets)
    for net in nets:
        nets[net]['buddy'] = nets[net]['already-had'][-1]
    generate_messages(nets, send_message=m)

def main():
    
    '''
    # Changing this to True will send out messages. Be cautious
    MESSASGE = False

    choice = input("Do you want to resend [r] or send new [n]? ")
    if choice == "r":
        resend_buddies(MESSASGE)
    elif choice == "n":
        send_main_buddies(MESSASGE)
    else:
        print("No option corresponds with that choice")
    print("DONE!")
    '''

if __name__ == '__main__':
    main()