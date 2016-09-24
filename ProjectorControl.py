#!/usr/bin/env python
""" fauxmo_minimal.py - Fabricate.IO

    This is a demo python file showing what can be done with the debounce_handler.
    The handler prints True when you say "Alexa, device on" and False when you say
    "Alexa, device off".

    If you have two or more Echos, it only handles the one that hears you more clearly.
    You can have an Echo per room and not worry about your handlers triggering for
    those other rooms.

    The IP of the triggering Echo is also passed into the act() function, so you can
    do different things based on which Echo triggered the handler.
"""

import fauxmo
import logging
import time
import serial
import subprocess
import os
import sys
import rxv

from debounce_handler import debounce_handler
logging.basicConfig(level=logging.DEBUG)

serialConnection = serial.Serial("/dev/ttyUSB0", 115200)
global OnCommand, OffCommand
OnCommand = "0614000400341100005D"
OffCommand = "0614000400341101005E"

def convertHex(command):
    output = ''
    while command:
        part = command[:2]
        output += ('\\x' + part).decode('string_escape')
        command = command[2:]
    return output

class device_handler(debounce_handler):
    """Publishes the on/off state requested,
       and the IP address of the Echo making the request.
    """
    TRIGGERS = {"projector": 52000, "speakers": 53000, "git": 54000, "input":55000}

    def act(self, client_address, name, state):
        print "Name", name, "State", state, "from client @", client_address
        rx = rxv.RXV("http://dentw04tc-c-107.dental.nyu.edu/YamahaRemoteControl/ctrl", "RX-A830")
        if(name == "projector"):
            if(state == True):
                command = convertHex(OnCommand)
                serialConnection.write(command)
                rx.input = "HDMI1"
                rx.volume = -10
            elif (state == False):
                command = convertHex(OffCommand)
                serialConnection.write(command)
                rx.input = "AirPlay"
                rx.volume = -30
        if(name == "git"):
            if(state == True):
                subprocess.call(['git pull'], shell=True)
                exit()
            elif(state == False):
                print "Figure out what to do with this"
        if(name == "speakers"):
            if(state == True):
                rx.on = True
            elif(state == False):
                rx.on = False
        if(name == "input"):
            Inputs = [i for i in rx.inputs()]
            i = Inputs.index(rx.input)
            if(state == True):
                if (Inputs[i] == Inputs[-1]):
                    rx.input = Inputs[0]
                else:
                    rx.input = Inputs[i+1]
                i += 1
            elif(state == False):
                if (i == 0):
                    rx.input = Inputs[-1]
                else:
                    rx.input = Inputs[i-1]
                i += 1
        return True

if __name__ == "__main__":
    # Startup the fauxmo server
    fauxmo.DEBUG = True
    p = fauxmo.poller()
    u = fauxmo.upnp_broadcast_responder()
    u.init_socket()
    p.add(u)

    # Register the device callback as a fauxmo handler
    d = device_handler()
    for trig, port in d.TRIGGERS.items():
        fauxmo.fauxmo(trig, u, p, None, port, d)

    # Loop and poll for incoming Echo requests
    logging.debug("Entering fauxmo polling loop")
    while True:
        try:
            # Allow time for a ctrl-c to stop the process
            p.poll(100)
            time.sleep(0.1)
        except Exception, e:
            logging.critical("Critical exception: " + str(e))
            break
