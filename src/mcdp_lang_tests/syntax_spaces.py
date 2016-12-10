# -*- coding: utf-8 -*-
from nose.tools import assert_equal, assert_raises

from comptests.registrar import comptest, run_module_tests
from mcdp_lang import parse_ndp
from mcdp_lang.eval_space_imp import eval_space
from mcdp_lang.parse_actions import parse_wrap
from mcdp_lang.parse_interface import parse_ndp_refine
from mcdp_lang.suggestions import get_suggestions, apply_suggestions
from mcdp_lang.syntax import Syntax
from mcdp_lang_tests.utils import parse_wrap_check, TestFailed
from mcdp_lang_tests.utils2 import eval_rvalue_as_constant
from mocdp.comp.context import Context


@comptest
def check_spaces1():
    def p(s):
        c = Context()
        r = parse_wrap_check(s, Syntax.space)
#         print r
        _x = eval_space(r, c)
#         print x
    p('V')
    p("V x m")
    p("V × m")
    p("V × m × J")
    p("m × m × m")
    p("m × (m × m)")

@comptest
def check_spaces2():
    _ndp = parse_ndp("""
    mcdp {
         
        a = catalogue {

        provides voltage [set-of(V)]
        provides capacity [J]

        requires cost [$]
        requires mass [kg]

        model1 | {1.5 V} | 1 J | 5 $ | 0.20 kg 
        model2 | {1.5 V} | 1 J | 5 $ | 0.20 kg 
        model3 | {5.0 V} | 1 J | 5 $ | 0.30 kg

    }
    }
    """)
    #print ndp

@comptest
def check_spaces3():  # changename
    parse_wrap_check('instance simple_cell', Syntax.dpinstance_from_type)
    parse_wrap_check('sub cell = instance simple_cell', Syntax.setname_ndp_instance1)

@comptest
def check_spaces4():
    parse_wrap_check('<5mm, 5mm, 5mm>', Syntax.tuple_of_constants)
    parse_wrap_check('step_up1 | {5 V}        | {1.5 V} |  5 $ | 20 g | <5mm, 5mm, 5mm>', Syntax.catalogue_row)
    parse_ndp("""
catalogue {
    provides voltage    [℘(V)]
    requires v_in       [℘(V)]
    requires cost       [$]
    requires mass       [g]
    requires shape      [m x m x m]
    
    step_up1 | {5 V}        | {1.5 V} |  5 $ | 20 g | <5mm, 5mm, 5mm>
    step_up2 |       {12 V} | {1.5 V} | 10 $ | 20 g | <5mm, 5mm, 5mm>
    step_up2 | {5 V,  12 V} | {1.5 V} | 10 $ | 20 g | <5mm, 5mm, 5mm>
}
""")
         

@comptest
def check_spaces5():
    pass

@comptest
def check_spaces6():
    pass

@comptest
def check_spaces7():
    source = """
    mcdp {
        provides x
        provided x ≤ 9.8 m/s^2
    }
    """
    x = parse_wrap(Syntax.ndpt_dp_rvalue, source)[0]
    xr = parse_ndp_refine(x, Context())
    
    suggestions = get_suggestions(xr)
    
    assert_equal(1, len(suggestions))
    assert_equal('m/s\xc2\xb2', suggestions[0][1])
    
    _s2 = apply_suggestions(source, suggestions)
#     if suggestions:
#         print s2
        

@comptest
def check_spaces_superscript1():
    parse_wrap_check('m^2', Syntax.space_pint_unit)
    # ¹²³⁴⁵⁶⁷⁸⁹
    parse_wrap_check('m¹', Syntax.space_pint_unit)
    parse_wrap_check('m²', Syntax.space_pint_unit)
    parse_wrap_check('m³', Syntax.space_pint_unit)
    parse_wrap_check('m⁴', Syntax.space_pint_unit)
    parse_wrap_check('m⁵', Syntax.space_pint_unit)
    parse_wrap_check('m⁶', Syntax.space_pint_unit)
    parse_wrap_check('m⁷', Syntax.space_pint_unit)
    parse_wrap_check('m⁸', Syntax.space_pint_unit)
    parse_wrap_check('m⁹', Syntax.space_pint_unit)

    eval_rvalue_as_constant('9.81 m/s²')

@comptest
def no_newlines_before_unit():
    s = '1\nm'

    with assert_raises(TestFailed): # does not work
        parse_wrap_check(s,  Syntax.pint_unit_simple)
        
    with assert_raises(TestFailed):
        parse_wrap_check(s,  Syntax.valuewithunit_number_with_units)
    
@comptest
def power1():
    parse_wrap_check('x^2', Syntax.rvalue_power_expr)
    parse_wrap_check('²', Syntax.superscripts)
    parse_wrap_check('x²', Syntax.rvalue_power_expr)
    parse_ndp("""
    mcdp {
        provides f [dimensionless]
        requires r [dimensionless]
        
        (provided f)²  <= required r
    }
    """)
    

@comptest
def suggestions_exponent():
    source = """
    mcdp {
        provides f [dimensionless]
        requires r [dimensionless]
        
        (provided f)^2 ≤ required r
    }
    """
    
    x = parse_wrap(Syntax.ndpt_dp_rvalue, source)[0]
    xr = parse_ndp_refine(x, Context())
    
    suggestions = get_suggestions(xr)
    assert_equal(1, len(suggestions))
    assert_equal('(provided f)\xc2\xb2', suggestions[0][1])
    
    s2 = apply_suggestions(source, suggestions)
    parse_ndp(s2)


@comptest
def suggestions_exponent2():
    s = """
    mcdp {  
   variable a, c [dimensionless] 
   c ≥ a^2 + 1
}"""

    x = parse_wrap(Syntax.ndpt_dp_rvalue, s)[0]
    xr = parse_ndp_refine(x, Context())
    
    suggestions = get_suggestions(xr)
#     print suggestions
    assert_equal(1, len(suggestions))
    assert_equal('a\xc2\xb2', suggestions[0][1])
    
    s2 = apply_suggestions(s, suggestions)
    parse_ndp(s2)
#     print s2

if __name__ == '__main__': 
    
    run_module_tests()
    