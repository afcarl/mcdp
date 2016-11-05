# -*- coding: utf-8 -*-
import functools

from contracts import contract
from contracts.utils import check_isinstance, raise_wrapped
from mcdp_maps.repr_map import sumn_repr_map
from mcdp_posets import (Int, Poset, Space, get_types_universe, Map, Nat, PosetProduct,
                         Rcomp, RcompUnits, is_top)
from mcdp_posets.rcomp_units import rcomp_add
import numpy as np


__all__ = [
    'SumNMap',
    'SumNNatsMap',
    'SumNIntMap',
    'SumNRcompMap',
]


_ = Space
 

class SumNMap(Map):
    
    @contract(Fs='tuple, seq[>=2]($RcompUnits)', R=RcompUnits)
    def __init__(self, Fs, R):
        for _ in Fs:
            check_isinstance(_, RcompUnits)
        check_isinstance(R, RcompUnits)
        self.Fs = Fs
        self.R = R
        
        sum_dimensionality_works(Fs, R)
        
        dom = PosetProduct(self.Fs)
        cod = R

        Map.__init__(self, dom=dom, cod=cod)
        
    def _call(self, x):
        res = sum_units(self.Fs, x, self.R)
        return res
    
    def __repr__(self):
        return 'SumNMap(%s → %s)' % (self.dom, self.cod)
    
    def repr_map(self, letter):
        return sumn_repr_map(letter, len(self.Fs))
    

class SumNRcompMap(Map):
    """ Sum of Rcomp. """
    
    @contract(n='int,>=0')
    def __init__(self, n):
        P = Rcomp()
        dom = PosetProduct((P,)*n)
        cod = P
        self.n = n
        Map.__init__(self, dom, cod)
        
    def _call(self, x):
        return functools.reduce(rcomp_add, x)

    def __repr__(self):
        return 'SumNRcompMap(%s)' % self.n
    
    def repr_map(self, letter):
        return sumn_repr_map(letter, self.n)

def sum_dimensionality_works(Fs, R):
    """ Raises ValueError if it is not possible to sum Fs to get R. """
    for Fi in Fs:
        check_isinstance(Fi, RcompUnits)
    check_isinstance(R, RcompUnits)

    for Fi in Fs:
        ratio = R.units / Fi.units
        try:
            float(ratio)
        except Exception as e: # pragma: no cover
            raise_wrapped(ValueError, e, 'Could not convert.', Fs=Fs, R=R)


# Fs: sequence of Rcompunits
def sum_units(Fs, values, R):
    for Fi in Fs:
        check_isinstance(Fi, RcompUnits)
    res = 0.0
    for Fi, x in zip(Fs, values):
        if is_top(Fi, x):
            return R.get_top()

        # reasonably sure this is correct...
        try:
            factor = 1.0 / float(R.units / Fi.units)
        except Exception as e:  # pragma: no cover (DimensionalityError)
            raise_wrapped(Exception, e, 'some error', Fs=Fs, R=R)

        try:
            res += factor * x
        except FloatingPointError as e:
            if 'overflow' in str(e):
                res = np.inf
                break
            else:
                raise

    if np.isinf(res):
        return R.get_top()

    return res


class SumNIntMap(Map):
    """ Sum of many spaces that can be cast to Int. """
    @contract(Fs='tuple, seq[>=2]($Space)', R=Poset)
    def __init__(self, Fs, R):
        dom = PosetProduct(Fs)
        cod = R
        Map.__init__(self, dom=dom, cod=cod)

        tu = get_types_universe()
        self.subs = []
        target = Int()
        for F in Fs:
            # need F to be cast to Int
            F_to_Int, _ = tu.get_embedding(F, target)
            self.subs.append(F_to_Int)

        self.to_R, _ = tu.get_embedding(target, R)

    def _call(self, x):
        res = 0
        target = Int()
        for xe, s in zip(x, self.subs):
            xe_int = s(xe)
            res = target.add(res, xe_int) # XXX
        r = self.to_R(res)
        return r
    
    def repr_map(self, letter):
        return sumn_repr_map(letter, self.n)


class SumNNatsMap(Map):

    """ sums together N natural numbers """
    def __init__(self, n):
        self.n = n
        N = Nat()
        dom = PosetProduct((N,) * n)
        cod = N
        Map.__init__(self, dom=dom, cod=cod)
        self.top = cod.get_top()
        self.n = n

    def _call(self, x):
        assert isinstance(x, tuple) and len(x) == self.n
        top = self.top
        res = 0
        N = self.dom[0]
        for xi in x:
            if is_top(N, xi):
                return top
            res += xi
        if np.isinf(res):
            return top

        return res
    
    def repr_map(self, letter):
        return sumn_repr_map(letter, self.n)
