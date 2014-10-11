from fetch import *

import re
import smtplib
import socket
import sys
from evernote.api.client import EvernoteClient

fromemail = retrieveFromOptions('email_address')
to = [sys.argv[1]]
subject = "Error Log - %s" % socket.gethostname()

dev_token = retrieveFromOptions('evernote_dev_token')
noteguid = retrieveFromOptions('noteguid')

client = EvernoteClient(token=dev_token)
note_store = client.get_note_store()

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

server = smtplib.SMTP(retrieveFromOptions('email_smtp_server'))
server.starttls()
server.login(retrieveFromOptions('email_address'), retrieveFromOptions('email_password'))
server.sendmail(fromemail, to, message)
server.quit()
