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

from squidwork.config import Config as BaseConfig


def Config(*args, **kwargs):
    """
    a config object with debug and port options already required
    """
    config = BaseConfig(*args, **kwargs)
    config.option('debug', type=bool)
    config.option('port', type=int)
    return config


def handlers(config_data,
             debug=False,
             js_route=r'/squidwork.js',
             ws_route=r'/connect.ws',
             json_route=r'/config.json'):
    """
    returns the core handlers required for websocket mirror functionality:
    - Coffeescript handler serving squidwork.js
    - BridgeWebSocket handler serving connect.ws
    - JSONHandler serving config.json

    you may configure the routes at which they are mounted using the *_route
    kwargs.
    """

    ws_name = 'squidwork_websocket'

    js = (js_route,
          CoffeescriptHandler,
          dict(source='templates/squidwork.coffee',
               socket_uri=lambda self: self.reverse_absolute(ws_name, protocol='ws'),
               debug=debug,
               template_relative_to_class=True))
    ws = (ws_route, BridgeWebSocket, None, ws_name)
    json = (json_route, JSONHandler, dict(data=config_data))

    return [js, ws, json]


def create_application(config, console_route=r'/', **settings):
    """
    create a new Tornado webapp with the given config data strucutre,
    which will be served as JSON
    """
    app_handlers = handlers(config, **settings)
    application = tornado.web.Application(
        app_handlers + [(console_route, ConsoleHandler)],
        **settings)
    return application
