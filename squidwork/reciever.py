import json

from .routing import Route 
from .message import Message, ENCODING

from zmq import SUBSCRIBE

class Reciever(object):
    """
    Recieves messages of a specific api endpoint on
    a ZeroMQ socket. Subscriptions are prefix-based, and we will
    establish the ZeroMQ-level subscription for you, but do not
    connect() it or anything
    """

    def __init__(self, socket, route=''):
        self.socket = socket
        self._prefix = Route(route)
        # this sets the message masking
        # we always mask by at least 'all' so we wouldn't get
        # non-squidwork ZMQ traffic
        self.socket.set_string(SUBSCRIBE, unicode(Route(route)))
        
    @property
    def prefix(self):
        return self._prefix

    def recieve(self):
        """
        Blocking. gets the next message off the stream
        """
        parts = self.socket.recv_multipart()
        return self.parse_zeromq_parts(parts)

    def parse_zeromq_parts(self, parts):
        """
        parse a multipart ZeroMQ packet into a squidwork message
        """
        # we don't care about the header
        data_str = parts[1].decode(ENCODING)
        data = json.loads(data_str)
        return Message.deserialize(data)

