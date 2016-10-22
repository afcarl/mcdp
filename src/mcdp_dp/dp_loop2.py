# -*- coding: utf-8 -*-
from collections import namedtuple

from contracts.utils import indent, raise_desc, raise_wrapped
from mcdp_posets import (LowerSet, NotEqual, NotLeq, PosetProduct, UpperSet,
    UpperSets, get_types_universe, poset_maxima, poset_minima)
from mcdp_posets.uppersets import upperset_project, LowerSets, lowerset_project
from mocdp import ATTRIBUTE_NDP_RECURSIVE_NAME
from mocdp.exceptions import do_extra_checks

from .primitive import Feasible, NotFeasible, PrimitiveDP
from .tracer import Tracer


__all__ = [
    'DPLoop2',
]

"""
    s ∈ Uppersets(R): internal state of iteration
    converged ∈ Uppersets(R): which ones have converged
    
    r ∈ Uppersets(R₁): lower bound on the result.
    r_converged  ∈ Uppersets(R₁): which are minimal
"""
KleeneIteration = namedtuple('KleeneIteration', 's s_converged r r_converged')

class DPLoop2(PrimitiveDP):
    """
                  ______
           f1 -- |  dp  |--- r1
           f2 -- |______|---. r2
              `-----[>=]----/
    """
    def __init__(self, dp1):
        self.dp1 = dp1

        F0 = self.dp1.get_fun_space()
        R0 = self.dp1.get_res_space()
        I0 = self.dp1.get_imp_space()

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
        M, _, _ = get_product_compact(I0, F2, R2)
        self.M0 = I0
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
        m0, _f2, _r2 = unpack(m)

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


#     def evaluate_f_m(self, f1, m):
#         """ Returns the resources needed
#             by the particular implementation.
#             raises NotFeasible 
#         """
#         raise NotImplementedError
#         F2 = self.F2
#         F1 = self.F
#         m0, f2 = self._unpack_m(m)
#         f = (f1, f2)
#         r = self.dp1.evaluate_f_m(f, m0)
#         try:
#             F2.check_leq(r, f2)
#         except NotLeq as e:
#             msg = 'Loop constraint not satisfied %s <= %s not satisfied.' % (F2.format(r), F2.format(f2))
#             msg += "\n f1 = %10s -->| ->[ %s ] --> %s " % (F1.format(f1), self.dp1, F2.format(r))
#             msg += "\n f2 = %10s -->|" % F2.format(f2)
#             raise_wrapped(NotFeasible, e, msg, compact=True)
# 
#         self.R.belongs(r)
#         return r

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
        s += indent(self.dp1.repr_long(), 'L ')

        if hasattr(self.dp1, ATTRIBUTE_NDP_RECURSIVE_NAME):
            a = getattr(self.dp1, ATTRIBUTE_NDP_RECURSIVE_NAME)
            s += '\n (labeled as %s)' % a.__str__()

        return s

    def solve(self, f1):
        t = Tracer()
        res = self.solve_trace(f1, t)
        return res
    
    def solve_trace(self, f1, trace):
        res = self.solve_all_cached(f1, trace)
        return res['res_r1']

    def solve_r(self, r):
        t = Tracer()
        res = self.solve_r_trace(r, t)
        return res
    
    def solve_r_trace(self, r, trace):
        res = self.solve_r_all(r, trace)
        return res['res_f1']

    def solve_all_cached(self, f1, trace):
        if not f1 in self._solve_cache:
            #print('solving again %s' % f1.__str__())
            R = self.solve_all(f1, trace)
            self._solve_cache[f1] = R
            
        return trace.result(self._solve_cache[f1])
    
    def solve_all(self, f1, trace):
        """ Returns an upperset in UR. You want to project
            it to R1 to use as the output. """
        dp0 = self.dp1
        R = dp0.get_res_space()
        R1 = R[0]
        UR = UpperSets(R)

        # we consider a set of iterates
        # we start from the bottom
        trace.log('Iterating in UR = %s' % UR.__str__())
        
        s0 = R.Us(R.get_minimal_elements()) 
        S = [KleeneIteration(s=s0, s_converged=R.Us(set()),
                                r=upperset_project(s0, 0),
                                r_converged=R1.Us(set()))]
            
        for i in range(1, 1000000):  # XXX
            with trace.iteration(i) as t:
                si_prev = S[-1].s
                si_next, converged = solve_f_iterate(dp0, f1, R, si_prev, t)
                iteration = KleeneIteration(s=si_next, 
                                            s_converged=converged,
                                            r=upperset_project(si_next, 0),
                                            r_converged=upperset_project(converged, 0))
                S.append(iteration)
                
                t.log('R = %s' % UR.format(si_next))

                if do_extra_checks():
                    try:
                        UR.check_leq(si_prev, si_next)
                    except NotLeq as e:
                        msg = 'Loop iteration invariant not satisfied.'
                        raise_wrapped(Exception, e, msg, si_prev=si_prev, 
                                      si_next=si_next, dp=self.dp1)
                
                t.values(state=S[-1])

                if UR.leq(si_next, si_prev):
                    t.log('Breaking because converged (iteration %s) ' % i)
                    #t.log(' solution is %s' % (UR.format(sip)))
                    # todo: add reason why interrupted
                    break

        trace.values(type='loop2', UR=UR, R=R, dp=self, iterations=S)
        
        res_all = S[-1].s
        res_r1 = upperset_project(res_all, 0)
        result = dict(res_all=res_all, res_r1=res_r1)
        
        return result

    def solve_r_all(self, r1, trace):
        """ Returns an upperset in UR. You want to project
            it to R1 to use as the output. """
        dp0 = self.dp1
        F = dp0.get_fun_space()
        F1 = F[0]
        LF = LowerSets(F)

        # we consider a set of iterates
        # we start from the bottom
        trace.log('Iterating in LF = %s' % LF.__str__())
        
        s0 = F.Ls(F.get_maximal_elements()) 
        S = [KleeneIteration(s=s0, s_converged=F.Ls(set()),
                                r=lowerset_project(s0, 0),
                                r_converged=F1.Ls(set()))]
            
        for i in range(1, 1000000):  # XXX
            with trace.iteration(i) as t:
                si_prev = S[-1].s
                si_next, converged = solve_r_iterate(dp0, r1, F, si_prev, t)
                iteration = KleeneIteration(s=si_next, 
                                            s_converged=converged,
                                            r=lowerset_project(si_next, 0),
                                            r_converged=lowerset_project(converged, 0))
                S.append(iteration)
                
                t.log('si_next = %s' % LF.format(si_next))

                if do_extra_checks():
                    try:
                        LF.check_leq(si_prev, si_next)
                    except NotLeq as e:
                        msg = 'Loop iteration invariant not satisfied.'
                        raise_wrapped(Exception, e, msg, si_prev=si_prev, 
                                      si_next=si_next, dp=self.dp1)
                
                t.values(state=S[-1])

                if LF.leq(si_next, si_prev):
                    t.log('Breaking because converged (iteration %s) ' % i)
                    break

        trace.values(type='loop2r', LF=LF, F=F, dp=self, iterations=S)
        
        res_all = S[-1].s
        res_f1 = lowerset_project(res_all, 0)
        result = dict(res_all=res_all, res_f1=res_f1)
        
        return result


def solve_f_iterate(dp0, f1, R, S, trace):
    """ 
    
        Returns the next iteration  si \in UR 

        Min ( h(f1, r20) \cup  !r20 ) 
        
    """
    UR = UpperSets(R)
    if do_extra_checks():
        UR.belongs(S)
    R2 = R[1]
    converged = set()  # subset of solutions for which they converged
    nextit = set()
    # find the set of all r2s

    for ra in S.minimals:
        hr = dp0.solve_trace((f1, ra[1]), trace)

        for rb in hr.minimals:
            valid = R.leq(ra, rb) 

            if valid:
                nextit.add(rb)

                feasible = R2.leq(rb[1], ra[1])
                if feasible:
                    converged.add(rb)

    nextit = R.Us(poset_minima(nextit, R.leq))
    converged = R.Us(poset_minima(converged, R.leq))

    return nextit, converged

def solve_r_iterate(dp0, r1, F, S, trace):
    
    LF = LowerSets(F)
    if do_extra_checks():
        LF.belongs(S)
    F2 = F[1]
    converged = set()  # subset of solutions for which they converged
    nextit = set()
    # find the set of all r2s

    for fa in S.maximals:
        hr = dp0.solve_r_trace((r1, fa[1]), trace)

        for fb in hr.maximals:
            # valid = R.leq(ra, rb) # ra <= rb
            valid = F.leq(fb, fa) # fb <= fa 

            if valid:
                nextit.add(fb)

                feasible = F2.leq(fa[1], fb[1])
                if feasible:
                    converged.add(fb)

    nextit = F.Ls(poset_maxima(nextit, F.leq))
    converged = F.Ls(poset_maxima(converged, F.leq))

    return nextit, converged

