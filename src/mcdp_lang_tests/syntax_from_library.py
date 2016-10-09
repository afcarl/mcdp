# -*- coding: utf-8 -*-
from comptests.registrar import comptest
from mcdp_lang.parse_actions import parse_wrap
from mcdp_lang.syntax import Syntax


@comptest
def check_from_library1():

    parse_wrap(Syntax.dpinstance_expr, 'instance load Sa')[0]
    parse_wrap(Syntax.dpinstance_expr, 'instance load(Sa)')[0]
    parse_wrap(Syntax.dpinstance_expr, 'instance load "Sa"')[0]
    parse_wrap(Syntax.dpinstance_expr, 'instance load("Sa")')[0]
    parse_wrap(Syntax.dpinstance_expr, "instance load 'Sa'")[0]
    parse_wrap(Syntax.dpinstance_expr, "instance load('Sa')")[0]

    parse_wrap(Syntax.dpinstance_expr, "new Sa")[0]
    parse_wrap(Syntax.dpinstance_expr, "new ('Sa')")[0]
    parse_wrap(Syntax.dpinstance_expr, "new('Sa')")[0]
    parse_wrap(Syntax.dpinstance_expr, "new 'Sa' ")[0]
    parse_wrap(Syntax.dpinstance_expr, "new Sa ")[0]


    parse_wrap(Syntax.code_spec, "code functions.call() ")
    parse_wrap(Syntax.space, "code functions.call() ")
    parse_wrap(Syntax.ndpt_dp_operand, "code functions.call() ")
    parse_wrap(Syntax.ndpt_dp_rvalue, "code functions.call() ")
