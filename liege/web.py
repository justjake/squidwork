import json
import os

import tornado.web
import tornado.ioloop
import wit

import squidwork.web as web
from squidwork.web.monitor import ScssHandler
from squidwork.config import Service
from squidwork import Sender, MessageEncoder
import squidwork.quick


class WitQueryHandler(tornado.web.RequestHandler):
    """
    takes get or post requests, processes them with wit.ai, sends the result
    across the network with Squidwork, and then returns the squidwork message
    to the requester.

    wit responses are routed first based on confidence, and then on intent.
    wit/error            - confedence not in response
    wit/failure/<intent> - very low confidence (C < 0.1)
    wit/low/<intent>     - low confidence      (0.1 < C < 0.3)
    wit/intent/<intent>  - regular confidence  (0.3 <= C)

    parameters

    wit_token: required, string. wit.ai api authorization token.
    fail_bound: float. wit responses below this confidence will be considered
        routed beneith to 'wit/failure'
    low_bound: float. with responses below this confidence but above fail_bound
        will be routed to 'wit/low'
    """

    def initialize(self, wit_token=None, socket=None,
                   failure_bound=0.1, low_bound=0.3):
        if wit_token is None:
            raise ValueError('needs a wit_token')
        if socket is None:
            raise ValueError('needs a ZeroMQ publish socket')

        self.wit = wit.Wit(wit_token)
        self.failure_bound = failure_bound
        self.low_bound = low_bound

        self.error = Sender(socket, 'wit/error')
        self.failure = Sender(socket, 'wit/failure')
        self.low = Sender(socket, 'wit/low')
        self.high = Sender(socket, 'wit/intent')

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def get(self):
        self.wit_query(self.get_argument('q'))

    def post(self):
        self.wit_query(self.get_argument('q'))

    def send_squidwork(self, wit_data):
        """
        send wit.ai data as a squidwork message with the appropriate route
        """

        if ('outcome' not in wit_data or
                'confidence' not in wit_data['outcome']):
            return self.error.send(wit_data)

        intent = wit_data['outcome']['intent']
        confidence = wit_data['outcome']['confidence']

        if confidence < self.failure_bound:
            return self.failure.send(wit_data, intent)

        if confidence < self.low_bound:
            return self.low.send(wit_data, intent)

        return self.high.send(wit_data, intent)

    def wit_query(self, query):
        """
        handles any with web query
        """
        response = self.wit.get_message(query)
        msg = self.send_squidwork(response)
        self.write(json.dumps(msg, cls=MessageEncoder, indent=2))


def uris_for_prefixes(self):
    prefixes = self.get_arguments('prefix')

    services = set()
    for pfx in prefixes:
        for svc in (Service.for_prefix(pfx)):
            services.add(svc)

    return {svc.prefix: list(svc.URIs) for svc in services}


def main():
    config = web.Config('liege-web')
    config.option('wit-token', type=str)
    config.retrieve()

    # where we send wit messages to
    if config.debug:
        print "Binding ZeroMQ at: " + str([squidwork.quick.resolve_hostname(u) for u in config.uris])
    socket = squidwork.quick.pub(*config.uris)

    handlers = web.handlers(config.raw_config, debug=config.debug)
    handlers += [
        (r'/', web.TemplateRenderer, dict(source='index.html')),
        (r'/wit', WitQueryHandler, dict(socket=socket,
                                        wit_token=config.wit_token)),
        (r'/app.js', web.CoffeescriptHandler, dict(source='app.coffee')),
        (r'/style.css', ScssHandler, dict(source='style.scss')),
        (r'/services.json', web.JSONHandler, dict(data=uris_for_prefixes))
    ]

    templates = os.path.dirname(os.path.realpath(__file__)) + '/templates'

    app = tornado.web.Application(handlers,
                                  debug=config.debug,
                                  template_path=templates)
    try:
        app.listen(config.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print ' keyboard interrupt: exiting.'

if __name__ == '__main__':
    main()
