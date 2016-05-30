from comptests.registrar import comptest
from mocdp.lang.parse_actions import parse_ndp
from mocdp.comp.flattening.flatten import flatten_add_prefix
from mocdp.unittests.generation import for_all_nameddps

@for_all_nameddps
def check_flattening(id_ndp, ndp):
    ndp2 = ndp.flatten()

@comptest
def check_flatten1():
    ndp = parse_ndp("""
    mcdp {
      requires r1 [R]
      requires r2 [R]
      
      provides f1 [R]
      
      f1 <= r1 * r2
    }
    """)
    print(ndp)
    assert 'r1' in ndp.get_rnames()
    assert '_invmult1' in ndp.context.names
    ndp2 = flatten_add_prefix(ndp, prefix='prefix')
    print(ndp2)
    assert 'prefix/r1' in ndp2.get_rnames()
    assert 'prefix/f1' in ndp2.get_fnames()
    assert 'prefix/_invmult1' in ndp2.context.names
    
@comptest
def check_flatten2():
    ndp = parse_ndp("""
    mcdp { 
    M = instance mcdp {
      requires r1 [R]
      requires r2 [R]
      
      provides f1 [R]
      
      f1 <= r1 * r2
    }
    
    }
    """)
    ndp2 = ndp.flatten()
    print('resulting ndp2:\n')
    print ndp2

@comptest
def check_flatten3():

    ndp = parse_ndp("""
    mcdp { 
    M = instance mcdp {
      requires r1 [R]
      requires r2 [R]
      
      provides f1 [R]
      
      f1 <= r1 * r2
    }
    provides M1 <= M.f1
    requires R1 >= M.r1
    requires R2 >= M.r2
    }
    """)
    ndp2 = ndp.flatten()
    print('resulting ndp2:\n')
    print ndp2

@comptest
def check_flatten4():

    ndp = parse_ndp("""
    mcdp { 
    M = instance mcdp {
      requires r1 [R]
      requires r2 [R]
      
      provides f1 [R]
      
      f1 <= r1 * r2
    }
    N = instance mcdp {
      requires r1 [R]
      requires r2 [R]
      
      provides f1 [R]
      
      f1 <= r1 * r2
    }
    provides M1 <= M.f1
    requires R1 >= M.r1
    requires R2 >= M.r2
    provides NF1 <= N.f1
    requires NR1 >= N.r1
    requires NR2 >= N.r2
    }
    """)
    ndp2 = ndp.flatten()
    print('resulting ndp2:\n')
    print ndp2


@comptest
def check_flatten5():
    pass

@comptest
def check_flatten6():
    pass

@comptest
def check_flatten7():
    pass

@comptest
def check_flatten8():
    pass

@comptest
def check_flatten9():
    pass

@comptest
def check_flatten10():
    pass

@comptest
def check_flatten11():
    pass
