import os
import time
from multiprocessing.pool import ThreadPool
import hashlib
from collections import namedtuple

import sqlobject
from wand.image import Image as Pixels

# hashset lookups would be slower than linear search over 3 items
# i think

def exts(space_sepd):
    """
    turns a space seperated string of extensions into
    something with an __in__ operation for .ext
    """
    as_list = map(lambda x: '.' + x, space_sepd.split(' '))
    return as_list

TEXT_EXT  = exts('txt html xhtml xml')
VID_EXT   = exts('mkv avi xvid divx')
IMAGE_EXT = exts('jpg jpeg gif png bmp')

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
    # TODO: gif support
    # TODO: enhance speed
    # see http://www.imagemagick.org/script/command-line-processing.php#geometry
    size = (128, 128)

    #def get_frames(num_frames, seq):
        #num_frames = min(len(seq), num_frames)
        #which_frames = map(lambda i: i * len(seq) / num_frames,
                #range(num_frames))
        #frames = []
        #for i in which_frames:
            #frames.append(seq[i])

    geom = 'x'.join(map(str, size)) + '>'

    with Pixels(filename=infile) as original:
        with original.convert('png') as img:
            img.transform(resize=geom)
            img.save(filename=outfile)


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

    def __repr__(self):
        return 'File({abs}, {root})'.format(abs=repr(self.absolute),
                root=repr(self.root))

    def __init__(self, abs_path, root):
        # make sure we start in the root
        if not abs_path.startswith(root):
            raise ValueError('file abspath outside of root')

        self.root = root
        self.absolute = abs_path
        self.meta = FileMeta.for_path(abs_path, root)

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
                return "%3.1f %s" % (num, x)
            num /= 1024.0
        return "%3.1f%s" % (num, 'TB')

    @property
    def relative(self):
        return self.absolute[len(self.root):]

    @property
    def file_url(self):
        return '/files/' + self.relative

    @property
    def thumb_url(self):
        """
        for things that aren't easily thumbnailed images,
        we can return a generic icon instead
        """
        _, ext = os.path.splitext(self.absolute)
        # TODO: use MIME for this

        if ext in TEXT_EXT:
            return '/static/icons/text.png'

        if ext in VID_EXT:
            return '/static/icons/vid.png'

        if ext in IMAGE_EXT:
            return '/static/icons/vid.png'

        return '/static/icons/generic.png'



def is_image(path):
    _, ext = os.path.splitext(path)
    if ext in IMAGE_EXT:
        return True
    return False


class Dir(File):
    @property
    def url(self):
        return '/' + self.relative

    @property
    def thumb_url(self):
        return '/static/icons/folder.png'


MockFileMeta = namedtuple('MockFileMeta', 
    'absolute hits rating rating_hits'.split(' '))
class FileMeta(sqlobject.SQLObject, File):
    """
    store rating metadata about a file, create thumbnails, and more!
    """

    class sqlmeta:
        lazyUpdate = True  # must call #syncUpdate or #sync to save changes

    MOCK = False

    absolute =    sqlobject.StringCol(notNone=True, unique=True,
                                      alternateID=True)
    hits =        sqlobject.IntCol(notNone=True, default=0)
    rating =      sqlobject.FloatCol(notNone=True, default=0.0)
    rating_hits = sqlobject.IntCol(notNone=True, default=0)

    def rate(self, rating):
        """
        store an incoming rating value, out of 10
        would rate/10
        """
        # no crazy bznz
        if rating > 10 or rating < 0:
            raise ValueError('Rating value out of bounds [0 - 10]')
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

    @classmethod
    def for_path(cls, absolute, root=None):
        """get or create for this path"""

        if cls.MOCK:
            return MockFileMeta(absolute=absolute, hits=0, rating=5.5, rating_hits=100)

        try:
            instance = cls.byAbsolute(absolute)
        except sqlobject.SQLObjectNotFound:
            instance = cls(absolute=absolute)
            instance.syncUpdate()
        instance.root = root
        return instance

class Image(File):
    def __init__(self, abs_path, root):
        _, ext = os.path.splitext(abs_path)
        if not ext in IMAGE_EXT:
            raise ValueError('Not an image-extension file', abs_path)

        super(Image, self).__init__(abs_path, root)

    def generate_thumb_in_background(self):
        run_background(gen_thumbnail_if_needed, None, (self.absolute,
                                                       self.thumb_path))

    def generate_thumb(self):
        generate_thumbnail(self.absolute, self.thumb_path)

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
