# squidwork.

Simple JSON wrapper protocol for ZeroMQ.

## Protocol: Pub-Sub Message Envelopes

http://zguide.zeromq.org/page:all#Pub-Sub-Message-Envelopes

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

All wire bytes are UTF8-encoded string, and start with the
string 'all'.

[1]: http://api.zeromq.org/4-0:zmq-setsockopt#toc6

## module `quick`

You can use `squidwork.quick.pub` and `squidwork.quick.sub` to
create the type of ZeroMQ socket you need to send or receive events,
and never have to import zmq yourself, or worry about the other
socket types. Here is a simple event publisher and a reciever:

```python
# event emitter
from squidwork.quick import pub
from squidwork import Sender
from time import sleep

endpoint = Sender(pub('tcp://127.0.0.1'))
while True:
    sleep(3)
    endpoint.send(['hello', 'world'])
```

```python
# event listener
from squidwork.quick import pub
from squidwork import Sender

reciever = Reciever(sub('tcp://127.0.0.1'))
while True:
    # this call blocks
    message = reciever.recieve()

    print message.origin
    print message.time
    print message.content
```

## Service definitions

squidwork also provides a main-entrypoint framework for loading
service definitions from a YAML file, so that we can define in
one place an apartment-wide list of ZeroMQ publishers. Now,
we could just use broadcast services to do anounces but we're 
an apartment so like a ten-line file synced with git is much easier.

We also support reading the file from an HTTP server (although this 
is so far untested).

## Working with the code

### Requirements

1. pyzmq
2. pyyaml (for config only)

### Integration Tests

The tests in `tests/` come in pairs, one sender and one receiver for each
strategy.
