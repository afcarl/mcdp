# -*- coding: utf-8 -*-
from .dp_generic_unary import WrapAMap
from contracts import contract
from contracts.utils import check_isinstance, raise_wrapped
from mcdp_posets import Map, PosetProduct
from mocdp.exceptions import DPInternalError
from multi_index import get_it


__all__ = [
    'Flatten',
    'Mux',
    'MuxMap',
]

class MuxMap(Map):
    def __init__(self, F, coords):
        try:
            R = get_R_from_F_coords(F, coords)
        except ValueError as e:
            msg = 'Cannot create Mux'
            raise_wrapped(DPInternalError, e, msg, F=F, coords=coords)

        self.coords = coords
        Map.__init__(self, F, R)

    def _call(self, x):
        r = get_it(x, self.coords, reduce_list=tuple)
        return r


class Mux(WrapAMap):

    @contract(coords='seq(int|tuple|list)|int')
    def __init__(self, F, coords):
#         library = get_conftools_posets()
#         _, F = library.instance_smarter(F)
        
        self.amap = MuxMap(F, coords)

        WrapAMap.__init__(self, self.amap)

        # This is used by many things (e.g. series simplification)
        self.coords = coords

    def __repr__(self):
        return 'Mux(%r → %r, %s)' % (self.F, self.R, self.coords)

    def repr_long(self):
        s = 'Mux(%s)' % self.amap.coords.__repr__()
        return s

#
# class Mux(PrimitiveDP):
#
#     @contract(coords='seq(int|tuple|list)|int')
#     def __init__(self, F, coords):
#         library = get_conftools_posets()
#         _, F = library.instance_smarter(F)
#         try:
#             R = get_R_from_F_coords(F, coords)
#         except ValueError as e:
#             msg = 'Cannot create Mux'
#             raise_wrapped(DPInternalError, e, msg, F=F, coords=coords)
#
#         self.coords = coords
#
#         M = PosetProduct(())
#         PrimitiveDP.__init__(self, F=F, R=R, M=M)
#
#     def solve(self, func):
#         if do_extra_checks():
#             self.F.belongs(func)
#
#         r = get_it(func, self.coords, reduce_list=tuple)
#
#         return self.R.U(r)
#
#     def __repr__(self):
#         return 'Mux(%r → %r, %s)' % (self.F, self.R, self.coords)
#
#     def repr_long(self):
#         s = 'Mux(%s)' % self.coords.__repr__()
#         return s

def get_R_from_F_coords(F, coords):
    return get_it(F, coords, reduce_list=PosetProduct)

def get_flatten_muxmap(F0):
    check_isinstance(F0, PosetProduct)
    coords = []
    for i, f in enumerate(F0.subs):
        if isinstance(f, PosetProduct):
            for j, _ in enumerate(f.subs):
                coords.append((i, j))
        else:
            coords.append(i)
    return coords

class Flatten(Mux):
    def __init__(self, F):
#         library = get_conftools_posets()
#         _, F0 = library.instance_smarter(F)
        coords = get_flatten_muxmap(F)
        Mux.__init__(self, F, coords)

    def __repr__(self):
        return 'Flatten(%r→%r, %s)' % (self.F, self.R, self.coords)
