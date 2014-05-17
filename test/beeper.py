"""
beeper.py for conf version 2
"""

from time import sleep
import threading

from squidwork.config import Config
from squidwork.quick import pub
from squidwork import Sender


def main():
    # Config: app name (defaults to $0)
    config = Config('beeper.py')
    # define what keys to read from settings / optional cli args
    # if options are not provided by cli args, then they MUST be in the
    # config.
    #
    # -'s in names are read in python as _'s
    # types are optional, but useful for argparse
    config.option('beep-rate', type=float)
    config.option('boop-rate', type=float)

    # parses args, loads the config file, gets options, throws errors
    # if options not satisfied
    config.retrieve()

    socket = pub(*config.uris)

    # can now read config values as proprties of the Config instance
    beep_thread('beep', socket, config.beep_rate).start()
    beep_thread('boop', socket, config.boop_rate).start()

    print 'URIs: ' + str(config.uris)

    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        print " keyboard interrupt, exiting."


def beep_thread(thing_to_send, socket, rate):
    def data(i):
        return dict(data=thing_to_send, seq=i)

    def fn():
        print 'Will send {} every {} seconds'.format(thing_to_send, rate)
        sender = Sender(socket, str(thing_to_send))
        i = 0
        while True:
            sleep(rate)
            print 'sending {}'.format(data(i))
            sender.send(data(i))
            i += 1

    t = threading.Thread(target=fn)
    t.daemon = True
    return t

if __name__ == '__main__':
    main()
