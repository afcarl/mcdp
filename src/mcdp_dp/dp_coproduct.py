# -*- coding: utf-8 -*-
from contracts import contract
from contracts.utils import check_isinstance, indent, raise_desc
from mcdp_posets import (
    Coproduct1, NotBelongs, NotEqual, get_types_universe, poset_minima)
from mcdp_posets.find_poset_minima.baseline_n2 import poset_maxima
from mcdp.development import do_extra_checks, mcdp_dev_warning

from .primitive import NotFeasible, PrimitiveDP


__all__ = [
    'CoProductDP',
]


class CoProductDP(PrimitiveDP):
    """ Returns the co-product of 1+ dps. """

    @contract(dps='tuple,seq[>=1]($PrimitiveDP)')
    def __init__(self, dps):
        check_isinstance(dps, tuple)
        tu = get_types_universe()

        F1 = dps[0].get_fun_space()
        R1 = dps[0].get_res_space()

        for dp in dps:
            Fj = dp.get_fun_space()
            Rj = dp.get_res_space()

            try:
                tu.check_equal(F1, Fj)
                tu.check_equal(R1, Rj)
            except NotEqual:
                msg = 'Cannot form the co-product.'
                raise_desc(ValueError, msg, dps=dps)

        F = F1
        R = R1
        Ms = [dp.get_imp_space() for dp in dps]

        self.dps = dps
        self.M = Coproduct1(tuple(Ms))
        PrimitiveDP.__init__(self, F=F, R=R, I=self.M)

    def evaluate(self, m):
        i, mi = self.M.unpack(m)
        return self.dps[i].evaluate(mi)

#     def evaluate_f_m(self, f, m):
#         """ Returns the resources needed
#             by the particular implementation m """
#         i, xi = self.M.unpack(m)
#         return self.dps[i].evaluate_f_m(f, xi)

    def get_implementations_f_r(self, f, r):
        """ Returns a nonempty set of elements of self.M.
            Might raise NotFeasible() """
        res = set()
        es = []
        ms = None
        for j, dp in enumerate(self.dps):
            try:
                ms = dp.get_implementations_f_r(f, r)
                # print('%s: dp.get_implementations_f_r(f, r) = %s ' % (j, ms))
                for m in ms:
                    if do_extra_checks():
                        Mj = dp.get_imp_space()
                        try:
                            Mj.belongs(m)
                        except NotBelongs:
                            raise ValueError(dp)
                    res.add(self.M.pack(j, m))
            except NotFeasible as e:
                es.append(e)
        if not ms:
            # no one was feasible
            msg = 'None was feasible'
            msg += '\n\n' + '\n\n'.join(str(e) for e in es)
            raise_desc(NotFeasible, msg, f=f, r=r, self=self)

        if do_extra_checks():
            for _ in res:
                self.M.belongs(_)

        return res

    def solve(self, f):
        R = self.get_res_space()

        s = []

        mcdp_dev_warning('use specific operation on antichains')
        for dp in self.dps:
            rs = dp.solve(f)
            s.extend(rs.minimals)

        res = R.Us(poset_minima(s, R.leq))

        return res

    def solve_r(self, r):
        F = self.get_fun_space()

        s = []

        mcdp_dev_warning('use specific operation on antichains')
        for dp in self.dps:
            lf = dp.solve_r(r)
            s.extend(lf.maximals)

        res = F.Ls(poset_maxima(s, F.leq))

        return res

    def __repr__(self):
        s = "^".join('%s' % x for x in self.dps)
        return 'CoProduct(%s)' % s

    def repr_long(self):
        s = 'CoProduct  %% %s ⇸ %s' % (self.get_fun_space(), self.get_res_space())
        for dp in self.dps:
            r1 = dp.repr_long()
            s += '\n' + indent(r1, '. ', first='^ ')
        return s
    
    def repr_h_map(self):
        con = " ∪ ".join('h%d(f)' % (i+1) for i in range(len(self.dps)))
        return 'f ⟼ Min {%s}' % con
    
    def repr_hd_map(self):
        con = " ∪ ".join('h*%d(r)' % (i+1) for i in range(len(self.dps)))
        return 'r ⟼ Max {%s}' % con
