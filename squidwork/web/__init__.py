"""
implements a tornado handlers and a application to bridge squidwork to
the web.

You can run the server with `python -m squidwork.websocket -c ./config.yml`
"""
import tornado.web

from squidwork.web.socket import (
    BridgeWebSocket)

from squidwork.web.handlers import (
    JSONHandler,
    CoffeescriptHandler,
    ConsoleHandler)


def handlers(config, **settings):
    """
    returns the core handlers required for websocket mirror functionality:
    - Coffeescript handler serving squidwork.js
    - BridgeWebSocket handler serving connect.ws
    - JSONHandler serving config.json
    """
    return [
        (r"/squidwork.js", CoffeescriptHandler,
            dict(source='templates/squidwork.coffee',
                 socket_uri=lambda self: self.reverse_url('websocket'),
                 debug=settings['debug'])),
        (r"/connect.ws", BridgeWebSocket, None, 'websocket'),
        (r"/config.json", JSONHandler, dict(data=config)),
    ]


def create_application(config, **settings):
    """
    create a new Tornado webapp with the given config data strucutre,
    which will be served as JSON
    """
    app_handlers = handlers(config, **settings)
    del settings['port']
    application = tornado.web.Application(
        app_handlers + [(r"/", ConsoleHandler)],
        **settings)
    return application
