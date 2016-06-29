from .examples import *
from .failures_parsing import *
from .failures_simplification import *
from .syntax_canonical import *
from .syntax_connections import *
from .syntax_coproduct import *
from .syntax_from_library import *
from .syntax_load import *
from .syntax_misc import *
from .syntax_numbers import *
from .syntax_power import *
from .syntax_sets import *
from .syntax_spaces  import *
from .syntax_tuples  import *
from .templates_test import *

from .syntax_multiset import *
from .syntax_intervals import *
from .syntax_conversions import *
from .syntax_uncertainty import *
from .syntax_catalogue import *
from .syntax_named_tuples import *

"""
    
    For syntax, use assert_syntax_error or parse_wrap_check:

    ```
    assert_syntax_error('1', Syntax.floatnumber)
    parse_wrap_check('1', Syntax.integer_or_float)
    parse_wrap_check('1', Syntax.integer_or_float, CDP.ValueExpr(1))
    ```
    
    These two make sure that you can parse and NDP, and if it is connected or not:
    
    assert_parsable_to_connected_ndp
    assert_parsable_to_unconnected_ndp
    
    Also useful:
        
        eval_rvalue_as_constant
        
        eval_rvalue_as_constant_same
        
        eval_rvalue_as_constant_same_exactly
        

"""
