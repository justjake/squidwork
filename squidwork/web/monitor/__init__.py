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

import os
from random import choice
import tornado.web
import tornado.ioloop
import scss
Scss = scss.Scss()

from squidwork.config import Service
from squidwork.sender import MessageEncoder
from squidwork import Message
from squidwork.quick import sub
from squidwork.async import AsyncReciever
from squidwork.web import handlers as api_handlers
from squidwork.web import Config
from squidwork.web.handlers import (
    JSONHandler, CoffeescriptHandler,
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
        source = self.template_string(self.args)
        self.write(Scss.compile(source))


def dummy_message():
    """
    generates a single dummy squidwork message
    """
    origins = """
    all/messages/recieved@mail.example.com
    all/messages/failed@mx.google.example.com
    all/alarm@critical.internal
    all/alert@critical.internal
    all/ear/passive@raspi.internal
    """.split()

    contents = [
        dict(item='souls', quantity=1000),
        dict(line='alas poor yorik', gratitude=-23),
        dict(insult='ill bash yer fukin head in swear on me mum',
             severity=None,
             british=True)
        ]

    body = choice(contents).copy()
    body.update(dict(dummy=True))

    return Message(body, origin=choice(origins))


def main():
    """
    run the app!
    currently very hairy. starts with dummy data
    """

    settings = dict(debug=True,
                    template_path=os.path.dirname(os.path.realpath(__file__)))

    conf = Config('squidwork.web.monitor')
    conf.option('cache-size', type=int, help='numer of elements to store')
    conf.option('display-size', type=int, help='numer of elements to store')
    conf.retrieve()

    port = conf.port

    # the message buffer stores the last N mesages
    cache = MessageCache(conf.cache_size)

    # subscribe to all services!
    uris = Service.all_uris()
    recvr = AsyncReciever(sub(*uris))
    recvr.on_recieve(cache.add)

    # generate some dummy data to pre-populate the cache with
    dummy = [dummy_message() for i in range(0, 20)]
    cache.add(*dummy)

    # we include the api_handlers from squidwork.web so we can use the
    # squidwork web<--WebSocket-->ZeroMq bridge
    all_handlers = api_handlers(conf.raw_config, **settings) + [

        # the index page is totally static -- all it does is request javascript
        (r"/", TemplateRenderer, dict(source='templates/index.html')),

        # JSON view of whatever is currently in our cache. this is how the
        # app gets its initial data on page load
        (r"/data.json", JSONHandler, dict(encoder=MessageEncoder, data=(
            lambda: {'latest': cache.cache, 'types': cache.by_origin}))),

        # big coffeescript app written with Mithril.js. All HTML structure on
        # the page is produced by view functions in app.coffee
        (r"/app.js", CoffeescriptHandler,
            dict(source='templates/app.coffee', count=conf.display_size)),

        # static, plain-jane scss
        (r"/style.css", ScssHandler, dict(source='templates/style.scss')),
    ]

    # spin up the app!
    app = tornado.web.Application(all_handlers, **settings)
    try:
        app.listen(port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print ' keyboard interrupt: exiting.'
