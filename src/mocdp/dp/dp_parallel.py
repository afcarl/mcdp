# -*- coding: utf-8 -*-
from .primitive import PrimitiveDP
from contracts.utils import indent
from mocdp.dp.dp_series import get_product_compact
from mocdp.dp.primitive import NormalForm
from mocdp.exceptions import do_extra_checks
from mocdp.posets import Map, PosetProduct, UpperSet, UpperSets, poset_minima
import itertools


__all__ = [
    'Parallel',
]


class Parallel(PrimitiveDP):

    def __init__(self, dp1, dp2):
        from mocdp import get_conftools_dps
        library = get_conftools_dps()
        _, self.dp1 = library.instance_smarter(dp1)
        _, self.dp2 = library.instance_smarter(dp2)

        F1 = self.dp1.get_fun_space()
        F2 = self.dp2.get_fun_space()
        F = PosetProduct((F1, F2))
        R1 = self.dp1.get_res_space()
        R2 = self.dp2.get_res_space()

        R = PosetProduct((R1, R2))

        M1 = self.dp1.get_imp_space_mod_res()
        M2 = self.dp2.get_imp_space_mod_res()
        # M = SpaceProduct((M1, M2))
        M, _, _ = get_product_compact(M1, M2)
        self.M1 = M1
        self.M2 = M2

        PrimitiveDP.__init__(self, F=F, R=R, M=M)
        
    def get_implementations_f_r(self, f, r):
        f1, f2 = f
        r1, r2 = r
        _, pack, _ = get_product_compact(self.M1, self.M2)

        m1s = self.dp1.get_implementations_f_r(f1, r1)
        m2s = self.dp2.get_implementations_f_r(f2, r2)
        options = set()
        for m1 in m1s:
            for m2 in m2s:
                m = pack(m1, m2)
                options.add(m)

        if do_extra_checks():
            for _ in options:
                self.M.belongs(_)

        return options
        
    def evaluate_f_m(self, f, m):
        """ Returns the resources needed
            by the particular implementation m """
        _, _, unpack = get_product_compact(self.M1, self.M2)
        f1, f2 = f
        m1, m2 = unpack(m)
        r1 = self.dp1.evaluate_f_m(f1, m1)
        r2 = self.dp2.evaluate_f_m(f2, m2)
        return (r1, r2)

    def solve(self, f):
        if do_extra_checks():
            F = self.get_fun_space()
            F.belongs(f)

        f1, f2 = f

        r1 = self.dp1.solve(f1)
        r2 = self.dp2.solve(f2)
        
        R = self.get_res_space()
        s = []
        for m1, m2 in itertools.product(r1.minimals, r2.minimals):
            s.append((m1, m2))

        res = R.Us(set(s))

        if do_extra_checks():
            tres = self.get_tradeoff_space()
            tres.belongs(res)

        return res

    def __repr__(self):
        return 'Parallel(%r, %r)' % (self.dp1, self.dp2)

    def repr_long(self):
        r1 = self.dp1.repr_long()
        r2 = self.dp2.repr_long()
        s = 'Parallel  %% %s -> %s' % (self.get_fun_space(), self.get_res_space())
        s += '\n' + indent(r1, '. ', first='\ ')
        s += '\n' + indent(r2, '. ', first='\ ')
        return s

    def get_normal_form(self):
        """
            
            alpha1: U(F1) x S1 -> U(R1)
            beta1:  U(F1) x S1 -> S1
            
            alpha2: U(F2) x S2 -> U(R2)
            beta2:  U(R2) x S2 -> S2
             
        """

        S1, alpha1, beta1 = self.dp1.get_normal_form()
        S2, alpha2, beta2 = self.dp2.get_normal_form()

        S, pack, unpack = get_product_compact(S1, S2)

        F = self.get_fun_space()
        R = self.get_res_space()
        F1 = F[0]
        # R1 = R[0]
        F2 = F[1]
        # R2 = R[1]
        UF = UpperSets(F)
        UR = UpperSets(R)

        D = PosetProduct((UF, S))
        """
            alpha: U(F1xF2) x (S1xS2) -> U(R1xR2)
            beta : U(F1xF2) x (S1xS2) -> (S1xS2)
        """
        class SeriesAlpha(Map):
            def __init__(self, dp):
                self.dp = dp
                dom = D
                cod = UR
                Map.__init__(self, dom, cod)

            def _call(self, x):
                (uf, s) = x
                (s1, s2) = unpack(s)

                res = set()
                for f1, f2 in uf.minimals:

                    uf1 = UpperSet(set([f1]), F1)
                    ur1 = alpha1((uf1, s1))

                    uf2 = UpperSet(set([f2]), F2)
                    ur2 = alpha2((uf2, s2))

                    # now I need to take all combinations
                    for a, b in itertools.product(ur1.minimals, ur2.minimals):
                        res.add((a, b))
                # now take the minimal
                resm = poset_minima(res, R.leq)
                r = UpperSet(resm, R)
                return r

        """
            alpha: U(F1xF2) x (S1xS2) -> U(R1xR2)
            beta : U(F1xF2) x (S1xS2) -> (S1xS2)
        """
        class SeriesBeta(Map):
            def __init__(self, dp):
                self.dp = dp
                dom = D
                cod = S
                Map.__init__(self, dom, cod)

            def _call(self, x):
                (uf, s) = x
                (s1, s2) = unpack(s)

                # now need to project down
                uf1, uf2 = upperset_project_two(F, uf)

                s1p = beta1((uf1, s1))
                s2p = beta2((uf2, s2))
                return pack(s1p, s2p)

        return NormalForm(S, SeriesAlpha(self), SeriesBeta(self))


def upperset_project_two(P, u):
    """ u = upperset in P
        P = Product(P1, P2) 
        returns u1, u2
    """
    m1 = set()
    m2 = set()
    for a,b in u.minimals:
        m1.add(a)
        m2.add(b)
    
    P1 = P[0]
    P2 = P[1]
    m1m = poset_minima(m1, P1.leq)
    m2m = poset_minima(m2, P2.leq)
    
    u1 = UpperSet(m1m, P1)
    u2 = UpperSet(m2m, P2)
    return u1, u2
        
