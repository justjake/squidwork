from distutils.core import setup

setup(name='squidwork',
      version='0.0.8r2',
      description='trivial JSON event protocol over ZeroMQ',
      author='Jake Teton-Landis',
      author_email='just.1.jake@gmail.com',
      url='https://github.com/justjake/squidwork',
      packages=[
          'squidwork',
          'squidwork.config',
          'squidwork.web',
          'squidwork.web.monitor',
          #'liege',
          ],
      package_dir={
          'squidwork': 'squidwork',
          'squidwork.config': 'squidwork/config',
          'squidwork.web': 'squidwork/web',
          'squidwork.web.monitor': 'squidwork/web/monitor',
          #'liege': 'liege',
          },
      package_data={
          'squidwork.web': ['templates/*'],
          'squidwork.web.monitor': ['templates/*'],
          #'liege': ['templates/*'],
          },
      install_requires=[
          "pyzmq",
          "pyyaml",
          "tornado=3.2.2",       # for web
          "CoffeeScript",  # for web
          "sqlobject",      # for gifserver 
          "pyScss", # for minitor, needs pcre-dev or it pisses warnings
          "werkzeug",  # for debugging
          'Wand'       # turns out PIL is shit, this should be better
        ])
