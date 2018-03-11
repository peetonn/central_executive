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
        tornado.web.Application.__init__(self, handlers)
        
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
        
class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        global modules
        module = self.get_argument('module')
        if module:
            if module in modules:
                lastCheckTs = modules[module]['ts']
                status = modules[module]['status']
                code = modules[module]['code']
                self.finish(json.dumps({'last_alive':timestampMs()-lastCheckTs,\
                                        'status': status,\
                                        'code': code}))
                return
        self.finish(json.dumps({'status': 'not found'}))

def udpDataWatcher(moduleName, port):
    global modules
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", port))
    fcntl.fcntl(s, fcntl.F_SETFL, os.O_NONBLOCK)
    s.settimeout(1)
    modules[moduleName] = { 'ts': timestampMs(), 'status':'no data', 'code':-1 }
    print("Watching " + moduleName + ". Waiting on port:" + str(port))
    while active:
        try:
            data, addr = s.recvfrom(8192)
            data = data.rstrip("\0")
            modules[moduleName] = { 'ts':timestampMs(), 'status':'ok', 'code': 0 }
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                modules[moduleName] = { 'ts':timestampMs(), 'status':'no data', 'code': -1 }
                sleep(1)

def webServiceWatcher(moduleName, url):
    print("Watching "+ moduleName +". URL: "+url)

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('--checkpoint', type=str,
                        dest='checkpoint_dir',
                        help='dir or .ckpt file to load checkpoint from',
                        metavar='CHECKPOINT', required=True)

    parser.add_argument('--in-path', type=str,
                        dest='in_path',help='dir or file to transform',
                        metavar='IN_PATH', required=True)

    help_out = 'destination (dir or file) of transformed file or files'
    parser.add_argument('--out-path', type=str,
                        dest='out_path', help=help_out, metavar='OUT_PATH',
                        required=True)

    parser.add_argument('--device', type=str,
                        dest='device',help='device to perform compute on',
                        metavar='DEVICE', default=DEVICE)

    parser.add_argument('--batch-size', type=int,
                        dest='batch_size',help='batch size for feedforwarding',
                        metavar='BATCH_SIZE', default=BATCH_SIZE)

    parser.add_argument('--allow-different-dimensions', action='store_true',
                        dest='allow_different_dimensions', 
                        help='allow different image dimensions')

    return parser

def check_opts(opts):
    exists(opts.checkpoint_dir, 'Checkpoint not found!')
    exists(opts.in_path, 'In path not found!')
    if os.path.isdir(opts.out_path):
        exists(opts.out_path, 'out dir not found!')
        assert opts.batch_size > 0

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
