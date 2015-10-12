from contracts import contract, raise_wrapped
from mocdp.comp.interfaces import NamedDP
from mocdp.dp.primitive import PrimitiveDP
from mocdp.posets.poset_product import PosetProduct
from mocdp.dp.dp_flatten import get_it
from mocdp.configuration import get_conftools_dps

__all__ = [
    'SimpleWrap',
    'dpwrap',
]


class SimpleWrap(NamedDP):
    def __init__(self, dp, fnames, rnames):
        
        _ , self.dp = get_conftools_dps().instance_smarter(dp)

        F = self.dp.get_fun_space()

        R = self.dp.get_res_space()

        try:
            # assume that dp has product spaces of given length

            if isinstance(rnames, list):
                if not len(set(rnames)) == len(rnames):
                    raise ValueError('Repeated rnames.')
            if isinstance(fnames, list):
                if not len(set(fnames)) == len(fnames):
                    raise ValueError('Repeated fnames.')


            if isinstance(F, PosetProduct):
                if not isinstance(fnames, list) or not len(F) == len(fnames):
                    raise ValueError("F incompatible")
                self.F_single = False
                self.Fnames = fnames

            else:
                if not isinstance(fnames, str):
                    raise ValueError("F and fnames incompatible: not a string")
                self.F_single = True
                self.Fname = fnames

            if isinstance(R, PosetProduct):
                if not isinstance(rnames, list) or not len(R) == len(rnames):
                    raise ValueError("R incompatible")
                self.R_single = False
                self.Rnames = rnames

            else:
                if not isinstance(rnames, str):
                    raise ValueError("R and rnames incompatible: want one string")
                self.R_single = True
                self.Rname = rnames

        except Exception as e:
            msg = 'Cannot wrap primitive DP.'
            raise_wrapped(ValueError, e, msg, dp=self.dp, F=F, R=R,
                          fnames=fnames, rnames=rnames)

    def get_dp(self):
        return self.dp

    def get_fnames(self):
        if self.F_single:
            return [self.Fname]
        else:
            return self.Fnames

    def get_rnames(self):
        if self.R_single:
            return [self.Rname]
        else:
            return self.Rnames

    def __repr__(self):
        return 'Wrap(%s|%s|%s)' % (self.get_fnames(), self.dp, self.get_rnames())
    
    def rindex(self, r):
        if self.R_single:
            if not r == self.Rname:
                raise ValueError('I only know %r; asked %r.' % (self.Rname, r))

            return ()

        rnames = self.get_rnames()
        try:
            return rnames.index(r)
        except ValueError:
            msg = 'Cannot find %r in %r.' % (r, rnames)
            raise ValueError(msg)


    def findex(self, f):
        if self.F_single:
            if not f == self.Fname:
                raise ValueError('I only know %r; asked %r.' % (self.Fname, f))
            return ()
        fnames = self.get_fnames()
        try:
            return fnames.index(f)
        except ValueError:
            msg = 'Cannot find %r in %r.' % (f, fnames)
            raise ValueError(msg)

    @contract(fname=str)
    def get_ftype(self, fname):
        F = self.get_dp().get_fun_space()
        i = self.findex(fname)
#         print('Asking type of %r in F = %r with index = %r' % (fname, F, i))
        return get_it(F, i, reduce_list=None)

    def get_ftypes(self, signals):
        # Returns the product space
        types = [self.get_ftype(s) for s in signals]
        return PosetProduct(tuple(types))

    @contract(rname=str)
    def get_rtype(self, rname):
        R = self.get_dp().get_res_space()
        i = self.rindex(rname)
#         print('Asking type of %r in R = %r with index = %r' % (rname, R, i))
        return get_it(R, i, reduce_list=None)

    def get_rtypes(self, signals):
#         if not signals: raise ValueError('empty')
        # Returns the product space
        types = [self.get_rtype(s) for s in signals]
        return PosetProduct(tuple(types))

    def desc(self):
        s = 'Wrap'
        s += '\n dp= %s' % self.get_dp()
        for f in self.get_fnames():
            s += '\n %15s (%10s) ' % (f, self.get_ftype(f))
        for r in self.get_rnames():
            s += '\n (%10s) %15s ' % (self.get_rtype(r), r)
        return s


@contract(dp=PrimitiveDP, returns=NamedDP, fnames='str|seq(str)', rnames='str|seq(str)')
def dpwrap(dp, fnames, rnames):
    return SimpleWrap(dp, fnames, rnames)
