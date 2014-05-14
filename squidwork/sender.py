import json
from datetime import datetime

from .routing import Origin, Route
from .message import TIME_FORMAT, ENCODING, Message

class MessageEncoder(json.JSONEncoder):
    """
    An encoder that knows how to serialize message objects.
    Subclass this encoder if you want to pass in your custom python
    objects instead of only JSON-serializeable things.

    See the JSON docs for more information
    """
    def default(self, obj):
        # messages become a hashmap
        if isinstance(obj, Message):
            return {'content': obj.content,
                    'origin': obj.origin,
                    'time': obj.time}

        # datetimes become the ISO format of datetime
        if isinstance(obj, datetime):
            return obj.strftime(TIME_FORMAT)

        # origins are encoded to the string representations
        if isinstance(obj, Origin):
            return str(obj)

        return super(MessageEncoder, self).default(obj)


class Sender(object):
    """
    Sends messages following the protocol for you
    """

    def __init__(self, socket, route='', hostname='', encoder=None):
        """
        create with a ZeroMQ socket and a name for this endpoint.
        socket: ZeroMQ socket
        app_name: str, something like 'ear/intent'
        encoder: subclass of our MessageEncoder that JSON-encodes
                 your objects
        """
        self.origin = Origin(route=Route(route), hostname=hostname)
        self.socket = socket
        self.encoder = encoder or MessageEncoder

    def send_message(self, message):
        """
        Send a raw message over the socket, unmodified.
        """
        # wee
        data = json.dumps(message, cls=self.encoder).encode(ENCODING)
        origin = str(self.origin).encode(ENCODING)
        self.socket.send_multipart([origin, data], copy=False)
        return message

    def create_message(self, content, origin=None, time=None):
        """
        Create a new message with our origin
        """
        return Message(content, origin=(origin or self.origin),
                time=time)

    def send(self, content, path='', time=None):
        """
        Send JSON content over the wire.
        content: any JSON encodable content to be wrapped in a new Message, 
                 or a pre-pepared Message instance of your own.
        path:    a suffix path, special for this event
        time:    use this time instead of the current time for the message
        """
        m = self.create_message(content, time=time, 
                origin=self.origin.route_to(path))
        return self.send_message(m)

    def send_path(self, path, content):
        return self.send(content, path=path)

    def __repr__(self):
        return 'squidwork.Sender(origin={oi})'.format(
                oi=self.origin)
