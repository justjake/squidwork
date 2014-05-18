import argparse
import yaml
from urlparse import urlparse
from urllib2 import urlopen
from pprint import pprint as pp

from .service import import_data


def create_argparser(**kwargs):
    """
    An option parser with the config option
    """
    opts = dict(
        description="ZeroMQ service with yaml configuration file")
    opts.update(kwargs)

    parser = argparse.ArgumentParser(**opts)
    parser.add_argument('-c', '--config', metavar='PATH', required=True,
                        help='YAML file with service definitions,'
                        'supports http')
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


def get_services(namespace):
    """
    gets all the services from the command-line options.
    """
    config = get_config(namespace.config)
    services = import_data(config)
    return services




def main():
    print "Getting all services..."
    pp(get_services())


if __name__ == '__main__':
    main()
