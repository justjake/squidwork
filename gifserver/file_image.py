import os
import time
from multiprocessing.pool import ThreadPool
import hashlib

import Image as ImageLib
import sqlobject

def ensure_stat(fn):
    def ensured(self, *args, **kwargs):
        if not hasattr(self, 'stat'):
            self.stat = os.stat(self.absolute)
        return fn(self, *args, **kwargs)
    return ensured


_workers = ThreadPool(4)
def run_background(func, callback=None, args=(), kwds={}):
    """run a function in the thread pool, with optional IOLoop callback"""
    if callback:
        _workers.apply_async(func, args, kwds, callback)
    else:
        _workers.apply_async(func, args, kwds)


def generate_thumbnail(infile, outfile):
    """generates a thumbnail image as a PNG and writes it to outfile"""
    size = (128, 128)
    # try:
    im = ImageLib.open(infile)
    # except IOError:
    #     # whatever
    #     return

    im.thumbnail(size, ImageLib.ANTIALIAS)
    im.save(outfile, 'PNG')


def gen_thumbnail_if_needed(infile, outfile):
    if os.path.isfile(outfile) and (
            os.path.getmtime(infile) < os.path.getmtime(outfile)):
        # its ok
        return
    return generate_thumbnail(infile, outfile)


class File(object):
    """
    Easily get properties for files
    there was probably a library class like this already; things got out of
    hand.
    """
    """needs to have self.absolute and self.relative set"""
    def __init__(self, root, relative):
        self.absolute = os.path.join(root, relative)
        self.relative = relative

    @property
    def basename(self):
        return os.path.basename(self.absolute)

    @property
    def is_directory(self):
        return os.path.isdir(self.absolute)

    @property
    @ensure_stat
    def mtime(self):
        return self.stat.st_mtime

    @property
    @ensure_stat
    def last_modified(self):
        return time.ctime(self.mtime)

    @property
    @ensure_stat
    def bytes(self):
        return float(self.stat.st_size)

    @property
    @ensure_stat
    def size(self):
        num = float(self.stat.st_size)
        for x in ['bytes','KB','MB','GB']:
            if -1024.0 < num < 1024.0:
                return "%3.1f%s" % (num, x)
            num /= 1024.0
        return "%3.1f%s" % (num, 'TB')


class Dir(File):
    @property
    def url(self):
        return '/' + self.relative

class Image(sqlobject.SQLObject, File):
    """
    store rating metadata about an image, create thumbnails, and more!
    """

    thumb_dir = '/tmp'

    class sqlmeta:
        lazyUpdate = True  # must call #syncUpdate or #sync to save changes

    absolute =    sqlobject.StringCol(notNone=True, unique=True,
                                      alternateID=True)
    hits =        sqlobject.IntCol(notNone=True, default=0)
    rating =      sqlobject.FloatCol(notNone=True, default=0.0)
    rating_hits = sqlobject.IntCol(notNone=True, default=0)

    def rate(self, rating):
        """
        store an incoming rating value
        """
        # no crazy bznz
        if rating > 10:
            return self.rating

        so_far = self.rating * self.ratingHits
        now = (so_far + rating) / (self.rating_hits + 1)
        self.rating = now
        self.ratingHits = self.rating_hits + 1
        self.syncUpdate()
        return now

    def hit(self):
        self.hits += 1
        self.syncUpdate()
        return self.hits

    def generate_thumb_in_background(self):
        run_background(gen_thumbnail_if_needed, None, (self.absolute,
                                                       self.thumb_path))

    def generate_thumb(self):
        generate_thumbnail(self.absolute, self.thumb_path)


    @property
    def image_url(self):
        return '/images/' + self.relative

    @property
    def thumb_url(self):
        return '/thumbs/' + self.thumb_name

    @property
    def thumb_name(self):
        """
        filename of the thumbnail for this file
        """
        return hashlib.md5(self.absolute).hexdigest() + '.png'

    @property
    def thumb_path(self):
        return os.path.join(self.thumb_dir, self.thumb_name)


    @classmethod
    def for_path(cls, absolute, relative=None):
        """get or create for this path"""
        try:
            instance = cls.byAbsolute(absolute)
        except sqlobject.SQLObjectNotFound:
            instance = cls(absolute=absolute)
            instance.syncUpdate()
        instance.relative = relative
        return instance
