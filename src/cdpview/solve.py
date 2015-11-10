# -*- coding: utf-8 -*-
from conf_tools import GlobalConfig
from contracts import contract
from contracts.utils import raise_desc
from mocdp.comp.context import Context
from mocdp.dp.solver import generic_solve
from mocdp.dp_report.generic_report_utils import generic_report
from mocdp.lang.blocks import eval_constant
from mocdp.lang.parse_actions import parse_ndp, parse_wrap
from mocdp.lang.syntax import Syntax
from mocdp.posets import UpperSets, get_types_universe
from quickapp import QuickAppBase
from reprep import Report
import logging
import os
from mocdp.posets.poset_product import PosetProduct

class ExpectationsNotMet(Exception):
    pass

class SolveDP(QuickAppBase):
    """ Solves an MCDP. """

    def define_program_options(self, params):
        params.add_string('out', help='Output dir', default=None)
        params.add_int('max_steps', help='Maximum number of steps', default=None)

        params.add_int('expect_nimp', help='Expected number of implementations.',
                        default=None)
        params.add_int('expect_nres', help='Expected number of resources.',
                        default=None)
        params.accept_extra()
        params.add_flag('plot', help='Show iterations graphically')
        params.add_flag('imp', help='Compute and show implementations.')

    def go(self):
        from conf_tools import logger
        logger.setLevel(logging.CRITICAL)
        GlobalConfig.global_load_dir("mocdp")

        options = self.get_options()
        if options.expect_nimp is not None:
            options.imp = True
        params = options.get_extra()

        if len(params) < 1:
            raise ValueError('Please specify filename.')

        filename = params[0]

        if options.out is None:
            out = os.path.dirname(filename)
            if not out:
                out = '.'
        else:
            out = options.out


        params = params[1:]



        s = open(filename).read()
        ndp = parse_ndp(s)
        dp = ndp.get_dp()
        fnames = ndp.get_fnames()

        F = dp.get_fun_space()

        if len(params) > 1:
            fg = interpret_params(params, fnames, F)
        else:
            p = params[0]
            fg = interpret_params_1string(p, F)

        print('query: %s' % F.format(fg))
        max_steps = options.max_steps
        try: 
            trace = generic_solve(dp, f=fg, max_steps=max_steps)
            print('Iteration result: %s' % trace.result)
            ss = trace.get_s_sequence()
            S = trace.S
            print('Fixed-point iteration converged to: %s' % S.format(ss[-1]))
            R = trace.dp.get_res_space()
            UR = UpperSets(R)
            sr = trace.get_r_sequence()
            rnames = ndp.get_rnames()
            x = ", ".join(rnames)
            print('Minimal resources needed: %s = %s' % (x, UR.format(sr[-1])))

        except:
            raise

        nres = len(sr[-1].minimals)
        if options.expect_nres is not None:
            if nres != options.expect_nres:
                msg = 'Found wrong number of resources'
                raise_desc(ExpectationsNotMet, msg,
                           expect_nres=options.expect_nres, nres=nres)

        if options.imp:
            M = dp.get_imp_space_mod_res()
            # print('M = %s' % M)

            nimplementations = 0
            for r in sr[-1].minimals:
                ms = dp.get_implementations_f_r(f=fg, r=r)
                nimplementations += len(ms)
                s = 'r = %s ' % R.format(r)
                for j, m in enumerate(ms):
                    # print('m = %s' % str(m))
                    s += "\n  implementation %d: m = %s " % (j + 1, M.format(m))
                print(s)
            if options.expect_nimp is not None:
                if options.expect_nimp != nimplementations:
                    msg = 'Found wrong number of implementations'
                    raise_desc(ExpectationsNotMet, msg, expect_nimp=options.expect_nimp,
                               nimplementations=nimplementations)

        if options.plot:
            r = Report()
            generic_report(r, dp, trace, annotation=None, axis0=(0, 0, 0, 0))

            params = '-'.join(params).replace(' ', '').replace('{', '').replace('}', '')
            out_html = os.path.splitext(os.path.basename(filename))[0] + '-%s.html' % params
            out_html = os.path.join(out, out_html)
            print('writing to %r' % out_html)
            r.to_html(out_html)


@contract(params="seq(str)")
def interpret_params(params, fnames, F):
    fds = []
    Fds = []
    context = Context()
    for p in params:
        res = parse_wrap(Syntax.constant_value, p)[0]
        vu = eval_constant(res, context)
        fds.append(vu.value)
        Fds.append(vu.unit)
    Fd = PosetProduct(tuple(Fds))
    fd = tuple(fds)

    if len(fnames) != len(fd):
        raise_desc(ValueError, 'Length does not match.', fnames=fnames,
                   params=params)

    if len(fnames) == 1:
        Fd = Fd[0]
        fd = fd[0]
    else:
        Fd = Fd
        fd = fd

    # TODO: check units compatible

    tu = get_types_universe()

    tu.check_leq(Fd, F)
    A_to_B, _ = tu.get_embedding(Fd, F)
    fg = A_to_B(fd)
    return fg

@contract(p="str")
def interpret_params_1string(p, F):
    context = Context()

    res = parse_wrap(Syntax.constant_value, p)[0]
    vu = eval_constant(res, context)

    Fd = vu.unit
    fd = vu.value

    # TODO: check units compatible

    tu = get_types_universe()

    tu.check_leq(Fd, F)
    A_to_B, _ = tu.get_embedding(Fd, F)
    fg = A_to_B(fd)
    return fg

mcdp_solve_main = SolveDP.get_sys_main()
