import numpy as np
from scipy.optimize import minimize
from scipy.integrate import solve_ivp


def get_tc(params, t_eval, adj_matrix, initial_value):
    A = np.zeros_like(adj_matrix)
    A[np.nonzero(initial_value)] = params

    def dP_dt(t, P):
        return A @ P

    t_span = (0, np.max(t_eval))
    ct = solve_ivp(dP_dt, t_span, initial_value, t_eval=t_eval).y.T
    return ct


def get_cr(diff, tc):
    cr, residuals, rank, s = np.linalg.lstsq(tc, diff, rcond=None)
    return cr


def get_loss(diff_exp, diff_model):
    frob_norm = np.linalg.norm(diff_exp - diff_model)
    return frob_norm


def model(params, t_eval, diff, adj_matrix, initial_value, plot=False):
    tc = get_tc(params, t_eval, adj_matrix, initial_value)
    cr = get_cr(diff, tc)
    diff_model = tc @ cr
    loss = get_loss(diff, diff_model)
    return loss


def global_fit_exafs_map(
    t_eval,
    diff,
    adj_matrix,
    p0,
    initial_value,
    constraints=None,
    bounds=None,
    plot=True,
    tol=1e-6,
):
    res = minimize(
        model,
        p0,
        method="Nelder-Mead",
        tol=tol,
        args=(t_eval, diff, adj_matrix, initial_value),
        constraints=constraints,
        bounds=bounds,
    )
    opt_p = res.x
    if plot:
        model(opt_p, t_eval, diff, adj_matrix, initial_value, plot=True)
