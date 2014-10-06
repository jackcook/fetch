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


### PREPARE EVERNOTE ###

dev_token = "INSERT_EVERNOTE_DEV_TOKEN_HERE"
notebookguid = ""
noteguid = ""

client = EvernoteClient(token=dev_token)
user_store = client.get_user_store()
note_store = client.get_note_store()
notebooks = note_store.listNotebooks()
notebook_exists = False

with open('data.txt', 'r+') as f:
	for line in f.readlines():
		key = line.split('=')[0]
		value = line.split('=')[1].replace('\n', '')
		if key == 'notebookguid':
			notebookguid = value
			notebook_exists = True
		elif key == 'noteguid':
			noteguid = value

	if notebook_exists == False:
		notebook = Types.Notebook()
		notebook.name = "Errors"
		new_notebook = note_store.createNotebook(dev_token, notebook)
		notebookguid = new_notebook.guid
		f.write('notebookguid=%s\n' % notebookguid)

		note_body = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note></en-note>"""
	
		note = Types.Note()
		note.title = '%s Errors' % socket.gethostname()
		note.notebookGuid = notebookguid
		note.content = note_body
		new_note = note_store.createNote(dev_token, note)
		noteguid = new_note.guid
		f.write('noteguid=%s\n' % noteguid)

### PREPARE TWILIO ###

account_sid = "INSERT_TWILIO_ACCOUNT_SID_HERE"
auth_token = "INSERT_TWILIO_AUTH_TOKEN_HERE"
client = TwilioRestClient(account_sid, auth_token)

### PREPARE TWITTER ###

api = twitter.Api(consumer_key='INSERT_TWITTER_CONSUMER_KEY_HERE', consumer_secret='INSERT_CONSUMER_SECRET_HERE', access_token_key='INSERT_ACCESS_TOKEN_KEY_HERE', access_token_secret='INSERT_ACCESS_TOKEN_SECRET_HERE')

def createGithubIssue(error):
	connection = httplib.HTTPSConnection('api.github.com', 443, timeout = 30)
	headers = {"Authorization":"token INSERT_GITHUB_AUTH_TOKEN_HERE", "user-agent":"python"}
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
	connection.request('GET', '/api/chat.postMessage?token=INSERT_SLACK_TOKEN_HERE&channel=INSERT_CHANNEL_ID_HERE&text=%s&pretty=1&username=Fetch&icon_url=http://104.131.74.5/logo/48.png' % error.replace(' ', '+'), None, {})
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
	requests.post('http://api.justyo.co/yo/', data={'api_token': 'INSERT_YO_API_TOKEN_HERE', 'username': username})
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
					Timer(2, makePhoneCall, [error, 'INSERT_PHONE_NUMBER_HERE']).start()
				if 's' in apis:
					sendSlackMessage(error)
				if 't' in apis:
					sendTextMessage(error, 'INSERT_PHONE_NUMBER_HERE')
				if 'e' in apis:
					sendToEvernote(error)
				if 'T' in apis:
					sendTweet(error)
				if 'y' in apis:
					sendYo('INSERT_YO_USERNAME_HERE')
			else:
				createGithubIssue(error)
				Timer(2, makePhoneCall, [error, 'INSERT_PHONE_NUMBER_HERE']).start()
				sendSlackMessage(error)
				sendTextMessage(error, 'INSERT_PHONE_NUMBER_HERE')
				sendToEvernote(error)
				sendTweet(error)
				sendYo('INSERT_YO_USERNAME_HERE')
			f.write(error + '\n')

check()
