from comptests.registrar import comptest
from mcdp_lang.syntax import Syntax
from mcdp_report.html import mark_unparsable
from contracts.interface import line_and_col
from nose.tools import assert_equal
from mcdp_lang.parse_interface import parse_ndp


def ast_to_html_(s):
    parse_expr = Syntax.ndpt_dp_rvalue
    from mcdp_report.html import ast_to_html
    html = ast_to_html(s, complete_document=False, extra_css=None, ignore_line=None,
                add_line_gutter=False, encapsulate_in_precode=True, add_css=False,
                parse_expr=parse_expr, add_line_spans=False, postprocess=None)
    return html
def mark_unparsable_(s):
    parse_expr = Syntax.ndpt_dp_rvalue
    return mark_unparsable(s, parse_expr)

@comptest
def parsing_error_recov01():
    s = """
    mcdp {
        requires r [m]
        unparsable-stuff
        provides f [m]
    }
    """.strip()
    s, expr, commented = mark_unparsable(s)
    parse_expr = Syntax.ndpt_dp_rvalue
    
    html = ast_to_html_(s)
    print html


@comptest
def parsing_error_recov02():
    parse_expr = Syntax.ndpt_dp_rvalue
    s = """
mcdp {
unp
}
""".strip()
    s2, expr, commented = mark_unparsable(s, parse_expr)
    print commented



@comptest
def parsing_error_recov03():
    s = "msg\na"
    c = 4
    line, col = line_and_col(c, s)
    assert s[c] == 'a'
    print line, col
    assert line == 1
    assert col == 0
    pass


@comptest
def parsing_error_recov04():
    s="""   
mcdp {
 provides x [m]
    unp   requires a [m]
}""".strip()

    parse_expr = Syntax.ndpt_dp_rvalue

    if False:
        s2, expr, commented = mark_unparsable(s, parse_expr)
        assert_equal(commented, set([2]))

    s="""   
mcdp {
 provides x [m]
    unp   
    requires a [m]
}""".strip()

    s2, expr, commented = mark_unparsable(s, parse_expr)

    
    assert_equal(commented, set([2]))


@comptest
def parsing_error_recov05():
    s="""   
mcdp {
 provides x [m]
    #@unp   
    
    requires a [m]
    
    
}""".strip()

    s="""mcdp {
    #@unp
}""".strip()

    html = ast_to_html_(s)
    print html
    from xml.etree import ElementTree as ET
    x = ET.fromstring(html)
    print x


@comptest
def parsing_error_recov06():
    s="""mcdp {
    unp}"""
    mark_unparsable_(s)
    pass


@comptest
def parsing_error_recov07():
    s="""#mcdp {unp}\n"""
    parse_ndp(s)
#     mark_unparsable_(s)


@comptest
def parsing_error_recov08():
    print Syntax.ndpt_dp_rvalue

    pass


@comptest
def parsing_error_recov09():
    pass


@comptest
def parsing_error_recov10():
    pass