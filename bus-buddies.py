from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import csv
import os
import random
import sms
import send_email
import time
import conf

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly https://www.googleapis.com/auth/gmail.send'

SPREADSHEET_ID = conf.SPREADSHEET_ID
RANGE_NAME = conf.RANGE_NAME

def get_google_sheets():
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    nets = {}

    if not values:
        print('No data found.')
    else:
        for row in values[1:]:
            if len(row) > 5 and row[5] != "":
                print("{} opted out".format(row[0]))
                continue
            nets[row[0]] = {
                "likes":row[1],
                "dislikes":row[2],
                "allergies":row[3],
                "number":strip_vals(row[4]),
                "buddy":None,
                "already-had":[],
                "email":row[6] if len(row) > 6 else None
            }
    return nets

def strip_vals(string):
    num = ""
    for char in string:
        if char.isdigit():
            num += char
    return num

def load_old_bus_buddies(nets):
    if not os.path.exists("hist.csv"):
        return
    with open("hist.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] in nets:
                nets[row[0]]["already-had"] = row[1:]


def update_bus_buddies(nets):
    former_list = {}
    with open("hist.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            former_list[row[0]] = row[1:]
    for net in nets:
        if net in former_list:
            former_list[net].append(nets[net]['buddy'])
        else:
            former_list[net] = [nets[net]['buddy']]

    with open("hist.csv", "w", newline='') as f:
        writer = csv.writer(f)
        for item in former_list:
            writer.writerow([item]+former_list[item])


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
    load_old_bus_buddies(nets)
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

if __name__ == '__main__':
    main()