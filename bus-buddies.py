from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import json
import os
import random
import sms
import google_api
import time
import config
import logging
import argparse

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/gmail.send']
SPREADSHEET_ID = config.SPREADSHEET_ID
RANGE_NAME = config.RANGE_NAME

class Clarinet():
    clarinet_list = {}
    @staticmethod
    def deserializeFormat(serial):
        c = Clarinet(
            serial['name'], 
            serial['likes'], 
            serial['dislikes'],
            serial['allergies'],
            serial['number'],
            serial['email']
        )
        c.history = serial['history']
        return c
    @staticmethod
    def serializeFormat(net):
        return {
            'name': net.name,
            'likes': net.likes,
            'dislikes': net.dislikes,
            'allergies': net.allergies,
            'number': net.number,
            'email': net.email,
            'history': net.history
        }
    def __init__(self, name, likes, dislikes, allergies, number, email):
        self.name = name
        self.likes = likes
        self.dislikes = dislikes
        self.allergies = allergies
        self.number = ''.join(n if n.isdigit() else '' for n in number)
        self.email = email
        self.buddy = None
        self.history = {}
        self.optout = False
    def setBuddy(self, name, game):
        self.buddy = Clarinet.clarinet_list[name]
        self.history[name] = game
    def __eq__(self, other):
        if isinstance(other, Clarinet):
            return other.name == self.name
        if isinstance(other, str):
            return other == self.name
        return False
    def __hash__(self):
        return hash(self.name)
    def print(self, cheer):
        return "Hi %s, your bus buddy for the %s game is %s.\nLikes: %s\nDislikes: %s\nAllergies: %s\n\n Go Bruins, %s" % (
            self.name, self.history[self.buddy], self.buddy.name, self.buddy.likes, self.buddy.dislikes, self.buddy.allergies, cheer
        )

def load_and_download_individuals():
    if os.path.exists('cached_history.json'):
        with open('cached_history.json', 'r') as f:
            nets = json.load(f)
        for name, values in nets.items():
            Clarinet.clarinet_list[name] = Clarinet.deserializeFormat(values)
    data = google_api.get_google_sheets(config.SPREADSHEET_ID, config.RANGE_NAME)
    for row in data:
        if row[0] in Clarinet.clarinet_list:
            Clarinet.clarinet_list[row[0]].likes = row[1]
            Clarinet.clarinet_list[row[0]].dislikes = row[2]
            Clarinet.clarinet_list[row[0]].allergies = row[3]
            Clarinet.clarinet_list[row[0]].number = row[4]
            Clarinet.clarinet_list[row[0]].email = row[5]
        else:
            Clarinet.clarinet_list[row[0]] = Clarinet(row[0], row[1], row[2], row[3], row[4], row[5])
        if len(row) > 6 and row[6].lower() == 'yes':
            Clarinet.clarinet_list[row[0]].optout = True
        else:
            Clarinet.clarinet_list[row[0]].optout = False

def match_buddies(game):
    net_list = []
    for k, v in Clarinet.clarinet_list.items():
        if not v.optout:
            net_list.append(k)
    buddies = net_list.copy()
    for name in net_list:
        potential_buddies = set(buddies.copy())
        if name in potential_buddies:
            potential_buddies.remove(name)  # Cannot be a buddy with yourself!
        for past in Clarinet.clarinet_list[name].history:
            if past in potential_buddies:
                potential_buddies.remove(past)
        if len(potential_buddies) == 0:
            raise Exception("WARNING! No possible buddies for {}".format(name))
        buddy = random.sample(potential_buddies, 1)[0]
        Clarinet.clarinet_list[name].setBuddy(buddy, game)
        buddies.remove(buddy)

def send_messages(game, cheer):
    result = input('Are you sure you want to send the messages. Type YES to confirm')
    if result == 'YES':
        for _, net in Clarinet.clarinet_list.items():
            if not net.optout:
                time.sleep(2)
                google_api.send_email(config.EMAIL, net.email, 'Bus Buddy for %s' % game, net.print(cheer))
                sms.send_sms_twilio(net.print(cheer), net.number)
    else:
        print('Logging locally to terminal and exiting')
        for _, net in Clarinet.clarinet_list.items():
            if not net.optout:
                print(net.print(cheer))
        exit(2)

def reserialize_individuals():
    blob = {}
    for key, value in Clarinet.clarinet_list.items():
        blob[key] = Clarinet.serializeFormat(value)
    with open('cached_history.json', 'w') as f:
        json.dump(blob, f)
    logging.log(0, 'Successfully wrote cached_history.json to disk')

def send_sample_messages(subject, body):
    result = input('Are you sure you want to send messsages? Type YES to confirm')
    if result == 'YES':
        for _, net in Clarinet.clarinet_list.items():
            google_api.send_email(config.EMAIL, net.email, subject, body)
            sms.send_sms_twilio(body, net.number)
            time.sleep(2.5)

def resend_game_message(game):
    result = input('Are you sure you want to resend messages for the %s game? Type YES to confirm' % game)
    if result == 'YES':
        for _, net in Clarinet.clarinet_list.items():
            pass # TODO

def main():
    parser = argparse.ArgumentParser()
    send_type = parser.add_mutually_exclusive_group()
    send_type.add_argument('--generate_new_messages', action='store_true', help='Send a new week of bus buddy messages')
    send_type.add_argument('--resend_game_messages', action='store_true', help='Resend the messages of a specific game')
    send_type.add_argument('--send_test_messages', action='store_true', help='Send a sample message with')
    
    parser.add_argument('--opponent', help='The opponent we are facing next')
    parser.add_argument('--cheer', help='The cheer (eg chop the trees) to postpend to the messages')
    parser.add_argument('--subject', help='subject of a test message to send')
    parser.add_argument('--body', help='the body of a test message to send')

    args = parser.parse_args()
    if args.send_test_messages:
        if args.body is None or args.subject is None:
            raise ValueError('Must provide both a --subject and a --body in order to send test messages')
        load_and_download_individuals()
        send_sample_messages(args.subject, args.body)
    elif args.resend_game_messages:
        if args.opponent is None:
            raise ValueError('Must provide a --opponent to resend messages')
    elif args.generate_new_messages:
        if args.opponent is None or args.cheer is None:
            raise ValueError('Must provide both a --opponent and a --cheer to send new messages')
        load_and_download_individuals()
        match_buddies(args.opponent)
        send_messages(args.opponent, args.cheer)
        reserialize_individuals()

if __name__ == '__main__':
    main()
