from __future__ import print_function
import zmq

"""
the quick package makes writing trivial ZeroMQ pubsub scripts
trivial
"""

context = zmq.Context.instance()

def pub(*uris):
    """
    create a publish socket, and optionally bind it.
    """
    socket = context.socket(zmq.PUB)
    for u in uris:
        socket.bind(u)
    return socket

def sub(*uris):
    """
    Create a subscribe socket, and optionally connect it.
    """
    socket = context.socket(zmq.SUB)
    for u in uris:
        socket.connect(u)
    return socket
