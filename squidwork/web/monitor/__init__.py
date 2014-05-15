"""
squidwork.web.monitor - a beautiful log of recent squidwork activity

depending on configuration, it displays a list of the last N squidwork events.
It can filter for uniqueness (squashing a bunch of duplicates), or just display
things chronologically.

monitor requires several extra packages to support its beautiy:
    - pyScss to render stylesheets

I feel like I might be pioneering strange application architectures at this
point. Here's what we've got so far:

- tornado webserver to deliver templates and websockets
- coffeescript js app
- view rendered on the client by Mithril.js
- ZeroMQ pub-sub data
- data becomes JSON
  - some is stream over WebSockets to front-end
  - some is plain-jain JSON

Nice: The worst part is that I can't tell if I'm a genius, or Don Music.
(That was a Sesame Street reference).
"""

import tornado.web
import tornado.ioloop
import scss
Scss = scss.Scss()

import squidwork.web.config as config
from squidwork.quick import sub
from squidwork.async import AsyncReciever
from squidwork.web import (
    handlers, JSONHandler, CoffeescriptHandler,
    TemplateRenderer)


class Cache(object):
    """
    Stores a fixed number of objects
    calls a callback when a new object is added
    """
    def __init__(self, max_count):
        self.cache = []
        self.cache_size = max_count
        self.callbacks = set()

    def add(self, *objs):
        """
        add new objects to the cache
        """
        for cb in self.callbacks:
            cb(*objs)

        self.cache.extend(objs)

        if len(self.cache) > self.cache_size:
            # retain the last N elements
            self.cache = self.cache[-self.cache_size:]

    def add_callback(self, cb):
        """
        add a callback. the callback should take varargs number of objects
        as its parameters
        """
        self.callbacks.add(cb)

    def remove_callback(self, cb):
        """
        removes a callback
        """
        self.callbacks.remove(cb)


class MessageCache(Cache):
    """
    keeps the latest message for each type as well as the usual cache
    """
    def __init__(self, max_count):
        super(MessageCache, self).__init__(max_count)
        self.by_origin = {}

    def add(self, *messages):
        for msg in messages:
            self.by_origin[str(msg.origin)] = msg
        super(MessageCache, self).add(*messages)


class ScssHandler(TemplateRenderer):
    """
    Serves compiled SCSS as CSS
    """
    def set_default_headers(self):
        self.set_header('Content-Type', 'text/css; charset=UTF-8')

    def get(self):
        source = self.template_string()
        self.write(Scss.compile(source))


def main():
    parser = config.create_argparser()
    parser.add_argument('n', '--num', help='number of elements to store',
                        default=15)
    options = parser.parse_args()
    settings = config.get_config(options.config)
    services = config.get_services(options)
    port = config.get_port(options)

    # the message buffer stores the last N mesages
    cache = MessageCache(options.num)
    recievers = []
    for svc in services:
        recvr = AsyncReciever(sub(*svc.URIs), svc.prefix)
        recvr.on_recieve(cache.add)
        recievers.append(recvr)

    app = tornado.web.Application(
        handlers() + [
            (r"/", TemplateRenderer, dict(source='templates/index.html')),
            (r"/latest.json", JSONHandler, dict(data=lambda:
                                                {'latest': cache.cache,
                                                 'types': cache.by_origin}))
            (r"/app.js", CoffeescriptHandler,
                dict(source='templates/app.coffee'))
        ],
        debug=True, **settings
        )

    app.listen(port)