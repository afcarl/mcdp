# -*- coding: utf-8 -*-
from contracts import contract
from contracts.utils import check_isinstance
from mcdp_posets import Map, MapNotDefinedHere
from mcdp_posets import RcompUnits
from mcdp_posets import is_top

from .dp_generic_unary import WrapAMap
from .dp_sum import MultValueMap


__all__ = [
    'MultValueDP',
]

class MultValueDP(WrapAMap):
    """
        f ⋅ c ≤ r
        
        We have:
        
            f ⟼ f (⋅U) c
            
        where (⋅U) is the upper continuous extension of multiplication
        (if c = Top and f = 0, then Top * 0 = 0).

        So the corresponding hᵈ is:
        
            if c == 0:
            
                we have 
                
                r ->  if r = 0:   f <= Top
                      if r > 0:   no solutions
            
            if c != Top:
                
                r ⟼ r (⋅U) c1    (or is it?)
                
                with c1 = 1 / c a number. 
                
                Note that we expect that if r = Top, 
            
            if c == Top:
            
                r |->   if r = 0, then f must be <= 0
                        if r = Top, then f <= Top
                        Not Defined if r > 0 but not Top
            
        
    From: The Cuntz semigroup and domain theory
        Klaus Keimel November 26, 2015

    There is no way to extend the multiplication to all of R+ in such a way 
    that it remains continuous for the interval topology. This fact had 
    been overlooked in [8] and had led to misleading statements in [8]. 
    If we extend multiplication by +∞ · 0 = 0 = 0 · (+∞), it remains continuous 
    for the upper topology, if we extend it by +∞ · 0 = +∞ = 0 · (+∞), 
    it remains continuous for the lower topology.

    """
    @contract(F=RcompUnits, R=RcompUnits, unit=RcompUnits)
    def __init__(self, F, R, unit, value):
        check_isinstance(F, RcompUnits)
        check_isinstance(R, RcompUnits)
        check_isinstance(unit, RcompUnits)

        amap = MultValueMap(F=F, R=R, unit=unit, value=value)
        # unit2 = inverse_of_unit(unit)
        # if value = Top:
        #    f |-> f * Top 
        #     
        if is_top(unit, value):
            amap_dual = MultValueDPHelper2Map(R, F)
        elif unit.equal(0.0, value):
            amap_dual = MultValueDPHelper1Map(R, F)
        else:    
            value2 = 1.0 / value
            amap_dual = MultValueMap(F=R, R=F, value=value2)
            
        WrapAMap.__init__(self, amap, amap_dual)




class MultValueDPHelper1Map(Map):
    """
        Implements:
                r ->  if r = 0:   f <= Top
                      if r > 0:   no solutions
    """
    def __init__(self, dom, cod):
        Map.__init__(self, dom=dom, cod=cod)
        
    def _call(self, x):
        # 0 |-> Top
        if self.dom.equal(x, 0.0):
            return self.cod.get_top()
        # otherwise undefined
        raise MapNotDefinedHere(x)
        

class MultValueDPHelper2Map(Map):
    """
        Implements:
         r |->   if r = 0, then f must be <= 0
                 if r = Top, then f <= Top
                 Not Defined if r > 0 but not Top
    """
    def __init__(self, dom, cod):
        Map.__init__(self, dom=dom, cod=cod)
        
    def _call(self, x):
        # 0 -> 0
        if self.dom.equal(x, 0.0):
            return 0.0
        # Top -> Top
        if is_top(self.dom, x):
            return self.cod.get_top()
        # otherwise undefined
        raise MapNotDefinedHere(x)
        
        