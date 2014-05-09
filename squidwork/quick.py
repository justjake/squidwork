from __future__ import print_function
import zmq

"""
the quick package makes writing trivial ZeroMQ pubsub scripts
trivial
"""

print("-- using squidwork quick, create no other contexts --")
"""
just a default context, nothing to see here
"""

context = zmq.Context.instance()

def pub(uri=None):
    """
    create a publish socket, and optionally bind it.
    """
    socket = context.socket(zmq.PUB)
    if uri:
        socket.bind(uri)
    return socket

def sub(uri=None):
    """
    Create a subscribe socket, and optionally connect it.
    """
    socket = context.socket(zmq.SUB)
    if uri:
        socket.connect(uri)
    return socket
