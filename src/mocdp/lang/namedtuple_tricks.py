from collections import namedtuple

def namedtuplewhere(a, b):
    fields = b.split(" ")
    assert not 'where' in fields
    fields.append('where')
    base = namedtuple(a, fields)
    base.__new__.__defaults__ = (None,)
    F = base
    # make the name available
    g = globals()
    g[a] = F
    return F

def get_copy_with_where(x, where):
    d = x._asdict()
    del d['where']
    d['where'] = where
    T = type(x)
    x1 = T(**d)
    return x1

def remove_where_info(x):
    from compmake.jobs.dependencies import isnamedtupleinstance
    if not isnamedtupleinstance(x):
        return x
    d = x._asdict()
    for k, v in d.items():
        d[k] = remove_where_info(v)
    del d['where']
    d['where'] = None
    T = type(x)
    x1 = T(**d)
    return x1
