"""
Transforms configs into JSON
"""

import json
from squidwork.sender import MessageEncoder
from squidwork.config import Service

class ServiceEncoder(MessageEncoder):
    """
    Can encode services as well as the rest of the lot
    """
    def default(self, obj):

        if isinstance(obj, Service):
            return {'prefix': obj.prefix,
                    'URIs': list(obj.URIs)}

        return super(ServiceEndcoder, self).default(obj)
