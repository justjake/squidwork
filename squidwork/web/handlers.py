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


class TemplateRenderer(tornado.web.RequestHandler):
    """
    render a template with the args given at app creation.
    sneaky dynamic behavior can be provided by making any of the template
    args callable, in which case the template will recieve the result of
    applying the callable to the TemplateRenderer instance
    """
    def initialize(self, source, **args):
        self.source = source
        self.args = args

    def reverse_absolute(self, name, protocol=None):
        """
        similar to reverse_url, but provides an absolute path
        """
        return "{protocol}://{host}{path}".format(
            protocol=(protocol or self.request.protocol),
            host=self.request.host,
            path=self.reverse_url(name))

    def expand_callable(self, val):
        if callable(val):
            return val(self)
        return val

    def process_args(self, args):
        """
        run any callables in the template args on ourself
        """
        val = {k: self.expand_callable(v) for k, v in args.iteritems()}
        return val

    def template_string(self, args):
        """
        render our template source to a string
        """
        args = self.process_args(args)
        return self.render_string(self.source, **args)

    def get(self):
        self.write(self.template_string(self.args))


class CoffeescriptHandler(TemplateRenderer):
    """
    serves the squidwork.coffee library file as compiled
    javascript with a pre-created connection to the given
    socket uri location
    """
    def set_default_headers(self):
        self.set_header('Content-Type', 'text/javascript; charset=UTF-8')

    @tornado.web.asynchronous
    def get(self):
        self.write('/* rendering template ... */\n')
        # render template into coffeescript
        cs = self.template_string(self.args)

        # then compile to javascript
        self.write('/* compiling coffeescript ... */\n')
        js = coffeescript.compile(cs)

        # and we're done!
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
