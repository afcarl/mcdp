# -*- coding: utf-8 -*-
from nose.tools import assert_equal

from comptests.registrar import comptest, run_module_tests
from mcdp_lang.parse_actions import parse_wrap
from mcdp_lang.parse_interface import parse_ndp_refine
from mcdp_lang.parts import CDPLanguage
from mcdp_lang.suggestions import get_suggestions, apply_suggestions
from mcdp_lang.syntax import Syntax
from mcdp_report.out_mcdpl import ast_to_mcdpl
from mocdp.comp.context import Context


CDP = CDPLanguage

@comptest
def check_correction():
    s = """ mcdp {
    provides f [m]
    f <= 10 m
    } """
    s = """
    mcdp {  
 provides endurance [s] 
 provides payload   [kg]
 battery = instance template 
  mcdp {
    provides capacity [J]
    requires mass     [kg]
  }
 actuation = instance template 
  mcdp {
    provides lift  [N]
    requires power [W]
  }
 capacity provided by battery >= 
    endurance * (actuation.power)
a = actuation. power
b = actuation .lift
 g = 9.81 m/s^2
 actuation.lift  >=
    (mass required by battery + payload) * g
}"""
    try_corrections2(s)
    
#     try_corrections(s)
# 
# def style_correction_transform(x, parents):  # @UnusedVariable
#     if isinstance(x, CDP.leq):
#         return CDP.leq('≤', where=x.where)
#     if isinstance(x, CDP.geq):
#         return CDP.geq('≥', where=x.where)
#         
#     if isinstance(x, CDP.NewFunction) and x.keyword is None:
#         w0 = x.where
#         w = Where(w0.string, w0.character, w0.character)
#         keyword = CDP.ProvidedKeyword('provided', w)
#         x2 = CDP.NewFunction(keyword=keyword, name=x.name, where=w0)
#         return x2
# #     
# #     if isinstance(x, CDP.Resource) and isinstance(x.keyword, CDP.DotPrep):
# # #         w0 = x.where
# #         s = '%s required by %s' % (x.s.value, x.dp.value)
# #         print s.__repr__()
# #         x2 = parse_wrap(Syntax.rvalue_resource_fancy, s)[0]
# #         
# # #         w = Where(w0.string, w0.character, w0.character)
# # #         keyword = CDP.ProvidedKeyword('provided', w)
# # #         x2 = CDP.Resource(dp=x.dp, s=x., where=w0)
# #         return x2
#     
# 
#     return x
# 
# def try_corrections(s):
#     x = parse_wrap(Syntax.ndpt_dp_rvalue, s)[0]
# #     print recursive_print(x)
#     context = Context()
#     xr = parse_ndp_refine(x, context)
# #     print recursive_print(xr)
#     t = namedtuple_visitor_ext(xr, style_correction_transform)
#     print recursive_print(t)
#     ts = ast_to_mcdpl(t)
#     print ts
#     
#     x2 = parse_wrap(Syntax.ndpt_dp_rvalue, ts)[0]
# #     print recursive_print(x2)

        
def try_corrections2(s):
    x = parse_wrap(Syntax.ndpt_dp_rvalue, s)[0]
    context = Context()
    xr = parse_ndp_refine(x, context)
    suggestions = get_suggestions(xr)
   
    for orig_where, sub in suggestions:
        orig_1 = orig_where.string[orig_where.character:orig_where.character_end]
        
        print 'Change %r in %r' % (orig_1, sub)
        
    s2 = apply_suggestions(s, suggestions)
    print s2
    x2 = parse_wrap(Syntax.ndpt_dp_rvalue, s2)[0]
    
#     print recursive_print(t)
#     ts = ast_to_mcdpl(t)
#     print ts
#      
#     x2 = parse_wrap(Syntax.ndpt_dp_rvalue, ts)[0]
# #     print recursive_print(x2)
CDP = CDPLanguage

@comptest
def check_print():
    s = """ mcdp {
#     provides f [m]
    f <= 10 m
    } """
    x = parse_wrap(Syntax.ndpt_dp_rvalue, s)[0]
#     print recursive_print(x)

    s2 = ast_to_mcdpl(x)
#     print s.__repr__()
#     print s2.__repr__()
    assert_equal(s.strip(), s2.strip())
    
if __name__ == '__main__': 
    
    run_module_tests()
    
    
    
    