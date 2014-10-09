from api import *
from aplo import *

import sys
from threading import Timer

check_done = True

def check():
    global check_done
    existingerrors = []
    newerrors = []

    with open('errors.txt', 'r') as f:
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
            with open('errors.txt', 'r+') as file:
                file.write(error + '\n')

            apis = ''
            if len(sys.argv) < 2:
                apis = 'all'
            else:
                apis = sys.argv[1]

            if 'all' not in apis:
                if 'g' in apis:
                    createGithubIssue(error)
                if 'p' in apis:
                    Timer(1, makePhoneCall, [error, retrieveFromOptions('phone_number')]).start()
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
                createGithubIssue(error)
                Timer(1, makePhoneCall, [error, retrieveFromOptions('phone_number')]).start()
                sendSlackMessage(error)
                sendTextMessage(error, retrieveFromOptions('phone_number'))
                sendToEvernote(error)
                sendTweet(error)
                sendYo(retrieveFromOptions('yo_username'))

            check_done = True
            print "Error distributed"

    check_done = True
    print "Check finished"

def recheck():
    global check_done
    Timer(1, recheck).start()

    if check_done == True:
        check_done = False
        check()

recheck()
