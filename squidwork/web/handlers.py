"""
Tornado application to serve the compiled Coffeescript API and
set up our websocket connections
"""
import tornado.web
import coffeescript
import json
import re


def pretty_json(data, **kwargs):
    """
    pretty-stringify data to JSON string,
    with nice indenting and seperators
    """
    defaults = dict(separators=(',', ': '),
                    indent=2,
                    sort_keys=True)
    defaults.update(kwargs)
    return json.dumps(data, **defaults)


class CoffeescriptHandler(tornado.web.RequestHandler):
    """
    serves the squidwork.coffee library file as compiled
    javascript with a pre-created connection to the given
    socket uri location
    """
    def initialize(self, source, **kwargs):
        self.source = source
        self.template_args = kwargs

    def set_default_headers(self):
        self.set_header('Content-Type', 'text/javascript; charset=UTF-8')

    def expand_callable(self, val):
        if callable(val):
            return val(self)
        return val

    @property
    def socket_uri(self):
        url = self.reverse_url(self.socket_name)
        return 'ws://{host}'.format(host=self.request.host) + url

    @tornado.web.asynchronous
    def get(self):
        self.write('/* rendering template ... */\n')
        # first coffeescript is transformed as a Tornado template
        # expand callable params where possible by invokign them on self
        args = {k: self.expand_callable(v)
                for k, v in self.template_args.iteritems()}
        cs = self.render_string(self.source, **args)

        # then it is rendered to javascript
        self.write('/* compiling coffeescript ... */\n')
        js = coffeescript.compile(cs)
        self.write(js)
        self.write('/* finished! */\n')
        self.finish()


class JSONHandler(tornado.web.RequestHandler):
    """
    Serves the data provided at initialization as JSON.

    If you want to be tricky, you can provide a callable `data` parameter,
    and the JSONHandler will use the result of the callable as data on each
    request.

    if you GET this with a parameter of ?var=valid.js.variable,
    then instead of plain JSON you will recieve a text/javascript setting
    valid.js.varibale = <the json>
    """
    function = type(lambda x: x)

    def initialize(self, data, encoder=json.JSONEncoder):
        self.encoder = encoder
        self._data = data

    @property
    def data(self):
        """
        allows us to provide a zero-argument function as data, so that
        we can have dynamic content
        """
        if callable(self._data):
            return self._data()
        return self._data

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def data_as_json(self):
        return pretty_json(self.data, cls=self.encoder)

    def get(self):
        # support echoing into a variable
        variable = self.get_argument('var', False)
        if variable:
            self.set_header('Content-Type', 'text/javascript; charset=UTF-8')
            safe = re.compile(r"^[\w|\d|\.]+$").match(variable)
            if not safe:
                # it's your funeral
                self.write('alert("unsafe variable name")')
                return
            self.write(variable + ' = ')
        self.write(self.data_as_json())


class ConsoleHandler(tornado.web.RequestHandler):
    """
    should become a full logging facility squidwork...
    but right now just serves a simple HTML page that includes our
    javascript.
    """
    def get(self):
        self.render('templates/console.html')
