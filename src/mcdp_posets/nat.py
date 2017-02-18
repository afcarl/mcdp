# -*- coding: utf-8 -*-
import functools
import random
import sys

from contracts.utils import raise_desc
from mcdp import MCDPConstants
from mcdp.development import do_extra_checks, mcdp_dev_warning

from .poset import NotLeq, Poset
from .space import NotBelongs, NotEqual


__all__ = [
   'Nat',
   'Int',
]

class NatTop():
    def __repr__(self):
        return "⊤"
    def __eq__(self, x):
        return isinstance(x, NatTop)
    def __hash__(self):
        return 43

class Nat(Poset):
    """
        This is represented as "int". 
        
        [0, 1, 2, 3) U {T}
    """
    def __init__(self):
        self.top = NatTop()

    def get_bottom(self):
        return 0

    def get_top(self):
        return self.top

    def witness(self):
        return self.get_bottom()

    def belongs(self, x):
        if isinstance(x, int):
            if x >= 0:
                return
            else:
                msg = '%s ≰ %s' % (0, x)
                raise_desc(NotBelongs, msg, x=x)
        else:
            if x == self.top:
                return

            raise_desc(NotBelongs, 'Not a valid Nat.', x=x)


    def join(self, a, b):
        # first the common case
        if isinstance(a, int) and isinstance(b, int):
            return max(a, b)
        # generic case
        if self.leq(a, b):
            return b
        if self.leq(b, a):
            return a
        assert False # pragma: no cover

    def meet(self, a, b):
        # first the common case
        if isinstance(a, int) and isinstance(b, int):
            return min(a, b)
        # generic case
        if self.leq(a, b):
            return a
        if self.leq(b, a):
            return b
        assert False # pragma: no cover

    def get_test_chain(self, n):
        s = [0]
        
        if MCDPConstants.Nat_chain_include_maxint:
            s.append(sys.maxint)
        
        f = lambda: random.randint(1, n) # xxx
        while len(s) < n - 1: # leave 1:  top 
            x = f()
            if not x in s:
                s.append(x)
        s = sorted(s)
        s.append(self.get_top())
        return s

    def __eq__(self, other):
        return isinstance(other, Nat)

    def __repr__(self):
        if MCDPConstants.use_unicode_symbols:
            return "ℕ" # TODO: make this configurable
        else:
            return "N"

    def format(self, x):
        if isinstance(x, int):
            return '%d' % x
        elif isinstance(x, long):
            return '%dL!' % x
        else:
            if x == self.top:
                return self.top.__repr__()
            else: # pragma: no cover
                raise ValueError(x, type(x)) 

    def _leq(self, a, b):
        # common case
        if isinstance(a, int) and isinstance(b, int):
            return a <= b
        # generic case
        if a == b:
            return True
        if a == self.top:
            return False
        if b == self.top:
            return True
        
        raise ValueError((a,b)) # pragma: no cover

    def leq(self, a, b):
        return self._leq(a, b)

    def check_leq(self, a, b):
        if do_extra_checks():
            self.belongs(a)
            self.belongs(b)
        if not self._leq(a, b):
            msg = '%s ≰ %s' % (a, b)
            raise NotLeq(msg)

    def check_equal(self, x, y):
        if not (x == y):
            raise NotEqual('%s != %s' % (x, y))


# Optimization: we use these instances
Nat_add_Nat = Nat()
Nat_add_top = Nat_add_Nat.get_top()
 
def Nat_add(a, b):
    """ Addition on Nat, extended for top """
    from mcdp_posets.poset import is_top
    N = Nat_add_Nat
    
    if is_top(N, a) or is_top(N, b):
        return Nat_add_top
    
    mcdp_dev_warning('catch overflow')
    assert isinstance(a, int), (a, type(a))
    assert isinstance(b, int), (b, type(b))
    res = a + b
    
    if res > sys.maxint:
        return N.get_top()
    
    assert isinstance(res, int), (res, type(res))
    return res


def Nat_mult_uppersets_continuous_seq(seq):
    """ Multiplication on Nat, extended for top, so that top*0 = Top """
    return functools.reduce(Nat_mult_uppersets_continuous, seq)

def Nat_mult_uppersets_continuous(a, b):
    """ Multiplication on Nat, extended for top, so that top*0 = 0 """
    from mcdp_posets.poset import is_top
    N = Nat_add_Nat
    
    a_is_zero = a == 0
    b_is_zero = b == 0
    
    if a_is_zero or b_is_zero:
        return 0
    
    if is_top(N, a) or is_top(N, b):
        return Nat_add_top
    
    mcdp_dev_warning('catch overflow')
    assert isinstance(a, int), (a, type(a))
    assert isinstance(b, int), (b, type(b))
    res = a * b
    if res > sys.maxint:
        return N.get_top()
    
    assert isinstance(res, int), (res, type(res))
    return res


def Nat_mult_lowersets_continuous(a, b):
    """ Multiplication on Nat, extended for top, so that top*0 = Top """
    from mcdp_posets.poset import is_top
    N = Nat_add_Nat
     
    if is_top(N, a) or is_top(N, b):
        return Nat_add_top

    assert isinstance(a, int), (a, type(a))
    assert isinstance(b, int), (b, type(b))

    res = a * b
    if res > sys.maxint:
        return N.get_top()
    
    assert isinstance(res, int), (res, type(res))
    return res

def RcompUnits_mult_lowersets_continuous(A, a, B, b, C):
    """ Multiplication on Rcompunits, extended for top, so that top*0 = Top """
    from mcdp_posets.poset import is_top
     
    if is_top(A, a) or is_top(B, b):
        return C.get_top()

    mcdp_dev_warning('catch overflow')
    return a * b

IntBottom = "int:-inf"
IntTop = "int:+inf"

class Int(Poset):
    """
        Integers (no top or bottom)
        ["-inf", ..., -1, 0, 1, ..., "+inf"]
    """
    def __init__(self):
        self.top = IntTop
        self.bottom = IntBottom

    def get_bottom(self):
        return self.bottom

    def get_top(self):
        return self.top

    def witness(self):
        return 42

    def belongs(self, x):
        if x == self.top or x == self.bottom:
            return

        if not isinstance(x, int):
            raise_desc(NotBelongs, 'Not an int.', x=x)

    def join(self, a, b):
        if self.leq(a, b):
            return b
        if self.leq(b, a):
            return a
        assert False # pragma: no cover

    def meet(self, a, b):
        if self.leq(a, b):
            return a
        if self.leq(b, a):
            return b
        assert False # pragma: no cover

    def get_test_chain(self, n):
        s = []
        f = lambda: random.randint(-100, 100)
        while len(s) < n - 2:
            x = f()
            if not x in s:
                s.append(x)
        s = sorted(s)
        s.insert(0, self.get_bottom())
        s.append(self.get_top())
        return s

    def __eq__(self, other):
        return isinstance(other, Int)

    def __repr__(self):
        if MCDPConstants.use_unicode_symbols:
            return "Z" # XXX
        else:
            return "Z"

    def format(self, x):
        if x == self.top:
            return self.top.__repr__()
        if x == self.bottom:
            return self.bottom.__repr__()
        return '%d' % x

    def _leq(self, a, b):
        if a == b:
            return True
        if a == self.top:
            return False
        if b == self.top:
            return True
        if a == self.bottom:
            return True
        if b == self.bottom:
            return False
        return a <= b

    def leq(self, a, b):
        return self._leq(a, b)

    def check_leq(self, a, b):
        if do_extra_checks():
            self.belongs(a)
            self.belongs(b)
        if not self._leq(a, b):
            msg = '%s ≰ %s' % (a, b)
            raise NotLeq(msg)

    def check_equal(self, x, y):
        if not (x == y):
            raise NotEqual('%s != %s' % (x, y))


