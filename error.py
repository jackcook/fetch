#!/usr/bin/env python
from datetime import datetime
import httplib
import os
import requests
import signal
import socket
import sys
from threading import Timer
from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
from pygithub3 import Github
from twilio.rest import TwilioRestClient
import twitter

def retrieveFromOptions(key):
	with open('data.txt', 'r+') as f:
		for line in f.readlines():
			lineKey = line.split('=')[0]
			lineValue = line.split('=')[1]
			if lineKey == key:
				if lineValue != "XXXXXXXXXX":
					return lineValue
	return None

def setOption(key, value):
	data = None
	lineNumber = 0
	with open('data.txt', 'r') as f:
		data = f.readlines()
		i = 0
		for line in data:
			if line.startswith('#') == False:
				lineKey = line.split('=')[0]
				lineValue = line.split('=')[1]
				if lineKey == key:
					lineNumber = i
					break
				i += 1
			
	with open('data.txt', 'w') as f:
		data[lineNumber] = "%s=%s" % (key, value)
		f.writelines(data)

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

api = twitter.Api(
	consumer_key=retrieveFromOptions('twitter_consumer_key'),
	consumer_secret=retrieveFromOptions('twitter_consumer_secret'),
	access_token_key=retrieveFromOptions('twitter_access_token_key'),
	access_token_secret=retrieveFromOptions('twitter_access_token_secret'))

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
		status = api.PostUpdate(tweet)
	except:
		pass
	print "Tweet has been tweeted"

def sendYo(username):
	requests.post('http://api.justyo.co/yo/', data={'api_token': retrieveFromOptions('yo_api_token'), 'username': username})
	print "%s has just been yo'd" % username

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
					createGithubIssue(error)
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
				createGithubIssue(error)
				Timer(2, makePhoneCall, [error, retrieveFromOptions('phone_number')]).start()
				sendSlackMessage(error)
				sendTextMessage(error, retrieveFromOptions('phone_number'))
				sendToEvernote(error)
				sendTweet(error)
				sendYo(retrieveFromOptions('yo_username'))
			f.write(error + '\n')

check()
