from fetch import *

from datetime import datetime
import httplib
import requests
import socket

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
from pygithub3 import Github
from twilio.rest import TwilioRestClient
import twitter

### PREPARE EVERNOTE ###

dev_token = retrieveFromOptions('evernote_dev_token')
notebookguid = retrieveFromOptions('notebookguid')
noteguid = retrieveFromOptions('noteguid')

client = EvernoteClient(token=dev_token)
user_store = client.get_user_store()
note_store = client.get_note_store()
notebooks = note_store.listNotebooks()
notebook_exists = False

if notebookguid == None:
    notebook = Types.Notebook()
    notebook.name = 'Errors'
    new_notebook = note_store.createNotebook(dev_token, notebook)
    notebookguid = new_notebook.guid
    setOption('notebookguid', notebookguid)

    note_body = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note></en-note>"""

    note = Types.Note()
    note.title = '%s Errors' % socket.gethostname()
    note.notebookGuid = notebookguid
    note.content = note_body
    new_note = note_store.createNote(dev_token, note)
    noteguid = new_note.guid
    setOption('noteguid', noteguid)

### PREPARE TWILIO ###

account_sid = retrieveFromOptions('twilio_account_sid')
auth_token = retrieveFromOptions('twilio_auth_token')
client = TwilioRestClient(account_sid, auth_token)

### PREPARE TWITTER ###

twitter_api = twitter.Api(
    consumer_key=retrieveFromOptions('twitter_consumer_key'),
    consumer_secret=retrieveFromOptions('twitter_consumer_secret'),
    access_token_key=retrieveFromOptions('twitter_access_token_key'),
    access_token_secret=retrieveFromOptions('twitter_access_token_secret'))

### API METHODS ###

def createGithubIssue(error):
    connection = httplib.HTTPSConnection('api.github.com', 443, timeout = 30)
    headers = {"Authorization":"token %s" % retrieveFromOptions('github_auth_token'), "user-agent":"python"}
    body = "{\n  \"title\": \"%s\"\n}" % error
    connection.request('POST', '/repos/Fetch-Errors/site/issues', body, headers)
    print "GitHub issue has been created"

def makePhoneCall(error, phonenumber):
    call = client.calls.create(url="http://fetch.jackcook.us/response.php?error=%s" % error.replace(' ', '+'),
        to=phonenumber,
        from_="+19177461129"
    )
    print "Phone call has been made"

def sendSlackMessage(error):
    connection = httplib.HTTPSConnection('slack.com', 443, timeout = 30)
    connection.request('GET', '/api/chat.postMessage?token=%s&channel=%s&text=%s&pretty=1&username=Fetch&icon_url=http://104.131.74.5/logo/48.png' % (retrieveFromOptions('slack_auth_token'), retrieveFromOptions('slack_channel_id'), error.replace(' ', '+')), None, {})
    print "Slack message has been sent"

def sendTextMessage(error, phonenumber):
    client.messages.create(
        to=phonenumber,
        from_="+19177461129",
        body=error,
    )
    print "Text message has been sent"

def sendToEvernote(error):
    current_note = note_store.getNote(dev_token, noteguid, True, True, True, True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = current_note.content
    content = content.replace('</en-note>', '')
    content += '[%s] %s<br clear="none"/>' % (timestamp, error)
    content += '</en-note>'

    updated_note = Types.Note()
    updated_note.title = "%s Errors" % socket.gethostname()
    updated_note.guid = noteguid
    updated_note.content = content
    updated_note.notebookGuid = notebookguid

    note = note_store.updateNote(dev_token, updated_note)
    print "Error has been logged to Evernote"

def sendTweet(error):
    try:
        tweet = (error[:137] + '...') if len(error) > 137 else error
        status = twitter_api.PostUpdate(tweet)
    except:
        pass
    print "Tweet has been tweeted"

def sendYo(username):
    requests.post('http://api.justyo.co/yo/', data={'api_token': retrieveFromOptions('yo_api_token'), 'username': username})
    print "%s has been yo'd" % username
