import re
import numpy as np
import matplotlib.pyplot as plt
import time
from functools import lru_cache
TRXAS_PATTERN = re.compile(r'c(\d+)o(\d+)b(\d+)')


def is_sample_data(fname):
    with open(fname, 'r') as f:
        line = f.readline()
        if re.match(r'#L .* Energy ', line):
            return True
        else:
            return False


@lru_cache(maxsize=128)
def process_header(header_line):
    # a typical header line
    # "#L N  Epoch  Energy  mono  monoE  undE ..."
    header = header_line[3:].strip()
    if re.match(r'.* Energy ', header):
        dset_type = "Energy"
    elif re.match(r'.* laserd ', header):
        dset_type = "laserd"
    else:
        raise ValueError("Unknown dataset type")
    
    labels = header.split()
    labels_mask = np.ones(len(labels), dtype=bool)
    record = []
    matches = [TRXAS_PATTERN.match(col) for col in labels]
    for index, match in enumerate(matches):
        if match:
            labels_mask[index] = False
            record.append(tuple(map(int, match.groups())))
    labels = [labels[n] for n in range(len(labels)) if labels_mask[n]]

    record = np.array(record)
    # np.savetxt('record.txt', record, fmt='%d')
    c_min, o_min, b_min = record.min(axis=0)
    c_max, o_max, b_max = record.max(axis=0)

    assert c_min == 0 and o_min == 0 and b_min == 0, "min index must be 0"
    shape = (c_max + 1, o_max + 1, b_max + 1)
    index = record[:, 0] * shape[1] * shape[2] + \
            record[:, 1] * shape[2] + record[:, 2]
    payload_mask = np.zeros(np.prod(shape), dtype=bool)
    payload_mask[index] = True 
    return dset_type, shape, labels, labels_mask, payload_mask


def fix_incomplete_dataset(payload_mask, shape, xas_data):
    """
    Fix incomplete dataset by removing the incomplete part. It's used when the
    dataset is not complete, i.e., the number of bunches in the last orbital
    is less than the number of bunches in the previous orbital. This function
    will remove the incomplete part and return the fixed dataset and the new
    shape.

    Parameters
    ----------
    payload_mask : np.ndarray
        The mask of the payload.
    shape : tuple
        The shape of the dataset when it's a complete dataset.
    xas_data : np.ndarray
        The dataset to be fixed, the incomplete part is filled with np.nan.
    
    Returns
    -------
    xas_data : np.ndarray
        The fixed dataset.
    new_shape : tuple
        The new shape of the dataset.
    """
    total_bunches = np.sum(payload_mask)
    mask = np.zeros((shape[0], shape[1], shape[2]), dtype=bool)
    effective_orbital = total_bunches // (shape[0] * shape[2])
    new_shape = (shape[0], effective_orbital, shape[2])
    mask[:, 0:effective_orbital] = True
    xas_data = xas_data[:, mask.reshape(-1)]
    return xas_data, new_shape


class TrXASDataset:
    def __init__(self, fname, ignore_incomplete=True):
        self.fname = fname
        with open(fname, 'r') as f:
            for line in f:
                if line.startswith('#L '): # Header line
                    dset_type, shape, labels, labels_mask, payload_mask = process_header(line)
                    break
        data = np.loadtxt(fname, comments='#', dtype=np.float32, delimiter='\t')
        self.num_energys = data.shape[0]
        self.labels = labels
        self.meta_data = data[:, labels_mask]
        self.dset_type = dset_type
        self.energy = self.get('Energy')

        xas_part = data[:, ~labels_mask]
        # fill the missing data with NaN, create a whole dataset
        xas_full = np.full((self.num_energys, np.prod(shape)), np.nan)
        xas_full[:, payload_mask] = xas_part
        if ignore_incomplete and np.prod(shape) != np.sum(payload_mask):
            # fix the incomplete dataset and remove all nan items
            xas_full, shape = fix_incomplete_dataset(payload_mask, shape, xas_full)

        self.shape = shape
        self.xas_data = xas_full
        # self.normalize()
    
    def get_energy_vs_time(self, channel=0):
        xas_full = self.xas_data.reshape(self.num_energys, self.shape[0], -1)
        return xas_full[:, channel]
    
    def get(self, label):
        index = self.labels.index(label)
        return self.meta_data[:, index]
    
    def get_temporal_coordinates(self, index):
        bunch = index % self.shape[0]
        orbital = index // self.shape[0]
        return (orbital, bunch)

    def normalize(self, repeat_rate=0):
        acquire_time = self.get('Seconds')
        xas_data = self.xas_data
        if repeat_rate > 0:
            offset = xas_data / (repeat_rate * acquire_time)
            xas_data = -np.log(1.0 - offset)

        xas_data = xas_data.reshape(self.num_energys, *self.shape)          # (rows, channel, orbital, bunch)
        ortial_mean_ch0 = np.nanmean(xas_data[:, 0], axis=1)                #  rows x bunch 
        xas_data[:, 1:] /= ortial_mean_ch0[:, np.newaxis, np.newaxis, :]    # normalize other channels
        self.xas_data = xas_data.reshape(self.num_energys, -1)
        self.normalized = True

    def plot(self, channel=0, orbital=0, bunch=0):
        num_channels = self.shape[0]
        fig, ax = plt.subplots(1, num_channels, figsize=(4 * num_channels, 3))
        xas_data = self.xas_data.reshape(self.num_energys, *self.shape)
        extent=(self.energys[0], self.energys[-1], 0, np.prod(self.shape[1:]))

        for i in range(num_channels):
            ax[i].imshow(xas_data[:, i].reshape(self.num_energys, -1).T, aspect='auto', extent=extent)
            ax[i].set_title(f'Channel {i}')
            ax[i].set_xlabel('Energy (keV)')
            ax[i].set_ylabel('XAS')
        plt.show()

    def process_energy(self, fileout, trig_index=1820, pre_avg_orbitals=5, 
                       aft_avg_bunches=11, n_pnt=17, do_perbunch=True):
        if self.dset_type != "Energy":
            raise TypeError(f"Expect Energy scan, but the file is {self.dset_type} scan.")

        extra_cols = ["Energy"]
        header_cols = []
        header_cols.extend(extra_cols)

        for j in range(n_pnt):
            header_cols.append("b%d" % j)
            header_cols.append("b%d-diff" % j)

        data = self.xas_data.reshape(self.num_energys, self.shape[0], -1)
        num_bunches = self.shape[2]

        # average before the laser trigger, used as normalization factor
        # for the ground state
        avg_before_slice_orbit0 = slice(trig_index - pre_avg_orbitals * num_bunches, trig_index)
        new_shape = (self.num_energys, 2, pre_avg_orbitals, num_bunches)
        data_roi = data[:, 1:, avg_before_slice_orbit0].reshape(new_shape)
        back12 = np.mean(data_roi, axis=(1, 2))  # average over channel and orbital     

        # average after the laser trigger, used as the excited state 
        avg_after_slice_orbit0 = slice(trig_index, trig_index + n_pnt * aft_avg_bunches)
        new_shape = (self.num_energys, 2, n_pnt, aft_avg_bunches)
        data_roi = data[:, 1:, avg_after_slice_orbit0].reshape(new_shape)
        forward12 = np.mean(data_roi, axis=(1, 3))  # average over channel and orbital     

        if do_perbunch:
            # extract the per-bunch data
            diff = forward12 - back12[:, 0: n_pnt]
        else: 
            diff = forward12 - np.mean(back12)

        data_out = np.empty([self.num_energys, len(header_cols)])
        num_extra = len(extra_cols)
        for i, label in enumerate(extra_cols):
            data_out[:, i] = self.get(label) 
        for i in range(n_pnt):
            data_out[:, num_extra + i * 2] = forward12[:, i]
            data_out[:, num_extra + i * 2 + 1] = diff[:, i]
        if fileout:
            np.savetxt(fileout, data_out, header=' '.join(header_cols), fmt='%.6f', comments='')

    def process_laserd(self, fileout, trig_index=1820, pre_avg_orbitals=5, 
                       aft_avg_bunches=11, n_pnt=17, do_perbunch=True):
        if self.type != "laserd":
            raise Exception("Expect laserd scan, but the file is %s scan." % self.type)

        extra_cols = ["laserd"]
        header_cols = []
        header_cols.extend(extra_cols)
        header_cols.append("diff")

            
if __name__ == '__main__':
    # read_trsaxs_dataset('/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099')
    for n in range(1):
        t0 = time.perf_counter()
        dset = TrXASDataset('/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099')
        dset.normalize()
        # dset.plot()
        # dset.process_energy('test.txt')
        t1 = time.perf_counter()
        print(f"Time elapsed: {t1 - t0:.2f} seconds")