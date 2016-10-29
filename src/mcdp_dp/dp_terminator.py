# -*- coding: utf-8 -*-
from mcdp_posets import LowerSet, PosetProduct, SpaceProduct, UpperSet

from .primitive import PrimitiveDP


__all__ = [
    'Terminator',
]

class Terminator(PrimitiveDP):
    """ AKA "True"
    
        f |-> True
        
        () |-> Top
    """

    def __init__(self, F):
        R = PosetProduct(())
        I = SpaceProduct(())
        PrimitiveDP.__init__(self, F=F, R=R, I=I)

    def solve(self, f):  # @UnusedVariable
        return UpperSet([()], self.R)
    
    def solve_r(self, r):
        assert r == ()
        maximals = self.F.get_maximal_elements()
        lf = LowerSet(maximals, self.F)
        return lf
    
    def evaluate(self, m):
        assert m == ()
        maximals = self.F.get_maximal_elements()
        LF = LowerSet(maximals, self.F)
        UR = UpperSet([()], self.R)
        return LF, UR

    def __repr__(self):
        return 'Terminator(%r)' % self.F
