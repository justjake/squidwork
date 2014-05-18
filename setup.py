from distutils.core import setup

setup(name='squidwork',
      version='0.0.8',
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
          "tornado",       # for web
          "CoffeeScript",  # for web
          "pyScss"         # for minitor, needs pcre-dev or it pisses warnings
        ])
