import logging
import os
import time
import unittest
from concurrent.futures import ProcessPoolExecutor, as_completed

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

from .trxas_graph import create_initial_state_array

logger = logging.getLogger(__name__)  # Create a logger for this module


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
    initial_concentrations = create_initial_state_array(
        adj_matrix
    )  # This dependency on trxas_graph needs to be handled if it's not a direct importable module in some environments.

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


def calculate_residuals_and_spectra(experimental_data, concentrations):
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

    Returns
    -------
    component_spectra : np.ndarray
        The calculated species-resolved spectra, shape (n_species, n_features).
    sum_sq_residuals : float
        The sum of the squared differences between the experimental data and the
        reconstructed model signal.
    """
    component_spectra, sum_sq_residuals_array, _, _ = np.linalg.lstsq(
        concentrations, experimental_data, rcond=None
    )
    return component_spectra, np.sum(sum_sq_residuals_array)


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
    t_eval, experimental_data, adj_matrix, bounds, tol, method, run_id
):
    """
    Wrapper function to run global_fit_kinetic_model for multiprocessing.
    Includes random initial parameter generation within the worker process.
    """
    # Generate random initial parameters within the worker process
    # This ensures each process gets a truly independent starting point
    # based on the provided bounds.
    t0 = time.perf_counter()
    scale = np.max(t_eval)
    bounds_scaled = np.array(bounds) / scale
    rand = np.random.uniform(0, 1, bounds_scaled.shape[0])
    initial_params = bounds_scaled[:, 0] * (1 - rand) + rand * bounds_scaled[:, 1]

    loss, opt_params, final_concentrations, final_spectra, res = (
        global_fit_kinetic_model(
            t_eval=t_eval,
            experimental_data=experimental_data,
            adj_matrix=adj_matrix,
            bounds=bounds,  # Pass original bounds to global_fit_kinetic_model, it will scale internally
            tol=tol,
            method=method,
            initial_params=initial_params
            * scale,  # Pass scaled initial params to the function, as global_fit_kinetic_model expects unscaled
        )
    )

    dt = time.perf_counter() - t0
    logger.info(
        f"Finished fitting {run_id} with {method} in {dt:.2f} seconds. Loss: {loss:.8g}."
    )
    return loss, opt_params, final_concentrations, final_spectra, res


def run_parallel_optimizations(
    num_runs, t_eval, experimental_data, adj_matrix, bounds, tol=1e-6, method="L-BFGS-B"
):
    """
    Runs global_fit_kinetic_model multiple times in parallel with different
    random starting points and returns the best result.

    Parameters
    ----------
    num_runs : int
        The number of independent optimization runs to perform.
    t_eval : np.ndarray
        Time points for evaluation.
    experimental_data : np.ndarray
        Experimental data matrix.
    adj_matrix : np.ndarray
        The adjacency matrix defining the reaction structure.
    bounds : list of tuples
        Bounds for each parameter, e.g., [(min1, max1), (min2, max2), ...].
    tol : float, optional
        Tolerance for optimization. Defaults to 1e-6.
    method : str, optional
        Optimization method. Defaults to "L-BFGS-B".

    Returns
    -------
    tuple: (float, np.ndarray, np.ndarray, np.ndarray, scipy.optimize.OptimizeResult, int)
        The best final loss, best optimized parameters, corresponding final concentrations,
        final spectra, the OptimizeResult object from the best run, and the run_id of the best run.
    """
    best_loss = np.inf
    best_opt_params = None
    best_final_concentrations = None
    best_final_spectra = None
    best_res = None
    best_run_id = -1

    # Use ProcessPoolExecutor for parallel execution
    # It's recommended to use 'spawn' start method for multiprocessing in some environments
    # to avoid issues, especially on macOS and Windows.
    # mp.set_start_method('spawn', force=True) # Uncomment if you encounter issues

    # max_workers=os.cpu_count() will use all available CPU cores
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Submit multiple optimization tasks with different random initial parameters
        futures = {
            executor.submit(
                run_single_optimization,
                t_eval,
                experimental_data,
                adj_matrix,
                bounds,
                tol,
                method,
                i,
            ): i
            for i in range(num_runs)
        }

        for future in as_completed(futures):
            run_id = futures[future]
            try:
                loss, opt_params, final_concentrations, final_spectra, res, _ = (
                    future.result()
                )
                # if abs(loss) < 1e-6:
                #     loss = 1e8
                if loss < best_loss:
                    best_loss = loss
                    best_opt_params = opt_params
                    best_final_concentrations = final_concentrations
                    best_final_spectra = final_spectra
                    best_res = res
                    best_run_id = run_id
            except Exception as exc:
                logger.info(f"Run {run_id} generated an exception: {exc}")

    logger.info(f"\n--- Parallel Optimization Summary ---")
    logger.info(f"Total runs: {num_runs}")
    logger.info(f"Best run ID: {best_run_id}")
    logger.info(f"Overall Best Loss: {best_loss:.8e}")
    logger.info(f"Optimized Parameters from best run: {np.round(best_opt_params, 3)}")

    return (
        best_opt_params,
        best_final_concentrations,
        best_final_spectra,
    )


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

    def test_parallel_fit_finds_best_parameters(self):
        """Tests that the parallel fit can find the best parameters from multiple runs."""
        logger.info("\nRunning test: test_parallel_fit_finds_best_parameters")
        num_parallel_runs = 5  # Number of parallel runs for the test

        best_loss, best_opt_params, _, _, best_res, best_run_id = (
            run_parallel_optimizations(
                num_runs=num_parallel_runs,
                t_eval=self.t_eval,
                experimental_data=self.mock_data,
                adj_matrix=self.adj_matrix,
                bounds=self.bounds,
                tol=1e-6,
                method="L-BFGS-B",
            )
        )

        self.assertLessEqual(
            best_loss,
            0.1,
            "Best loss from parallel runs is too high, indicating poor fit.",
        )
        self.assertTrue(
            np.allclose(best_opt_params, self.true_params, rtol=0.2),
            f"Best optimized parameters {np.round(best_opt_params, 3)} are not close to true values {self.true_params}.",
        )
        self.assertIsInstance(
            best_res,
            type(minimize(lambda x: x[0] ** 2, [1]).fun),
            "Returned best_res is not a SciPy OptimizeResult object.",
        )
        logger.info(
            f"PASSED: test_parallel_fit_finds_best_parameters (Best run ID: {best_run_id}, Loss: {best_loss:.4f})"
        )


if __name__ == "__main__":
    # Example usage of parallel optimization
    # First, let's create some dummy data and a reaction network
    # This part would typically be your actual experimental setup

    # Define a simple A -> B -> C reaction network
    adj_matrix = np.array(
        [
            [0, 0, 0],  # From A
            [1, 0, 0],  # From B
            [0, 1, 0],  # From C
        ]
    )
    # Define "true" parameters for generating mock data
    true_params_for_mock = np.array([0.05, 0.02])  # k_AB, k_BC

    # Define time points for simulation and experimental data
    t_eval_example = np.linspace(0, 100, 200)

    # Generate "true" concentrations for mock data
    # (Note: In a real scenario, you wouldn't know true_concentrations)
    # Assuming create_initial_state_array creates [1, 0, 0, ...]
    try:
        initial_concs_example = create_initial_state_array(adj_matrix)
    except Exception:
        # Fallback if trxas_graph is not set up in your test environment
        initial_concs_example = np.array([1.0, 0.0, 0.0])

    true_concentrations_example = calculate_concentrations(
        true_params_for_mock, t_eval_example, adj_matrix
    )

    # Define "pure spectra" for species A, B, and C
    # This converts concentrations into an observable signal
    pure_spectra_example = np.array(
        [
            [
                1.0,
                0.2,
                0.0,
            ],  # Spectrum for A (e.g., strong at wavelength 1, weak at wavelength 2)
            [0.3, 1.0, 0.1],  # Spectrum for B
            [0.1, 0.1, 0.8],  # Spectrum for C
        ]
    )

    # Generate mock experimental data by multiplying concentrations by spectra and adding noise
    np.random.seed(42)  # For reproducibility of mock data
    mock_experimental_data = (
        true_concentrations_example @ pure_spectra_example
    ) + np.random.normal(
        0, 0.05, (t_eval_example.shape[0], pure_spectra_example.shape[1])
    )

    # Define bounds for the rate constants to be optimized
    # The number of bounds should match the number of non-zero elements in adj_matrix (i.e., len(params))
    # For A->B->C, there are two rates, so two sets of bounds.
    bounds_example = [(0.001, 1.0), (0.001, 1.0)]

    # logger.info("--- Starting parallel optimization ---")
    # Run parallel optimization
    (
        best_loss_found,
        best_params_found,
        final_concs_best_run,
        final_spectra_best_run,
        best_result_object,
        best_run_id,
    ) = run_parallel_optimizations(
        num_runs=10,  # Number of parallel runs (adjust based on your CPU cores)
        t_eval=t_eval_example,
        experimental_data=mock_experimental_data,
        adj_matrix=adj_matrix,
        bounds=bounds_example,
        tol=1e-8,
        method="L-BFGS-B",
    )

    logger.info("\n--- Best Fit Results ---")
    logger.info(f"Best Loss: {best_loss_found:.6f}")
    logger.info(f"Best Parameters: {best_params_found}")
    logger.info(f"Best Run ID: {best_run_id}")
    logger.info("\n--- Comparison to True Parameters ---")
    logger.info(f"True Parameters: {true_params_for_mock}")

    # Optional: Plotting the results from the best fit
    plt.figure(figsize=(12, 6))

    # Plot experimental data
    plt.subplot(1, 2, 1)
    plt.plot(
        t_eval_example,
        mock_experimental_data,
        "o",
        markersize=3,
        label="Experimental Data",
    )
    # Reconstruct the signal from best fit concentrations and spectra
    reconstructed_signal = final_concs_best_run @ final_spectra_best_run
    plt.plot(
        t_eval_example, reconstructed_signal, "-", linewidth=2, label="Best Fit Model"
    )
    plt.title("Experimental Data vs. Best Fit Model")
    plt.xlabel("Time")
    plt.ylabel("Signal")
    plt.legend()

    # Plot concentrations from the best fit
    plt.subplot(1, 2, 2)
    for i in range(final_concs_best_run.shape[1]):
        plt.plot(
            t_eval_example,
            final_concs_best_run[:, i],
            label=f"Species {i+1} Concentration",
        )
    plt.title("Best Fit Concentrations")
    plt.xlabel("Time")
    plt.ylabel("Concentration")
    plt.legend()

    plt.tight_layout()
    plt.show()

    # Run unit tests
    logger.info("\n--- Running Unit Tests ---")
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
