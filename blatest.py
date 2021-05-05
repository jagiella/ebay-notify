#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  4 12:25:01 2021

@author: nickj
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import eventlet 
eventlet.monkey_patch() 

import time, threading

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SECRET_KEY'] = b'_5#y2L"F4Q8z\n\xec]/'
socketio = SocketIO(app)

@app.route('/')
def hello_world():    
    return render_template('flask.html')

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    emit('my response', str(time.time()))

class Emitter:
    def __init__(self, socketio):
        self.socketio = socketio
        self.emitter = threading.Thread(target=self.emit)
        self.emitter.start()
        
    # @socketio.on('my response', namespace='/')    
    def emit(self):
        while(True):
            print('emit')
            # self.socketio.emit('my response', 'bla '+str(time.time()))
            socketio.emit('my response', 'bla '+str(time.time()))
            time.sleep(5)

if __name__ == '__main__':
    emitter = Emitter(socketio)
    socketio.run(app, host='0.0.0.0', port=1234, debug=True)