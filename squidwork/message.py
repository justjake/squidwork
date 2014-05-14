from socket import gethostname
from datetime import datetime

from .routing import Origin

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
ENCODING = 'utf-8'

class Message(object):
    """
    a message we will send over the wire as part of our protocol
    we want at least 3 properties for all messages, so that they
    can be easily routed and filtered from client apps

    time:   time at which the message data was *generated*; when the
            event actually occured, not when the message was sent
            or recieved.

    origin: where the message originates from, in app/endpoint/path@host.name
            format.

    content: some JSON-serializable content. Refer to Python's stdlib docs
             for what qualifies.
    """
    def __init__(self, content, origin='', time=None):
        self.origin = origin or build_origin(origin)
        self.time = time or datetime.now()
        self.content = content

    def __str__(self):
        return "<Message from {origin} at {time}: {content}>".format(
                    origin=self.origin,
                    time=self.time.isoformat(),
                    content=str(self.content))

    def __repr__(self):
        return "squidwork.Message({content}, {origin}, {time})".format(
                content=repr(self.content),
                origin=repr(self.origin),
                time=repr(self.time))

    @property
    def path(self):
        """
        The API endpoint this message comes from. Note that not starting
        a route with PREFIX will prevent default handlers from catching it.
        """
        return self.origin.route.path

    @classmethod
    def deserialize(cls, json_map):
        """
        Deserialize a JSON map of a message into a Messsage instance
        """
        if ('content' in json_map and 'origin' in json_map and 
            'time'    in json_map):
            return cls(json_map['content'], 
                    time=datetime.strptime(json_map['time'], TIME_FORMAT),
                    origin=Origin.deserialize(json_map['origin']))
        raise ValueError('Could not decode {} as {}'.format(str(json_map), str(cls)))
