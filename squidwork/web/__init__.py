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

def create_application(config, **settings):
    """
    create a new Tornado webapp with the given config data strucutre,
    which will be served as JSON
    """
    del settings['port']
    application = tornado.web.Application([
        (r"/squidwork.js", CoffeescriptHandler, 
            dict(source='templates/squidwork.coffee', socket_name='websocket',
                debug=settings['debug'])),
        (r"/connect.ws", BridgeWebSocket, None, 'websocket'),
        (r"/config.json", JSONHandler, 
            dict(data=config)),
        (r"/", ConsoleHandler)
        ], **settings)
    return application
