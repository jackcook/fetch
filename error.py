#!/usr/bin/env python
from api import *

import sys
from threading import Timer

def check():
    Timer(2, check).start()
    existingerrors = []
    newerrors = []
    with open('errors.txt', 'r+') as f:
        existingerrors = f.readlines()
        with open('/var/log/apache2/error.log') as errorfile:
            for line in errorfile.readlines():
                data = line.split('] ')
                if data[1] == '[:error':
                    error = data[4]
                    if error not in existingerrors:
                        if error not in newerrors:
                            newerrors.append(error)
        for error in newerrors:
            error = error.replace('\n', '')

            apis = ''
            if len(sys.argv) < 2:
                apis = 'all'
            else:
                apis = sys.argv[1]

            if 'all' not in apis:
                if 'g' in apis:
                    api.createGithubIssue(error)
                if 'p' in apis:
                    Timer(2, makePhoneCall, [error, retrieveFromOptions('phone_number')]).start()
                if 's' in apis:
                    sendSlackMessage(error)
                if 't' in apis:
                    sendTextMessage(error, retrieveFromOptions('phone_number'))
                if 'e' in apis:
                    sendToEvernote(error)
                if 'T' in apis:
                    sendTweet(error)
                if 'y' in apis:
                    sendYo(retrieveFromOptions('yo_username'))
            else:
                api.createGithubIssue(error)
                Timer(2, makePhoneCall, [error, retrieveFromOptions('phone_number')]).start()
                sendSlackMessage(error)
                sendTextMessage(error, retrieveFromOptions('phone_number'))
                sendToEvernote(error)
                sendTweet(error)
                sendYo(retrieveFromOptions('yo_username'))
            f.write(error + '\n')

check()