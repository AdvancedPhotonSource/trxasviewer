import logging
import time
import unittest

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

logger = logging.getLogger(__name__)  # Create a logger for this module


def _get_initial_state_indices(adj_matrix):
    """
    Helper function to find the indices of all initial states.

    An initial state is one with no incoming transitions from other states.

    Parameters:
    - adj_matrix: 2D list representing adjacency (1 at [i][j] means j → i)

    Returns:
    - A list of integer indices for the initial states.
    """
    num_states = len(adj_matrix)
    initial_indices = []
    for i in range(num_states):
        # Sum the values in the row `i` to count incoming edges from other states.
        # We exclude the diagonal element `adj_matrix[i][i]`, which represents a self-loop.
        num_parents = sum(adj_matrix[i][j] for j in range(num_states) if i != j)

        if num_parents == 0:
            initial_indices.append(i)
    return initial_indices


def find_initial_states(adj_matrix):
    """
    Finds all states with no incoming transitions (parents).

    Parameters:
    - adj_matrix: 2D list representing adjacency (1 at [i][j] means j → i)

    Returns:
    - A list of names for the initial states (e.g., ['S1', 'S4']).
    """
    num_states = len(adj_matrix)
    if num_states == 0:
        return []

    state_names = [f"S{i + 1}" for i in range(num_states)]

    # Use the helper function to get the indices of initial states
    initial_indices = _get_initial_state_indices(adj_matrix)

    # Map indices to state names
    return [state_names[i] for i in initial_indices]


def create_initial_state_array(adj_matrix):
    """
    Creates an array indicating the initial states of a system.

    This function identifies states with no incoming transitions from other states
    and represents them with a 1 in an output array. All other states are
    represented with a 0.

    Parameters:
    - adj_matrix: A 2D list (square matrix) where adj_matrix[i][j] = 1
                  signifies a transition from state j to state i.

    Returns:
    - A list of integers (e.g., [1, 0, 0, 1]) where a 1 at index `i`
      indicates that state `i` is an initial state.
    """
    num_states = len(adj_matrix)
    if num_states == 0:
        return []

    initial_array = [0] * num_states

    # Use the helper function to get the indices of initial states
    initial_indices = _get_initial_state_indices(adj_matrix)

    # Set the value to 1 for each initial state index
    for i in initial_indices:
        initial_array[i] = 1

    return initial_array


def create_q_matrix(adj_matrix, params):
    """Constructs a Q-matrix (rate matrix) from an adjacency matrix and rate parameters.

    The Q-matrix is a fundamental component in kinetic modeling, where:
    1. Off-diagonal elements Q_ij (i != j) represent the rate of transition
       from state j to state i.
    2. Diagonal elements Q_ii represent the total rate of leaving state i,
       calculated as the negative sum of all other elements in that column.

    Parameters
    ----------
    adj_matrix : np.ndarray
        A 2D array defining the reaction network structure. A non-zero element
        at adj_matrix[i, j] indicates a reaction from species j to species i.
    params : np.ndarray
        A 1D array of rate constants corresponding to the non-zero elements
        in the adjacency matrix.

    Returns
    -------
    np.ndarray
        The fully constructed Q-matrix.

    Raises
    ------
    ValueError
        If the number of rate parameters in `params` does not match the
        number of connections defined in `adj_matrix`.
    """
    # Start with a copy of the adjacency matrix and ensure the diagonal is zero.
    q_matrix = np.array(adj_matrix, dtype=float)
    np.fill_diagonal(q_matrix, 0)

    # Validate that the number of rates matches the number of connections.
    num_connections = np.count_nonzero(q_matrix)
    if num_connections != len(params):
        raise ValueError(
            f"The number of connections in adj_matrix ({num_connections}) "
            f"must equal the number of rate parameters ({len(params)})."
        )

    # Populate the off-diagonal rates from the params vector.
    q_matrix[q_matrix != 0] = 1.0 / params

    # Calculate the diagonal elements. Each diagonal element is the negative
    # sum of all other elements in its column.
    column_sums = np.sum(q_matrix, axis=0)
    np.fill_diagonal(q_matrix, -column_sums)

    return q_matrix


def calculate_concentrations(params, t_eval, adj_matrix):
    """Solves the system of differential equations to get time-dependent concentrations.

    This function constructs a rate matrix 'A' from the given kinetic parameters
    and solves the first-order linear differential equation dP/dt = A @ P, where P
    represents the concentrations of different species over time.

    Parameters
    ----------
    params : np.ndarray
        A 1D array of rate constants. These are the values to be optimized.
    t_eval : np.ndarray
        A 1D array of time points at which to evaluate the concentrations.
    adj_matrix : np.ndarray
        A 2D array defining the reaction network structure.

    Returns
    -------
    np.ndarray
        A 2D array of shape (len(t_eval), n_species) containing the calculated
        concentrations of each species at each time point in t_eval.
    """
    # Generate the full Q-matrix (rate matrix) using the provided params.
    rate_matrix = create_q_matrix(adj_matrix, params)
    initial_concentrations = create_initial_state_array(adj_matrix)

    # Define the system of ordinary differential equations (ODEs).
    def dP_dt(t, P):
        """Calculates the time derivative of concentrations."""
        return rate_matrix @ P

    t_span = (0, np.max(t_eval))

    # Solve the ODE system.
    solution = solve_ivp(
        dP_dt, t_span, initial_concentrations, t_eval=t_eval, dense_output=True
    )

    # Transpose the solution to get shape (n_times, n_species).
    concentrations = solution.y.T
    return concentrations


def calculate_residuals_and_spectra(
    experimental_data, concentrations, force_groundstate=True
):
    """Calculates species spectra and the sum of squared residuals.

    This function solves the linear system `concentrations @ spectra = experimental_data`
    using linear least-squares. It returns both the calculated spectra and the
    sum of squared residuals, which can be used directly as a loss metric.

    Parameters
    ----------
    experimental_data : np.ndarray
        The experimental data array, with shape (n_times, n_features).
    concentrations : np.ndarray
        The time-dependent concentration matrix from `calculate_concentrations`,
        with shape (n_times, n_species).
    force_groundstate : bool, optional
        If True (default), the spectrum for the last species (assumed to be
        the ground state) is forced to be zero.

    Returns
    -------
    component_spectra : np.ndarray
        The calculated species-resolved spectra, shape (n_species, n_features).
    sum_sq_residuals : float
        The sum of the squared differences between the experimental data and the
        reconstructed model signal.
    """
    if force_groundstate:
        # Prepare to solve the least-squares problem for the n-1 excited species
        active_concentrations = concentrations[:, :-1]
    else:
        # Prepare to solve for all species
        active_concentrations = concentrations

    # --- Call lstsq once on the prepared concentrations ---
    component_spectra_temp, sum_sq_residuals_array, _, _ = np.linalg.lstsq(
        active_concentrations, experimental_data, rcond=None
    )

    # --- Format the output based on the constraint ---
    if force_groundstate:
        # Add a row of zeros for the ground state spectrum to the result
        zeros_row = np.zeros((1, component_spectra_temp.shape[1]))
        component_spectra = np.vstack([component_spectra_temp, zeros_row])
    else:
        component_spectra = component_spectra_temp

    # Sum the residuals from each feature column to get a single loss value.
    # np.sum() on an empty array (if it occurs) correctly returns 0.0.
    total_residuals = np.sum(sum_sq_residuals_array)

    return component_spectra, total_residuals


def objective_function(params, t_eval, experimental_data, adj_matrix):
    """The main model function that calculates loss for a given set of parameters.

    This is the objective function for the optimization. It takes a set of rate
    parameters and computes the total error (loss) compared to the experimental data.

    Parameters
    ----------
    params : np.ndarray
        A 1D array of rate constants to be evaluated.
    t_eval : np.ndarray
        Time points for evaluation.
    experimental_data : np.ndarray
        Experimental data matrix.
    adj_matrix : np.ndarray
        The adjacency matrix defining the reaction structure.
    initial_concentrations : np.ndarray
        Initial concentrations of the species.

    Returns
    -------
    float
        The calculated loss value (square root of the sum of squared residuals).
    """
    concentrations = calculate_concentrations(params, t_eval, adj_matrix)
    component_spectrum, sum_sq_residuals = calculate_residuals_and_spectra(
        experimental_data, concentrations
    )
    # logger.info(concentrations.shape, component_spectrum.shape, experimental_data.shape) # Mute this print for cleaner multiprocessing output
    return np.sqrt(sum_sq_residuals)


def global_fit_kinetic_model(
    t_eval,
    experimental_data,
    adj_matrix,
    bounds=None,
    tol=1e-6,
    method="L-BFGS-B",
    initial_params=None,  # Add initial_params as an argument for multiprocessing
):
    """Performs a global optimization to find the best-fit rate parameters.

    Parameters are described in the other functions.

    Returns
    -------
    tuple: (float, np.ndarray, np.ndarray, scipy.optimize.OptimizeResult)
        The final loss, optimized parameters, final concentrations,
        final spectra, and the full result object from the `minimize` function.
    """
    scale = np.max(t_eval)
    t_eval_scaled = t_eval / scale  # Use a new variable for scaled t_eval

    if bounds is not None:
        bounds_scaled = np.array(bounds) / scale  # Ensure bounds are also scaled

    if initial_params is None:
        # Generate initial parameters if not provided (for first run or a new process)
        if bounds is not None:
            rand = np.random.uniform(0, 1, bounds_scaled.shape[0])
            initial_params_scaled = (
                bounds_scaled[:, 0] * (1 - rand) + rand * bounds_scaled[:, 1]
            )
        else:
            raise ValueError(
                "If initial_params are not provided, bounds must be provided to generate them."
            )
    else:
        # If initial_params are provided, scale them if bounds are used for scaling
        initial_params_scaled = np.array(initial_params) / scale

    res = minimize(
        fun=objective_function,
        x0=initial_params_scaled,  # Use scaled initial params
        method=method,
        tol=tol,
        args=(t_eval_scaled, experimental_data, adj_matrix),  # Use scaled t_eval
        bounds=bounds_scaled if bounds is not None else None,  # Use scaled bounds
    )

    opt_params_scaled = res.x

    # Scale back the optimized parameters
    opt_params = opt_params_scaled * scale

    # Calculate final concentrations and spectra with the optimized parameters
    # and original t_eval for plotting/analysis if desired
    final_concentrations = calculate_concentrations(opt_params, t_eval, adj_matrix)
    final_spectra, _ = calculate_residuals_and_spectra(
        experimental_data, final_concentrations
    )
    final_loss = np.sum(
        np.square((final_concentrations @ final_spectra - experimental_data))
    )

    # logger.info(
    #     f"Process {os.getpid()} finished. Final Loss: {final_loss:.4f}, Optimized Parameters: {np.round(opt_params, 3)}"
    # )

    return final_loss, opt_params, final_concentrations, final_spectra, res


def run_single_optimization(
    t_eval_raw,
    experimental_data_raw,
    adj_matrix,
    bounds,
    fit_trange,
    tol,
    method,
    run_id,
):
    """
    Wrapper function to run global_fit_kinetic_model for multiprocessing.
    Includes random initial parameter generation within the worker process.
    """
    # Generate random initial parameters within the worker process
    # This ensures each process gets a truly independent starting point
    # based on the provided bounds.
    t0 = time.perf_counter()

    # crop the negative time points
    mask = (t_eval_raw >= fit_trange[0]) * (t_eval_raw <= fit_trange[1])
    t_eval = t_eval_raw[mask]
    experimental_data = experimental_data_raw[mask]

    scale = np.max(t_eval)
    bounds_scaled = np.array(bounds) / scale
    rand = np.random.uniform(0, 1, bounds_scaled.shape[0])
    initial_params = bounds_scaled[:, 0] * (1 - rand) + rand * bounds_scaled[:, 1]

    loss, opt_params, opt_concentrations, opt_spectra, res = global_fit_kinetic_model(
        t_eval=t_eval,
        experimental_data=experimental_data,
        adj_matrix=adj_matrix,
        bounds=bounds,  # Pass original bounds to global_fit_kinetic_model, it will scale internally
        tol=tol,
        method=method,
        initial_params=initial_params * scale,
    )

    # some time points may not be evaluated due to the settings in fit_trange
    t_eval_valid = t_eval_raw[t_eval_raw >= 0]  # get all valid t_eval
    final_concentrations = calculate_concentrations(
        opt_params, t_eval_valid, adj_matrix
    )
    # pad zeros to the pre-pump time points
    pad_rows = t_eval_raw.size - t_eval_valid.size
    # t0 concentrations
    initial_concentrations = create_initial_state_array(adj_matrix)
    total_concentrations = np.sum(initial_concentrations)

    final_concentrations = np.pad(
        final_concentrations, ((pad_rows, 0), (0, 0)), mode="constant",
    )
    final_concentrations[0:pad_rows, -1] = total_concentrations

    dt = time.perf_counter() - t0
    logger.info(
        f"Finished fitting {run_id} with {method} in {dt:.2f} seconds. Loss: {loss:.8g}."
    )
    return loss, opt_params, final_concentrations, opt_spectra, res


# --- Unit Test Suite ---


class TestKineticModel(unittest.TestCase):
    """Unit test suite for the kinetic model fitting functions."""

    def setUp(self):
        """Set up the test environment before each test method.

        This method prepares a consistent set of data for a simple
        A -> B -> C reaction model, including the "true" parameters and
        a mock experimental dataset with noise.
        """
        # Define the kinetic model structure (A->B->C)
        self.adj_matrix = np.array(
            [[0, 0, 0], [1, 0, 0], [0, 1, 0]]  # To A  # To B  # To C
        )
        self.true_params = np.array([0.5, 0.2])  # k1=0.5, k2=0.2
        # Mock initial concentrations - will be overridden by create_initial_state_array for actual runs
        # For testing purposes, we assume create_initial_state_array returns consistent results
        # if not defined in the original module.
        try:
            self.initial_concs = create_initial_state_array(self.adj_matrix)
        except Exception:
            # Fallback for testing if trxas_graph is not readily available
            self.initial_concs = np.array([1.0, 0.0, 0.0])

        self.t_eval = np.linspace(0, 20, 100)

        # Set a random seed for reproducible tests
        np.random.seed(0)

        # Generate mock data based on the true model
        # Temporarily use the initial_concs argument for calculate_concentrations in setUp
        # as it's not present in the current `calculate_concentrations` definition.
        # This highlights a potential mismatch between setUp and the actual function signature.
        # For the provided `calculate_concentrations`, initial_concentrations are always
        # obtained from `create_initial_state_array(adj_matrix)`.
        # To make the test runnable, we'll ensure `create_initial_state_array` is used.
        true_concentrations = calculate_concentrations(
            self.true_params, self.t_eval, self.adj_matrix
        )
        # Define "pure spectra" for species A, B, and C
        pure_spectra = np.array(
            [
                [1.0, 0.2],  # Spectrum for A
                [0.3, 1.0],  # Spectrum for B
                [0.1, 0.1],  # Spectrum for C
            ]
        )
        # The mock data is the combination of concentrations and spectra plus noise
        self.mock_data = (true_concentrations @ pure_spectra) + np.random.normal(
            0, 0.02, (self.t_eval.shape[0], 2)
        )
        self.bounds = [(0.01, 10.0), (0.01, 10.0)]  # Example bounds for parameters

    def test_q_matrix_creation(self):
        """Tests that the create_q_matrix function assembles the matrix correctly."""
        logger.info("Running test: test_q_matrix_creation")
        q_matrix = create_q_matrix(self.adj_matrix, self.true_params)

        expected_q_matrix = np.array(
            [[-0.5, 0.0, 0.0], [0.5, -0.2, 0.0], [0.0, 0.2, 0.0]]
        )

        # Use unittest's assertion tools
        self.assertTrue(
            np.allclose(q_matrix, expected_q_matrix),
            "Q-Matrix did not match expected values.",
        )
        logger.info("PASSED: test_q_matrix_creation")

    def test_global_fit_finds_correct_parameters(self):
        """Tests that the global fit can recover the true parameters from mock data."""
        logger.info("\nRunning test: test_global_fit_finds_correct_parameters")
        # For a single run, initial_params would typically be provided or generated.
        # Here we'll rely on the internal generation within global_fit_kinetic_model.
        # We need to ensure that the global_fit_kinetic_model can be called with the new signature
        # as updated for parallel processing.

        # When calling directly, provide bounds if initial_params is None
        loss, opt_params, _, _, res = global_fit_kinetic_model(
            t_eval=self.t_eval,
            experimental_data=self.mock_data,
            adj_matrix=self.adj_matrix,
            bounds=self.bounds,  # Provide bounds to generate initial params
            tol=1e-6,
            method="L-BFGS-B",
        )

        # Check if the optimization was successful
        self.assertTrue(res.success, "Optimization reported failure.")

        # Check if the recovered parameters are close to the true parameters
        # A relative tolerance (rtol) is used to account for noise and optimizer precision.
        self.assertTrue(
            np.allclose(opt_params, self.true_params, rtol=0.2),
            f"Optimized parameters {np.round(opt_params, 3)} are not close to true values {self.true_params}.",
        )
        logger.info("PASSED: test_global_fit_finds_correct_parameters")
