#!/usr/bin/env python
import os
import sys

def retrieveFromOptions(key):
    with open('options.txt', 'r+') as f:
        for line in f.readlines():
            lineKey = line.split(' = ')[0]
            lineValue = line.split(' = ')[1].replace('\n', '')
            if lineKey == key:
                if lineValue != "XXXXXXXXXX":
                    return lineValue
    return None

def setOption(key, value):
    data = None
    lineNumber = 0
    with open('options.txt', 'r') as f:
        data = f.readlines()
        i = 0
        for line in data:
            if line.startswith('#') == False:
                lineKey = line.split(' = ')[0]
                lineValue = line.split(' = ')[1]
                if lineKey == key:
                    lineNumber = i
                    break
                i += 1
            
    with open('options.txt', 'w') as f:
        data[lineNumber] = "%s = %s\n" % (key, value)
        f.writelines(data)

import api
import error