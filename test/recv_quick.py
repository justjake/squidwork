from __future__ import print_function
from pprint import pprint

from squidwork import Reciever
from squidwork.quick import sub

def main():
    print('Binding socket...')
    socket = sub("tcp://127.0.0.1:9999")
    print('Done.')

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
