from __future__ import print_function
"""
Listens to everything configured in your config file, and logs it.
"""
import threading
from datetime import datetime
from pprint import pprint as pp
from time import sleep

import squidwork.config as config
from squidwork.quick import sub
from squidwork import Reciever

#print_lock = threading.Lock()

def main():
    services = config.get_services()

    print("All services:")
    pp(services)

    uris = set()
    for svc in services:
        uris = uris.union(svc.URIs)

    threads = [create_listener_thread(u) for u in uris]

    for t in threads:
        t.daemon = True # i don't really know what this does
        t.start()

    while True:
        # wait for death
        sleep(1)

def log(message):
    in_time = datetime.today()
    timestamp = "Sent: {out}, Recv: {in_}, delta: {diff}s".format(
            out=message.time.isoformat(),
            in_=in_time.isoformat(),
            diff=(in_time - message.time).seconds)
    origin = "Origin: " + str(message.origin)

    #print_lock.acquire()
    print(timestamp)
    print(origin)
    pp(message.content)
    #print_lock.release()



def create_listener_thread(uri):
    def body():
        print('Listening for all messages from ' + uri)
        recv = Reciever(sub(uri))
        while True:
            log(recv.recieve())
    return threading.Thread(target=body)

if __name__ == '__main__':
    main()
