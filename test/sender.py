from time import sleep
import zmq

from squidwork import Sender

def main():
    context = zmq.Context.instance()
    socket = content.socket(zmq.PUB)
    sender = Sender('test', socket)

    socket.bind('ipc://tmp/squidwork_test')

    loop(sender, 10)

def loop(sender, sleeps):
    k = 0
    while True:
        sleep(sleeps)
        data = range(0, k)
        print "[{k}]: sending {data}".format(k=k, data=str(data))
        sender.send(range(0, k))
        k = k + 1

if __name__ == '__main__':
    main()
