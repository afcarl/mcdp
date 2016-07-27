# -*- coding: utf-8 -*-
from contracts import contract
from mcdp_posets import Poset
from mcdp_dp.dp_generic_unary import WrapAMap
from mcdp_posets.maps.identity import IdentityMap


__all__ = [
    'Identity',
    'IdentityDP',
    'FunctionNode',
    'ResourceNode',
]


class IdentityDP(WrapAMap):

    @contract(F=Poset)
    def __init__(self, F):
        amap = IdentityMap(F, F)
        WrapAMap.__init__(self, amap)

    def __repr__(self):
        return 'Id(%r)' % self.F


class OpaqueIdentity(WrapAMap):
    """ This is an identity that is never normalized out 
        by series() """
    @contract(F=Poset)
    def __init__(self, F):
        amap = IdentityMap(F, F)
        WrapAMap.__init__(self, amap)

    def __repr__(self):
        return 'OpaqueIdentity(%r)' % self.F

class ResourceNode(OpaqueIdentity):
    pass

class FunctionNode(OpaqueIdentity):
    pass

Identity = IdentityDP
