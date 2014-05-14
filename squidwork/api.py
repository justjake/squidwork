"""
Mutli-headed routes.
may be overkill and too complicated, this is one of those
things that I'd write a "dsl" for in Ruby just because it's fun
to do meta-programming things
"""

from .routing import Route
from .sender import Sender

class GenericAPI(object):
    """
    An API is an object that manages multiple senders
    bound to one socket, so that it's easy to standardize
    and send to multiple paths as part of program flow.

    Specialized API classes should be created with the API
    function below.
    """

    # this should be re-defined by subclasses
    root = Route()

    def __init__(self, socket):
        self.socket = socket
        self.cache = {}
        self.sender = Sender(self.socket, self.root)

    @property
    def prefix(self):
        return self.root.path

def API(root, **routes):
    """
    Create a new API class for your application.
    'root' shoudl be your base route, and **routes
    is a mapping of route-shortname -> path suffix for your
    API.

    Example:

    >>> FooAPI = API(Route('com/jake/foo'),
        now='done/now',
        later='done/later',
        free='cost/free',
        exp='cost/expensive')
    >>> api = FooAPI(pub('tcp://172.0.0.1:9999'))
    >>> api.now.send(['foo', 'bar'])
    """

    # this creats a dict of properties that create Senders for
    # all the friendly name --> suffix combidantions passed in
    props = {'root': Route(root)}
    for (short, path) in routes.iteritems():
        props[short] = lambda self, content: self.sender.send_path(path, content)

    return type('API', (GenericAPI,), props)
