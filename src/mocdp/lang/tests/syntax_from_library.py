# -*- coding: utf-8 -*-
from comptests.registrar import comptest
from mocdp.lang.parse_actions import parse_wrap
from mocdp.lang.syntax import Syntax

@comptest
def check_from_library1():

    parse_wrap(Syntax.dpinstance_expr, 'instance load S')[0]
    parse_wrap(Syntax.dpinstance_expr, 'instance load(S)')[0]
    parse_wrap(Syntax.dpinstance_expr, 'instance load "S"')[0]
    parse_wrap(Syntax.dpinstance_expr, 'instance load("S")')[0]
    parse_wrap(Syntax.dpinstance_expr, "instance load 'S'")[0]
    parse_wrap(Syntax.dpinstance_expr, "instance load('S')")[0]

    parse_wrap(Syntax.dpinstance_expr, "new S")[0]
    parse_wrap(Syntax.dpinstance_expr, "new ('S')")[0]
    parse_wrap(Syntax.dpinstance_expr, "new('S')")[0]
    parse_wrap(Syntax.dpinstance_expr, "new 'S' ")[0]
    parse_wrap(Syntax.dpinstance_expr, "new S ")[0]

