"""
Puts it all together.
- serves /squidwork.js, processed so that the API jest werks
- serves  JSON /config.json which lists all the services provided
  to the running module
- servces /connect.ws, which is the websocket Squidwork bridge
"""
import tornado

from squidwork.web import create_application
from squidwork.config import get_config
from squidwork.web.config import create_argparser, get_port

def main():
    parser = create_argparser(prog='python -m squidwork.websocket')
    args = parser.parse_args()
    port = get_port(args)
    config_data = get_config(args.config)

    app = create_application(config=config_data, **config_data['Webapp'])

    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()

main()
