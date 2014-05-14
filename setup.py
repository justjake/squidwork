from distutils.core import setup

setup(name='squidwork',
        version='0.0.3',
        description='trivial JSON event protocol over ZeroMQ',
        author='Jake Teton-Landis',
        author_email='just.1.jake@gmail.com',
        url='https://github.com/justjake/squidwork',
        packages=['squidwork', 'squidwork.config', 'squidwork.websocket'],
        install_requires=[
          "pyzmq",
          "pyyaml",
          "tornado" # for websocket
          ]
        )
