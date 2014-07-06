"""
Views for showing a multi-column files list
"""
import re
import os
import urllib
from random import randrange

from tornado.web import HTTPError

import squidwork.web.debuggable as debuggable
from squidwork import Sender, MessageEncoder
import squidwork.quick

from file_image import File, Image, Dir, FileMeta, is_image
from collections import OrderedDict, namedtuple

# a column in the SortedTableView
Column = namedtuple('Column', ['friendly', 'ident', 'sort_key', 'display_key'])


class SortedTableView(debuggable.Handler):
    """
    an apache-like directory listing table
    because i dont wanna do any javascript for now
    """

    def initialize(self, debug=False):
        super(SortedTableView, self).initialize(debug=debug)
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
            raise Exception('column {} not in view'.format(column))

        data = sorted(data, key=self.columns[column].sort_key)

        if order == 'dsc':
            data = list(reversed(data))

        return data

    def generate_query_string(self, column):
        """
        generates the query string to sort by a column, or, if currently
        sorting by that column, reverse the sort
        """
        DEFAULT = 'dsc'
        OTHER = 'asc'
        col_ident = self.get_argument('col', default=self.default_col)
        col_order = self.get_argument('order', default=DEFAULT)

        if col_ident != column.ident:
            return '?' + urllib.urlencode(dict(col=column.ident, order=DEFAULT))

        new_order = OTHER

        if col_order == OTHER:
            new_order = DEFAULT

        return '?' + urllib.urlencode(dict(col=column.ident, order=new_order))


def hits_or(other):
    """
    acess an objects hits, or if it has no attr hits,
    some other property
    """
    def hits_or_other(f):
        if hasattr(f, 'meta'):
            return f.meta.hits
        return other(f)
    return hits_or_other


hits_or_name = hits_or(lambda f: f.basename)
hits_or_none = hits_or(lambda f: None)


class DirectoryLister(SortedTableView):
    def initialize(self, path, debug=False):
        super(DirectoryLister, self).initialize(debug=debug)
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

        everything = [File(os.path.join(abs_path, f), self.root) for f in
                      os.listdir(abs_path)]


        files = []
        directories = []
        for f in everything:
            if f.basename[0] == '.':
                # hidden file
                # do not display
                continue

            if f.is_directory:
                directories.append(Dir(f.absolute, self.root))
                continue

            if is_image(f.absolute):
                img = Image(f.absolute, self.root)
                img.generate_thumb_in_background()
                files.append(img)
                continue

            files.append(f)


        files = self.order(files)
        directories = self.order(directories)
        columns = self.columns.values()

        #raise Exception('hi')

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
