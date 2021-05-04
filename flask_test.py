#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  4 12:25:01 2021

@author: nickj
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

import time, threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def hello_world():    
    return render_template('flask.html')

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    # emit('my response', str(time.time()))

class Emitter:
    def __init__(self):
        self.emitter = threading.Thread(target=self.emit)
        self.emitter.start()
    def emit(self):
        while(True):
            socketio.emit('my response', str(time.time()))
            time.sleep(1)

if __name__ == '__main__':
    emitter = Emitter()
    socketio.run(app, host='0.0.0.0', port=1234, debug=True)