from __future__ import print_function
import zmq
from pprint import pprint

from squidwork import Reciever

def main():
    context = zmq.Context.instance()
    socket = context.socket(zmq.SUB)
    print('Binding socket...')
    socket.connect("tcp://127.0.0.1:9999")
    print('Done.')
    # socket.connect('ipc://tmp/squidwork_test')

    reciever = Reciever(socket, 'test')

    print('Entering recieve loop.')
    loop(reciever)

def loop(reciever):
    while True:
        try:
            pprint(reciever.recieve())
        except ValueError as e:
            pprint(e)

if __name__ == '__main__':
    main()
