# -*- coding: utf-8 -*-
from .poset import Poset
from .space import NotBelongs
from contracts.utils import raise_desc


__all__ = [
   'Single',
]


class Single(Poset):
    def __init__(self, element):
        self.element = element

    def get_bottom(self):
        return self.element 

    def get_top(self):
        return self.element 

    def belongs(self, x):
        if not x == self.element:
            msg = 'Not the single element.'
            raise_desc(NotBelongs, msg, x=x)

    def join(self, a, b):
        self.belongs(a)
        self.belongs(b)
        assert a == b == self.element
        return self.element

    def meet(self, a, b):
        self.belongs(a)
        self.belongs(b)
        assert a == b == self.element
        return self.element

    def witness(self):
        return self.element

    def get_test_chain(self, n):  # @UnusedVariable
        return [self.element]

    def __eq__(self, other):
        return isinstance(other, Single) and other.element == self.element

    def __repr__(self):
        return "{%s}" % self.element

    def format(self, x):
        return x.__str__()

    def check_leq(self, a, b):
        self.belongs(a)
        self.belongs(b)
        return True

    def check_equal(self, a, b):  # @UnusedVariable
        return True


