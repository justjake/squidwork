"""
squidwork web interface authentication framework
basically I was bored on an airplane and wanted to see if i could build
this sort of system from memory
"""
import debuggable
import tornado.web
import datetime

# useful because it knows about datetime encoding (!?)
from squidwork.sender import MessageEncoder
from squidwork.message import TIME_FORMAT
import json


class WithSession(object):
    """
    mixin class.
    provides access to sessions
    """
    cookie_name = 'SQUIDWORK'

    def get_session(self):
        """retrieves the signed JSON session from a secure cookie"""
        raw = self.get_secure_cookie(self.cookie_name)
        if raw:
            return json.loads(raw)
        return {}

    def save_session(self, session, expires_days=30):
        """saves the given session (a dict) as a secure cookie"""
        self.set_secure_cookie(
                name=self.cookie_name, 
                value=json.dumps(session, cls=MessageEncoder),
                expires_days=expires_days)

    @property
    def session(self):
        if hasattr(self, '_current_session'):
            return self._current_session

        self._current_session = self.get_session()
        return self._current_session


class WithAuth(WithSession):
    """
    mixin class.
    knows how to auth a session and not much else
    """
    AUTH = 'auth'

    def is_authed(self, session):
        """True if the session is authenticated"""
        return self.AUTH in session and session[self.AUTH]

    def mark_authed(self, session):
        session[self.AUTH] = True
        return session

    @classmethod
    def needs_auth(self, meth):
        def authed_method(self, *args, **kwargs):
            session = self.get_session()
            if not self.is_authed(session):
                raise tornado.web.HTTPError(403, 'Not authorized.')
            return meth(self, *args, **kwargs)
        return authed_method


class AuthHandler(WithAuth, debuggable.Handler):
    """subclass and add a get() method if you want a stand-alone form"""
    AUTH = 'auth'

    def initialize(self, secret, **kwargs):
        super(AuthHandler, self).initialize(**kwargs)
        self.secret = secret # APP SECRET

    def post(self):
        given_key = self.get_argument('key', 'lol incorrect key')
        if given_key != self.secret:
            raise tornado.web.HTTPError(403, 'Incorrect key')

        session = self.get_session()
        self.mark_authed(session)
        self.save_session(session)
