from __future__ import print_function
from squidwork import Sender
from squidwork.config import create_argparser, get_services, Service
from squidwork.quick import pub
from pprint import pprint as pp
from time import sleep

services = get_services(create_argparser().parse_args())

our_names = 'beep', 'boop'
senders = {}

pp("Creating senders...")
for name in our_names:
    route = name + '/sender'
    service = Service.for_exact_prefix(route)
    uris = service.URIs
    print("Got URIs: " + str(uris))
    sender = Sender(pub(*uris), route)
    senders[name] = sender

pp("Done:")
pp(senders)

while True:
    for name in our_names:
        sleep(3)
        pp("Sending " + name)
        senders[name].send([name])
