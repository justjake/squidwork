from .mapping import ManyToMany

# a is prefixes
# b is URIs
_prefix_to_uri = ManyToMany()


class Service(object):
    """
    service API route prefix, and the ZeroMQ uri(s) to find it at.

    Currently the library of possible services is global, although
    this may change if anyone wants to do multiple independent config
    file things.
    """
    def __init__(self, prefix, *uris):
        if len(uris) == 0:
            raise ValueError('Service must have a prefix')

        for uri in uris:
            _prefix_to_uri.assoc(prefix, uri)

        self._prefix = prefix
        self._URIs = _prefix_to_uri.subscript_a(prefix)

    @property
    def prefix(self):
        return self._prefix

    @property
    def URIs(self):
        return frozenset(self._URIs)

    def add_uri(self, uri):
        """
        Add another URI to a service
        """
        _prefix_to_uri.assoc(self.prefix, uri)

    def __repr__(self):
        return "Service({prefix}, {uri})".format(
            uri=", ".join(list(self.URIs)),
            prefix=repr(self.prefix))

    @classmethod
    def for_exact_prefix(cls, prefix):
        """
        Find the service with the given exact prefix
        """
        if not _prefix_to_uri.has_a(prefix):
            return None
        # gets a random URI already associated with this prefix,
        # because we end up getting all of them anyways during
        # construction.
        some_uri = list(_prefix_to_uri.subscript_a(prefix))[0]
        return cls(prefix, some_uri)

    @classmethod
    def for_prefix(cls, prefix):
        """
        returns all the Services who's prefixes match
        the given prefix, ie, for_prefix('') will match
        all Services
        """
        return [cls.for_exact_prefix(p)
                for p in _prefix_to_uri.As()
                if p.startswith(prefix)]

    @classmethod
    def all_for_uri(cls, uri):
        """
        Find all the services that bind the given URI
        """
        if not _prefix_to_uri.has_b(uri):
            return None
        prefixes = list(_prefix_to_uri.subscript_b(uri))
        return [cls(p, uri) for p in prefixes]


def import_data(data):
    """
    Imports all the service entries in a data dump
    for example, a YAML file should look like

    Services
        - route: ear
          uris:
            - tcp://192.168.0.201:9000
        - route: darksouls
          uris:
            - tcp://192.168.0.205:9000
    """
    KEY = 'Services'

    if KEY not in data:
        raise ValueError('config data does not contain key {}'.format(KEY))

    data = data[KEY]

    if not isinstance(data, list):
        raise ValueError('config data not a list: {}'.format(data))

    return [Service(s['prefix'], *(s['uris'])) for s in data]
