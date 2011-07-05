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

participants = set()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", user_id="1")

class SocketIOConnection(tornadio.SocketConnection):

    def on_open(self, *args, **kwargs):
        print "New Client"
        participants.add(self)

    def on_close(self):
        participants.remove(self)
        
    def on_message(self, message):
        print str(message).split(" ")
        for p in participants:
            p.send(simplejson.dumps(message))


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

