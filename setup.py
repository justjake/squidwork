from distutils.core import setup

setup(name='squidwork',
        version='0.0.3',
        description='trivial JSON event protocol over ZeroMQ',
        author='Jake Teton-Landis',
        author_email='just.1.jake@gmail.com',
        url='https://github.com/justjake/squidwork',
        packages=['squidwork', 'squidwork.config', 'squidwork.web'],
        package_dir={
            'squidwork': 'squidwork',
            'squidwork.config': 'squidwork/config',
            'squidwork.web' : 'squidwork/web',
            },
        package_data={'squidwork.web': ['templates/*']},
        install_requires=[
          "pyzmq",
          "pyyaml",
          "tornado",       # for websocket
          "CoffeeScript",  # for websocket
          "pyScss"
          ]
        )
