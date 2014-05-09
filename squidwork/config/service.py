# map from prefix aka name -> Service
services = {}

class Service(object):
    """
    service API route prefix and the ZeroMQ uri to find it at
    """
    def __init__(self, uri, prefix=''):
        self._prefix = prefix
        self.uri = uri
        services[prefix] = self

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def set_prefix(self, new_prefix):
        del services[self._prefix]
        self._prefix = new_prefix
        services[new_prefix] = self


    def __repr__(self):
        return "Service({uri}, {prefix})".format(
                uri=repr(self.uri), prefix=repr(self.prefix))

    @classmethod
    def all(cls):
        """
        all the services
        """
        return services.values()

    @classmethod
    def for_prefix(cls, prefix):
        if prefix in services:
            return services[prefix]
        return None

def import_yaml_data(data):
    """
    Imports all the service entries in a YAML data dump
    YAML file should look like

    Services
        - route: ear
          uri:   tcp://192.168.0.201:9000
        - route: darksouls
          uri:   tcp://192.168.0.205:9000
    """
    if 'Services' not in data:
        return None

    data = data['Services']

    if not isinstance(data, list):
        return None

    return [Service(s['uri'], s['prefix']) for s in data]

