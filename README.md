# squidwork.

Simple JSON wrapper protocol for ZeroMQ.

We send two-part messages over the ZeroMQ sockets:

    PART1: (the origin)  STRING like 'myapp/user/login@host.name'
    PART2: (the message) JSON of format {
        'content': JSON,
        'time'   : STRING like '%Y-%m-%d %H:%M',
        'origin' : STRING like 'myapp/user/login@host.name'
    }

We send the message in two seperate parts to handle endpoint
subscriptions neatly: ZeroMQ manages subscriptions by checking
for byte equality between the subscription filters and every
inbound message. [More info][1].
Byte-string equality is easy on strings, and
hard on JSON coming from an unsorted hashmap ;)

we put the hostname origin at the end because who cares where
its coming from? only what the API startpoint is.

All wire bytes are UTF8-encoded string

[1]: http://api.zeromq.org/4-0:zmq-setsockopt#toc6
