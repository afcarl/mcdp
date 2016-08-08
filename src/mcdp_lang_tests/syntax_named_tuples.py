# -*- coding: utf-8 -*-
from comptests.registrar import comptest, comptest_fails
from mcdp_lang import parse_poset, parse_ndp
from mcdp_lang.parse_actions import parse_wrap
from mcdp_lang.syntax import Syntax

@comptest
def check_lang_namedtuple1():
    parse_wrap(Syntax.PRODUCTWITHLABELS, 'product')
    parse_wrap(Syntax.space_product_with_labels, 'product(weight: g, energy: J)')
    P = parse_poset('product(weight: g, energy: J)')
    print P
    print P.format((2.0, 1.0))

@comptest
def check_lang_namedtuple2():
    parse_ndp("""
    
mcdp {

    provides capability [ product(weight: g, energy: J) ]
    
    capability <= < 1g, 1J>

}
    
    """)

@comptest
def check_lang_namedtuple3():
    parse_wrap(Syntax.rvalue_label_indexing, "capability..weight ")[0]

    parse_ndp("""
    
mcdp {

    provides capability [ product(weight: g, energy: J) ]
    
    capability..weight <= 1g
    capability..energy <= 2J
    
    
}
    
    """)



@comptest_fails
def check_lang_namedtuple4():

    parse_ndp("""
    
mcdp {

    provides capability [ product(weight: g, energy: J) ]
    
    (capability).weight <= 1g
    # (capability).energy <= 1J
    
}
    
    """)

@comptest
def check_lang_namedtuple5():
    parse_wrap(Syntax.fvalue_label_indexing, "capability..weight ")[0]

    parse_ndp("""
    
mcdp {

    requires capability [ product(weight: g, energy: J) ]
    
    capability..weight >= 1g
    capability..energy >= 1J
    
}
    
    """)


@comptest
def check_lang_namedtuple6():
    pass


@comptest
def check_lang_namedtuple7():
    pass

