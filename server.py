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
        
class ClientCollection:
    
    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    @classmethod
    def initialized(cls):
        return hasattr(cls, "_instance")
    
    def __init__(self):
        self.users = {}
    
    def add(self, name, client):
        success = False
        if name not in self.users:
            self.users[name] = client
            success = True
            
        return success
    
    def remove(self, name):
        if name in self.users:
            del self.users[name]    
        
    def get_clients(self, omitt_name):
        clients = []
        for name, client in self.users.iteritems():
            if name != omitt_name:
                clients.append((name, client))
        return clients
        
        
class ChatRoomHandler(tornado.web.RequestHandler):
    def get(self):
        username = self.get_argument("username", default="not-set", strip=True)
        self.render("chatroom.html", username=username)
        
        
class PortalHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("portal.html")


class SocketIOConnection(tornadio.SocketConnection):

    def __init__(self, *args, **kwargs):
        tornadio.SocketConnection.__init__(self, *args, **kwargs)
        self.username = None

    def on_open(self, *args, **kwargs):
        print "New Client"

    def on_close(self):
        client_collection = ClientCollection.instance()
        clients = client_collection.get_clients(self.username)
        for name, client in clients:
            client.send({"remove_client": self.username})
        
        client_collection.remove(self.username)
        
    def on_message(self, message):
        print message
        client_collection = ClientCollection.instance()
        
        if "new_user" in message:
            username = message["new_user"]
            client_collection.add(username, self)
            clients = client_collection.get_clients(username)
            
            for name, client in clients:
                # Add existing clients to this current one
                self.send({"new_client": name})
                
                # Send the the current new client to all existing ones
                client.send({"new_client": username})
            self.username = username
            
        elif "new_message" in message and self.username:
            clients = client_collection.get_clients(self.username)
            for name, client in clients:
                client.send(message)

if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    SocketIOConnectionRouter = tornadio.get_router(SocketIOConnection)

    #configure the Tornado application
    application = tornado.web.Application(
        [(r"/", PortalHandler),
        (r"/portal.html", PortalHandler),
        (r"/chatroom.html", ChatRoomHandler),
        SocketIOConnectionRouter.route()],
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

