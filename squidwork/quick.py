from __future__ import print_function
import zmq
from urlparse import urlparse
from socket import gethostbyname

"""
the quick package makes writing trivial ZeroMQ pubsub scripts trivial.
"""

context = zmq.Context.instance()


def resolve_hostname(uri):
    """
    turns a hostname-based TCP uri into a IP-based URI, because ZeroMQ can't
    bind() to a hostname for some reason
    """
    if not uri.startswith('tcp://'):
        return uri

    host, port = urlparse(uri).netloc.split(':')
    return 'tcp://{ip}:{port}'.format(ip=gethostbyname(host), port=port)


def pub(*uris):
    """
    create a publish socket, and optionally bind it.
    resolves hostnames automatically
    """
    socket = context.socket(zmq.PUB)
    for u in uris:
        socket.bind(resolve_hostname(u))
    return socket


def sub(*uris):
    """
    Create a subscribe socket, and optionally connect it.
    """
    socket = context.socket(zmq.SUB)
    for u in uris:
        socket.connect(u)
    return socket
