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

    def __init__(self, socket, route='', encoder=None):
        """
        create with a ZeroMQ socket and a name for this endpoint.
        socket: ZeroMQ socket
        app_name: str, something like 'ear/intent'
        encoder: subclass of our MessageEncoder that JSON-encodes
                 your objects
        """
        self.origin = Origin(route=Route(route))
        self.socket = socket
        self.encoder = encoder or MessageEncoder

    def send(self, content, time=None):
        """
        Send JSON content over the wire.
        content: any JSON encodable content to be wrapped in a new Message, 
                 or a pre-pepared Message instance of your own.
        time:    override time with this value.
        """
        # don't wrap messages!
        if isinstance(content, Message):
            m = content
        else:
            # create message, time of time now
            m = Message(content, origin=self.origin)

        # override time if requested
        if time:
            m.time = time

        # wee
        data = json.dumps(m, cls=self.encoder).encode(ENCODING)
        origin = str(self.origin).encode(ENCODING)
        self.socket.send_multipart([origin, data], copy=False)
