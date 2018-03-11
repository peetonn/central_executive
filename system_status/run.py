# -*- coding: utf-8 -*-
from __future__ import print_function
import os, sys, signal
sys.path.insert(0, 'src')

# adding import path for the directory above this sctip (for deeplab modules)
myPath = os.path.dirname(sys.argv[0])
rootPath = os.path.join(myPath,'..')
uploadPath =  os.path.join(rootPath, "upload")
resultsPath = os.path.join(rootPath, "results")
modelsDir = os.path.join(rootPath, 'ce-models');

sys.path.append(rootPath)

import socket
import fcntl
import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
import uuid
from tornado.options import define, options
from Queue import Queue
from threading import Thread
from datetime import datetime
import re
import time
import datetime
import time
import json
import subprocess
import numpy
import glob
import tornado
import errno

port = 8080
active = True
modules = {}

#******************************************************************************
def timestampMs():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/status", StatusHandler)
        ]
        settings = dict(
            static_path=os.path.join(os.path.dirname(__file__), "static")
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
        
class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        global modules
        module = self.get_argument('module')
        if module:
            if module in modules:
                status = modules[module]
                lastCheckTs = modules[module]['ts']
                status['last_alive'] = timestampMs()-lastCheckTs
                self.finish(json.dumps(status))
                return
        self.finish(json.dumps({'status': 'not found'}))

def statusOk():
    return { 'ts':timestampMs(), 'status':'ok', 'code': 0, 'face': '٩(^‿^)۶' }

def statusNodata():
    return { 'ts': timestampMs(), 'status':'no data', 'code':-1, 'face': 'ε(´סּ︵סּ`)з' }

def statusError(err, msg):
    return { 'ts': timestampMs(), 'status':'error', 'code':err, 'msg': msg, 'face': '(╥﹏╥)' }


def udpDataWatcher(moduleName, port):
    global modules
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", port))
    fcntl.fcntl(s, fcntl.F_SETFL, os.O_NONBLOCK)
    s.settimeout(1)
    modules[moduleName] = statusNodata()
    print("Watching " + moduleName + ". Waiting on port:" + str(port))
    while active:
        try:
            data, addr = s.recvfrom(8192)
            data = data.rstrip("\0")
            modules[moduleName] = statusOk()
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                modules[moduleName] = statusNodata()
                sleep(1)

def webServiceWatcher(moduleName, url):
    print("Watching "+ moduleName +". URL: "+url)
    modules[moduleName] = statusNodata()

####
def signal_handler(signum, frame):
    global active
    print('Received stop signal, exiting...')
    tornado.ioloop.IOLoop.instance().stop()
    active = False

def main():
    signal.signal(signal.SIGINT, signal_handler)
    watchers = {}
    watchers['opt'] = Thread(target=udpDataWatcher, args=('opt', 21234,))
    watchers['om'] = Thread(target=udpDataWatcher, args=('om', 21235,))
    watchers['segmenter'] = Thread(target=webServiceWatcher, args=('segmenter', 'test',))
    watchers['styler'] = Thread(target=webServiceWatcher, args=('styler', 'test',))

    for k in watchers:
        watchers[k].start()

    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

    for k in watchers:
        watchers[k].join()

if __name__ == "__main__":
    main()
