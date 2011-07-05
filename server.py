import urllib
import time
import random
import simplejson
from os import path as op

import tornado.web
import tornado.httpclient
import tornadio
import tornadio.router
import tornadio.server


ROOT = op.normpath(op.dirname(__file__))

participants = {}
new_user = 0

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        new_user = len(participants)
        self.render("index.html", user_id=new_user)

class SocketIOConnection(tornadio.SocketConnection):

    def __init__(self, *args, **kwargs):
        tornadio.SocketConnection.__init__(self, *args, **kwargs)
        self.user_id = new_user

    def on_open(self, *args, **kwargs):
        print "New Client"
        
        if participants:
            for user_id,participant in participants.iteritems():
                message = ["new_client", user_id]
                self.send(simplejson.dumps(message))
        
        message = ["new_client", new_user]
        for user_id,participant in participants.iteritems():
            participant.send(simplejson.dumps(message))
            
        participants[new_user] = self

    def on_close(self):
        del participants[self.user_id]
        #participants.remove(self)
        
    def on_message(self, message):
        user_id, text = message.split(" ", 1)
        for user_id,participant in participants.iteritems():
            participant.send(simplejson.dumps([user_id, text]))


if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    SocketIOConnectionRouter = tornadio.get_router(SocketIOConnection)

    #configure the Tornado application
    application = tornado.web.Application(
        [(r"/", IndexHandler), SocketIOConnectionRouter.route()],
        static_path = op.join(ROOT, "static"),
        enabled_protocols = ['websocket',
                             'flashsocket',
                             'xhr-multipart',
                             'xhr-polling'],
        flash_policy_port = 843,
        flash_policy_file = op.join(ROOT, 'flashpolicy.xml'),
        socket_io_port = 8001,
        
    )
    tornadio.server.SocketServer(application)
    io_loop = tornado.ioloop.IOLoop.instance()
    io_loop.start()

