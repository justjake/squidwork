"""
squidwork - python3

simple python event typing and routing using ZeroMQ sockets
sends two-part messages over the ZeroMQ sockets.
    PART1: STRING like 'myapp/user/login@host.name' aka the origin
    PART2: JSON of format {
        'content': JSON,
        'time'   : STRING like '%Y-%m-%d %H:%M',
        'origin' : STRING like 'myapp/user/login@host.name'
    }
We send the message in two seperate parts to handle endpoint
subscriptions neatly: ZeroMQ manages subscriptions by checking
for byte equality between the subscription filters and every
inbound message. Byte-string equality is easy on strings, and
hard on JSON coming from an unsorted hashmap ;)

we put the hostname origin at the end because who cares where
its coming from? only what the API startpoint is.

All wire bytes are UTF8-encoded string

More info: http://api.zeromq.org/4-0:zmq-setsockopt#toc6
"""

__author__ = 'Jake Teton-Landis <just.1.jake@gmail.com>'

from message import Message
from reciever import Reciever
from sender import Sender, MessageEncoder
from api import API
