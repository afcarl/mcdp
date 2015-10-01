# -*- coding: utf-8 -*-
from .poset import NotLeq, Poset
from contracts.utils import raise_desc
from mocdp.posets.space import NotBelongs
import numpy as np

__all__ = [
   'Rcomp',
   'RcompUnits',
]

class RcompTop():
    def __repr__(self):
        return "⊤"
    def __eq__(self, x):
        return isinstance(x, RcompTop)
    def __hash__(self):
        return 42  # "RCompTop"

class Rcomp(Poset):
    def __init__(self):
        self.top = RcompTop()

    def get_bottom(self):
        return 0.0

    def get_top(self):
        return self.top

    def belongs(self, x):
        if x == self.top:
            return True

        if not isinstance(x, float):
            raise_desc(NotBelongs, 'Not a float.', x=x)

        if not 0 <= x:
            msg = '%s ≰ %s' % (0, x)
            raise_desc(NotBelongs, msg, x=x)

        return True

    def join(self, a, b):
        if self.leq(a, b):
            return b
        if self.leq(b, a):
            return b
        assert False

    def meet(self, a, b):
        if self.leq(a, b):
            return a
        if self.leq(b, a):
            return b
        assert False

    def get_test_chain(self, n):
        s = [self.get_bottom()]
        s.extend(sorted(np.random.rand(n - 2) * 10))
        s.append(self.get_top())
        return s

    def __eq__(self, other):
        return isinstance(other, Rcomp)

    def __repr__(self):
#         return "ℜ ⋃ {⊤}"
#         return "ℜ"
        return "R"

    def format(self, x):
        self.belongs(x)
        if x == self.top:
            return self.top.__repr__()
        else:
            return '%.3f' % x

    def _leq(self, a, b):
        if a == b:
            return True
        if a == self.top:
            return False
        if b == self.top:
            return True
        return a <= b

    def check_leq(self, a, b):
        self.belongs(a)
        self.belongs(b)
        if not self._leq(a, b):
            msg = '%s ≰ %s' % (a, b)
            raise NotLeq(msg)

    def multiply(self, a, b):
        """ Multiplication, extended for top """
        if a == self.top or b == self.top:
            return self.top
        return a * b

    def add(self, a, b):
        """ Addition, extended for top """
        if a == self.top or b == self.top:
            return self.top
        return a + b

class RcompUnits(Rcomp):
    def __init__(self, units):
        Rcomp.__init__(self)
        self.units = units

    def __repr__(self):
        s = Rcomp.__repr__(self)
        return s + "[%s]" % self.units
#
#     def belongs(self, x):
#         return Rcomp.belongs(self, x)
    def __eq__(self, other):
        if not isinstance(other, Rcomp):
            return False

        if isinstance(other, RcompUnits):
            return other.units == self.units

        return True










