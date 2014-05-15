"""
Config extension for webapps.
adds the --host and --port arguments to the argparser, and parsing
of host and port from the 'Webapp' section of a config file
"""

from squidwork.config import create_argparser as base_argparser
from squidwork.config import get_config, get_services


WEBAPP = 'Webapp'


def create_argparser(**kwargs):
    """
    creates an argparser with all the options needed for web things
    (namely, adds the --port flag)
    """
    parser = base_argparser(**kwargs)

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
    port = None

    if WEBAPP in data:
        web_settings = data[WEBAPP]
        if 'port' in web_settings:
            port = web_settings['port']

    # override with command lien options
    port = namespace.port or port

    # if either are None, throw a value error
    if port is None:
        raise ValueError('No port supplied in config, or on command lin')

    return port
