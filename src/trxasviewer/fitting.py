import numpy as np
from scipy.optimize import minimize
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import unittest

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
    q_matrix[q_matrix != 0] = params

    # Calculate the diagonal elements. Each diagonal element is the negative
    # sum of the other elements in its column.
    column_sums = np.sum(q_matrix, axis=0)
    np.fill_diagonal(q_matrix, -column_sums)

    return q_matrix

def calculate_concentrations(params, t_eval, adj_matrix, initial_concentrations):
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
    initial_concentrations : np.ndarray
        A 1D array of the initial concentrations for each species at t=0.

    Returns
    -------
    np.ndarray
        A 2D array of shape (len(t_eval), n_species) containing the calculated
        concentrations of each species at each time point in t_eval.
    """
    # Generate the full Q-matrix (rate matrix) using the provided params.
    rate_matrix = create_q_matrix(adj_matrix, params)

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


def objective_function(params, t_eval, experimental_data, adj_matrix, initial_concentrations):
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
    concentrations = calculate_concentrations(params, t_eval, adj_matrix, initial_concentrations)
    _, sum_sq_residuals = calculate_residuals_and_spectra(experimental_data, concentrations)
    return np.sqrt(sum_sq_residuals)


def global_fit_kinetic_model(
    t_eval,
    experimental_data,
    adj_matrix,
    initial_params,
    initial_concentrations,
    constraints=None,
    bounds=None,
    plot=True,
    tol=1e-6,
):
    """Performs a global optimization to find the best-fit rate parameters.

    Parameters are described in the other functions.

    Returns
    -------
    scipy.optimize.OptimizeResult
        The full result object from the `minimize` function.
    """
    res = minimize(
        fun=objective_function,
        x0=initial_params,
        method="Nelder-Mead",
        tol=tol,
        args=(t_eval, experimental_data, adj_matrix, initial_concentrations),
        constraints=constraints,
        bounds=bounds,
    )

    opt_params = res.x
    print(f"\nOptimization finished.\nFinal Loss: {res.fun:.4f}\nOptimized Parameters: {np.round(opt_params, 3)}")

    if plot:
        # To plot the final result, fully recalculate the final state.
        final_concentrations = calculate_concentrations(
            opt_params, t_eval, adj_matrix, initial_concentrations
        )
        final_spectra, _ = calculate_residuals_and_spectra(
            experimental_data, final_concentrations
        )
        model_signal = final_concentrations @ final_spectra

        # Plotting logic
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Plot 1: Concentrations over time
        ax1.set_title("Concentrations vs. Time")
        ax1.plot(t_eval, final_concentrations)
        ax1.legend([f'Species {i+1}' for i in range(final_concentrations.shape[1])])
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Concentration")

        # Plot 2: Model fit vs. Experimental Data (showing first feature)
        ax2.set_title("Model Fit vs. Experimental Data")
        ax2.plot(t_eval, experimental_data[:, 0], 'o', label="Experimental Data (Feature 1)", alpha=0.7)
        ax2.plot(t_eval, model_signal[:, 0], '-', label="Model Fit", linewidth=2)
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Signal")
        ax2.legend()
        fig.tight_layout()
        plt.show()

    return res

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
        self.adj_matrix = np.array([
            [0, 0, 0],  # To A
            [1, 0, 0],  # To B
            [0, 1, 0]   # To C
        ])
        self.true_params = np.array([0.5, 0.2])  # k1=0.5, k2=0.2
        self.initial_concs = np.array([1.0, 0.0, 0.0])
        self.t_eval = np.linspace(0, 20, 100)
        
        # Set a random seed for reproducible tests
        np.random.seed(0)

        # Generate mock data based on the true model
        true_concentrations = calculate_concentrations(
            self.true_params, self.t_eval, self.adj_matrix, self.initial_concs
        )
        # Define "pure spectra" for species A, B, and C
        pure_spectra = np.array([
            [1.0, 0.2],  # Spectrum for A
            [0.3, 1.0],  # Spectrum for B
            [0.1, 0.1]   # Spectrum for C
        ])
        # The mock data is the combination of concentrations and spectra plus noise
        self.mock_data = (true_concentrations @ pure_spectra) + \
                         np.random.normal(0, 0.02, (self.t_eval.shape[0], 2))

    def test_q_matrix_creation(self):
        """Tests that the create_q_matrix function assembles the matrix correctly."""
        print("Running test: test_q_matrix_creation")
        q_matrix = create_q_matrix(self.adj_matrix, self.true_params)
        
        expected_q_matrix = np.array([
            [-0.5, 0., 0.],
            [0.5, -0.2, 0.],
            [0., 0.2, 0.]
        ])
        
        # Use unittest's assertion tools
        self.assertTrue(
            np.allclose(q_matrix, expected_q_matrix),
            "Q-Matrix did not match expected values."
        )
        print("PASSED: test_q_matrix_creation")

    def test_global_fit_finds_correct_parameters(self):
        """Tests that the global fit can recover the true parameters from mock data."""
        print("\nRunning test: test_global_fit_finds_correct_parameters")
        # Use an initial guess that is different from the true values
        initial_params_guess = np.array([0.8, 0.1])
        
        fit_result = global_fit_kinetic_model(
            t_eval=self.t_eval,
            experimental_data=self.mock_data,
            adj_matrix=self.adj_matrix,
            initial_params=initial_params_guess,
            initial_concentrations=self.initial_concs,
            plot=False,  # Disable plotting for automated tests
            tol=1e-6,
        )
        
        # Check if the optimization was successful
        self.assertTrue(fit_result.success, "Optimization reported failure.")
        
        # Check if the recovered parameters are close to the true parameters
        # A relative tolerance (rtol) is used to account for noise and optimizer precision.
        self.assertTrue(
            np.allclose(fit_result.x, self.true_params, rtol=0.2),
            f"Optimized parameters {np.round(fit_result.x, 3)} are not close to true values {self.true_params}."
        )
        print("PASSED: test_global_fit_finds_correct_parameters")

if __name__ == '__main__':
    # This block allows the tests to be run from the command line
    # by executing `python your_script_name.py`
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
