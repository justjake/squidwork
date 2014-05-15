"""
Tornado application to serve the compiled Coffeescript API and
set up our websocket connections
"""
import tornado.web
import coffeescript
import json

def pretty_json(data, **kwargs):
    """
    pretty-stringify data to JSON string,
    with nice indenting and seperators
    """
    defaults = dict(seperators=(',', ': '),
            indent=4,
            sort_keys=True)
    defaults.update(kwargs)
    return json.dumps(data, **kwargs)


class CoffeescriptHandler(tornado.web.RequestHandler):
    """
    serves the squidwork.coffee library file as compiled
    javascript with a pre-created connection to the given
    socket uri location
    """
    def initialize(self, source, socket_name):
        self.source = source
        self.socket_name = socket_name

    def set_default_headers(self):
        self.set_header('Content-Type', 'text/javascript; charset=UTF-8')

    @property
    def socket_uri(self):
        url = self.reverse_url(self.socket_name)
        return 'ws://{host}'.format(host=self.request.host) + url

    @tornado.web.asynchronous
    def get(self):
        self.write('/* rendering template ... */\n')
        cs = self.render_string(self.source,
                WEBSOCKET_URI=self.socket_uri)
        self.write('/* compiling coffeescript ... */\n')
        js = coffeescript.compile(cs)
        self.write(js)
        self.write('/* finished! */\n')
        self.finish()


class JSONHandler(tornado.web.RequestHandler):
    """
    Serves the data provided at initialization as JSON
    """
    def initialize(self, data, encoder=json.JSONEncoder):
        self.encoder = encoder
        self.data = data

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def data_as_json(self):
        return pretty_json(self.data, cls=self.encoder)

    def get(self):
        self.write(self.data_as_json())


class ConsoleHandler(tornado.web.RequestHandler):
    """
    should become a full logging facility squidwork...
    but right now just serves a simple HTML page that includes our
    javascript.
    """
    def get(self):
        self.render('templates/console.html')
