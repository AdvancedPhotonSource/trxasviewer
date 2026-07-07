import numpy as np
import pytest
from trxasviewer.core.fitting import (
    create_q_matrix, calculate_concentrations, create_initial_state_array,
    find_initial_states,
)


def test_create_q_matrix_2state():
    # adj[1][0] = 1 means transition from state 0 → state 1
    # So state 0 is the source (decays) and state 1 is the sink (ground state)
    adj = np.array([[0, 0], [1, 0]])
    params = np.array([1.0])  # one rate
    Q = create_q_matrix(adj, params)
    assert Q.shape == (2, 2)
    # State 0 has one outgoing transition so its diagonal must be negative
    assert Q[0, 0] < 0
    # State 1 has no outgoing transitions so its diagonal is 0
    assert Q[1, 1] == 0.0


def test_concentrations_sum_to_one():
    adj = np.array([[0, 0], [1, 0]])
    params = np.array([0.5])
    t_eval = np.linspace(0, 10, 100)
    conc = calculate_concentrations(params, t_eval, adj)
    # Concentrations should sum to ~1 at all times
    assert np.allclose(conc.sum(axis=1), 1.0, atol=1e-6)


def test_find_initial_states_simple():
    adj = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    initial = find_initial_states(adj)
    # Only state 2 (index 2) has no incoming edges from other "initial" states
    assert len(initial) > 0


def test_create_initial_state_array():
    adj = np.array([[0, 0], [1, 0]])
    arr = create_initial_state_array(adj)
    assert len(arr) == 2
    # First state has no parents → initial
    assert arr[0] == 1
    assert arr[1] == 0
