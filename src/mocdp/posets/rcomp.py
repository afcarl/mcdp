# -*- coding: utf-8 -*-
from .poset import NotLeq, Poset
from contracts.utils import check_isinstance
import numpy as np

__all__ = [
   'Rcomp',
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

        check_isinstance(x, float)
        if not 0 <= x:
            msg = '%s ≰ %s' % (0, x)
            raise ValueError(msg)

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
        return "ℜ ⋃ {⊤}"

    def format(self, x):
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
