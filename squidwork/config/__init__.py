"""
squidwork.config provies a unified interface to command line arguments and
the squidwork YAML configuration file. Please see the example config file
conf2.yml for a detail description of the configuration file format.

basically it's YAML that looks like this:

conf-version: 2
services:
    some-name:
        routes:
            - hi
            - another/route
        uris:
            tcp://love.gov:6969
    another-name
        routes:
            - hi
            - another/route
        uris:
            tcp://hate.co.nz:6969
"""

__author__ = 'Jake Teton-Landis'

from squidwork.routing import Route
from squidwork.config.service import Service, ConfigError

import argparse

# required for load_yaml
import yaml
from urllib2 import urlopen
from urlparse import urlparse


def load_yaml(location):
    """
    loads YAML from a local file or an HTTP uri. Used to load the config file
    in Config#retrieve()
    """
    o = urlparse(location)

    if o.scheme == 'http' or o.scheme == 'https':
        f = urlopen(location)
    else:
        f = open(location)

    return yaml.safe_load(f)


class ValueFromConfig(object):
    def __str__(self):
        return 'VALUE_FROM_CONFIG'

    def __repr__(self):
        return str(self)


class Config(object):
    """
    Unified command line argument and configuration file loader. Abstracts
    over argparse and config file direct access. Uses argparse to create the
    command-line interface, and you may pass kwargs through to the
    ArgumentParser when instantiating a new Config.

    Define options that your app requires using the `option` method, and then
    retrieve command line args and load the config file with the `retrieve`
    method.

    After calling `Config#retrieve` you may access your config options as
    dot-properties of the config object. Retrieve the configuration will also
    populate the Service index, see squidwork.config.service for more
    information

    Usage example:

    >>> config = Config('my app')
    >>> config.option('dog-name')

    Config#option passes args through to 
    >>> config.option('threshold', type=float, help="sound level b4 scolding")
    >>> config.retrieve()

    Dashed option names are python-ized by replacing each - with a _
    >>> dog = Dog(name=config.dog_name)

    see test/beeper.py for a concrete usage example
    """

    VALUE_FROM_CONFIG = ValueFromConfig()

    def __init__(self, name=None, **kwargs):
        options = {}
        if name:
            options.update(dict(prog=name))
        options.update(kwargs)

        self.parser = argparse.ArgumentParser(**options)
        self.parser.add_argument('-c', '--config', required=True,
            help=('YAML file with service definitions. Local path or an '
                  'HTTP(S) URI'))
        self.parser.add_argument('-n', '--name', required=True,
            help='service definition name to load from the config file')

        self._options = set()

    def option(self, key, **kwargs):
        """
        define a new option for your program. Options are either read from
        the command line using argparse, or from the config file service
        definition.

        all options are required to be defined eventually, and cannot have
        default values.

        options not defined using this method will be availible from
        self.raw_config once the config file has been loaded.

        kwargs will be passed to argparse#add_argument, so you may specify
        command-line help
        """
        if key in self._options:
            return

        # default values are unsupported
        if 'default' in kwargs:
            print ('Config warning: default options are not supported. Please'
                   ' use a config file instead.')
            del kwargs['default']

        default_kwargs = dict(default=self.VALUE_FROM_CONFIG)
        default_kwargs.update(kwargs)

        self.parser.add_argument('--' + key, **default_kwargs)
        self._options.add(key)
        return self

    def retrieve(self, args=None):
        """
        parse command line args, load config file
        """
        if args is None:
            # from sys.argv
            ns = self.parser.parse_args()
        else:
            # as provided
            ns = self.parser.parse_args(args)
        raw = load_yaml(ns.config)

        if 'services' not in raw:
            raise ConfigError('no `services` block in config file')

        if ns.name not in raw['services']:
            raise ConfigError(
                'service `{}` not among {} in config file'.format(ns.name,
                    raw['services'].keys()))

        # put all defined options into loaded_opts, and then raise an exception
        # if we wanted something but it wasn't in the args or the conf
        svc = raw['services'][ns.name]
        loaded_opts = {}
        not_given = []
        for opt in self._options:
            python_name = opt.replace('-', '_')
            if opt in svc:
                loaded_opts[python_name] = svc[opt]
            # we use this dummy VALUE_FROM_CONFIG because it's to-string method
            # tells the user that the item will come from config, and it's
            # better than using None, which could possibly be specified on the
            # command line (???)
            if python_name in ns and ns.__dict__[python_name] is not self.VALUE_FROM_CONFIG:
                loaded_opts[python_name] = ns.__dict__[python_name]

            # it's an error if a required options wasn't defined in either the
            # args or the config file, but we want to note all such errors
            if python_name not in loaded_opts or (
                    loaded_opts[python_name] is self.VALUE_FROM_CONFIG):
                not_given.append(opt)

        if len(not_given) > 0:
            raise ValueError(("Options not defined: {omitted} in args {args}"
                " or conf {cfg}").format(omitted=", ".join(not_given),
                                         args=ns,
                                         cfg=svc))

        self.__dict__.update(loaded_opts)
        self.raw_config = raw
        self.raw_service = svc

        # handle service definition things
        Service.import_config_data(raw)
        if 'uris' in svc:
            self.uris = set(svc['uris'])
        if 'routes' in svc:
            self.routes = set([Route(r) for r in svc['routes']])

        return self
