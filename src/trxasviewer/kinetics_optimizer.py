from concurrent.futures import ProcessPoolExecutor, as_completed

from PySide6.QtCore import QObject, Signal, Slot, QTimer

# Multiprocessing Manager for shared queue
from multiprocessing import Manager
from .core.fitting import run_single_optimization


class KineticOptimizerWorker(QObject):
    """
    A QObject subclass to run the parallel optimization in a separate QThread.
    It communicates progress and results back to the GUI via signals.
    """

    # Define signals that the GUI can connect to
    progress_updated = Signal(int)  # Emits current progress percentage (0-100)
    log_message = Signal(str)  # Emits informative messages for the log display
    optimization_finished = Signal(
        tuple
    )  # Emits the final best results (params, concs, spectra, loss, run_id)
    error_occurred = Signal(str)  # Emits error messages

    def __init__(
        self,
        t_eval,
        experimental_data,
        adj_matrix,
        bounds,
        num_runs,
        tol,
        method,
        fit_trange=None,
        parent=None,
    ):
        super().__init__(parent)
        self.t_eval = t_eval
        self.experimental_data = experimental_data
        self.adj_matrix = adj_matrix
        self.bounds = bounds
        self.num_runs = num_runs
        self.tol = tol
        self.method = method
        # Default fit_trange spans the full time axis
        self.fit_trange = fit_trange if fit_trange is not None else (t_eval.min(), t_eval.max())

        self._is_running = False
        self.completed_runs = 0

        # Use multiprocessing.Manager to create a queue that can be shared between processes
        self.manager = Manager()
        self.progress_queue = self.manager.Queue()

        # QTimer to periodically check the multiprocessing queue from this QThread
        self.queue_monitor_timer = QTimer(self)
        self.queue_monitor_timer.timeout.connect(self._check_queue)
        self.queue_monitor_timer.setInterval(
            100
        )  # Check the queue every 100 milliseconds

    def _check_queue(self):
        """
        Polls the multiprocessing queue for messages from the worker processes.
        """
        while not self.progress_queue.empty():
            try:
                message = (
                    self.progress_queue.get_nowait()
                )  # Get message without blocking
                msg_type = message.get("type")

                if msg_type == "run_completed":
                    self.completed_runs += 1
                    current_loss = message.get("loss")
                    run_id = message.get("run_id")
                    self.log_message.emit(
                        f"Run {run_id+1}/{self.num_runs} completed. Loss: {current_loss:.6e}"
                    )
                    progress_percent = int((self.completed_runs / self.num_runs) * 100)
                    self.progress_updated.emit(progress_percent)
                elif msg_type == "error":
                    self.error_occurred.emit(
                        f"Error in run {message.get('run_id')}: {message.get('message')}"
                    )
            except Exception as e:
                self.error_occurred.emit(f"Error processing queue message: {e}")
                # Break to prevent an infinite loop on a bad message
                break

        # Stop the timer if all expected runs are completed and the queue is empty
        # This condition helps ensure clean shutdown and state management.
        if self.completed_runs >= self.num_runs and self.progress_queue.empty():
            self.queue_monitor_timer.stop()
            self._is_running = False  # Mark as finished

    @Slot()
    def run_optimization(self):
        """
        This method is executed in the separate QThread when the thread starts.
        It initiates the parallel optimization and handles the final results.
        """
        if self._is_running:
            self.log_message.emit("Optimization is already running.")
            return

        self._is_running = True
        self.completed_runs = 0  # Reset counter for a new run
        self.progress_updated.emit(0)  # Reset progress bar
        self.log_message.emit(f"Starting {self.num_runs} parallel optimization runs...")

        self.queue_monitor_timer.start()  # Start monitoring the progress queue

        try:
            best_loss = float("inf")
            best_params = None
            best_concs = None
            best_spectra = None
            best_result = None
            best_run_id = -1

            with ProcessPoolExecutor() as executor:
                futures = {
                    executor.submit(
                        run_single_optimization,
                        self.t_eval,
                        self.experimental_data,
                        self.adj_matrix,
                        self.bounds,
                        self.fit_trange,
                        self.tol,
                        self.method,
                        run_id,
                    ): run_id
                    for run_id in range(self.num_runs)
                }

                for future in as_completed(futures):
                    run_id = futures[future]
                    try:
                        loss, opt_params, final_concs, final_spectra, res = future.result()
                        self.progress_queue.put(
                            {"type": "run_completed", "run_id": run_id, "loss": loss}
                        )
                        if loss < best_loss:
                            best_loss = loss
                            best_params = opt_params
                            best_concs = final_concs
                            best_spectra = final_spectra
                            best_result = res
                            best_run_id = run_id
                    except Exception as exc:
                        self.progress_queue.put(
                            {
                                "type": "error",
                                "run_id": run_id,
                                "message": str(exc),
                            }
                        )

            # Emit final results to the GUI (happens after all runs are done)
            self.optimization_finished.emit(
                (
                    best_params,
                    best_concs,
                    best_spectra,
                    best_loss,
                    best_run_id,
                )
            )
            self.log_message.emit("Optimization process completed successfully!")

        except Exception as e:
            self.error_occurred.emit(f"Optimization process failed: {e}")
        finally:
            self.queue_monitor_timer.stop()  # Ensure timer is stopped
            self._is_running = False  # Reset running state
