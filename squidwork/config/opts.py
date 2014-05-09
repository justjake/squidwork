import argparse
import yaml
from urlparse import urlparse
from urllib2 import urlopen
from pprint import pprint as pp

from .service import import_yaml_data

def create():
    """
    An option parser with the config option
    """
    parser = argparse.ArgumentParser(description="ZeroMQ service with yaml configuration file")
    parser.add_argument('-c', '--config', metavar='PATH', required=True,
            help='YAML file with service definitions, supports http')
    return parser

def get_config(location):
    """
    Returns the data of the config file at the location
    """
    o = urlparse(location)

    if o.scheme == 'http' or o.scheme == 'https':
        f = urlopen(location)
    else:
        f = open(location)

    return yaml.safe_load(f)

def get_services():
    parser = create()
    args = parser.parse_args()
    config = get_config(args.config)
    services = import_yaml_data(config)
    return services

if __name__ == '__main__':
    main()
