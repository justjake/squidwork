"""
squidwork.config provies three things:

    - an optparse constructor with one parameter, -c | --config
    - a simple YAML format for defining ZeroMQ publishers and 
      thier possible routes,
    - a load function that understands HTTP so you can load such
      a config file off a central server to all possible consumers
      on your network

Basically the design for the whole package is me iterating through all
the things I'd need to get two publishers on the network without
having to juggle more than one config file.
"""

__author__ = 'Jake Teton-Landis'

from .opts import create, get_services
from .service import Service
