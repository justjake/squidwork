"""
Contains a collection datatype used to map between service prefixes
and URIs
"""

from collections import defaultdict

class ManyToMany(object):
    """
    A two-way many-to-many hashmap
    """

    def __init__(self):
        self.a_to_b = defaultdict(lambda: set())
        self.b_to_a = defaultdict(lambda: set())

    def assoc(self, a, b):
        """
        associate value a with value b, so that when you index
        off of b, you get a set of a, and when you index off of a,
        you get a set of b
        """
        self.a_to_b[a].add(b)
        self.b_to_a[b].add(a)

    def subscript_a(self, a):
        """
        Returns all bs associated with a
        """
        return self.a_to_b[a]

    def subscript_b(self, b):
        """
        Returns all as associated with b
        """
        return self.b_to_a[b]

    def has_a(self, a):
        """
        True if a is a key in As
        """
        return a in self.a_to_b 

    def has_b(self, b):
        """
        True if b is a key in Bs
        """
        return b in self.b_to_a

    def As(self):
        """
        all As
        """
        return self.a_to_b.keys()

    def Bs(self):
        """
        all Bs
        """
        return self.b_to_a.keys()

    def deassoc(self, a, b):
        """
        disassociate a from b
        """
        Bs = self.subscript_a(a)
        As = self.subscript_b(b)

        Bs.remove(b)
        As.remove(a)

        if len(Bs) == 0:
            # a no longer associated with anything
            del self.a_to_b[a]

        if len(As) == 0:
            # b no longer associated with anythong
            del self.b_to_a[b]
