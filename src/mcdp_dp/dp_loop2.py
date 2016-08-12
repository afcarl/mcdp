# -*- coding: utf-8 -*-
from contracts.utils import indent, raise_desc, raise_wrapped
from mcdp_dp.dp_loop import Iteration
from mcdp_dp.primitive import Feasible, NotFeasible, PrimitiveDP
from mcdp_dp.tracer import Tracer
from mcdp_posets import (LowerSet, NotEqual, NotLeq, PosetProduct, UpperSet,
    UpperSets, get_types_universe, poset_maxima, poset_minima)
from mocdp.exceptions import do_extra_checks
import itertools
from mcdp_posets.space import Map


__all__ = [
    'DPLoop2',
]


class DPLoop2(PrimitiveDP):
    """
                  ______
           f1 -> |  dp  |--->r1
           f2 -> |______|---. r2
              `-----[>=]----/
    """
    def __init__(self, dp1):
        self.dp1 = dp1

        F0 = self.dp1.get_fun_space()
        R0 = self.dp1.get_res_space()
        M0 = self.dp1.get_imp_space_mod_res()

        if not isinstance(F0, PosetProduct) or len(F0.subs) != 2:
            msg = 'The function space must be a product of length 2.'
            raise_desc(ValueError, msg, F0=F0)

        if not isinstance(R0, PosetProduct) or len(R0.subs) != 2:
            msg = 'The resource space must be a product of length 2.'
            raise_desc(ValueError, msg, R0=R0)
            
        F1, F2 = F0[0], F0[1]
        R1, R2 = R0[0], R0[1]
        
        tu = get_types_universe()
        
        try:
            tu.check_equal(F2, R2)
        except NotEqual as e:
            msg = ('The second component of function and resource space '
                   'must be equal.')
            raise_wrapped(ValueError, e, msg, F2=F2, R2=R2)

        F = F1
        R = R1

        from mcdp_dp.dp_series import get_product_compact
        M, _, _ = get_product_compact(M0, F2, R2)
        self.M0 = M0
        self.F1 = F1
        self.F2 = F2
        self.R1 = R1
        self.R2 = R2

        self._solve_cache = {}
        PrimitiveDP.__init__(self, F=F, R=R, I=M)


    def _unpack_m(self, m):
        if do_extra_checks():
            self.M.belongs(m)
        from mcdp_dp.dp_series import get_product_compact
        _, _, unpack = get_product_compact(self.M0, self.F2, self.R2)
        m0, f2, r2 = unpack(m)
        return m0, f2, r2

    def evaluate(self, m):
        from mcdp_posets.category_product import get_product_compact
        _, _, unpack = get_product_compact(self.M0, self.F2, self.R2)
        m0, f2, r2 = unpack(m)

        LF0, UR0 = self.dp1.evaluate(m0)
        assert isinstance(LF0, LowerSet), (LF0, self.dp1)
        assert isinstance(UR0, UpperSet), (UR0, self.dp1)

        # now extract first components f1 and r1
        f1s = set()
        for fi in LF0.maximals:
            fi1, _ = fi
            f1s.add(fi1)
        f1s = poset_maxima(f1s, self.F.leq)
        LF = self.F.Ls(f1s)

        r1s = set()
        for ri in UR0.minimals:
            ri1, _ = ri
            r1s.add(ri1)
        r1s = poset_minima(r1s, self.F.leq)
        UR = self.R.Us(r1s)

        return LF, UR

    def get_implementations_f_r(self, f1, r1):
        from mcdp_posets.category_product import get_product_compact
        M, M_pack, _ = get_product_compact(self.M0, self.F2, self.R2)
        options = set()

        R = self.solve_all_cached(f1, Tracer())
        res = R['res_all']

        for (r1_, r2_) in res.minimals:
            if self.R1.leq(r1_, r1):
                f2 = r2_
                m0s = self.dp1.get_implementations_f_r((f1, f2), (r1_, r2_))
                for m0 in m0s:
                    m = M_pack(m0, f2, r2_)
                    options.add(m)
            
        if do_extra_checks():
            for _ in options:
                M.belongs(_)

        return options


    def evaluate_f_m(self, f1, m):
        """ Returns the resources needed
            by the particular implementation.
            raises NotFeasible 
        """
        raise NotImplementedError
        F2 = self.F2
        F1 = self.F
        m0, f2 = self._unpack_m(m)
        f = (f1, f2)
        r = self.dp1.evaluate_f_m(f, m0)
        try:
            F2.check_leq(r, f2)
        except NotLeq as e:
            msg = 'Loop constraint not satisfied %s <= %s not satisfied.' % (F2.format(r), F2.format(f2))
            msg += "\n f1 = %10s -->| ->[ %s ] --> %s " % (F1.format(f1), self.dp1, F2.format(r))
            msg += "\n f2 = %10s -->|" % F2.format(f2)
            raise_wrapped(NotFeasible, e, msg, compact=True)

        self.R.belongs(r)
        return r

    def check_unfeasible(self, f1, m, r1):
        m0, f2, r2 = self._unpack_m(m)
        r = (r1, r2)
        f = (f1, f2)
        F1 = self.F1
        F2 = self.F2
        try:
            self.dp1.check_unfeasible(f, m0, r)
        except Feasible as e:
            used = self.dp1.evaluate_f_m(f, m0)
            R0 = self.dp1.R
            if R0.leq(used, r):
                msg = 'loop: asking to show it is unfeasible (%s, %s, %s)' % (f1, m, r)
                msg += '\nBut inner is feasible and loop constraint *is* satisfied.'
                msg += "\n f1 = %10s -->| ->[ m0= %s ] --> %s <= %s" % (F1.format(f1), self.M0.format(m0),
                                                                        R0.format(used), R0.format(r))
                msg += "\n f2 = %10s -->|" % F2.format(f2)
                raise_wrapped(Feasible, e, msg, compact=True, dp1=self.dp1.repr_long())

    def check_feasible(self, f1, m, r1):
        m0, f2, r2 = self._unpack_m(m)
        r = (r1, r2)
        f = (f1, f2)

        try:
            self.dp1.check_feasible(f, m0, r)
        except NotFeasible as e:
            msg = 'loop: Asking loop if feasible (f1=%s, m=%s, r=%s)' % (f1, m, r)
            msg += '\nInternal was not feasible when asked for (f=%s, m0=%s, r=%r)' % (f, m0, r)
            raise_wrapped(NotFeasible, e, msg, dp1=self.dp1.repr_long(), compact=True)
 
    def __repr__(self):
        return 'DPLoop2(%r)' % self.dp1

    def repr_long(self):
        s = 'DPLoop2:   %s -> %s\n' % (self.get_fun_space(), self.get_res_space())
        return s + indent(self.dp1.repr_long(), 'L ')

    def solve(self, f1):
        t = Tracer()
        res = self.solve_trace(f1, t)
        return res
    
    def solve_trace(self, f1, trace):
        res = self.solve_all_cached(f1, trace)
        return res['res_r1']

    def solve_all_cached(self, f1, trace):
        if not f1 in self._solve_cache:
            R = self.solve_all(f1, trace)
            self._solve_cache[f1] = R
            
        return trace.result(self._solve_cache[f1])
    
    def solve_all(self, f1, trace):
        """ Returns ur1, ur """
        
        F1 = self.F1
        R1 = self.R1
        R2 = self.R2
        R = self.dp1.R
        dp0 = self.dp1

        if do_extra_checks():
            F1.belongs(f1)

        UR = UpperSets(R)

        trace.values(type='loop2', UR=UR, R=R, dp=self)

        # we consider a set of iterates
        # we start from the bottom
        zeros = R2.get_minimal_elements()
        minimals = set(itertools.product((f1,), zeros))
        f0s = dp0.F.Us(minimals)
        s0 = dp0.solveU(f0s)
        UR.belongs(s0)
        trace.log('Iterating in UR = %s' % UR)
        trace.log('Starting from %s' % UR.format(s0))
        # trace.log('dp0: %s' % self.dp1.repr_long())

        S = [Iteration(s=s0, converged=set())]
        for i in range(1000000):  # XXX
            with trace.iteration(i) as t:
                si = S[-1].s

                sip, converged = dploop2_iterate(dp0, f1, R, si, t)

                t.values(sip=sip, converged=converged)
                t.log('it %d: sip = %s' % (i, UR.format(sip)))
                t.log('it %d: converged = %s' % (i, UR.format(converged)))

                if do_extra_checks():
                    try:
                        UR.check_leq(si, sip)
                    except NotLeq as e:
                        msg = 'Loop iteration invariant not satisfied.'
                        raise_wrapped(Exception, e, msg, si=si, sip=sip, dp=self.dp1)

                S.append(Iteration(s=sip, converged=converged))

                if UR.leq(sip, si):
                    t.log('Breaking because converged (iteration %s) ' % i)
                    t.log(' solution is %s' % (UR.format(sip)))
                    break

        res_all = S[-1].s

        trace.log('res_all: %s' % UR.format(res_all))
        res_r1 = R1.Us(poset_minima([r1 for (r1, _) in res_all.minimals], leq=R1.leq))
        return dict(res_all=res_all, res_r1=res_r1)

    def get_normal_form(self):
        """
            S0 is a Poset
            alpha0: U(F0) x S0 -> UR0
            beta0:  U(F0) x S0 -> S0
        """

        S0, alpha0, beta0 = self.dp1.get_normal_form()

        F = self.dp1.get_fun_space()
        R = self.dp1.get_res_space()
        F1 = F[0]
        R1 = R[0]
        R2 = R[1]
        UR = UpperSets(R2)

        from mcdp_dp.dp_series import get_product_compact
        S, pack, unpack = get_product_compact(S0, UR)

        UF1 = UpperSets(F1)
        F1R2 = PosetProduct((F1, R2))
        UF1R2 = UpperSets(F1R2)


        """
        S = S0 x UR is a Poset
        alpha: UF1 x S -> UR
        beta: UF1 x (S0 x UR) -> (S0 x UR)
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

                solutions = set()
                # for each r
                for f2 in rs.minimals:
                    # take the product

                    x = UpperSet(set((_, f2) for _ in fs.minimals), F1R2)
                    # this is an elment of U(F1xR)
                    UF1R2.belongs(x)

                    # get what alpha0 says
                    y0 = alpha0((x, s0))
                    # this is in UR
                    UR.belongs(y0)

                    # now check which ones are ok
                    for r in y0.minimals:
                        if R.leq(r, f2):
                            solutions.add(r)

                u = poset_minima(solutions, R.leq)
                a1 = UpperSet(u, R)
                return a1


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

                # print('loop-beta: product of %s and %s' % (fs, rs))
                # make the dot product

                rs2 = set()
                for r in rs.minimals:

                    x = UpperSet(set(itertools.product(fs.minimals, rs.minimals)), F1R)
                    # this is an elment of U(F1xR2)
                    UF1R.belongs(x)

                    # get what beta0 says
                    s0p = beta0((x, s0))

                # get what alpha0 says
                y0 = alpha0((x, s0))
                # this is in UR1R2
                UR.belongs(y0)

                res = pack(s0p, y0)
                # beta: UF1 x (S0 x UR)  -> (S0 x UR)
                #       <fs , <s0, rs>> |->

                return res

        return S, DPAlpha(self), DPBeta(self)

def dploop2_iterate(dp0, f1, R, S, trace):
    """ Returns the next iteration  si \in UR 
    
    
        Min ( h(f1, r20) \cup  !r20 ) 
        
    """
    UR = UpperSets(R)
    if do_extra_checks():
        UR.belongs(S)
    R1 = R[0]
    R2 = R[1]
    converged = set()  # subset of solutions for which they converged
    nextit = set()
    # find the set of all r2s

    for (r1, r2) in S.minimals:
        # what are the results of solve(f1, f2)?
        hr = dp0.solve_trace((f1, r2), trace)

        # print('(f1,r2)=(%s,%s)' % (f1, r2))
        # print('| -> %s ' % hr)

        for (r1b, r2b) in hr.minimals:
            valid = R1.leq(r1, r1b)

            if valid:
                nextit.add((r1b, r2b))

                feasible = R2.leq(r2, r2b)
                if feasible:
                    converged.add((r1b, r2b))

    nextit = R.Us(poset_minima(nextit, R.leq))
    converged = R.Us(poset_minima(converged, R.leq))

    return nextit, converged

