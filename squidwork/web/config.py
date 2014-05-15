"""
Config extension for webapps.
adds the --host and --port arguments to the argparser, and parsing
of host and port from the 'Webapp' section of a config file
"""

from squidwork.config import create_argparser as base_argparser
from squidwork.config import get_config

WEBAPP = 'Webapp'

def create_argparser(**kwargs):
    parser = base_argparser(**kwargs)

    #parser.add_argument('-h', '--host', metavar='HOSTNAME OR IP',
            #help='hostname or ip address to listen on')
    parser.add_argument('-p', '--port',
            help='port to listen on')
    return parser

def get_port(namespace):
    """
    uses the command-line options if supplied, or reads the values
    from the config file.

    We expect webapp settings to be under the Webapp: mapping in the
    YAML config
    """
    data = get_config(namespace.config)
    #host = None
    port = None

    if WEBAPP in data:
        web_settings = data[WEBAPP]
        #if 'host' in web_settings:
            #host = web_settings['host']
        if 'port' in web_settings:
            port = web_settings['port']

    # override with command lien options
    #host = namespace.host or host
    port = namespace.port or port

    # if either are None, throw a value error
    #if host is None:
        #raise ValueError('No hostname supplied in config, or on command line')
    if port is None:
        raise ValueError('No port supplied in config, or on command lin')

    return port
