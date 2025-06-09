import numpy as np
import matplotlib.pyplot as plt


class TrXASResult:
    def __init__(self, data):
        self.data = data
        self.svd = self.get_svd(data)
        self.plot_diff()

    def plot_diff(self):
        t_axis = data["t_axis"]
        valid_t = t_axis >= 0
        plt.imshow(self.data["diff"][:, valid_t].T, cmap="coolwarm", origin="lower")
        plt.colorbar()
        plt.show()
        plt.close()

    def get_svd(self, data):
        t_axis = data["t_axis"]
        valid_t = t_axis >= 0

        u, s, v = np.linalg.svd(data["diff"][:, valid_t], full_matrices=False)
        s_accumulated = np.cumsum(s)
        # s_accumulated /= s_accumulated[-1]
        # plt.plot(s_accumulated, "ro")
        plt.plot(s, "ro")
        plt.show()
        return (u, s, v)

    def get_svd_models(self):
        return self.svd[1]

    def get_low_rank_approximation(self, rank=3):
        u, s, v = self.svd
        up = u[0:, :rank]
        sp = np.diag(s[0:rank])
        vp = v[:rank, 0:]
        return up @ sp @ vp


if __name__ == "__main__":
    f = "/Users/mqichu/Documents/trxas_data/kinetics_results/result_setup-full-00242-00258/results.npz"
    data = np.load(f)
    tr = TrXASResult(data)
