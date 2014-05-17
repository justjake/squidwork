from __future__ import print_function
"""
Listens to everything configured in your config file, and logs it.
"""
import threading
from datetime import datetime
from pprint import pprint as pp
from time import sleep

from squidwork.config import Config, Service
from squidwork.quick import sub
from squidwork import Reciever


def main():
    # we don't care about the value because we're only interested in service
    # definitions. Unfortunatley you may need a dummy service definition
    Config().retrieve()
    uris = Service.all_uris()

    if len(uris) == 0:
        print('No URIs! Exiting.')
        return

    print('Will listen to uris: ' + str(uris))

    for u in uris:
        create_listener_thread(u).start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print(' keyboard interrupt, exiting.')
        return


def log(message):
    in_time = datetime.today()
    timestamp = "Sent: {out}, Recv: {in_}, delta: {diff}s".format(
        out=message.time.isoformat(),
        in_=in_time.isoformat(),
        diff=(in_time - message.time).seconds)
    origin = "Origin: " + str(message.origin)

    print(timestamp)
    print(origin)
    pp(message.content)


def create_listener_thread(uri):
    def body():
        print('Listening for all messages from ' + uri)
        recv = Reciever(sub(uri))
        while True:
            log(recv.recieve())
    t = threading.Thread(target=body)
    t.daemon = True
    return t

if __name__ == '__main__':
    main()
