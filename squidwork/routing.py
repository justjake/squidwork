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
        path = str(path)
        self.path = path

        # if we already have the prefix, remove it
        if path.startswith(PREFIX + SEPERATOR):
            self.path=path[len(PREFIX + SEPERATOR):]

        # if we are the prefix, remove everything
        if path == PREFIX:
            self.path = ''

    def __str__(self):
        """
        >>> str(Route())
        'all'

        >>> str(Route('all'))
        'all'

        >>> str(Route('some/route'))
        'all/some/route'

        >>> str(Route('all/some/route'))
        'all/some/route'
        """
        if self.path:
            return PREFIX + SEPERATOR + self.path
        return PREFIX

    def route_to(self, suffix):
        """
        return a route from this route to the suffix

        >>> str(Route('root/path').route_to('sub/path'))
        'all/root/path/sub/path'

        >>> str(Route('root/path').route_to('/'))
        'all/root/path'
        """
        if suffix == '' or suffix == SEPERATOR:
            return Route(str(self))

        return Route(self.path + SEPERATOR + suffix)

    def __repr__(self):
        return '<Route {}>'.format(str(self))

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

class Origin(object):
    """
    A message origin, containing an API path and a hostname
    """
    def __init__(self, hostname=DEFAULT_HOSTNAME, route=None):
        # enforce starts with 'all'
        if not isinstance(route, Route):
            route = Route(route)

        self.route = route or Route()
        self.hostname = hostname or DEFAULT_HOSTNAME

    def __str__(self):
        """
        >>> str(Origin('some.host'))
        'all@some.host'

        >>> str(Origin('some.host', Route('some/path')))
        'all/some/path@some.host'
        """
        return str(self.route) + HOST_SEPERATOR + self.hostname

    def __repr__(self):
        return '<Origin {}>'.format(str(self))

    def route_to(self, suffix):
        return Origin(hostname=self.hostname, 
                route=self.route.route_to(suffix))

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


if __name__ == '__main__':
    import doctest
    doctest.testmod()
