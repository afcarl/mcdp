# -*- coding: utf-8 -*-
from .utils import (assert_parsable_to_connected_ndp, assert_semantic_error,
    assert_syntax_error)
from comptests.registrar import comptest
from contracts import contract
from contracts.utils import raise_wrapped
from mocdp.lang.parts import ValueWithUnits
from mocdp.lang.syntax import (floatnumber, integer, integer_or_float,
    number_with_unit, parse_wrap)
from mocdp.posets.rcomp import R_Weight
from nose.tools import assert_equal


@contract(string=str)
def parse_wrap_check(string, expr, result):
    try:
        res = parse_wrap(expr, string)[0]  # note the 0, first element
        assert_equal(result, res)
    except BaseException as e:
        msg = 'Cannot parse %r' % string
        raise_wrapped(Exception, e, msg, expr=expr, string=string, expected=result)

@comptest
def check_numbers1():
    parse_wrap_check('1.0', floatnumber, 1.0)
    assert_syntax_error('1', floatnumber)
    parse_wrap_check('1', integer, 1)
    parse_wrap_check('1', integer_or_float, 1)

@comptest
def check_numbers2():
    parse_wrap_check('1.0 [g]', number_with_unit, ValueWithUnits(1.0, R_Weight))
    assert_syntax_error('1', number_with_unit)
    parse_wrap_check('1 [g]', number_with_unit, ValueWithUnits(1, R_Weight))

@comptest
def check_numbers3():
    # Need connections: don't know the value of a

    assert_parsable_to_connected_ndp("""    
    cdp  {
        requires a [g]
        
        a >= 2 [g]
    }
    """)

@comptest
def check_numbers3_neg():
    assert_semantic_error("""    
    cdp  {
        provides f [g]
        requires r [g]
        
        r >= f * -2 [R]
    }
    """)


# @comptest
# def check_numbers3_emptyunit():
#     parse_wrap_check('[]', empty_unit, dict(unit=R_dimensionless))
#     parse_wrap_check('1 []', number_with_unit, ValueWithUnits(1, R_dimensionless))



