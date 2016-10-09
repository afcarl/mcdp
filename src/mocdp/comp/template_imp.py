from mcdp_dp import PrimitiveDP
from mcdp_posets import FiniteCollectionAsSpace, LowerSet, UpperSet

__all__ = [
    'Dummy',
    'Template',
]

class Template(PrimitiveDP):
    def __init__(self, F, R):
        I = FiniteCollectionAsSpace(['*'])
        PrimitiveDP.__init__(self, F=F, R=R, I=I)

    def evaluate(self, i):
        assert i == '*'
        rs = UpperSet(set([self.R.get_bottom()]), self.R)
        fs = LowerSet(set([self.F.get_top()]), self.F)
        return fs, rs
        
    def solve(self, f):  # @UnusedVariable
        minimals = [self.R.get_bottom()]
        return UpperSet(set(minimals), self.R)

Dummy = Template
#
# def template(functions, resources):
#
#     fnames = list(functions)
#     rnames = list(resources)
#
#     get_space = lambda x: parse_wrap(Syntax.unit_expr, x)[0]
#
#     Fs = tuple(get_space(functions[x]) for x in fnames)
#     Rs = tuple(get_space(resources[x]) for x in rnames)
#
#     F = PosetProduct(Fs)
#     R = PosetProduct(Rs)
#
#     if len(fnames) == 1:
#         F = F[0]
#         fnames = fnames[0]
#     if len(rnames) == 1:
#         R = R[0]
#         rnames = rnames[0]
#
#     return SimpleWrap(Template(F, R), fnames, rnames)
