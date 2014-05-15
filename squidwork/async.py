"""
contains an async implementation of Reciver,
AsyncReciver, that can be used with the Tornado event loop
"""
from zmq.eventloop.zmqstream import ZMQStream
import zmq.eventloop.ioloop
zmq.eventloop.ioloop.install()

from squidwork import Reciever

class AsyncReciever(Reciever):
    """
    similar to Reciever, except you can bind a callback using the
    on_recieve method that will fire as soon as the socket recieves
    a message.

    See `on_recieve`
    """

    def __init__(self, socket, origin=''):
        super(type(self), self).__init__(socket, origin)
        self.stream = ZMQStream(self.socket)

    def on_recieve(self, callback):
        """
        Sets `callback` to be run whenever this receiver gets a
        message. the callback is a runnable that takes one 
        parameter: a message

        You may set callback to None to pause message handling.
        """

        def zmq_cb(multipart):
            message = self.parse_zeromq_parts(multipart)
            return callback(message)

        if callback is None:
            zmq_cb = None

        self.stream.on_recv(zmq_cb)

    def close(self):
        """
        close the ZeroMQ socket stream
        """
        self.on_recieve(None)
        return self.stream.close()
