# -*- coding: utf-8 -*-
from .poset import NotLeq, Poset
from .space import NotBelongs
from contracts import contract
from contracts.utils import check_isinstance, indent, raise_desc

__all__ = [
    'PosetProduct',
]


class PosetProduct(Poset):
    """ A product of Posets with the product order. """
    @contract(subs='seq(str|$Poset|code_spec)')
    def __init__(self, subs):
#         if not subs:
#             raise ValueError('subs cannot be empty')
        from mocdp.configuration import get_conftools_posets
        library = get_conftools_posets()
        self.subs = tuple([library.instance_smarter(s)[1] for s in subs])

    def __len__(self):
        return len(self.subs)

    def __getitem__(self, index):
        check_isinstance(index, int)
        return self.subs[index]

    def get_top(self):
        return tuple([s.get_top() for s in self.subs])

    def get_bottom(self):
        return tuple([s.get_bottom() for s in self.subs])

    def check_leq(self, a, b):
        problems = []
        for i, (sub, x, y) in enumerate(zip(self.subs, a, b)):
            try:
                sub.check_leq(x, y)
            except NotLeq as e:
                msg = '#%d (%s): %s ≰ %s.' % (i, sub, x, y)
                msg += '\n' + indent(str(e).strip(), '| ')
                problems.append(msg)
        if problems:
            msg = 'Leq does not hold.\n'
            msg = "\n".join(problems)
            raise_desc(NotLeq, msg, args_first=False, self=self, a=a, b=b)

    def belongs(self, x):
        if not isinstance(x, tuple):
            raise_desc(NotBelongs, 'Not a tuple', x=x, self=self)

        problems = []
        for i, (sub, xe) in enumerate(zip(self.subs, x)):
            try:
                sub.belongs(xe)
            except NotBelongs as e:
                msg = '#%s: Component %s does not belong to factor %s' % (i, xe, sub)
                msg += '\n' + indent(str(e).strip(), '| ')
                problems.append(msg)

        if problems:
            msg = 'The point does not belong to this product space.\n'
            msg += "\n".join(problems)
            raise_desc(NotBelongs, msg, args_first=False, self=self, x=x)

    def format(self, x):
        ss = []
        for _, (sub, xe) in enumerate(zip(self.subs, x)):
            ss.append(sub.format(xe))

        return '(' + ', '.join(ss) + ')'

    def get_test_chain(self, n):
        """
            Returns a test chain of length n
        """
        chains = [s.get_test_chain(n) for s in self.subs]
        res = zip(*tuple(chains))
        return res

    def __repr__(self):
        def f(x):
            if isinstance(x, PosetProduct):
                return "(%r)" % x
            else:
                return x.__repr__()

        if len(self.subs) == 0:
            return "1"

        if len(self.subs) == 1:
            return '(%s×)' % list(self.subs)[0]

        return "×".join(map(f, self.subs))

    def __eq__(self, other):
        return isinstance(other, PosetProduct) and other.subs == self.subs
