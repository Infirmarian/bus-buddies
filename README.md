# Bus Buddies
### This program is intended to randomly select buddies for the UCLA Clarinet section, and then alert those buddies via email and SMS
#### Instructions
This program requires an AWS account to use Amazon's Simple Notification Service, as well as a Google API key to read spreadsheets and send email.

In order to set up the program, copy `ex_conf.py` to a new file `conf.py` and replace the information with your spreadsheet, sheet range and sending email. In addition, to actually cause the program to send messages, change the value of the variable on bus-buddies.py:155 to be `MESSASGE = True`. This is hard-coded to false to prevent extraneous messages from being sent.

