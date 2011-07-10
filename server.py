import logging
from os import path as op

import tornado.web
import tornadio
import tornadio.server

FLASH_POLICY_PORT = 843
WEB_SERVER_PORT = 8001

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
    
    def get_client_names(self):
        return self.users.keys()
        
        
class ChatRoomHandler(tornado.web.RequestHandler):
    def get(self):
        username = self.get_argument("username", default=None, strip=True)
        client_names = ClientCollection.instance().get_client_names()
        
        # Make sure the username doesn't already exist
        if username and username not in client_names:
            self.render("chatroom.html", username=username)
        else:
            self.render("portal.html")
        
        
class PortalHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("portal.html")


class SocketIOConnection(tornadio.SocketConnection):
    def __init__(self, *args, **kwargs):
        tornadio.SocketConnection.__init__(self, *args, **kwargs)
        self.username = None

    def on_open(self, *args, **kwargs):
        pass

    def on_close(self):
        client_collection = ClientCollection.instance()
        clients = client_collection.get_clients(self.username)
        for name, client in clients:
            client.send({"remove_client": self.username})
        
        client_collection.remove(self.username)
        
    def on_message(self, message):
        client_collection = ClientCollection.instance()
        
        if "new_user" in message:
            username = message["new_user"]
            client_collection.add(username, self)
            clients = client_collection.get_clients(username)
            
            for name, client in clients:
                # Add existing clients to this new one
                self.send({"new_client": name})
                
                # Send this new client to all existing ones
                client.send({"new_client": username})
            self.username = username
            
        elif "new_message" in message and self.username:
            clients = client_collection.get_clients(self.username)
            for name, client in clients:
                client.send(message)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.WARNING)
    root_dir = op.normpath(op.dirname(__file__))
    static_path = op.join(root_dir, "static")
    
    SocketIOConnectionRouter = tornadio.get_router(SocketIOConnection)

    # Configure the Tornado application
    application = tornado.web.Application(
        [(r"/favicon.ico", tornado.web.StaticFileHandler, {"path":static_path}),
        (r"/", PortalHandler),
        (r"/portal.html", PortalHandler),
        (r"/chatroom.html", ChatRoomHandler),
        SocketIOConnectionRouter.route()],
        static_path = static_path,
        enabled_protocols = ['websocket',
                             'flashsocket',
                             'xhr-multipart',
                             'xhr-polling'],
        flash_policy_port = FLASH_POLICY_PORT,
        flash_policy_file = op.join(root_dir, 'flashpolicy.xml'),
        socket_io_port = WEB_SERVER_PORT,
    )
    
    tornadio.server.SocketServer(application)
    tornado.ioloop.IOLoop.instance().start()

