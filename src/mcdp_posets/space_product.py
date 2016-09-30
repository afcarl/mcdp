# -*- coding: utf-8 -*-
from contracts import contract
from contracts.utils import check_isinstance, indent, raise_desc
from mocdp import ATTRIBUTE_NDP_RECURSIVE_NAME, ATTR_LOAD_NAME

from .space import NotBelongs, NotEqual, Space


__all__ = [
    'SpaceProduct',
]


class SpaceProduct(Space):
    """ A product of Spaces. """

    @contract(subs='seq($Space)')
    def __init__(self, subs):
        assert isinstance(subs, tuple)
        self.subs = subs

    def __len__(self):
        return len(self.subs)

    def __getitem__(self, index):
        check_isinstance(index, int)
        return self.subs[index]

    def check_equal(self, a, b):
        problems = []
        for i, (sub, x, y) in enumerate(zip(self.subs, a, b)):
            try:
                sub.check_equal(x, y)
            except NotEqual as e:
                msg = '#%d (%s): %s ≰ %s.' % (i, sub, x, y)
                msg += '\n' + indent(str(e).strip(), '| ')
                problems.append(msg)
        if problems:
            msg = 'Equal does not hold.\n'
            msg = "\n".join(problems)
            raise_desc(NotEqual, msg, args_first=False, self=self, a=a, b=b)

    def belongs(self, x):
        if not isinstance(x, tuple):
            raise_desc(NotBelongs, 'Not a tuple', x=x, self=self)
        if not len(x) == len(self.subs):
            raise_desc(NotBelongs, 'Length does not match: len(x) = %s != %s'
                       % (len(x), len(self.subs)),
                        x=x, self=self)

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
        if not isinstance(x, tuple):
            raise_desc(NotBelongs, 'Not a tuple', x=x, self=self)

        ss = []
        for _, (sub, xe) in enumerate(zip(self.subs, x)):
            label = getattr(sub, 'label', '_')
            if not label or label[0] == '_':
                s = sub.format(xe)
            else:
                s = '%s:%s' % (label, sub.format(xe))
            ss.append(s)

    # 'MATHEMATICAL LEFT ANGLE BRACKET' (U+27E8) ⟨
    # 'MATHEMATICAL RIGHT ANGLE BRACKET'   ⟩

        return '⟨' + ', '.join(ss) + '⟩'

    def witness(self):
        return tuple(x.witness() for x in self.subs)

    def __repr__(self):
        name = type(self).__name__
        args = []
        for s in self.subs:
            res = s.__repr__()
            if hasattr(s, ATTRIBUTE_NDP_RECURSIVE_NAME):
                a = getattr(s, ATTRIBUTE_NDP_RECURSIVE_NAME)
                res += '{%s}' % "/".join(a)
            args.append(res)

        return '%s(%d: %s)' % (name, len(self.subs), ",".join(args))

    def repr_long(self):
        s = "%s[%s]" % (type(self).__name__, len(self.subs))
        for i, S in enumerate(self.subs):
            prefix0 = " %d. " % i
            prefix1 = "    "
            s += "\n" + indent(S.repr_long(), prefix1, first=prefix0)
            if hasattr(S, ATTRIBUTE_NDP_RECURSIVE_NAME):
                a = getattr(S, ATTRIBUTE_NDP_RECURSIVE_NAME)
                s += '\n  labeled as %s' % a.__str__()

        return s


    def __str__(self):
        if hasattr(self, ATTR_LOAD_NAME):
            return "`" + getattr(self, ATTR_LOAD_NAME)

        def f(x):
            if hasattr(x, ATTR_LOAD_NAME):
                res = '`' + getattr(x, ATTR_LOAD_NAME)
            else:
                r = x.__str__()
                if  r[-1] != ')' and (isinstance(x, SpaceProduct) or ("×" in r)):
                    res = "(%s)" % r
                else:
                    res = r

            if hasattr(x, ATTRIBUTE_NDP_RECURSIVE_NAME):
                a = getattr(x, ATTRIBUTE_NDP_RECURSIVE_NAME)
                res += '{%s}' % "/".join(a)
            return res

        if len(self.subs) == 0:
            return "𝟙"
            # return "1"

        if len(self.subs) == 1:
            return '(%s×)' % f(list(self.subs)[0])

        return "×".join(map(f, self.subs))

    def __eq__(self, other):
        return isinstance(other, SpaceProduct) and other.subs == self.subs
