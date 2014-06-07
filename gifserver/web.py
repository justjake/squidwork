from collections import OrderedDict, namedtuple
import os

from sqlobject import sqlhub, connectionForURI
import tornado.log
import tornado.web
import tornado.ioloop
from tornado.web import HTTPError

import squidwork.web as web
from squidwork.web.monitor import ScssHandler
from squidwork import Sender, MessageEncoder
import squidwork.quick

from file_image import File, Image, Dir
import urllib

"""
a column in the SortedTableView
"""
Column = namedtuple('Column', ['friendly', 'ident', 'sort_key', 'display_key'])


class SortedTableView(tornado.web.RequestHandler):
    """
    an apache-like directory listing table
    because i dont wanna do any javascript for now
    """

    def initialize(self):
        self.columns = OrderedDict()
        self.default_col = None

    def add_column(self, friendly, ident, sort_key, display_key):
        self.columns[ident] = Column(friendly, ident, sort_key, display_key)

    def order(self, data):
        """
        returns your data ordered by whatever column the user selected
        """
        column = self.get_argument('col', default=self.default_col)
        order = self.get_argument('order', default='asc')

        if column not in self.columns:
            return data

        data = sorted(data, key=self.columns[column].sort_key)

        if order == 'dsc':
            data = list(reversed(data))

        return data

    def generate_query_string(self, column):
        """
        generates the query string to sort by a column, or, if currently
        sorting by that column, reverse the sort
        """
        col_ident = self.get_argument('col', default=self.default_col)
        col_order = self.get_argument('order', default='asc')

        if col_ident != column.ident:
            return '?' + urllib.urlencode(dict(col=column.ident, order='asc'))

        new_order = 'asc'

        if col_order == 'asc':
            new_order = 'dsc'

        return '?' + urllib.urlencode(dict(col=column.ident, order=new_order))


def hits_or(other):
    """
    acess an objects hits, or if it has no attr hits,
    some other property
    """
    def hits_or_other(f):
        if hasattr(f, 'hits'):
            return f.hits
        return other(f)
    return hits_or_other

hits_or_name = hits_or(lambda f: f.name)
hits_or_none = hits_or(lambda f: None)


class DirectoryLister(SortedTableView):
    def initialize(self, path):
        super(DirectoryLister, self).initialize()
        self.root = path
        self.default_col = 'name'
        self.add_column('Name', 'name', lambda f: f.basename,
                        lambda f: f.basename)
        self.add_column('Last Modified', 'mod', lambda f: f.mtime,
                        lambda f: f.last_modified)
        self.add_column('Size', 'size', lambda f: f.bytes, lambda f: f.size)
        self.add_column('Hits', 'hits', hits_or_name, hits_or_none)

    def get(self, path, include_body=True):
        # preable taken from StaticFileHandler
        # Set up our path instance variables.
        self.path = self.parse_url_path(path)
        del path  # make sure we don't refer to path instead of self.path again
        absolute_path = self.get_absolute_path(self.root, self.path)
        self.absolute_path = self.validate_absolute_path(self.root,
                                                         absolute_path)
        if self.absolute_path is None:
            return

        # typing is hard
        abs_path = self.absolute_path
        rel_path = self.path

        everything = [File(self.root, os.path.join(rel_path, f)) for f in
                      os.listdir( abs_path)]
        files = []
        directories = []
        for f in everything:
            if f.is_directory:
                directories.append(Dir(abs_path, f.relative))
                continue

            img = Image.for_path(f.absolute, f.relative)
            img.generate_thumb_in_background()
            files.append(img)

        files = self.order(files)
        directories = self.order(directories)
        columns = self.columns.values()

        self.render('index.html', files=files, dirs=directories, path=rel_path,
                    columns=columns, query_string=self.generate_query_string)

    def parse_url_path(self, url_path):
        """Converts a static URL path into a filesystem path.
        """
        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)
        return url_path

    def validate_absolute_path(self, root, absolute_path):
        root = os.path.abspath(root)
        # os.path.abspath strips a trailing /
        # it needs to be temporarily added back for requests to root/
        if not (absolute_path + os.path.sep).startswith(root):
            raise HTTPError(403, "%s is not in root static directory",
                            self.path)
        if os.path.isdir(absolute_path) and not self.request.path.endswith('/'):
            self.redirect(self.request.path + "/", permanent=True)
            return
        if not os.path.exists(absolute_path):
            raise HTTPError(404)
        return absolute_path

    @classmethod
    def get_absolute_path(cls, root, path):
        abspath = os.path.abspath(os.path.join(root, path))
        return abspath


class HitCountImageServer(tornado.web.StaticFileHandler):
    """indexes and thumbnailifies images as it serves them"""
    def get(self, path, include_body=True):
        self.path = self.parse_url_path(path)
        absolute_path = self.get_absolute_path(self.root, self.path)
        self.absolute_path = self.validate_absolute_path(self.root,
                                                         absolute_path)
        if self.absolute_path is None:
            return

        should_count = self.get_argument('count', 'true')
        if should_count != 'false':
            # count access times with hit()
            img = Image.for_path(self.absolute_path)
            img.hit()
            img.generate_thumb_in_background()

        return super(HitCountImageServer, self).get(path, include_body)


def configure(args=None):
    """do one-time global setup things"""
    config = web.Config('gifserver')
    config.option('images')    # directories full of images
    config.option('thumbs')    # directory to store thumbnails in
    config.option('database')  # SQLObject database URI
    config.retrieve(args)

    # set up connections
    sqlhub.processConnection = connectionForURI(config.database)
    # socket = squidwork.quick.pub(*config.uris)
    Image.createTable(ifNotExists=True)

    # configure thumbnails
    Image.thumb_dir = config.thumbs

    return config


def main():
    # options
    config = configure()

    handlers = web.handlers(config.raw_config, debug=config.debug)
    handlers += [
        (r'/app.js', web.CoffeescriptHandler, dict(source='app.coffee')),
        (r'/style.css', ScssHandler, dict(source='style.scss')),
        (r'/thumbs/(.*)', tornado.web.StaticFileHandler,
                          dict(path=config.thumbs)),
        (r'/images/(.*)', HitCountImageServer, dict(path=config.images)),
        (r'/(.*)', DirectoryLister, dict(path=config.images))
    ]

    home = os.path.dirname(os.path.realpath(__file__))
    static = home + '/static'
    templates = home + '/templates'

    app = tornado.web.Application(handlers,
                                  debug=config.debug,
                                  template_path=templates,
                                  static_path=static)
    try:
        app.listen(config.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print ' keyboard interrupt: exiting.'

if __name__ == '__main__':
    main()
