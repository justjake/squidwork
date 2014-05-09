"""
string finageling
"""
from socket import gethostname

DEFAULT_HOSTNAME = gethostname()
PREFIX = 'all'
SEPERATOR = '/'
HOST_SEPERATOR = '@'


class Route(object):
    """
    An API path
    """
    def __init__(self, path=''):
        self.path = path

        # if we already have the prefix, remove it
        if path.startswith(PREFIX + SEPERATOR):
            self.path=path[len(PREFIX + SEPERATOR):]

        # if we are the prefix, remove everything
        if path == PREFIX:
            self.path = ''

    def __str__(self):
        if self.path:
            return PREFIX + SEPERATOR + self.path
        return PREFIX

    def __repr__(self):
        return '<Route {}>'.format(str(self))


class Origin(object):
    """
    A message origin, containing an API path and a hostname
    """
    def __init__(self, hostname=DEFAULT_HOSTNAME, route=None):
        # enforce starts with 'all'
        if isinstance(route, str):
            route = Route(route)

        self.route = route or Route()
        self.hostname = hostname

    def __str__(self):
        return str(self.route) + HOST_SEPERATOR + self.hostname

    def __repr__(self):
        return '<Origin {}>'.format(str(self))

    @property
    def path(self):
        return self.route.path

    @path.setter
    def set_path(self, new_path):
        self.route.path = new_path

    @classmethod
    def deserialize(cls, string):
        """
        Turns a string'd origin into a real one
        """
        (route, hostname) = string.split(HOST_SEPERATOR)
        route = Route(route)
        return Origin(hostname=hostname, route=route)
