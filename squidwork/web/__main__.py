"""
Puts it all together.
- serves /squidwork.js, processed so that the API jest werks
- serves  JSON /config.json which lists all the services provided
  to the running module
- servces /connect.ws, which is the websocket Squidwork bridge
"""
import tornado

from squidwork.web import create_application, Config


def main():
    config = Config().retrieve()

    app = create_application(config.raw_config, debug=config.debug)

    app.listen(config.port)
    tornado.ioloop.IOLoop.instance().start()


main()
