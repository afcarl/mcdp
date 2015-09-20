from mocdp.unittests.generation import for_all_dps
from mocdp.poset_utils import poset_check_chain

@for_all_dps
def check_dp1(_id_dp, dp):
    funsp = dp.get_fun_space()

    f_top = funsp.get_top()
    f_bot = funsp.get_bottom()

#     ressp = dp.get_res_space()
#     r_top = ressp.get_top()
#     r_bot = ressp.get_bot()

    u0 = dp.solve(f_bot)
    u1 = dp.solve(f_top)

    trsp = dp.get_tradeoff_space()

    print('u0', u0)
    print('u1', u1)

    trsp.check_leq(u0, u1)


@for_all_dps
def check_dp2(_id_dp, dp):
    funsp = dp.get_fun_space()

    chain = funsp.get_test_chain(n=5)
    poset_check_chain(funsp, chain)

    trchain = map(dp.solve, chain)

    trsp = dp.get_tradeoff_space()
    poset_check_chain(trsp, trchain)

    print trchain

