# -*- coding: utf-8 -*-
from .primitive import PrimitiveDP
from contracts.utils import indent, raise_desc, raise_wrapped
from mocdp.posets import Map, NotLeq, PosetProduct, UpperSet, UpperSets
import itertools
from mocdp.dp.primitive import NotFeasible, Feasible


__all__ = [
    'DPLoop0',
]
#
# if False:
#     class SimpleLoop(PrimitiveDP):
#
#         def __init__(self, dp1):
#             from mocdp import get_conftools_dps
#
#             library = get_conftools_dps()
#             _, self.dp1 = library.instance_smarter(dp1)
#
#             funsp = self.get_fun_space()
#             ressp = self.get_res_space()
#
#             if not funsp == ressp:
#                 raise_desc(ValueError, "Need exactly same space", funsp=funsp, ressp=ressp)
#
#         def get_fun_space(self):
#             return self.dp1.get_fun_space()
#
#         def get_res_space(self):
#             return self.dp1.get_res_space()
#
#         def solve(self, func):
#
#             funsp = self.dp1.get_fun_space()
#             fU = UpperSets(funsp)
#
#             f = [funsp.U(func)]
#             r = [self.dp1.solveU(f[0])]
#     #
#     #         print('f', f)
#     #         print('r', r)
#
#             for _ in range(10):  # XXX
#     #             fi = fU.join(f[0], r[-1])
#                 fi = r[-1]
#     #             print('fi', fi)
#                 ri = self.dp1.solveU(fi)
#     #             print('ri', ri)
#
#                 if False:
#                     try:
#                         fU.check_leq(fi, ri)
#                     except NotLeq as e:
#                         msg = 'Loop iteration invariant not satisfied.'
#                         msg += '\n %s <= %s: %s' % (fi, ri, e)
#                         raise_desc(Exception, msg, fi=fi, ri=ri, dp=self.dp1)
#
#                 f.append(fi)
#                 r.append(ri)
#
#                 if f[-1] == f[-2]:
#                     print('breaking because of f converged: %s' % f[-1])
#                     break
#     #
#     #         print f
#     #         print r
#
#             return r[-1]

#
#
# class DPLoop(PrimitiveDP):
#
#     def __init__(self, dp1):
#
#         from mocdp import get_conftools_dps
#
#         library = get_conftools_dps()
#         _, self.dp1 = library.instance_smarter(dp1)
#
#         funsp = self.dp1.get_fun_space()
#         ressp = self.dp1.get_res_space()
#
#         check_isinstance(funsp, PosetProduct)
#         check_isinstance(ressp, PosetProduct)
#
#         if len(funsp) != 2:
#             raise ValueError('funsp needs to be length 2: %s' % funsp)
#
#         if len(ressp) != 2:
#             raise ValueError('ressp needs to be length 2: %s' % ressp)
#
#         self.F1 = funsp[0]
#         self.R1 = ressp[0]
#         self.R2 = funsp[1]
#
#         if not (funsp[1]) == (ressp[1]):
#             raise_desc(ValueError, "Spaces incompatible for loop",
#                        funsp=funsp, ressp=ressp,
#                        ressp1=ressp[1], funsp1=funsp[1])
#
#         F = self.F1
#         R = self.R1
#         PrimitiveDP.__init__(self, F=F, R=R)
#
#     def get_normal_form(self):
#         """
#             S0 is a Poset
#             alpha0: U(F0) x S0 -> U(R0)
#             beta0:  U(F0) x S0 -> S0
#         """
#
#         S0, alpha0, beta0 = self.dp1.get_normal_form()
#
#         R1 = self.R1
#         R2 = self.R2
#         F1 = self.F1
#         UR2 = UpperSets(self.R2)
#
#         S = PosetProduct((S0, UR2))
#         UF1 = UpperSets(self.F1)
#         UR1 = UpperSets(self.R1)
#         F1R2 = PosetProduct((F1, R2))
#         UF1R2 = UpperSets(F1R2)
#         UR1R2 = UpperSets(PosetProduct((self.R1, R2)))
#
#         """
#         S = S0 x UR2 is a Poset
#         alpha: UF1 x S -> UR1
#         beta: UF1 x S -> S
# """
#         class DPAlpha(Map):
#             def __init__(self, dp):
#                 self.dp = dp
#
#                 dom = PosetProduct((UF1, S))
#                 cod = UR1
#                 Map.__init__(self, dom, cod)
#
#             def _call(self, x):
#                 (fs, (s0, rs)) = x
#                 # fs is an upper set of F1
#                 UF1.belongs(fs)
#                 # rs is an upper set of R2
#                 UR2.belongs(rs)
#
#                 # alpha0: U(F0) x S0 -> U(R0)
#                 # alpha0: U(F1xR2) x S0 -> U(R1xR2)
#                 print('rs: %s' % rs)
#                 print('fs: %s' % fs)
#                 # make the dot product
#                 print set(itertools.product(fs.minimals, rs.minimals))
#                 x = UpperSet(set(itertools.product(fs.minimals, rs.minimals)), F1R2)
#                 # this is an elment of U(F1xR2)
#                 UF1R2.belongs(x)
#
#                 # get what alpha0 says
#                 y0 = alpha0((x, s0))
#                 # this is in UR1R2
#                 UR1R2.belongs(y0)
#
#                 # now drop to UR1
#                 u = set([m[0] for m in y0.minimals])
#                 u = poset_minima(u, R1.leq)
#                 a1 = UpperSet(u, R1)
#
#                 return a1
#
#
#         class DPBeta(Map):
#             def __init__(self, dp):
#                 self.dp = dp
#
#                 dom = PosetProduct((UF1, S))
#                 cod = S
#                 Map.__init__(self, dom, cod)
#
#             def _call(self, x):
#                 # beta0:  U(F0) x S0 -> S0
#                 # beta0: U(F1xR1) x S0 -> S0
#
#                 # beta: UF1 x S -> S
#                 # beta: UF1 x (S0 x UR2) -> (S0 x UR2)
#                 fs, (s0, rs) = x
#
#                 # fs is an upper set of F1
#                 UF1.belongs(fs)
#                 # rs is an upper set of R2
#                 UR2.belongs(rs)
#
#                 # make the dot product
#                 x = UpperSet(set(itertools.product(fs.minimals, rs.minimals)), F1R2)
#                 # this is an elment of U(F1xR2)
#                 UF1R2.belongs(x)
#
#                 # get what beta0 says
#                 s0p = beta0((x, s0))
#
#                 # get what alpha0 says
#                 y0 = alpha0((x, s0))
#                 # this is in UR1R2
#                 UR1R2.belongs(y0)
#
#                 # now drop to UR2
#                 u = [m[1] for m in y0.minimals]
#                 u = poset_minima(u, R2.leq)
#                 m1 = UpperSet(u, R2)
#
#                 return s0p, m1
#
#         return S, DPAlpha(self), DPBeta(self)
#
#     def __repr__(self):
#         return 'DPloop(%s)' % self.dp1
#
#     def solve(self, func):
#         raise NotImplementedError()
#         from mocdp.posets import NotLeq, UpperSets
#
#         funsp = self.dp1.get_fun_space()
#         ressp = self.dp1.get_res_spe
#         fU = UpperSets(ressp)
#
#         f = [funsp.U(func)]
#         q = [self.R2.get_bottom()]
#
# #
# #         print('f', f)
# #         print('r', r)
#
#         for i in range(10):  # XXX
# #             fi = fU.join(f[0], r[-1])
#             fi = r[-1]
# #             print('fi', fi)
#             ri = self.dp1.solveU(fi)
# #             print('ri', ri)
#             f.append(fi)
#             r.append(ri)
#
#             if f[-1] == f[-2]:
#                 print('breaking because of f converged: %s' % f[-1])
#                 break
# #
# #         print f
# #         print r
#
#         return r[-1]


class DPLoop0(PrimitiveDP):
    """
        This is the version in the papers
                  ______
           f1 -> |  dp  |--->r
           f2 -> |______| |
              `-----------/
    """
    def __init__(self, dp1):
        from mocdp import get_conftools_dps

        library = get_conftools_dps()
        _, self.dp1 = library.instance_smarter(dp1)

        F0 = self.dp1.get_fun_space()
        R0 = self.dp1.get_res_space()
        M0 = self.dp1.get_imp_space_mod_res()

        if not isinstance(F0, PosetProduct):
            raise ValueError('Funsp is not a product: %r' % F0)

        if len(F0) != 2:
            raise ValueError('funsp needs to be length 2: %s' % F0)

        F1 = F0[0]
        F2 = F0[1]

        if not(F2 == R0):
            raise_desc(ValueError, "Spaces incompatible for loop",
                       funsp=F0, ressp=R0)

        F = F1
        R = R0
        # M = M0
        # from mocdp.dp.dp_series import prod_make
        from mocdp.dp.dp_series import get_product_compact
        M, _, _ = get_product_compact(M0, F2)
        PrimitiveDP.__init__(self, F=F, R=R, M=M)
        self.M0 = M0
        self.F2 = F2

    def evaluate_f_m(self, f1, m):
        """ Returns the resources needed
            by the particular implementation.
            raises NotFeasible 
        """
        from mocdp.dp.dp_series import get_product_compact
        F2 = self.F2
        F1 = self.F

        _, _, unpack = get_product_compact(self.M0, self.F2)
        m0, f2 = unpack(m)
        f = (f1, f2)
        r = self.dp1.evaluate_f_m(f, m0)
        try:
            F2.check_leq(r, f2)
        except NotLeq as e:
            msg = 'Loop constraint not satisfied %s <= %s not satisfied.' % (F2.format(r), F2.format(f2))
            msg += "\n f1 = %10s -->| ->[ %s ] --> %s " % (F1.format(f1), self.dp1, F2.format(r))
            msg += "\n f2 = %10s -->|" % F2.format(f2)
            raise_wrapped(NotFeasible, e, msg, compact=True)
        return r

    def check_unfeasible(self, f1, m, r):
        from mocdp.dp.dp_series import get_product_compact
        F2 = self.F2
        F1 = self.F

        M, _, unpack = get_product_compact(self.M0, F2)
        M.belongs(m)
        m0, f2 = unpack(m)
        f = (f1, f2)

        try:
            self.dp1.check_unfeasible(f, m0, r)
        except Feasible as e:
            used = self.dp1.evaluate_f_m(f, m0)
            if F2.leq(used, f2):
                msg = 'loop: asking to show it is unfeasible (%s, %s, %s)' % (f1, m, r)
                msg += '\nBut inner is feasible and loop constraint *is* satisfied.'
                msg += "\n f1 = %10s -->| ->[ m0= %s ] --> %s <= %s" % (F1.format(f1), M.format(m0),
                                                                    F2.format(used), F2.format(r))
                msg += "\n f2 = %10s -->|" % F2.format(f2)
                raise_wrapped(Feasible, e, msg, compact=True, dp1=self.dp1.repr_long())

    def check_feasible(self, f1, m, r):
        from mocdp.dp.dp_series import get_product_compact
        F2 = self.F2
        F1 = self.F

        M, _, unpack = get_product_compact(self.M0, F2)
        M.belongs(m)
        m0, f2 = unpack(m)
        f = (f1, f2)

        try:
            self.dp1.check_feasible(f, m0, r)
        except NotFeasible as e:
            msg = 'loop: Asking loop if feasible (f1=%s, m=%s, r=%s)' % (f1, m, r)
            msg += '\nInternal was not feasible when asked for (f=%s, m0=%s, r=%r)' % (f, m0, r)
            raise_wrapped(NotFeasible, e, msg, dp1=self.dp1.repr_long(), compact=True)

        used = self.dp1.evaluate_f_m(f, m0)
        if F2.leq(used, f2):
            pass
        else:
            msg = 'loop: Asking loop to show feasible (f1=%s, m=%s, r=%s)' % (f1, m, r)
            msg += '\nbut loop constraint is *not* satisfied.'
            msg += "\n f1 = %10s -->| ->[ %s ] --> used = %s <= r = %s" % (F1.format(f1), self.dp1,
                                                                F2.format(used), F2.format(r))
            msg += "\n f2 = %10s -->|" % F2.format(f2)
            raise_desc(NotFeasible, msg)

#
#     def is_feasible(self, f1, m, r):
#         from mocdp.dp.dp_series import get_product_compact
#         _, _, unpack = get_product_compact(self.M0, self.F2)
#         m0, f2 = unpack(m)
#         f = (f1, f2)
#         print('checking feasilbility for loop')
#         print('f = %s' % str(f))
#         print('m0 = %s, f2 = %s' % (m0, f2))
#
#         if not self.dp1.is_feasible(f, m0, r):
#             print('The internal one is not feasibile with (%s, %s, %s)' % (f, m0, r))
#             return False
#         used = self.evaluate_f_m(f, m0)
#         print('used = %s' % str(used))
#         ok1 = self.R.leq(used, r)
#         ok2 = self.R.leq(r, f2)
#         print('ok1 = %s' % ok1)
#         print('ok2 = %s' % ok2)
#         return ok1 and ok2

    def get_normal_form(self):
        """
            S0 is a Poset
            alpha0: U(F0) x S0 -> UR
            beta0:  U(F0) x S0 -> S0
        """

        S0, alpha0, beta0 = self.dp1.get_normal_form()

        F = self.dp1.get_fun_space()
        R = self.dp1.get_res_space()
        F1 = F[0]
        UR = UpperSets(R)

#         S = PosetProduct((S0, UR))

        # from mocdp.dp.dp_series import prod_make
        # S = prod_make(S0, UR)
        from mocdp.dp.dp_series import get_product_compact
        S, pack, unpack = get_product_compact(S0, UR)

        UF1 = UpperSets(F1)
#         UR1 = UpperSets(self.R1)
        F1R = PosetProduct((F1, R))
        UF1R = UpperSets(F1R)

#         UR1R2 = UpperSets(PosetProduct((self.R1, R2)))
#         from mocdp.dp.dp_series import prod_get_state

        """
        S = S0 x UR is a Poset
        alpha: UF1 x S -> UR
        beta: UF1 x S -> S
"""
        class DPAlpha(Map):
            def __init__(self, dp):
                self.dp = dp

                dom = PosetProduct((UF1, S))
                cod = UR
                Map.__init__(self, dom, cod)

            def _call(self, x):
                (fs, s) = x
                (s0, rs) = unpack(s)

                # fs is an upper set of F1
                UF1.belongs(fs)
                # rs is an upper set of R2
                UR.belongs(rs)

                # alpha0: U(F0) x S0 -> U(R0)
                # alpha0: U(F1xR2) x S0 -> U(R1xR2)
                #print('rs: %s' % rs)
                #print('fs: %s' % fs)
                # make the dot product
                #print set(itertools.product(fs.minimals, rs.minimals))
                x = UpperSet(set(itertools.product(fs.minimals, rs.minimals)), F1R)
                # this is an elment of U(F1xR)
                UF1R.belongs(x)

                # get what alpha0 says
                y0 = alpha0((x, s0))
                # this is in UR
                UR.belongs(y0)

#                 # now drop to UR1
#                 u = set([m[0] for m in y0.minimals])
#                 u = poset_minima(u, R1.leq)
#                 a1 = UpperSet(u, R1)

                return y0


        class DPBeta(Map):
            def __init__(self, dp):
                self.dp = dp

                dom = PosetProduct((UF1, S))
                cod = S
                Map.__init__(self, dom, cod)

            def _call(self, x):
                # beta0: U(F0) x S0 -> S0
                # beta0: U(F1xR1) x S0 -> S0

                # beta: UF1 x S -> S
                # beta: UF1 x (S0 x UR) -> (S0 x UR)
                fs, s = x
                # (s0, rs) = prod_get_state(S0, UR, s)
                (s0, rs) = unpack(s)

                # fs is an upper set of F1
                UF1.belongs(fs)
                # rs is an upper set of R2
                UR.belongs(rs)

                # make the dot product
                x = UpperSet(set(itertools.product(fs.minimals, rs.minimals)), F1R)
                # this is an elment of U(F1xR2)
                UF1R.belongs(x)

                # get what beta0 says
                s0p = beta0((x, s0))

                # get what alpha0 says
                y0 = alpha0((x, s0))
                # this is in UR1R2
                UR.belongs(y0)

                # now drop to UR2
#                 u = [m[1] for m in y0.minimals]
#                 u = poset_minima(u, R.leq)
#                 m1 = UpperSet(u, R)

                # from mocdp.dp.dp_series import prod_make_state
                # res = prod_make_state(S0, UR, s0p, y0)
                res = pack(s0p, y0)
                return res

        return S, DPAlpha(self), DPBeta(self)

    def __repr__(self):
        return 'DPLoop0(%s)' % self.dp1

    def repr_long(self):
        s = 'DPLoop0:   %s -> %s\n' % (self.get_fun_space(), self.get_res_space())
        return s + indent(self.dp1.repr_long(), 'L ')

    def solve(self, f1):
        F = self.dp1.get_fun_space()
        F1 = F[0]
        F1.belongs(f1)
        R = self.dp1.get_res_space()

        UR = UpperSets(R)
        UF = UpperSets(F)

        def iterate(si):
            """ Returns the next iteration """
            # compute the product
            UR.belongs(si)
            upset = set()
            for r in si.minimals:
                upset.add((f1, r))
            upset = UpperSet(upset, F)
            UF.belongs(upset)
            # solve the 
            res = self.dp1.solveU(upset)
            UR.belongs(res)
            return res

        # we consider a set of iterates
        # we start from the bottom
        s0 = UR.get_bottom()

        S = [s0]
            
        for i in range(100):  # XXX
            # now take the product of f1
            si = S[-1]
            sip = iterate(si)

            try:
                UR.check_leq(si, sip)
            except NotLeq as e:
                msg = 'Loop iteration invariant not satisfied.'
                raise_wrapped(Exception, e, msg, si=si, sip=sip, dp=self.dp1)

            S.append(sip)

            if UR.leq(sip, si):
                print('Breaking because converged (iteration %s)' % i)
                break 
        return S[-1]
