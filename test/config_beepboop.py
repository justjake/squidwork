from __future__ import print_function
from squidwork import Sender
from squidwork.config import get_services, Service
from squidwork.quick import pub
from pprint import pprint as pp
from time import sleep

services = get_services()

our_names = 'beep', 'boop'
senders = {}

pp("Creating senders...")
for name in our_names:
    route = name + '/sender'
    service = Service.for_prefix(route)
    uri = service.uri
    print("Got URI: " + str(uri))
    sender = Sender(pub(uri), route)
    senders[name] = sender

pp("Done:")
pp(senders)

while True:
    for name in our_names:
        sleep(3)
        pp("Sending " + name)
        senders[name].send(name)
