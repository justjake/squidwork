import os
from sqlobject import sqlhub, connectionForURI
import tornado.log
import tornado.web
import tornado.ioloop

import squidwork.web as web
import squidwork.web.debuggable as debuggable
from squidwork.web.monitor import ScssHandler

from file_image import File, Image, Dir, FileMeta, is_image
from misc_handlers import HitCountImageServer, CanUpload, AuthHandler
from directory_lister import DirectoryLister


def configure(args=None):
    """do one-time global setup things"""
    config = web.Config('gifserver')
    config.option('images')    # directories full of images
    config.option('thumbs')    # directory to store thumbnails in
    config.option('database')  # SQLObject database URI
    config.option('app_secret')    # Cookie secret
    config.option('password')   # used for authing
    config.retrieve(args)
    if config.images[-1] is not '/':
        config.images += '/'

    # set up connections
    sqlhub.processConnection = connectionForURI(config.database)
    # socket = squidwork.quick.pub(*config.uris)
    FileMeta.createTable(ifNotExists=True)

    # configure thumbnails
    Image.thumb_dir = config.thumbs

    return config


def main():
    # options
    config = configure()

    handlers = web.handlers(config.raw_config, debug=config.debug)
    handlers += [
        (r'/upload.exe', CanUpload, dict(debug=config.debug, root=config.images + '/uploads')),
        (r'/auth.exe', AuthHandler, dict(secret=config.password, debug=config.debug)),
        (r'/app.js', web.CoffeescriptHandler, dict(source='app.coffee')),
        (r'/style.css', ScssHandler, dict(source='style.scss')),
        (r'/thumbs/(.*)', tornado.web.StaticFileHandler,
                          dict(path=config.thumbs)),
        (r'/files/(.*)', HitCountImageServer, dict(path=config.images)),
        (r'/(.*)', DirectoryLister, dict(debug=config.debug, path=config.images))
    ]

    home = os.path.dirname(os.path.realpath(__file__))
    static = home + '/static'
    templates = home + '/templates'

    if config.debug:
        app_class = debuggable.DebugApplication
    else:
        app_class = tornado.web.Application

    app = app_class(handlers,
                    debug=config.debug,
                    template_path=templates,
                    static_path=static,
                    cookie_secret=config.app_secret)
    try:
        print('Listening on {}'.format(config.port))
        app.listen(config.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print ' keyboard interrupt: exiting.'

if __name__ == '__main__':
    main()
