from tornado import websocket
import json

from squidwork.sender import MessageEncoder
from squidwork.quick import sub
from squidwork.async import AsyncReciever

from squidwork.web.handlers import pretty_json


ACTION = 'action'
TARGET = 'target'
SUB    = 'SUB'
UNSUB  = 'UNSUB'


class BridgeWebSocket(websocket.WebSocketHandler):
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

    def any_has_prefix(self, prefix, things):
        for thing in things:
            if thing.startswith(prefix):
                return True

        return False

    def sub(self, uri, prefix=''):
        """
        subscribe the web client to this socket
        """

        ident = self.ident(uri, prefix)
        idents = self.recievers.iterkeys()

        # we don't need to actually create more filtered sockets if we
        # already have a general one on the books.
        # the javascript end will handle choosing the most specific
        # subscriber callback for any message we send over the wire
        if ident in self.recievers or self.any_has_prefix(ident, idents):
            # already subscribed
            self.write_message({'success': 'already subscribed'})
            return

        # create a new reciever and a callback for it
        rcvr = AsyncReciever(sub(uri), prefix)
        self.recievers[ident] = rcvr
        rcvr.on_recieve(self.write_squidwork)

        self.write_message({'success': 'subscribed'})

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

        self.write_message({'success': 'unsubscribed'})
