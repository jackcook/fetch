import re
import smtplib
import socket
import sys
from evernote.api.client import EvernoteClient

fromemail = "INSERT_EMAIL_ADDRESS_HERE"
to = [sys.argv[1]]
subject = "Error Log - %s" % socket.gethostname()

dev_token = "INSERT_EVERNOTE_DEV_TOKEN_HERE"
noteguid = ""

client = EvernoteClient(token=dev_token)
note_store = client.get_note_store()

with open('data.txt', 'r+') as f:
    for line in f.readlines():
        key = line.split('=')[0]
        value = line.split('=')[1].replace('\n', '')
        if key == 'noteguid':
            noteguid = value

text = note_store.getNoteContent(dev_token, noteguid).replace('<br clear="none"/>', '\n')
text = re.sub('<[^>]+>', '', text)
text = text.replace('\n\n', '\n').replace('\n\n', '\n')
list = text.split('\n')

text = ''
for s in reversed(list):
    text += s + '\n'
text = text.replace('\n', '', 1)

message = """\
From: %s
To: %s
Subject: %s

%s
""" % (fromemail, ", ".join(to), subject, text)

server = smtplib.SMTP("INSERT_SMTP_SERVER_HERE")
server.starttls()
server.login('INSERT_EMAIL_ADDRESS_HERE', 'INSERT_EMAIL_PASSWORD_HERE')
server.sendmail(fromemail, to, message)
server.quit()