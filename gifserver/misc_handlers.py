import re
import os
from StringIO import StringIO

import Image
from IPython import embed  # for debugging
import tornado.web
import squidwork.web.debuggable as debuggable
from tornado.httpclient import AsyncHTTPClient

from file_image import Image as WebImage, FileMeta, is_image


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
            meta = FileMeta.for_path(self.absolute_path)
            meta.hit()
            if is_image(self.absolute_path):
                img = WebImage(self.absolute_path, None)
                img.generate_thumb_in_background()

        return super(HitCountImageServer, self).get(path, include_body)

    def get_content_type(self):
        """
        according to maxb, we should whitelist specific content types
        to serve.

        images and video are ok,
        I'll serve everything else as octet-stream
        """
        content_type = super(HitCountImageServer, self).get_content_type()
        content_type = content_type or 'application/octet-stream'

        # allow images and video
        if re.match(r'^image/', content_type) or (
                re.match(r'^video/',  content_type)):
            return content_type

        if re.match(r'^text/', content_type):
            return 'text/plain'

        # otherwise return octet stream
        return 'application/octet-stream'


class CanUpload(debuggable.Handler):
    """
    on a post of a file and a filename, upload that file to that filename dest.
    on a post of a URI and a filename, HTTP GET that URi and save it to that
    filename.

    only allows things if the upload secret equals the stored secret
    intended to handle the POST to any given directory, and should be used as 
    a mixin or a proxy delegate

    The root is the location to upload files inside of.
    """

    illegal = re.compile(r'[^\w\d]')
    spaces = re.compile(r'\s+|/+')

    def initialize(self, root, secret, debug=False):
        super(CanUpload, self).initialize(debug=debug)
        self.root = root
        self.secret = secret

    def get(self):
        return self.render('upload.html', dest=self.root)

    # @tornado.web.asynchronous
    def post(self):
        given_secret = self.get_argument('key', 'lol incorrect key')
        if given_secret != self.secret:
            raise tornado.web.HTTPError(403, 'Incorrect key')

        dest = self.safe_dest(self.get_argument('fname'))

        uri = self.get_argument('uri', False)
        if uri:
            return self._upload_uri_to(dest)
        return self._upload_file_to(dest)

    def safe_dest(self, path):
        """
        return the file path we should write to.
        Raises a client error 400 if the file already exists, or the path
        is outside the URI's web root
        """

        # isallow empty paths
        if not path:
            raise tornado.web.HTTPError(400, 'No path given')

        safe = lambda s: self.illegal.sub('', s)
        # santize a bit
        path, extension = os.path.splitext(path)
        words = self.spaces.split(path)
        safe_words = [safe(w) for w in words]
        fname = '-'.join(safe_words) + '.' + safe(extension)
        abs_path = os.path.abspath(os.path.join(self.root, fname))

        if os.path.exists(abs_path):
            raise tornado.web.HTTPError(403, 'File already exists')

        return abs_path

    def _upload_file_to(self, path):
        """
        uploads file 0 in the post to the given path
        """
        return self.write_data_as_img(
            self.request.files['file1'][0]['body'], path)

    def _upload_uri_to(self, path):
        """
        starts the upload of some web URI to a specific path on the server.
        trusts everything, relies on not serving bullshit
        """
        def finish_upload(http_res):
            http_res.rethrow()  # errors if needed
            self.write_data_as_img(http_res.body, path)

        uri = self.get_argument('uri')
        client = AsyncHTTPClient()
        client.fetch(uri, callback=finish_upload)

    def write_data_as_img(self, data, path):
        """
        no more validation
        only saving
        """
        img = Image.open(StringIO(data))
        img.save(path)
        self.finish('nice file :^)')

