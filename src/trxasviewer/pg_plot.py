import pyqtgraph as pg

PGCOLORS = ("r", "b", "k", "m", "g", "m", "y")
PGSYMBOLS = ("o", "s", "t", "d", "+", "*", "x", "p", "h")


def plot_kinetics_profile(results, kinetics_hdl, fit_data=None, points_only=False):
    """Plots the kinetics data with optional fitted curve."""
    kinetics_hdl.clear()
    kinetics_hdl.addLegend()

    if not results["kinetics"]:
        return

    for idx, (key, value) in enumerate(results["kinetics"].items()):
        data = value["profile"]["main"]
        x, y = data[0], data[1]
        pen = pg.mkPen(PGCOLORS[idx % len(PGCOLORS)], width=2)

        # Plot line only if not points_only
        if not points_only:
            kinetics_hdl.plot(x, y, pen=pen)

        # Always plot points
        scatter_plot = pg.ScatterPlotItem(
            x=x,
            y=y,
            size=3,
            pen=pen,
            brush=None,
            name=value["long_label"],
        )
        kinetics_hdl.addItem(scatter_plot)

        # Optional error bars
        if data.shape[0] == 3:
            yerr = data[2]
            beam = (x.max() - x.min()) / 200
            kinetics_hdl.addItem(
                pg.ErrorBarItem(x=x, y=y, height=yerr, beam=beam, pen=pen)
            )

    # Optional: plot fitted line
    if fit_data is not None:
        fit_pen = pg.mkPen("k", width=2)
        fit_x, fit_y = fit_data[0], fit_data[1]
        kinetics_hdl.plot(fit_x, fit_y, pen=fit_pen, name="Fit")

    kinetics_hdl.setLabel("left", "Intensity (a.u.)")
    kinetics_hdl.setLabel("bottom", "Time", units="s")


def plot_kinetics_error(results, kinetics_err_hdl, x_range=(-1, 10)):
    """
    Plot the error profile of the kinetics data.
    """
    kinetics_err_hdl.clear()
    kinetics_err_hdl.addLegend()
    for idx, (key, value) in enumerate(results["kinetics"].items()):
        pen = pg.mkPen(PGCOLORS[idx % len(PGCOLORS)], width=2)
        err_profile = value["profile"]["error"]
        if err_profile is not None:
            kinetics_err_hdl.plot(
                err_profile[:, 0],
                err_profile[:, 1],
                pen=pen,
                symbol=PGSYMBOLS[idx % len(PGSYMBOLS)],
                symbolPen=pen,
                name=key,
            )
    kinetics_err_hdl.setLabel("left", "Normalized Uncertainty")
    kinetics_err_hdl.setLabel("bottom", "Number of scans")
    return
