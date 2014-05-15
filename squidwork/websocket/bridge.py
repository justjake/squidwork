from tornado import websocket
from zmq.eventloop.zmqstream import ZMQStream
import json

from squidwork import Reciever
from squidwork.sender import MessageEncoder
from squidwork.quick import sub

from squidwork.websocket.web import pretty_json

import zmq.eventloop.ioloop
zmq.eventloop.ioloop.install()

class AsyncReciever(Reciever):

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

ACTION = 'action'
TARGET = 'target'
SUB =    'SUB'
UNSUB =  'UNSUB'


class SquidworkWebSocket(websocket.WebSocketHandler):
    """
    A JSON API to subscribe/unsubscribe from squidwork sockets.
    Currently provides no security, so could be leveredged for DoS
    connection spam attacks if we were to make tons of connections on
    behelf of our JavaScript clients
    """

    def open(self):
        """
        run when a new websocket connection is initiated
        """
        self.recievers = {}

    def on_close(self):
        """
        shut down all recievers
        """
        for rcvr in self.recievers.values():
            rcvr.close()

    def on_message(self, message):
        """
        run when we recieve a message from the web client.
        We expect JSON messages in the format
        {'action': 'SUB' | 'UNSUB',
         'target': [URI, PREFIX] | [URI] }

        where URI = 'tcp://192.168.0.1:9000' or similar, and
              PREFIX = 'app/route'

        if no prefix is supplied for a SUB or UNSUB, we will
        perform a full SUB/UNSUB.
        """
        data = json.loads(message)

        if ACTION not in data and TARGET not in data:
            raise ValueError('Incorrect message: {}'.format(message))

        if data[ACTION] == SUB:
            return self.sub(*data[TARGET])

        if data[ACTION] == UNSUB:
            return self.unsub(*data[TARGET])

        self.write_message(
                {'error': 'unknow action "{}"'.format(data[ACTION])})

    def write_squidwork(self, message):
        """
        Write a squidwork message to the wire as JSON
        """
        data = pretty_json(message, cls=MessageEncoder)
        self.write_message(data)

    def ident(self, uri, prefix):
        return uri + '/' + prefix

    def sub(self, uri, prefix=''):
        """
        subscribe the web client to this socket
        """

        ident = self.ident(uri, prefix)

        if ident in self.recievers:
            # already subscribed
            return

        # create a new reciever and a callback for it
        rcvr = AsyncReciever(sub(uri), prefix)
        self.recievers[ident] = rcvr
        rcvr.on_recieve(self.write_squidwork)

        self.write_message(
                {'success': 'subscribed'})

    def unsub(self, uri, prefix=''):
        """
        unsubscribe from the given prefix on the URI
        """
        ident = self.ident(uri, prefix)

        if ident not in self.recievers:
            return self.write_message(
                    {'error': 'not subscribed to URI "{}"'.format(uri)})

        rcvr = self.recievers[uri]
        rcvr.close()
        del self.recievers[uri]

        self.write_message(
                {'success': 'unsubscribed'})
