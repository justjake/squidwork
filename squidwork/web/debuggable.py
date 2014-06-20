"""Demonstration of tornado web server with werkzeug interactive debugger.

Ron DuPlain <ron.duplain@gmail.com>

https://gist.github.com/rduplain/4983839
2013-02-19 - 2013-07-27

Tested on Python 2:

* Python 2.7.3
* Tornado 2.4.1 and 3.1
* Werkzeug 0.8.3 and 0.9.3

... and Python 3:

* Python 3.3.0
* Tornado 3.1
* Werkzeug 0.9.3

Call `python2.7 tornado_debug.py --debug` to enable debugger, off otherwise.

Whenever an exception occurs in a handler, the "get_error_html" method kicks
in, rendering the werkzeug interactive debugger in the browser. As it is
rendered, the traceback and its frames are stored on the application
object. The DebugApplication is a subclass of tornado.web.Application so that
you can swap it out during development, and it contains a dummy WSGI
application (Werkzeug is WSGI) so that it can load Werkzeug's debug
middleware. Then all calls to __debugger__ URIs are intercepted and passed to
this middleware.

That is, in normal operation, all requests are business as usual on your
tornado server. WSGI is only introduced to serve the debugger, which has a
snapshot of the traceback. So you should be able to use this with traditional
tornado applications without introducing synchronous constraints. There's a
shared object between the Application and the Handler, so look out for that if
you are threading yourself. I don't have any tricky asynchronous code to test
this on, but if you can serve HTML, then this debugger is a
possibility. Websockets are out of scope here, since this interaction assumes
request-response with a rendered HTML template.

You can inspect code at different stack frames from within the browser. These
frames are kept on the application object until the process is restarted, and
you can even issue other requests to your tornado application while interacting
within a traceback. Naturally, it's a bad idea to run this in production.
"""


import logging

import tornado.ioloop
import tornado.web
import tornado.wsgi


class Handler(tornado.web.RequestHandler):
    "General-purpose handler for routing to application-level interfaces."

    def initialize(self, debug=False):
        # Since we are using the same Handler class for both debug and normal
        # modes, we check for debug flag here. Alternatively, define
        # get_error_html in a subclass and pass that class to the Application
        # on instantiation.
        if debug:
            self.get_error_html = self.get_debugger_html

    def get_debugger_html(self, status_code, **kwargs):
        assert isinstance(self.application, DebugApplication)
        traceback = self.application.get_current_traceback()
        keywords = self.application.get_traceback_renderer_keywords()
        html = traceback.render_full(**keywords).encode('utf-8', 'replace')
        return html.replace(b'WSGI', b'tornado')


class ApplicationMixin(object):
    "Provide a run method to start the application server."

    def run(self, port, logger=logging.getLogger()):
        logger.info('Running tornado on port %(port)d.' % {'port': port})
        self.listen(port)
        tornado.ioloop.IOLoop.instance().start()


class Application(tornado.web.Application, ApplicationMixin):
    "Tornado Application with a run method."


class DebugApplication(Application, ApplicationMixin):
    "Tornado Application supporting werkzeug interactive debugger."

    # This supports get_error_html in Handler above.

    def __init__(self, *args, **kwargs):
        from werkzeug.debug import DebuggedApplication
        self.debug_app = DebuggedApplication(self.debug_wsgi_app, evalex=True)
        self.debug_container = tornado.wsgi.WSGIContainer(self.debug_app)
        super(DebugApplication, self).__init__(*args, **kwargs)

    def __call__(self, request):
        if '__debugger__' in request.uri:
            # Do not call get_current_traceback here, as this is a follow-up
            # request from the debugger. DebugHandler loads the traceback.
            return self.debug_container(request)
        return super(DebugApplication, self).__call__(request)

    @classmethod
    def debug_wsgi_app(cls, environ, start_response):
        "Fallback WSGI application, wrapped by werkzeug's debug middleware."
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return ['Failed to load debugger.\n']

    def get_current_traceback(self):
        "Get the current Python traceback, keeping stack frames in debug app."
        traceback = get_current_traceback()
        for frame in traceback.frames:
            self.debug_app.frames[frame.id] = frame
        self.debug_app.tracebacks[traceback.id] = traceback
        return traceback

    def get_traceback_renderer_keywords(self):
        "Keep consistent debug app configuration."
        # DebuggedApplication generates a secret for use in interactions.
        # Otherwise, an attacker could inject code into our application.
        # Debugger gives an empty response when secret is not provided.
        return dict(evalex=self.debug_app.evalex, secret=self.debug_app.secret)


def get_current_traceback():
    "Get the current traceback in debug mode, using werkzeug debug tools."
    # Lazy import statement, as debugger is only used in development.
    from werkzeug.debug.tbtools import get_current_traceback
    # Experiment with skip argument, to skip stack frames in traceback.
    traceback = get_current_traceback(skip=2, show_hidden_frames=False,
                                      ignore_system_exceptions=True)
    return traceback
