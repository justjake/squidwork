import zmq
from pprint import pprint

from squidwork import Reciever

def main():
    context = zmq.Context.instance()
    socket = content.socket(zmq.PUB)
    reciever = Reciever('test', socket)

    socket.connect('ipc://tmp/squidwork_test')

    loop(reciever)

def loop(reciever):
    while True:
        try:
            pprint(reciever.recive())
        except ValueError as e:
            pprint(e)

if __name__ == '__main__':
    main()
