from __future__ import print_function
from time import sleep

from squidwork import Sender
from squidwork.quick import pub

def main():
    print('Binding socket...')
    sender = Sender(pub('tcp://127.0.0.1:9999'), 'test')
    print('Done.')

    print('Entering send loop...')
    loop(sender, 3.0)

def loop(sender, sleeps):
    k = 0
    while True:
        sleep(sleeps)
        data = range(0, k)
        print("[{k}]: sending {data}".format(k=k, data=str(data)))
        sender.send(range(0, k))
        k = k + 1

if __name__ == '__main__':
    main()
